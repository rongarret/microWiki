#!/usr/bin/env python
# coding: utf-8

import config, fsdb, os, datetime
from rcstore import rcstore

import auth, sys
from auth import email_re

def main():

  flag = 0

  if not config.admins:
    print 'You must specifiy at least one admin email address in config.py'
    flag = 1
    pass

  if config.fb_app_id=='...':
    print 'You have to edit config.py to install your Facebook app id.'
    flag = 1
    pass

  if flag: return

  if os.path.exists(config.content_root):
    print 'Content directory exists.  Skipping content initialization.'
  else:

    os.makedirs(config.content_root)
    content = rcstore(fsdb.fsdb(config.content_root, 1))
    
    start = open('start-page.txt').read()
    syntax_ref = open('markdown-ref.txt').read()
    
    start_html = os.popen("./md2html < start-page.txt").read()
    syntax_html = os.popen("./md2html < markdown-ref.txt").read()
    
    metadata = {'timestamp' : datetime.datetime.now(),
                'username' : 'μWiki',
                'useremail': 'μWiki'}
    
    content.store('Start', start, start_html, metadata)
    content.store('SyntaxGuide', syntax_ref, syntax_html, metadata)
    
    print 'μWiki content has been initialized.'
    pass

  email = config.admins[0]
  if not email_re.match(email):
    print email, 'is not a valid email address'
    return
  try:
    auth.restore_state()
  except:
    auth.save_state()
    pass
  if auth.invitations:
    print 'Initial invitation has already been created.'
    return
  id = auth.make_session_id()
  auth.invitations[id] = auth.Invitation(id, email)
  auth.save_state()
  print auth.invitations
  print 'Initial invitation ID is ', id
  print 'Go to http://[my-host]/register/%s to register.' % id
  return

if __name__=='__main__': main()
