
# This file implements code for abstract descriptions of HTML input
# forms.

import sys
import cStringIO
from cgi import escape as html_escape
from html import as_html, tagType
tagType('Input')
from html import Input
from utils import getformslot

def callWithStringOutput(f):
  stdout = sys.stdout
  w = cStringIO.StringIO()
  try:
    sys.stdout = w
    f()
  finally:
    sys.stdout = stdout
  s = w.getvalue()
  w.close()
  return s

import re
import string
quotetrans = string.maketrans('\x91\x92\x93\x94','\'\'""')

def smart_quote_translate(s):
  s = string.translate(s, quotetrans)
  s = re.sub('\xe2\x80\x9c', '"', s)
  s = re.sub('\xe2\x80\x9d', '"', s)
  s = re.sub('\xe2\x80\x98', "'", s)
  s = re.sub('\xe2\x80\x99', "'", s)
  return s

class FormInput(object):
  def as_html(self):
    return callWithStringOutput(self.render)
  pass

# Text input.  Type depends on number of rows.  1=textinput >1=textarea
# 0 = password
#
class TextInput(FormInput):
  def __init__(self, id, cols=40, rows=1, default='', maxlen=None, oneTime=0):
    self.id = id
    self.cols = cols
    self.rows = rows
    self.default = default
    self.maxlen = maxlen or cols
    self.oneTime = oneTime
    
  def render(self, val=None):
    opts = ' disabled' if (self.oneTime) else ''
    if val == None: val = self.value() or '' 
    val = html_escape(val.strip(), 1)
    if opts: print '<input type=hidden id="%s" name="%s" value="%s">' % (self.id, self.id, val)
    if self.rows > 1:
      print "<textarea id='%s' name='%s' rows=%d cols=%d%s>%s</textarea>" % \
            (self.id, self.id, self.rows, self.cols, opts, val),
    else:
      print '<input type=%s id="%s" name="%s" size=%d maxlength=%d value="%s" %s>' % \
            ('text' if self.rows==1 else 'password',
             self.id, self.id, self.cols, self.maxlen, val, opts)

  def value(self):
    v = getformslot(self.id)
    if v==None: return self.default
    if isinstance(v, str): return smart_quote_translate(v)
    if isinstance(v, long): return str(v)
    if isinstance(v, int): return str(v)
    if isinstance(v, float): return str(v)
    return self.default

class PasswordInput(TextInput):
  def __init__(self, id):
    TextInput.__init__(self, id, rows=0)
    pass
  pass

# Submit input
#
class Submit(FormInput):
  def __init__(self, label='Submit'):
    self.label = label
    return
  def as_html(self):
    return '<input type="submit" value="%s">' % self.label
  pass


# FileInput
#
def getFileItem(name):
  try:
    fileitem = form[name]
    filename = fileitem.filename
    filestream = fileitem.file
    if len(filename)<=0: return (None, None)
    return (filename, filestream)
  except:
    return (None, None)

class FileInput(FormInput):
  def __init__(self, id):
    self.id = id
  
  def as_html(self):
    return '''<input type=file id="%s" name="%s">''' % (self.id, self.id)

  def value(self):
    return getFileItem(self.id)

# Hidden inputs for carrying state around
#
class HiddenInput:
  def __init__(self, id, initial_value):
    self.id = id
    self.initial_value = initial_value
    self.override_value = None
    
  def as_html(self):
    return '<input type=hidden name="%s" id="%s" value="%s">' % \
           (self.id, self.id, self.value())
  
  def value(self):
    return self.override_value or getformslot(self.id) or self.initial_value


# An abstract class that implements selections from an enumerated list
#
default_bg_color = 'white'

class Select:
  def __init__(self, id, items, bgcolor=None, width='100%', 
               default=None, rmap=None):
    self.id = id
    self.items = items
    self.columns = 4
    self.default = default
    self.rmap = rmap    # Reverse map from id to item
    self.header = \
       '<table bgcolor=%s cellspacing=0 cellpadding=0 width=%s>' % \
       (bgcolor or default_bg_color, width)
    self.footer = '</table>\n'
    return
  
  def buttonRenderItems(self, vals, type):
    cnt = 0
    print self.header
    for item in self.items:
      if cnt % self.columns == 0: print '<tr>'
      print '<td align=right>'
      print '<input type=%s id=%s name=%s value="%s" label="%s"' % \
            (type, self.id, self.id, cnt, html_escape(str(item),1))
      if item in vals: 
        print "checked",
      print "></td><td align=left><font face=sans-serif size=-1>", item, "</font></td><td>&nbsp;</td>"
      cnt = cnt + 1
    print self.footer
    return
  
  def menuRenderItems(self, vals):
    cnt = 0
    for item in self.items:
      if hasattr(item, 'id'): cnt = item.id()
      print '<option label="%s" id="%s" value="%s" name="%s"' % \
            (item, cnt, cnt, html_escape(str(item), 1)),
      if item in vals: print "selected",
      print ">", item, '</option>'
      cnt = cnt+1
      pass
    return

  # Try to separate content from layout (incomplete)
  def buttonItems(self, selected_values, type):
    id = self.id
    buttons = []
    cnt=0
    for item in self.items:
      s = html_escape(str(item), 1)
      b = Input(s, id=id, name=id, value=cnt, type=type, label=s)
      if s in selected_values: b.props['checked']=None
      cnt=cnt+1
      buttons.append(b)
      pass
    return buttons


# Selections where only one item may be selected (i.e. radio buttons
# or ordinary menus)
#
class SingleSelect(Select):
  def buttonRender(self, val=None):
    if val == None: val = self.value() or self.default
    # NOTE: This code is in transition
#    self.buttonRenderItems([val], 'radio')
    print as_html(self.buttonItems([val], 'radio'))

  def menuRender(self, val=None):
    if val == None: val = self.value()
    print "<select id=%s name=%s>" % (self.id, self.id)
    self.menuRenderItems([val])
    print "</select>"

  def value(self):
    global form
    val = getformslot(self.id)
    if val == None: return self.default
    rmap = self.rmap or self.items
    try: return rmap[int(val)]
    except: return self.default

class RadioButtons(SingleSelect):
  def as_html(self): return callWithStringOutput(self.buttonRender)

class Menu(SingleSelect):
  def as_html(self): return callWithStringOutput(self.menuRender)

# Selections where multiple items may be selected (i.e. check boxes or
# multi-select menus (rarely used))
# 
class MultiSelect(Select):
  def buttonRender(self, vals=None):
    if vals == None: vals = self.value()
    # NOTE: This code is in transition
#    self.buttonRenderItems(vals, 'checkbox')
    print as_html(self.buttonItems(vals, 'checkbox'))

  def menuRender(self, vals=None):
    if vals == None: vals = self.value()
    print "<select id=%s name=%s multiple>" % (self.id, self.id)
    self.menuRenderItems(vals)
    print "</select>"    

  def value(self):
    global form
    val = getformslot(self.id)
    if val == None: return []
    rmap = self.rmap or self.items
    if not isinstance(val, list): return [rmap[int(val)]]
    return [rmap[int(x)] for x in val]

class CheckBoxes(MultiSelect):
  def as_html(self): return callWithStringOutput(self.buttonRender)

class MultiMenu(MultiSelect):
  def as_html(self): return callWithStringOutput(self.menuRender)

# Composite date and time input
#
import datetime
today = datetime.date.today()
tomorrow = datetime.date.fromordinal(today.toordinal()+1)
thisyear = today.year
monthnames = ['Jan','Feb','Mar','Apr','May','Jun',
              'Jul','Aug','Sep','Oct','Nov','Dec']

class DateInput(FormInput):

  def __init__(self, id, years=6, default=0):
    if isinstance(years, int): years = range(thisyear, thisyear+years)
    if default==0: default = tomorrow
    self.id = id
    self.days = Menu(id+'_day', range(1,32), default=default.day)
    self.months = Menu(id+'_month', monthnames,
                       default=monthnames[default.month-1])
    self.years = Menu(id+'_year', years, default=default.year)
    pass
  
  def render(self):
    # This hidden input is needed so that we can make dateinput a required
    # input in a StandardForm.
    print '<input type=hidden name=%s value=1>' % self.id
    print as_html(self.months), as_html(self.days), as_html(self.years)
    pass

  def value(self):
    try:
      y = int(self.years.value())
      m = self.months.items.index(self.months.value())+1
      d = int(self.days.value())
      return datetime.date(y,m,d)
    except:
      return None
    pass
  pass

class TimeInput(FormInput):
  def __init__(self, id, increment=15, default=0):
    self.id = id
    d_hour=12
    d_minute=0
    d_ampm='AM'
    if default: 
      self.default = default
      if default.hour==12:
        d_hour = 12
        d_ampm='PM'
      elif default.hour > 12:
        d_hour = default.hour-12
        d_ampm = 'PM'
      else:
        d_hour = default.hour
        d_ampm = 'AM'
    self.hour = Menu(id+'_hour', range(1,13), default=d_hour)
    self.minute = Menu(id+'_minute',
                       ['%02d' % x for x in range(0,60,increment)],
                       default='%02d' % d_minute)
    self.ampm = Menu(id+'_ampm', ['AM','PM'], default=d_ampm)
    pass

  def render(self):
    print as_html(self.hour), ':', as_html(self.minute), as_html(self.ampm)
    pass
  
  def value(self):
    try:
      return datetime.time(hour = int(self.hour.value()) % 12 +
                           ((self.ampm.value()=='PM')*12),
                           minute = int(self.minute.value()))
    except:
      return None
    pass
  pass

# Forms

from utils import threadvars

class Form():

  def __init__(self, items, method='POST', url=None, submit='Submit'):
    self.method = method
    self.url = url
    self.submit = Submit(submit)
    self.items = items
    pass

  def render(self):
    print '<form method="%s" action="%s">' % \
          (self.method, self.url or threadvars.req.uri())
    for i in self.items: print as_html(i)
    print self.submit.as_html()
    print '</form>'
    
  def as_html(self):
    return callWithStringOutput(self.render)
  
