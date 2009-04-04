import os, os.path

class fsdb(object):

  def __repr__(self): return '<fsdb at %s>' % self.rootpath

  def __init__(self, rootpath, create=False):
    self.rootpath = rootpath
    if not os.path.exists(rootpath) and create: os.makedirs(rootpath)
    pass

  def path(self, key): return '%s/%s' % (self.rootpath, key)

  def __getitem__(self, key):
    if self.has_key(key): return open(self.path(key)).read()
    else: raise KeyError, key

  def __setitem__(self, key, value): open(self.path(key), 'w').write(value)

  def has_key(self, key): return os.path.exists(self.path(key))

  def keys(self): return os.listdir(self.rootpath)

  def get(self, key, default=None):
    return self[key] if self.has_key(key) else default
  
  pass

