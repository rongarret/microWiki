from __future__ import with_statement

import Cookie
import threading
import os
from cgi import escape as html_escape
from yaro import Yaro
from config import unicode_encoding

content_type = 'text/html; charset=' + unicode_encoding

threadvars = threading.local()

# Set up a standard threadvar environment so we don't have to keep passing
# REQ around all over the place
#
def threadvars_wrap(app):
  def wrap(req):
    threadvars.req = req
    threadvars.env = req.environ
    threadvars.tlp = req.environ['SCRIPT_NAME'] # Top Level Path
    threadvars.form = req.query or req.form
    return app(req)
  return wrap

def getformslot(k): return threadvars.form.get(k)

def getcookie(k):
  c = threadvars.req.cookie.get(k)
  return c.value if c else None

def setcookie(k, v, path=None):
  threadvars.req.res.headers.add_header(
    "Set-cookie", '%s=%s ; path=%s' % (k, v, path or threadvars.tlp or '/'))

def getselectorvar(v):
  # See http://wsgi.org/wsgi/Specifications/routing_args
  return threadvars.req.environ['wsgiorg.routing_args'][1][v]

# mpath = Munged path, prepend the local applicaiton path
# Could probably use a better name
#
def mpath(path):
  return threadvars.tlp + path

def forward(url, delay=0, absolute=False):
  return threadvars.req.redirect(url if absolute else mpath(url))

from html import *

# Internal link, prepend application path
def ilink(content, url):
  return link(content, mpath(url))

def html_wrap(app):
  def wrap(req):
    req.res.headers['Content-type'] = content_type
    return [as_html(app(req))]
  return wrap

stdwrap = lambda app: Yaro(html_wrap(threadvars_wrap(app)))

from selector import Selector

# consume_path must be false as long as TLP is captured inside Selector
#
app = Selector(consume_path=False)

pages = []

# Page decorator
def page(path, methods=['GET','POST']):
  def wrap(f):
    app.add(path, **dict(((m, f) for m in methods)))
    # Selector adds new paths to the end of the search list, but we want
    # it at the beginning to allow incremental development.
    app.mappings.insert(0, app.mappings.pop())
    pages.insert(0, (path, app.mappings[0]))
    return f
  return wrap

from urllib import urlopen
from contextlib import closing

def urlget(url):
  with closing(urlopen(url)) as f:
    return f.read()
  pass

# @method decorator
def method(cls):
  return lambda f: setattr(cls, f.func_name, f)

def prefix_equal(s1, s2):
  l = min(len(s1), len(s2))
  return s1[:l]==s2[:l]

def reset(req):
  if req.environ.get('mod_wsgi.process_group'):
    os.kill(os.getpid(), signal.SIGINT)
    pass
  return meta_refresh(1,'.')

####################################
#
# EMail
#

from smtplib import SMTP

def sendmail_send_email(msg, toaddr):
  p = os.popen("/usr/sbin/sendmail -t", "w")
  p.write(msg)
  sts = p.close()
  if sts != None: raise "Sendmail status: %s" % sts
  pass

def smtp_send_email(msg, toaddr):
  try:
    s = SMTP(smtp_host)
    s.sendmail(smtp_user, [toaddr], msg)
    s.quit()
    pass
  except:
    pass
  pass

try:
  (smtp_host, smtp_user)
  send_email = smtp_send_email
except:
  send_email = sendmail_send_email
  pass

##################################

import hashlib, base64

def make_session_id():
  return base64.b32encode(hashlib.sha1(open('/dev/random').read(20)).digest())
