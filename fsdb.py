# FSDB - File System Data Base
#
# FSDB is a simple key-value store that stores items in files whose
# names are the keys.  Another way to think of FSDB is as an abstraction
# layer on top of a filesystem.  The main advantage of FSDB is that it
# will work anywhere.
#

from __future__ import with_statement

import os, os.path

class fsdb(object):

  def __repr__(self):
    return '<fsdb at %s>' % self.rootpath

  def __init__(self, rootpath, create=False):
    self.rootpath = rootpath
    if not os.path.exists(rootpath) and create: os.makedirs(rootpath)
    pass

  def path(self, key):
    return '%s/%s' % (self.rootpath, key)

  def __getitem__(self, key):
    if self.has_key(key):
      with open(self.path(key)) as f:
        return f.read()
      pass
    else: raise KeyError, key
    pass
  
  def __setitem__(self, key, value):
    with open(self.path(key), 'w') as f:
      f.write(value)
      pass
    pass

  def __delitem__(self, key):
    os.remove(self.path(key))
  
  def has_key(self, key):
    return os.path.exists(self.path(key))
  
  def keys(self):
    return os.listdir(self.rootpath)

  def get(self, key, default=None):
    return self[key] if self.has_key(key) else default
  
  pass


# Like fsdb except that it pickles its contents so it can store any
# object, not just strings
#

import cPickle as pickle

class pfsdb(fsdb):

  def __getitem__(self, key):
    if self.has_key(key):
      with open(self.path(key)) as f:
        return pickle.load(f)
      pass
    else: raise KeyError, key
    pass

  def __setitem__(self, key, value):
    with open(self.path(key), 'w') as f:
      pickle.dump(value, f)
      pass
    pass

  pass

    
