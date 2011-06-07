#!/usr/bin/env python
# coding: utf-8

# One-time initialization of μWiki

import config, fsdb, os, datetime
from rcstore import rcstore

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
