#!/usr/bin/env python
# coding: utf-8

# Generate initial content for μWiki

import config, fsdb, os, datetime
from rcstore import rcstore

import auth, sys
from auth import email_re

def main():

  if os.path.exists(config.content_root):
    print 'Content directory exists.'
    return
  
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
  
  print 'μWiki content successfully initialized.'
  return

if __name__=='__main__': main()
