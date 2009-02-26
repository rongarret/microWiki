# Patch to fix a known bug in cgitb -- see http://bugs.python.org/issue4643

import cgitb
from cgitb import __UNDEF__,lookup

def scanvars(reader, frame, locals):
  """Scan one logical line of Python and look up values of variables used."""
  import tokenize, keyword
  vars, lasttoken, parent, prefix, value = [], None, None, '', __UNDEF__
  for ttype, token, start, end, line in tokenize.generate_tokens(reader):
    if ttype == tokenize.NEWLINE: break
    if ttype == tokenize.NAME and token not in keyword.kwlist:
      if lasttoken == '.':
        if parent is not __UNDEF__:
          
          # Bug fix here
          try:
            value = getattr(parent, token, __UNDEF__)
          except Exception:
            value = __UNDEF__
            pass
          
          vars.append((prefix + token, prefix, value))
        else:
          where, value = lookup(token, frame, locals)
          vars.append((token, where, value))
          pass
        pass
      pass
    elif token == '.':
      prefix += lasttoken + '.'
      parent = value
    else:
      parent, prefix = None, ''
      pass
    lasttoken = token
    pass
  return vars

cgitb.scanvars = scanvars
