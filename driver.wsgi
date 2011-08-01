#!/usr/bin/env python

import sys, os, threading
from wsgiref.simple_server import make_server

if __name__!='__main__':
  d=os.path.dirname(__file__)
  sys.path.append(d)
  pass

from uwiki import init, application

init()

# For best results run with 'python -i driver.wsgi'

if __name__=='__main__':
  srv = make_server('localhost', 8080, application)
  t = threading.Thread(target=srv.serve_forever)
  t.daemon = 1
  t.start()
  print 'Serving port 8080'
