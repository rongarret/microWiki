import os, os.path, weakref, logging

logging.basicConfig()
log = logging
logging.getLogger().setLevel(logging.INFO)

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
    log.info('Reading %s' % self.filename)
    try:
      self.last_write = os.stat(self.filename)[8]
      self._content = open(self.filename).read()
    except: self._content = None
    if self.new_content and self.new_content != self._content:
      log.warn('Content conflict for %s' % file.filename)
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
      log.info('Writing %s' % self.filename)
      open(self.filename, 'w').write(self.new_content)
      self._content = self.new_content
      self.new_content = None
      self.last_write = os.stat(self.filename)[8]
      pass
    pass

  pass
