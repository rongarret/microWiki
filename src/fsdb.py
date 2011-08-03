# FSDB - File System Data Base
#
# FSDB is a simple key-value store that stores items in files whose
# names are the keys.  Another way to think of FSDB is as an abstraction
# layer on top of a filesystem.  The main advantage of FSDB is that it
# will work anywhere.
#

# Remain backwards-compatible with Python 2.5 for now
from __future__ import with_statement

import os, os.path

class fsdb(object):
  
  def __repr__(self):
    return '<fsdb at %s>' % self.rootpath

  def __init__(self, rootpath, create=False, serializer=None):
    self.rootpath = rootpath
    self.serializer = serializer  # A tuple (serializer, deserializer)
    if not os.path.exists(rootpath) and create: os.makedirs(rootpath)
    pass

  def path(self, key):
    return '%s/%s' % (self.rootpath, key)

  def __getitem__(self, key):
    if self.has_key(key):
      with open(self.path(key)) as f:
        r = f.read()
        if self.serializer: r = self.serializer[1](r)
        return r
      pass
    else: raise KeyError, key
    pass
  
  def __setitem__(self, key, value):
    with open(self.path(key), 'w') as f:
      if self.serializer: value = self.serializer[0](value)
      f.write(value)
      pass
    pass

  def __delitem__(self, key):
    if self.has_key(key): os.remove(self.path(key))
  
  def has_key(self, key):
    return os.path.exists(self.path(key))
  
  def keys(self):
    return os.listdir(self.rootpath)

  def get(self, key, default=None):
    return self[key] if self.has_key(key) else default
  
  pass

# Wrap a dbm-style db with a serializer/deserializer
class sddb(object):
  
  def __init__(self, db, serializer, deserializer):
    self.db = db
    self.serializer = serializer
    self.deserializer = deserializer
    pass
  
  def __getitem__(self, key):
    return self.deserializer(self.db[key])
  
  def __setitem__(self, key, value):
    self.db[key] = self.serializer(value)
    pass
  
  def __delitem__(self, key):
    del self.db[key]
  
  def has_key(self, key):
    return self.db.has_key(key)
  
  def keys(self):
    return self.db.keys()
  
  def close(self):
    return self.db.close()
  
  def get(self, key):
    return self[key] if self.has_key(key) else None

  def __len__(self):
    return len(self.db)

  def sync(self):
    self.db.sync()

  pass

# PDB - dbm database with pickle as a serializer

import cPickle

def pdb(db):
  return sddb(db, cPickle.dumps, cPickle.loads)
