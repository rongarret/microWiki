from utils import *
from html import *
from yaro import Yaro
from session import get_session
import sys, cgitb, cgitb_patch

def form_wrap(app):
  def wrap(req):
    threadvars.req = req
    return app(req)
  return wrap

def style(thing):
  return [HTMLItems(
    stylesheet('http://mcia.cc/style.css'),
    link('Menu', href=rpath('/menu')),
    link('Reset', href=rpath('/reset')),
    link('Logout', href=rpath('/logout')),
    HR,
    thing).as_html()]

def style_wrap(app):
  return lambda req: style(app(req))

def wsgi_tb_wrap(app):
  def wrap(env, start_response):
    try:
      return app(env, start_response)
    except:
      ei = sys.exc_info()
      start_response('500 Server error', [('Content-type','text/html')], ei)
      return cgitb.html(ei)
    pass
  return wrap

def yaro_tb_wrap(app):
  def wrap(req):
    try:
      # Must force HTML generation here or errors will escape
      return HTMLString(as_html(app(req)))
    except:
      req.res.status='500 Server error'
      return HTMLString(cgitb.html(sys.exc_info()))
    pass
  return wrap

def tlp_wrap(app):
  def wrap(env, start_response):
    env['TOP_LEVEL_PATH']=env['SCRIPT_NAME']
    threadvars.env = env
    return app(env, start_response)
  return wrap

def standard_wrap(app):
  return wsgi_tb_wrap(Yaro(style_wrap(yaro_tb_wrap(form_wrap(app))),
                           extra_props = [('session', get_session)]))

