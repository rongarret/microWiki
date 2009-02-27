import config
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
#  return [unicode(as_html(thing)).decode(config.unicode_encoding)]

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
content_type_header = 'text/html; charset=' + config.unicode_encoding

md_pages = { 'Start': helptext }
html_pages = {}

from fdict import fdict
md_pages = fdict(config.content_root)

def static(req):
  return HTMLString(open(req.environ['selector.vars']['file']).read())

def start(req):
  req.redirect('/view/Start')

def generate_html(md):
  umd = unicode(md, config.unicode_encoding)
  html = markdown.markdown(umd, ['wikilink(base_url=,end_url=)'])
  return html.encode(config.unicode_encoding)

def view(req):
  req.res.headers['Content-type'] = content_type_header
  name = req.environ['selector.vars']['page']
  md = md_pages.get(name)
  if md:
    return HTMLItems(link(H2('Edit'), '/edit/%s' % name), HR,
                     HTMLString(generate_html(md)))
  else:
    # Page not found
    l = [name, ' not found. ', link('Create it', '/edit/%s' % name)]
    r = req.environ.get('HTTP_REFERER') or req.environ.get('HTTP_REFERRER')
    if r: l.append(HTMLItems(' or ', link('cancel', r)))
    return HTMLItems(*l)
  pass

def edit(req):
  req.res.headers['Content-type']='text/html'
  name = req.environ['selector.vars']['page']
  md_content = md_pages.get(name) or '# %s\n\nNew page' % name
  d = { 'name':name, 'md_content':md_content, 'spath':spath,
        'helptext': helptext }
  return HTMLString(template % d)

def post(req):
  name = req.environ['selector.vars']['page']
  md_pages[name] = getformslot('content')
  return req.redirect('/view/%s' % name)
