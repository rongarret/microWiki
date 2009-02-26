#!/usr/bin/env python2.5
"""yaro - Yet Another Request Object (for WSGI)

A simple but non-restrictive abstraction of WSGI for end users.

(See the docstrings of the various functions and classes.)

Copyright (C) 2006-2007 Luke Arno - http://lukearno.com/

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to:

The Free Software Foundation, Inc., 
51 Franklin Street, Fifth Floor, 
Boston, MA  02110-1301, USA.

Luke Arno can be found at http://lukearno.com/

"""

import urllib
import cgi
import mimetypes
import Cookie
from cStringIO import StringIO

from wsgiref import headers, util


class URI(object):
    """URI info from a WSGI environ."""

    def __init__(self, environ):
        """Just pass in environ to populate."""
        self.scheme = environ['wsgi.url_scheme']
        if environ.get('HTTP_HOST'):
            self.host = environ['HTTP_HOST']
            if ':' in self.host:
                self.host, self.port = self.host.split(':')
            else:
                if self.scheme == 'http':
                    self.port = '80'
                else:
                    self.port = '443'
        else:
            self.host += environ['SERVER_NAME']
            self.port += environ['SERVER_PORT']
        self.script = environ.get('SCRIPT_NAME', '')
        self.path = environ.get('PATH_INFO', '')
        self.query = environ.get('QUERY_STRING', '')

    def __call__(self, path=None, with_qs=False):
        """Complete URI string with optional query string and path.
        
        path=None and will default to self.path (from PATH_INFO)
        with_qs=False and requests inclusion or not of query string.

        This is handy for doing redirects within your application
        or generating forms or links or other URI related things.
        """
        if path is None:
            path = self.path
        if path == '':
            uri = self.application_uri()
        elif path[0:1] != '/':
            uri = self.application_uri()
            uri = '/'.join((uri + self.path).split('/')[:-1])
            while path[:3] == '../':
                uri = '/'.join(uri.split('/')[:-1])
                path = path[3:]
            path = '/' + path
        else:
            uri = self.server_uri()
        uri += urllib.quote(path)
        if with_qs and self.query:
            uri += '?' + self.query
        return uri

    def server_uri(self):
        """URI of server with no script_name or path_info or query_string."""
        uri = self.scheme + '://' + self.host
        if self.scheme + self.port not in ('http80', 'https443'):
            uri += ':' + self.port
        return uri

    def application_uri(self):
        """URI up to and including script_name."""
        return self.server_uri() + urllib.quote(self.script)


class Request(object):
    """Yet another request object (for WSGI), as advertised."""

    # all the expected members other than res and start_response_called
    # these are the attrs which we do not want to cache
    _volitile_attrs = ['__class__',
                       '__delattr__',
                       '__dict__',
                       '__doc__',
                       '__getattr__',
                       '__getattribute__',
                       '__hash__',
                       '__init__',
                       '__module__',
                       '__new__',
                       '__reduce__',
                       '__reduce_ex__',
                       '__repr__',
                       '__setattr__',
                       '__str__',
                       '__weakref__',
                       '_load_body',
                       '_load_cookie',
                       '_parse_form',
                       '_parse_query',
                       '_start_response',
                       'content_length',
                       'content_type',
                       'environ',
                       'exc_info',
                       'extra_props',
                       'forward',
                       'load_prop',
                       'method',
                       'query',
                       'redirect',
                       'start_response',
                       'uri',
                       'wsgi_forward']

    def save_to_environ(self):
        """Save values of attrs in environ.
        
        Fields in ._volitile_attrs and .extra_props are _not_
        persisted to environ.
        """
        dct = self.environ.get('yaro.cached_attrs', {})
        for attr in dir(self):
            if attr not in (self._volitile_attrs 
                             + [p[0] for p in self.extra_props or []]):
                dct[attr] = getattr(self, attr)
        self.environ['yaro.cached_attrs'] = dct

    def load_from_environ(self):
        """Load values of attrs cached in environ.
        
        Fields in ._volitile_attrs and .extra_props are _not_
        persisted to environ.
        """
        self.__dict__.update(self.environ.get('yaro.cached_attrs', {}))

    def __init__(self, environ, start_response, extra_props=None):
        """Set up the various attributes."""
        self.environ = environ
        self._start_response = start_response
        self.start_response_called = False
        self.method = environ['REQUEST_METHOD']
        self.content_type = environ.get('CONTENT_TYPE', '')
        self.content_length = environ.get('CONTENT_LENGTH', '')
        self.uri = URI(environ)
        self.res = Response(self.uri())
        self._parse_query()
        self.extra_props = extra_props
        if extra_props is not None:
            for prop_spec in extra_props:
                self.load_prop(*prop_spec)
        self.exc_info = None
        self.load_from_environ()
        self.save_to_environ()

    def start_response(self, *a, **kw):
        """Wrap the real start_response and set flag when called.
        
        This provides a means to prevent the real start_response from 
        getting called more than once.

        The flag is self.start_response_called = True|False.
        """
        self.start_response_called = True
        return self._start_response(*a, **kw)

    def load_prop(self, attr_name, key, default=None):
        """Add an arbitrary property."""
        if isinstance(key, str):
            value = self.environ.get(key, default)
        else:
            value = key(self.environ)
        setattr(self, attr_name, value)

    def forward(self, app):
        """Forward the request to another Yaro compatible handler."""
        return app(self)

    def wsgi_forward(self, wsgiapp):
        """Forward the request to a WSGI compatible handler."""
        self.save_to_environ()
        return wsgiapp(self.environ, self.start_response)

    def __getattr__(self, attr):
        """Support lazy loading of form or body."""
        if attr == 'form' and not 'form' in self.__dict__:
            self._parse_form()
        elif attr == 'body' and not 'body' in self.__dict__:
            self._load_body()
        elif attr == 'cookie' and not 'cookie' in self.__dict__:
            self._load_cookie()
        return self.__dict__[attr]

    def _parse_query(self):
        """Populate a dictionary in self.query from the querystring.
        
        The dictionary created will have strings or lists of strings
        as its values.
        
        If you have a parameter like ?foo[]=bar then 
        self.query['foo'] == ['bar'] ('bar' will be in a list even if 
        it has only one member). The key will be 'foo'.

        In other words, this is a way to indicate that you want a 
        list and avoid boilerplate.

        When a name does not end in brackets, you will end up with a 
        list only if there is more than one parameter by that name.

        If 'foo[]' and 'foo' are both used as input names, they will 
        step on each other. Use one or the other.
        """
        qu = cgi.parse_qs(self.uri.query)
        query = {}
        for key, value in qu.iteritems():
            if key.endswith('[]'):
                if not isinstance(value, list):
                    value = [value]
                query[key[:-2]] = value
            else:
                if isinstance(value, list) and len(value) == 1:
                    value = value[0]
                query[key] = value
        self.query = query

    def _parse_form(self):
        """Populate a dictionary in self.form from webform data.
        
        The dictionary created will have strings, cgi.FieldStorage 
        objects (used for file uploads) or lists of strings and/or 
        cgi.FieldStorage objects as its values.
        
        If your form data has an field named "foo[]", its value 
        will be found in self.form in a list even if it has only 
        one member. The key will be 'foo'.

        In other words, this is a way to indicate that you want a
        list and avoid boilerplate.

        When a name does not end in brackets, you will end up with 
        a list only if there is more than one field by that name.

        If 'foo[]' and 'foo' are both used as input names, they 
        will step on each other. Use one or the other.
        """
        form = {}
        clen = self.environ.get('CONTENT_LENGTH', 0)
        if clen:
            sio = StringIO(self.environ['wsgi.input'].read(int(clen)))
            fs = cgi.FieldStorage(fp=sio,
                                  environ=self.environ,
                                  keep_blank_values=True) 
            sio.seek(0)
            self.environ['wsgi.input'] = sio
            for key in fs:
                value = fs[key]
                if key.endswith("[]"):
                    if not isinstance(value, list):
                        value = [value]
                    key = key[:-2]
                if isinstance(value, list):
                    newvalue = []
                    for v in value:
                        if v.filename:
                            newvalue.append(v)
                        else:
                            newvalue.append(v.value)
                    form[key] = newvalue
                else:
                    if value.filename is None:
                        value = value.value
                    form[key] = value
        self.form = form

    def _load_body(self):
        """Set self.body with the raw body of the request."""
        clen = self.environ.get('CONTENT_LENGTH', 0)
        if clen:
            self.body = self.environ['wsgi.input'].read(int(clen))
        else:
            self.body = ""

    def _load_cookie(self):
        """Set self.cookie with a populated Cookie.SimpleCookie."""
        self.cookie = Cookie.SimpleCookie()
        self.cookie.load(self.environ.get('HTTP_COOKIE', ''))

    def redirect(self, location, permanent=False):
        """Set the location header and status."""
        self.res.headers['Location'] = location
        if permanent is True:
            self.res.status = "301 Moved Permanently" 
        else:
            self.res.status = "302 Found"


class Response(object):
    """Hold on to info about the response to a request."""

    def __init__(self, uri):
        """Set up various useful defaults."""
        self._headers = []
        self.headers = headers.Headers(self._headers)
        guess = mimetypes.guess_type(uri)[0]
        self.headers['Content-Type'] = guess or 'text/html'
        self.status = '200 OK'
        self.body = ""


class Yaro(object):
    """WSGI wrapper for something that takes and returns Request."""

    def __init__(self, app, extra_props=None):
        """Take the thing to wrap."""
        self.app = app
        self.extra_props = extra_props

    def __call__(self, environ, start_response):
        """Create Request, call thing, unwrap results and respond."""
        req = Request(environ, start_response, self.extra_props)
        body = self.app(req)
        req.save_to_environ()
        if body is None:
            body = req.res.body
        if not req.start_response_called:
            req.start_response(req.res.status, req.res._headers, req.exc_info)
            req.start_response_called = True
        if isinstance(body, str):
            return [body]
        elif isiterable(body):
            return body
        else:
            return util.FileWrapper(body)


class OYaro(object):
    """WSGI wrapper for something that takes and returns Request.
    
    For use with bound methods (things that need a reference to the
    instance of which they are a member when called).
    """

    def __init__(self, app, extra_props=None):
        """Take the thing to wrap."""
        self.app = app
        self.extra_props = extra_props

    def __call__(self, instance, environ, start_response):
        """Create Request, call thing, unwrap results and respond."""
        req = Request(environ, start_response, self.extra_props)
        body = self.app(instance, req)
        req.save_to_environ()
        if body is None:
            body = req.res.body
        if not req.start_response_called:
            req.start_response(req.res.status, req.res._headers, req.exc_info)
            req.start_response_called = True
        if isinstance(body, str):
            return [body]
        elif isiterable(body):
            return body
        else:
            return util.FileWrapper(body)


def oYaro(extra_props=None):
    """Decorate a bound method so that it calls an OYaro instance."""
    def oy_decorator(fn):
        oy = OYaro(fn, extra_props)
        def newfn(self, environ, start_response):
            return oy(self, environ, start_response)
        newfn.__name__ = fn.__name__
        newfn.__dict__ = fn.__dict__
        newfn.__doc__ = fn.__doc__
        return newfn
    return oy_decorator


def isiterable(it):
    """Return True if 'it' is iterable else return False."""
    try:
        iter(it)
    except:
        return False
    else:
        return True


#  'start_response_called', 


if __name__ == '__main__':

    import code
    
    from wsgiref.simple_server import make_server

    def foo(req):
        #req.res.body = 'Hello, World!'
        sc = Cookie.SimpleCookie(); sc['mycookie'] = 'cookieval'
        req.res.headers.add_header(*tuple(str(sc).split(': ', 1)))
        code.interact(local=locals(), banner="%s: %s" % (req.method, req.uri()))
        if req.uri.path.endswith('.rdr'):
            req.redirect('../proudhon.txt')
        elif req.uri.path.endswith('.fwd'):
            return req.forward(bar)
        elif req.uri.path.endswith('.wsgi'):
            return req.wsgi_forward(baz)
        else:
            req.res.body = req.uri()

    def bar(req):
        return "Hello Bar"

    def baz(environ, start_response):
        start_response("201 Created", [])
        return ['Baz here.']

    def boing(req):
        req.stuff = 'This is stuff you should see.'
        return req.wsgi_forward(Yaro(zoink))

    def zoink(req):
        return req.stuff

    class OYaroTestApp(object):
        @oYaro()
        def hi(self, req):
            return "Hi, my name is %s" % self.__class__.__name__

    try:
        make_server('localhost', 9999, OYaroTestApp().hi).serve_forever()
    except KeyboardInterrupt, ki:
        print 'I said "Good day!"'
