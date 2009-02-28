import os, filecmp, codecs
from glob import glob

'''
A dictionary-like class with a file-based backing store and simlpe revision
tracking.
'''

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
  
  def store(self, path, content):
#    codecs.open(path, encoding='utf-8', mode='w').write(content)
    open(path, 'w').write(content)
    pass

  def revisions(self, key):
    f1 = self.path(key)
    return max([int(p.split('~')[1]) for p in glob('%s~*' % f1)] or [0])
  
  def revise(self, key, content):
    f1 = self.path(key)
    try:
      size = os.stat(f1).st_size
    except OSError:
      self.store(f1, content)  # File doesn't exist, create it
      return
    # Don't revise if content unchanged
    if size == len(content) and open(f1).read() == content: return
    # Get the next revision number
    i = self.revisions(key)
    os.rename(f1, self.path('%s~%s' % (key, i+1)))
    self.store(f1, content)
    pass
  
  def __getitem__(self, key):
    if not dict.has_key(self, key):
#      self[key] = codecs.open(self.path(key), encoding='utf-8').read()
      self[key]=open(self.path(key)).read()
      pass
    return dict.__getitem__(self, key)

  def __setitem__(self, key, content):
    dict.__setitem__(self, key, content)
    self.revise(key, content)
    pass
  pass
