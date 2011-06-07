
# Revision Control store

import cPickle as pickle

class rcstore(object):

  HTML = 'html'
  MARKDOWN = 'mrk'
  METADATA = 'mtd'
  REVISION = 'rev'
  
  def __init__(self, db = {}):
    self.db = db
    pass

  def latest_revision(self, name):
    return int(self.db.get('%s.%s' % (name, rcstore.REVISION), 0))

  def get(self, name, type, rev=None):
    rev = rev or self.latest_revision(name)
    return self.db.get('%s~%s.%s' % (name, rev, type))
  
  def store(self, name, markdown, html, metadata):
    rev = self.latest_revision(name)
    if rev:
      old_markdown = self.get(name, self.MARKDOWN)
      if markdown == old_markdown: return # Don't store content if unchanged
      pass
    rev = rev + 1
    self.db['%s~%s.%s' % (name, rev, self.MARKDOWN)] = markdown
    self.db['%s~%s.%s' % (name, rev, self.HTML)] = html
    self.db['%s~%s.%s' % (name, rev, self.METADATA)] = pickle.dumps(metadata)
    self.db['%s.%s' % (name, self.REVISION)] = str(rev)
    pass

  pass
