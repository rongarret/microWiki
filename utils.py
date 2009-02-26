
from html import *
import threading
import signal, os

threadvars = threading.local()

def add_cookie(req, cookie):
  req.res.headers.add_header(*tuple(str(cookie).split(': ', 1)))

def no_cache(req):
  req.res.headers.add_header('cache-control','no-cache')

def lines(*l):
  result=[]
  for i in l:
    result.append(i)
    result.append(BR)
  return HTMLList(result)

def rpath(path): return threadvars.env['TOP_LEVEL_PATH']+path

def path_to_current_page():
  env = threadvars.req.environ
  return env['SCRIPT_NAME'] + env['PATH_INFO']

def theForm(): return threadvars.req.form

def getformslot(name): return theForm().get(name)

def reset(req):
  if req.environ.get('mod_wsgi.process_group'):
    os.kill(os.getpid(), signal.SIGINT)
    pass
  return meta_refresh(1,'.')

####################################
#
# EMail
#

from smtplib import SMTP

def sendmail_send_email(msg, toaddr):
  p = os.popen("/usr/sbin/sendmail -t", "w")
  p.write(msg)
  sts = p.close()
  if sts != None: raise "Sendmail status: %s" % sts
  pass

def smtp_send_email(msg, toaddr):
  try:
    s = SMTP(smtp_host)
    s.sendmail(smtp_user, [toaddr], msg)
    s.quit()
    pass
  except:
    pass
  pass

try:
  (smtp_host, smtp_user)
  send_email = smtp_send_email
except:
  send_email = sendmail_send_email
  pass
