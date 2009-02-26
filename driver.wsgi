#!/usr/bin/env python

import sys, os.path

try:
  __file__
  sys.path.append(os.path.dirname(__file__))
except NameError:
  __file__ = '?'

from app import init, application

init()

if __name__=='__main__':
  from wsgiref.simple_server import make_server
  srv = make_server('', 8080, application)
  print 'Serving port 8080'
  srv.serve_forever()
