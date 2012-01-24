# coding: utf-8

import urllib
import facebook
import datetime
from utils import *
from forms import *
from config import *

import dbhash as mydbm
from fsdb import pdb

invitations = pdb(mydbm.open(data_root + '/wikidata/invitations.db', 'c'))
sessions = pdb(mydbm.open(data_root + '/wikidata/sessions.db', 'c'))
users = pdb(mydbm.open(data_root + '/wikidata/users.db', 'c'))

def store_user(user):
  users[user.email] = user
  users.sync()
  pass

def get_users():
  return [users[k] for k in users.keys()]


login_banner = HTMLString('<center><br><br><h1>Welcome!</h1><br><br>')

# This should probably be in config
dssid_base_url = 'https://secure.dswi.net/dssid'

def getsession(session_id):
  return sessions.get(session_id)

class Invitation(object):
  def __init__(self, id, email):
    self.id = id
    self.email = email
    self.timestamp = datetime.datetime.now()
    return

  def age(self): # in hours
    dt = datetime.datetime.now() - self.timestamp
    return dt.days * 24.0 + dt.seconds/3600.0
  
  pass

class Session(object):
  def __init__(self, id):
    self.id = id
    self.user = None
    self.invitation_id = None
    return

  def store(self):
    sessions[self.id]=self
    sessions.sync()
  pass

# This could use some refactoring

class User(object):
  def __init__(self):
    self.email = None
    self.fb_name = None
    self.fb_uid = None
    self.google_name = None
    self.google_uid = None
    self.dssid_uid = None
    self.dssid_name = None
    return
  pass

def find_fb_user(fb_uid):
  for u in get_users():
    if u.fb_uid==fb_uid: return u
    pass
  return None

def find_google_user(google_uid):
  for u in get_users():
    if u.google_uid==google_uid: return u
    pass
  return None

def find_dssid_user(dssid_uid):
  for u in get_users():
    if u.dssid_uid==dssid_uid: return u
    pass
  return None

fb_preamble = '''
<head>

<script src="http://connect.facebook.net/en_US/all.js"></script>

<script>

  function fb_login() {
    FB.login(function(response) {
      // As of December 13th, 2011, the JavaScript SDK now only supports OAuth 2.0 for authentication
      if (response.authResponse) {
          document.location='check_fb_auth' + '?accessToken=' + response.authResponse.accessToken + '&userID=' + response.authResponse.userID
      }
      else { 
          alert("Login cancelled"); 
      }
    })
  }

</script>

</head>

<body>

  <div id="fb-root"></div>
  <script>
  FB.init({appId: '%(fb_app_id)s', status: true, cookie: true, xfbml: false});
  </script>
''' % {'fb_app_id' : fb_app_id}

# Add a prefix to the current URL, preserving the application component
def add_path_prefix(req, prefix):
  uri = req.uri()
  host = req.uri.server_uri()
  return mpath(prefix + uri[len(host):])

def session_wrap(app):
  def wrap(req):
    req.session_id = getcookie('session')
    if not req.session_id:
      setcookie('session', make_session_id())
      forward(add_path_prefix(req, '/check_cookie'))
      return
    req.session = getsession(req.session_id)
    if not req.session:
      forward('/lost_session')
      return
    return app(req)
  return wrap

@page('/check_cookie/{cont:any}')
@stdwrap
def check_cookie(req):
  cont = getselectorvar('cont')
  session_id = getcookie('session')
  if not session_id:
    setcookie('session', make_session_id())
    return ['Cookies are required.  Please enable cookies and ',
            ilink('try again', '/'+cont)]
  if not getsession(session_id):
    sessions[session_id] = Session(session_id)
    sessions.sync()
    pass
  forward('/'+cont)
  return

@page('/check_javascript/{cont:any}')
@stdwrap
def root(req):
  cont = '/' + getselectorvar('cont')
  return [HTMLString('''
  <html>
  <body onload='document.location="%s"'>
  <noscript>Javascript is required.  Please enable Javascript and
  <a href="%s">try again</a>.</noscript>
  </body>
  </html>
  ''' % (mpath(cont), mpath('/check_javascript' + cont)))]

@page('/lost_session')
@stdwrap
def lost_session(req):
  session_id = getcookie('session')
  if not session_id:
    setcookie('session', make_session_id())
    forward('/cookie_test/lost_session')
    return
  sessions[session_id] = Session(session_id)
  sessions.sync()
  return ['''Your login session has timed out.   Please ''',
          ilink('log in again.', '/login')]

def auth_wrap(app):
  def wrap(req):
    if not req.session.user: return forward('/login')
    return app(req)
  return session_wrap(wrap)

def admin_wrap(app):
  def wrap(req):
    if not admins: return app(req)
    if not req.session.user: return forward('/login')
    if req.session.user.email in admins: return app(req)
    return forward('/unauth')
  return session_wrap(wrap)  

@page('/check_fb_auth')
@stdwrap
@session_wrap
def check_fb_auth(req):
  uid = req.query['userID']
  user = find_fb_user(uid)
  if user:
    # User has already registered
    req.session.user = user
    req.session.store()
    forward('/start')
    return
  if not (req.session.invitation_id or req.session.user):
    # Not registered, not invited, not logged in
    forward('/unauth')
    return
  # Set up a new user
  access_token = req.query['accessToken']
  graph = facebook.GraphAPI(access_token)
  userinfo = graph.get_object("me")
  user = req.session.user
  if not user:
    if not invitations.has_key(req.session.invitation_id):
      return ['Sorry, your invitation has expired.']
    user = User()
    user.email = invitations[req.session.invitation_id].email
    req.session.user = user
    req.session.store()
    pass
  user.fb_uid = uid
  user.fb_name = userinfo['name']
  store_user(user)
  forward('/start')
  return

@page('/check_google_auth')
@stdwrap
@session_wrap
def check_google_auth(req):
  keys = threadvars.form.keys()
  d = {}
  for k in keys: d[k]=getformslot(k)
  d['openid.mode'] = 'check_authentication'
  url = 'https://www.google.com/accounts/o8/ud?' + urllib.urlencode(d)
  valid = prefix_equal(urlget(url), 'is_valid:true')
  if not valid:
    return ['Invalid login.', ilink('Try again', '/login')]
  uid = getformslot('openid.identity')
  user = find_google_user(uid)
  if user:
    # User has already registered
    req.session.user = user
    req.session.store()
    forward('/start')
    return
  if not (req.session.invitation_id or req.session.user):
    # Not registered, not invited, not logged in
    forward('/unauth')
    return
  # Set up a new user
  name = '%s %s' % (getformslot('openid.ext1.value.firstname'),
                    getformslot('openid.ext1.value.lastname'))
  user = req.session.user
  if not user:
    if not invitations.has_key(req.session.invitation_id):
      return ['Sorry, your invitation has expired.']
    user = User()
    user.email = invitations[req.session.invitation_id].email
    req.session.user = user
    req.session.store()
    pass
  user.google_uid = uid
  user.google_name = name
  store_user(user)
  forward('/start')
  return

@page('/check_dssid_auth')
@stdwrap
@session_wrap
def check_dssid_auth(req):
  url = dssid_base_url + '/verify?sid=' + getformslot('sid')
  s = urlget(url)
  if s != 'valid':
    return ['Invalid login.', BR, url, BR, s]
  uid = getformslot('uid')
  user = find_dssid_user(uid)
  if user:
    # Already registered
    req.session.user = user
    req.session.store()
    forward('/start')
    return
  if not (req.session.invitation_id or req.session.user):
    # Not registered, not invited, not logged in
    forward('/unauth')
    return
  # Set up a new user
  name = getformslot('name')
  user = req.session.user
  if not user:
    if not invitations.has_key(req.session.invitation_id):
      return ['Sorry, your invitation has expired.']
    user = User()
    user.email = invitations[req.session.invitation_id].email
    req.session.user = user
    req.session.store()
    pass
  user.dssid_uid = uid
  user.dssid_name = name
  store_user(user)
  forward('/start')  
  return

@page('/unauth')
@stdwrap
def unauth(req):
  return ['Sorry, you are not an authorized user. ',
          ilink("Try again", '/login')]

@page('/start')
@stdwrap
@auth_wrap
def start(req):
  forward('/view/Start')

@page('/logout')
@stdwrap
@session_wrap
def logout(req):
  req.session.user = None
  req.session.store()
  forward('/')
  return

@page('/login')
@stdwrap
@session_wrap
def login(req):

  openid_items = [
    ('openid.ns', 'http://specs.openid.net/auth/2.0'),
    ('openid.claimed_id',
     'http://specs.openid.net/auth/2.0/identifier_select'),
    ('openid.identity', 'http://specs.openid.net/auth/2.0/identifier_select'),
    ('openid.realm', req.uri.server_uri()),
    ('openid.return_to', req.uri('check_google_auth')),
    ('openid.mode', 'checkid_setup'),
    ('openid.ns.pape', 'http://specs.openid.net/extensions/pape/1.0'),
# Uncomment to force fresh login every time
#    ('openid.pape.max_auth_age', '0'),
    ('openid.ns.ax', 'http://openid.net/srv/ax/1.0'),
    ('openid.ax.mode', 'fetch_request'),
    ('openid.ax.required', 'firstname,lastname'),
# Uncomment to get the Google email address
#    ('openid.ax.required', 'email,firstname,lastname'),
#    ('openid.ax.type.email', 'http://schema.openid.net/contact/email'),
    ('openid.ax.type.firstname', 'http://axschema.org/namePerson/first'),
    ('openid.ax.type.lastname', 'http://axschema.org/namePerson/last')
    ]

  fb_button = Button('Log in with Facebook', 'fb_login()')
  if fb_app_id == '...': fb_button = '[Facebook login not configured]'

  google_button = Form([HiddenInput(k,v) for (k,v) in openid_items],
                       submit='Log in with Google',
                       url="https://www.google.com/accounts/o8/ud")

  dssid_button = Form([HiddenInput('url', req.uri('check_dssid_auth')),
                       HiddenInput('ri', 'name')],
                      submit='Log in with DSSID',
                      url = dssid_base_url + '/auth')
  
  return [HTMLString(fb_preamble),
          login_banner,
          dssid_button,
          google_button,
          fb_button,
          HTMLString('</body>')]

@page('/users')
@stdwrap
@auth_wrap
def show_users(req):
  l = []
  names = [u.dssid_name or u.google_name or u.fb_name for u in get_users()]
  names = [str(name) for name in names]
  names.sort()
  for name in names:
    wikilink = '/view/' + ''.join([s.capitalize() for s in name.split()])
    l.append(Tag('li', ilink(name, wikilink)))
    pass
  return [Tag('h1', 'μWiki registered users'), Tag('ul', l)]

@page('/register/{key}')
@stdwrap
def register(req):
  key = getselectorvar('key')
  invitation = invitations.get(key)
  if not invitation:
    return ['Sorry, that is not a valid invitation code.']
  if invitation.age()>invitation_timeout:
    return ['Sorry, that invitation code has expired.']
  session_id = getcookie('session')
  session = getsession(session_id)
  if not session:
    forward('/check_javascript/check_cookie/register/'+key)
    return
  session.invitation_id = key
  session.store()
  forward('/login')

import re

email_re = re.compile(r"^[a-zA-Z0-9._%-+]+\@[a-zA-Z0-9._%-]+\.[a-zA-Z]{2,}$")

invitation_email = '''To: %(addr)s
From: μWiki <μwiki@localhost>
Subject: Try μWiki

You are cordially invited to try μWiki.  Follow this link

%(url)s

to set up your account.
'''

@page('/invite')
@stdwrap
@admin_wrap
def invite(req):
  ti = TextInput('email')
  email = ti.value()
  if email and email_re.match(email):
    send_invitation(req, email)
    return ['Invitation sent.', ilink("Send another", '/invite')]
  msg = 'NOTE: No admins configured.  This wiki is not secure.'
  if admins: msg = ''
  return [msg, BR, Form(['Send an invitation email to:', ti])]

def send_invitation(req, addr):
  id = make_session_id()
  url = req.uri(mpath('/register/' + id))
  invitations[id] = Invitation(id, addr)
  invitations.sync()
  send_email(invitation_email % { 'addr' : addr, 'url' : url },  addr)
  return

@page('/setup')
@stdwrap
def setup(req):

  if not admins: req.redirect('invite')
  
  if len(invitations)==0:
    for a in admins:
      send_invitation(req, a)
      pass
    return ['Initial invitations sent.']

  return ['This wiki has already been set up.']
