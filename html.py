from cgi import escape
from types import GeneratorType

def propstring(propname, propvalue):
  v = escape(propvalue(), 1) if callable(propvalue) else propvalue
  return propname if v is None else '%s="%s"' % (propname, v)

def no_content_tag_string(tag_name, **props):
  if props:
    propstr = ' '.join([propstring(p, v) for (p, v) in props.iteritems()])
    return '<%s %s>' % (tag_name, propstr)
  return '<%s>' % tag_name

def tag_string_with_content(tag_name, content, **props):
  return '%s%s</%s>' % (no_content_tag_string(tag_name, **props),
                        as_html(content), tag_name)

def tag_string(tag_name, content, **props):
  if content is None:
    return no_content_tag_string(tag_name, **props)
  else:
    return tag_string_with_content(tag_name, content, **props)

def as_html(thing):
  if hasattr(thing, 'as_html'): return thing.as_html()
  elif callable(thing): return as_html(thing())
  elif isinstance(thing, (list, GeneratorType)):
    return ''.join([as_html(i) for i in thing])
  else: return escape(str(thing))
  pass

# If you want to insert a literal unescaped HTML string wrap it in this
class HTMLString(str):
  def as_html(self): return self
  pass

# Hack to allow Python reserved words as properties by adding an underscore
def python_reserved_word_props_hack(props):
  for k in props:
    if k[0]=='_' or k[-1]=='_':
      props[k.strip('_')] = props[k]
      del props[k]
      pass
    pass
  return props

class Tag(object):
  def __init__(self, tag_name, *_content, **props):
    self.tag_name = tag_name
    self.content = _content[0] if _content else None
    self.props = python_reserved_word_props_hack(props)
    return    
  def as_html(self):
    return tag_string(self.tag_name, self.content, **self.props)
  __str__ = as_html
  pass

def tagType(name):
  class C(Tag):
    def __init__(self, *_content, **props):
      content = _content[0] if _content else ''
      Tag.__init__(self, name, content, **props)
      pass
    pass
  C.__name__ = name
  globals()[name] = C
  return C

tagType('IMG')
tagType('TD')
tagType('TH')
tagType('H1')
tagType('H2')
tagType('H3')
tagType('H4')

HR=Tag('HR')
BR=Tag('BR')

Link = tagType('A')
Link.__name__ = 'Link'

def link(content, *href, **props):
  if href: return Link(content, href=href[0], **props)
  else: return Link(content, **props)

def meta_refresh(time, location):
  return HTMLString('<meta http-equiv="refresh" content="%s; url=%s">' %
                    (time, location))

def stylesheet(url):
  return Tag('Link', '', rel='stylesheet', type='text/css', href=url)

class HTMLList(list):
  def as_html(self):
    return '\n'.join(as_html(i) for i in self)
  pass

def HTMLItems(*l): return HTMLList(l)

class TR(Tag):
  def __init__(self, content, **props):
    content = [item if isinstance(item, (TD,TH)) else TD(item)
               for item in content]
    Tag.__init__(self, 'TR', HTMLList(content), **props)
    pass
  pass

class Table(Tag):
  def __init__(self, content, **props):
    content = [item if isinstance(item, TR) else TR(item)
               for item in content]
    Tag.__init__(self, 'TABLE', HTMLList(content), **props)
    pass
  pass

def Button(name, onClick):
  return Tag('Input', type='button', value=name, onclick=onClick)
