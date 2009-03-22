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
  s.add('/view/{page}/{revision}', GET=view)
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

def md2html(md):
  umd = unicode(md, config.unicode_encoding)
  html = markdown.markdown(umd, ['wikilink(base_url=,end_url=)'])
  return html.encode(config.unicode_encoding)

def view(req):
  req.res.headers['Content-type'] = content_type_header
  name = req.environ['selector.vars']['page']
  rev = req.environ['selector.vars'].get('revision')
  if rev:
    # View a particular revision
    md = md_pages.get('%s~%s' % (name, rev))
    if not md: return ['%s revision %s not found' % (name, rev)]
    return ['%s revision %s ' % (name, rev),
            link('(back)', '/view/%s' % name),
            HR, HTMLString(md2html(md))]
  # View the latest revision, with options to edit or view previous revs
  md = md_pages.get(name)
  if md:
    l = [name, ' | ', link('EDIT', '/edit/%s' % name)]
    revs = md_pages.revisions(name)
    if revs:
      l.append(' | Previous versions: ')
      l.extend([link(str(i), '/view/%s/%s' % (name, i))
                for i in range(1, revs+1)])
      pass
    l.append(HR)
    l.append(HTMLString(md2html(md)))
    return HTMLItems(*l)
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
