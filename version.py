
from datetime import datetime

class version(object):

  def __init__(self, content, prev=None):
    self.prev = prev
    self.versions = prev.versions if prev else []
    self.timestamp = datetime.now()
    self.content = content
    self.versions.append(self)
    self.verno = self.versions.index(self)
    pass

  def __str__(self): return str(self.content)
  def __unicode__(self): return unicode(self.content)
  def __repr__(self):
    return '<%s version %s>' % (self.earliest().content, self.verno)
  
  def __del__(self):
    # Break possible circular references
    self.versions  = None
    self.prev = None
    self.next = None
    pass
  
  def latest(self): return self.versions[-1]
  def earliest(self): return self.versions[0]

  def next(self):
    try: return self.versions[self.verno+1]
    except IndexError: return None
    pass
  
  def prev(self):
    try: return self.versions[self.verno-1]
    except IndexError: return None
    pass

  def revise(self, content):
    if self.content == content: return self
    else: return version(content, self)
    pass
  
  pass

import weakref, os

class File(object):
  
  files = weakref.WeakValueDictionary()

  def __new__(cls, filename):
    f = cls.files.get(filename)
    if f: return f
    f = object.__new__(cls)
    cls.files[filename] = f
    return f
  
  def __init__(self, filename):
    self.filename = filename
    self.new_content = None
    self.last_write = None
    self.update()
    pass

  def update(self):
    print 'Loading'
    try:
      self.last_write = os.stat(self.filename)[8]
      self._content = open(self.filename).read()
    except: self._content = None
    if self.new_content and self.new_content != self._content:
      print 'Conflict!'
      pass
    pass

  def set_content(self, content):
    if content != self._content:
      self.new_content = content
    else:
      self.new_content = None
      pass
    pass

  def get_content(self):
    if self.new_content: return self.new_content
    try: last_write = os.stat(self.filename)[8]
    except: last_write = None
    if last_write != self.last_write: self.update()
    return self._content

  content = property(get_content, set_content)
  
  def store(self):
    if self.new_content:
      print 'Saving'
      open(self.filename, 'w').write(self.new_content)
      self._content = self.new_content
      self.new_content = None
      pass
    pass

  pass
