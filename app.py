
from wrappers import standard_wrap, tlp_wrap
from selector import Selector
from html import *
from utils import getformslot
import markdown
import re

s = Selector(wrap=standard_wrap)
application = tlp_wrap(s)
s.parser.default_pattern='segment'

import wrappers

def style(thing):
  return [str(as_html(thing))]
#  return [unicode(as_html(thing)).encode('latin-1')]

wrappers.style = style

def slashify(req):
  return req.redirect('%s/' % req.environ.get('SCRIPT_NAME'))

def init():
  s.add('', GET=slashify)
  s.add('/', GET=start)
  s.add('/view/{page}', GET=view)
  s.add('/edit/{page}', GET=edit)
  s.add('/post/{page}', POST=post)
  s.add('/static/{file}', GET=static)
  pass

template = open('uWiki.template').read()
spath = '/static'
helptext = open('markdown-ref.txt').read()

md_pages = { 'Start': helptext }
html_pages = {}

from fdict import fdict
md_pages = fdict('content/md')
html_pages = fdict('content/html')

def static(req):
  return HTMLString(open(req.environ['selector.vars']['file']).read())

def start(req):
  req.redirect('/view/Start')

def view(req):
  req.res.headers['Content-type']='text/html'
  name = req.environ['selector.vars']['page']
  content = html_pages.get(name)
  if content:
    return HTMLItems(link(H2('Edit'), '/edit/%s' % name), HR,
                     HTMLString(content))
  else:
    return HTMLItems('Page not found. ', link('Create it', '/edit/%s' % name))

def edit(req):
  req.res.headers['Content-type']='text/html'
  name = req.environ['selector.vars']['page']
  md_content = md_pages.get(name) or '# %s\n\nNew page' % name
  d = { 'name':name, 'md_content':md_content, 'spath':spath,
        'helptext': helptext }
  return HTMLString(template % d)

def post(req):
  name = req.environ['selector.vars']['page']
  md = getformslot('content')
  umd = unicode(md, 'latin-1')
  md_pages[name] = md
  c = markdown.markdown(umd, ['wikilink(base_url=,end_url=)'])
  html_pages[name] = c.encode('latin-1')
  return req.redirect('/view/%s' % name)
