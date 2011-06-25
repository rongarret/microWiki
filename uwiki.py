# coding: utf-8

from html import *
from utils import *
from auth import auth_wrap
import os, sys, datetime
import auth, config

from selector import not_found

# HORRIBLE HACK alert -- this converts ALL links to internal links,
# which at the moment they all happen to be.  But this should be changed
# at some point.
#
link = ilink

template = open('uWiki.template').read()

separator = ' | '

content_type_header = 'text/html; charset=' + config.unicode_encoding

helptext = open('markdown-ref.txt').read()  # For inclusion on editing page

auth.login_banner = HTMLString(
  '<center><br><br><h1>Welcome to μWiki!</h1><br><br>')

import fsdb
from rcstore import rcstore, pickle
content = rcstore(fsdb.fsdb(config.content_root))

# The URL for static content needs to be computed dynamically because
# don't know our application name until we're called.  This could and
# probably should be cached, but KISS for now.
#
def spath(): return mpath('/static')

def stylesheet():
  return Tag('link', rel="stylesheet", type="text/css",
             href=mpath("/static/uwiki.css"))

def init():
  try: auth.restore_state()
  except: auth.save_state()
  pass

application = app # From utils, should probably not be there

@page('/foo[/{x:any}]')
@stdwrap
def foo(req):
  return [ilink('foo','/foo'), ' TLP=[', threadvars.tlp, ']', BR,
          req.uri(), BR,
          req.uri.path, BR,
          req.uri.application_uri(), BR,
          '[%s]' % req.uri.script]

@page('/')
@stdwrap
def start(req):
  forward('/view/Start')

@page('/static/{file:any}')
@Yaro
@threadvars_wrap   # No stdwrap because that includes html_wrap
def static(req):
  filename = getselectorvar('file')
  # Close a security hole where someone passes a '..' relative
  # pathname as a url-encoded string
  if '/' in filename: return req.wsgi_forward(not_found)
  try:
    s = open('static/' + filename).read()
  except:
    return req.wsgi_forward(not_found)
  return [s]

@page('/view/{page}[/{revision}]')
@stdwrap
@auth_wrap
def view(req):
  req.res.headers['Content-type'] = content_type_header
  name = getselectorvar('page')
  rev = getselectorvar('revision')
  markdown = content.get(name, rcstore.MARKDOWN, rev)
  html = content.get(name, rcstore.HTML, rev)
  
  if rev:
    # View a particular revision
    if not markdown: return ['%s revision %s not found' % (name, rev)]
    return [Tag('b', name), ' revision ', rev, separator,
            link('BACK', '/revs/%s' % name), HR, HTMLString(html)]

  # View the latest revision, with options to edit or view previous revs
  if markdown:
    l = [stylesheet(),
         Tag('b', name), separator,
         link('EDIT', '/edit/%s' % name)]
    revs = content.latest_revision(name)
    if revs>1:
      l.extend([separator, link('OLDER VERSIONS', '/revs/' + name)])
      pass
    l.extend([separator,
              link('START', '/start'), separator,
              link('LOGOUT', '/logout'), HR, HTMLString(html)])
    return l
  # Page not found
  r = req.environ.get('HTTP_REFERER') or req.environ.get('HTTP_REFERRER') \
      or '/'
  if '~' in name or '/' in name:
    return ['Illegal Wikilink: ', name,
            '.  Wikilinks may not containt "~" or "/" characters. ',
            link('BACK', r)]
  l = [name, ' not found. ', link('CREATE IT', '/edit/%s' % name),
       ' or ', link('CANCEL', r)]
  return l

@page('/revs/{page}')
@stdwrap
@auth_wrap
def revs(req):
  page = getselectorvar('page')
  revs = content.latest_revision(page)
  if revs<2: return ['There are no previous versions of this page.']  
  l = []
  for rev in xrange(1, revs):
    mtd = pickle.loads(content.get(page, content.METADATA, rev))
    l.append(Tag('li', [link(mtd['timestamp'],
                             '/view/' + page + '/' + str(rev)),
                        ' by ', mtd['username']]))
    pass
  return [Tag('b', ['Older versions of ', page, ': ']),
          link('[BACK]', '/view/' + page),
          Tag('ol', l)]


@page('/edit/{page}')
@stdwrap
@auth_wrap
def edit(req):
  req.res.headers['Content-type']='text/html'
  name = req.environ['selector.vars']['page']
  base_version = content.latest_revision(name)
  markdown = content.get(name, rcstore.MARKDOWN) or '# %s\n\nNew page' % name
  d = { 'name' : name, 'md_content' : markdown, 'spath' : spath(),
        'base_version' : base_version, 'helptext' : helptext, 'msg' : name }
  return [HTMLString(template % d)]

@page('/post/{page}', ['POST'])
@stdwrap
@auth_wrap
def post(req):
  name = req.environ['selector.vars']['page']
  latest_version = content.latest_revision(name)
  base_version = int(getformslot('base_version'))
  if latest_version != base_version:
    return resolve(name, base_version, latest_version)
  u = req.session.user
  metadata = { 'timestamp' : datetime.datetime.now(),
               'username' : u.fb_name or u.google_name,
               'useremail' : u.email }
  content.store(name, getformslot('content'), getformslot('html'), metadata)
  return forward('/view/%s' % name)

import merge3, StringIO

def lines(s): return StringIO.StringIO(s).readlines()

merge_msg = '''Someone else has modified this page since you started editing
it. Your changes have been merged with theirs.  Please check that the results
of the merge are satisfactory and re-save the page.'''

conflict_msg = '''Someone else has modified this page since you started editing
it.  Trying to merge your changes has resulted in conflicts that cannot be
automatically resolved.  Please resolve these conflicts manually and re-save
the page.'''

def resolve(name, base_version, latest_version):
  new = getformslot('content')
  base = content.get(name, rcstore.MARKDOWN, base_version) or ''
  latest = content.get(name, rcstore.MARKDOWN, latest_version) or ''
  m = merge3.Merge3(lines(base), lines(new), lines(latest))
  mg = list(m.merge_groups())
  conflicts = 0
  for g in mg:
    if g[0]=='conflict': conflicts+=1
    pass
  merged = ''.join(m.merge_lines(
    start_marker='\n!!!--Conflict--!!!\n!--Your version--',
    mid_marker='\n!--Other version--',
    end_marker='\n!--End conflict--\n'))
  d = { 'name' : name, 'md_content' : merged, 'spath' : spath(),
        'base_version' : latest_version, 'helptext' : helptext,
        'msg' : conflict_msg if conflicts else merge_msg }
  return HTMLString(template % d)
