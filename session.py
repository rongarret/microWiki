
import datetime, Cookie
from base64 import b32encode
from utils import add_cookie
from html import Tag, link

def path_info(req):
  env = req.environ
  return (env['TOP_LEVEL_PATH'], env['SCRIPT_NAME'], env['PATH_INFO'])

def munge_path(req, dest):
  tl,sn,pi = path_info(req)
  return tl + dest + sn[len(tl):] + pi

def munge_path1(req, dest):
  tl,sn,pi = path_info(req)
  return tl + dest + pi

def new_session_id(): return b32encode(open('/dev/urandom').read(5))

class Session(object):
  def __init__(self):
    self.message = None
    self.user = None
    self.created = datetime.datetime.now()
    pass
  def get_message(self):
    m = self.message
    self.message = None
    return m
  pass

sessions={}
def store_session(session): sessions[session.sid] = session

def get_session(env):
  try: sid=Cookie.SimpleCookie(env.get("HTTP_COOKIE",""))['sid'].value
  except KeyError: return None
  if sessions.has_key(sid): return sessions[sid]
  session = Session()
  session.ip = env['REMOTE_ADDR']
  session.sid = sid
  store_session(session)
  return session

def set_cookie(req):
  sc = Cookie.SimpleCookie()
  sc['sid'] = new_session_id()
  sc['sid']['path'] = '/'
  add_cookie(req, sc)
  return req.redirect(munge_path1(req, '/check-cookie'))

def check_cookie(req):
  if req.session: return req.redirect(munge_path1(req, ''))
  return [Tag('H3','Cookies Required'),
          'Please enable cookies and ',
          link('try again', href=munge_path1(req, '/set-cookie'))]

def session_wrap(app):
  def middleware(req):
    if req.session: return app(req)
    return req.redirect(munge_path(req, '/set-cookie'))
  return middleware

def login_wrap(app):
  def middleware(req):
    s = req.session
    if s and s.user: return app(req)
    if s:
      s.message="You have to log in before you can view that page."
      return req.redirect(munge_path(req, '/login'))
    return req.redirect(munge_path(req, '/set-cookie'))
  return middleware
