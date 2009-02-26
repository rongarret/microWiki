import os, codecs

class fdict(dict):

  def __init__(self, root):
    self.root = root
    pass

  def path(self, key):
    return '%s/%s' % (self.root, key)

  def has_key(self, key):
    return dict.has_key(self, key) or os.path.exists(self.path(key))

  def get(self, key):
    return self[key] if self.has_key(key) else None
  
  def __getitem__(self, key):
    if not dict.has_key(self, key):
#      self[key] = codecs.open(self.path(key), encoding='latin-1').read()
      self[key]=open(self.path(key)).read()
      pass
    return dict.__getitem__(self, key)

  def __setitem__(self, key, content):
    dict.__setitem__(self, key, content)
#    codecs.open(self.path(key), encoding='latin-1', mode='w').write(content)
    open(self.path(key), 'w').write(content)
    pass
  pass
