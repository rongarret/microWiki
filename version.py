
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
