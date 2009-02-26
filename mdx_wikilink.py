#!/usr/bin/env python

'''
WikiLink Extention for Python-Markdown
======================================

Converts CamelCase words to relative links.  Requires Python-Markdown 1.6+

Basic usage:

    >>> import markdown
    >>> text = "Some text with a WikiLink."
    >>> md = markdown.markdown(text, ['wikilink'])
    >>> md
    '\\n<p>Some text with a <a href="/WikiLink/" class="wikilink">WikiLink</a>.\\n</p>\\n\\n\\n'

To define custom settings the simple way:

    >>> md = markdown.markdown(text, 
    ...     ['wikilink(base_url=/wiki/,end_url=.html,html_class=foo)']
    ... )
    >>> md
    '\\n<p>Some text with a <a href="/wiki/WikiLink.html" class="foo">WikiLink</a>.\\n</p>\\n\\n\\n'
    
Custom settings the complex way:

    >>> md = markdown.Markdown(text, 
    ...     extensions = ['wikilink'], 
    ...     extension_configs = {'wikilink': [
    ...                                 ('base_url', 'http://example.com/'), 
    ...                                 ('end_url', '.html'),
    ...                                 ('html_class', '') ]},
    ...     encoding='utf8',
    ...     safe_mode = True)
    >>> str(md)
    '\\n<p>Some text with a <a href="http://example.com/WikiLink.html">WikiLink</a>.\\n</p>\\n\\n\\n'

Use MetaData with mdx_meta.py (Note the blank html_class in MetaData):

    >>> text = """wiki_base_url: http://example.com/
    ... wiki_end_url:     .html
    ... wiki_html_class:
    ... 
    ... Some text with a WikiLink."""
    >>> md = markdown.Markdown(text, ['meta', 'wikilink'])
    >>> str(md)
    '\\n<p>Some text with a <a href="http://example.com/WikiLink.html">WikiLink</a>.\\n</p>\\n\\n\\n'

From the command line:

    python markdown.py -x wikilink(base_url=http://example.com/,end_url=.html,html_class=foo) src.txt

By [Waylan Limberg](http://achinghead.com/).

Project website: http://achinghead.com/markdown-wikilinks/
Contact: waylan [at] gmail [dot] com

License: [BSD](http://www.opensource.org/licenses/bsd-license.php) 

Version: 0.4 (Oct 14, 2006)

Dependencies:
* [Python 2.3+](http://python.org)
* [Markdown 1.6+](http://www.freewisdom.org/projects/python-markdown/)
* For older dependencies use [WikiLink Version 0.3]
(http://code.limberg.name/svn/projects/py-markdown-ext/wikilinks/tags/release-0.3/)
'''

import markdown

class WikiLinkExtension (markdown.Extension) :
    def __init__(self, configs):
        # set extension defaults
        self.config = {
                        'base_url' : ['/', 'String to append to beginning or URL.'],
                        'end_url' : ['/', 'String to append to end of URL.'],
                        'html_class' : ['wikilink', 'CSS hook. Leave blank for none.']
        }
        
        # Override defaults with user settings
        for key, value in configs :
            # self.config[key][0] = value
            self.setConfig(key, value)
        
    def extendMarkdown(self, md, md_globals):
        #md.registerExtension(self) #???
        
        # Add configs to md instance
        md.wiki_config = self.config
        
        # Append preproccessor to end
        WIKILINK_PREPROCESSOR = WikiLinkPreprocessor()
        WIKILINK_PREPROCESSOR.md = md
        md.preprocessors.append(WIKILINK_PREPROCESSOR)
        
        # Append inline pattern to end
        # WIKILINK_RE = r'(?P<escape>\\|\b)(?P<camelcase>([A-Z]+[a-z-_]+){2,})\b'
        WIKILINK_RE = r'\[\[(?P<wikilink>[\w ]+)]]'
        WIKILINK_PATTERN = WikiLinks(WIKILINK_RE)
        WIKILINK_PATTERN.md = md
        md.inlinePatterns.append(WIKILINK_PATTERN)

def canonicalize(s):
    return ''.join([w[0].upper()+w[1:] for w in s.split()])

class WikiLinks (markdown.BasePattern) :
  
    def handleMatch(self, m, doc) :
        if  0: # m.group('escape') == '\\':
            a = doc.createTextNode(m.group('camelcase'))
        else :
            url = '%s%s%s'% (self.md.wiki_config['base_url'][0],
                             canonicalize(m.group('wikilink')),
#                             m.group('camelcase'), \
                             self.md.wiki_config['end_url'][0])
#            label = m.group('camelcase').replace('_', ' ')
            label = m.group('wikilink')
            a = doc.createElement('a')
            a.appendChild(doc.createTextNode(label))
            a.setAttribute('href', url)
            if self.md.wiki_config['html_class'][0] :
                a.setAttribute('class', self.md.wiki_config['html_class'][0])
        return a
    
class WikiLinkPreprocessor(markdown.Preprocessor) :
    
    def run(self, lines) :
        '''
        Updates WikiLink Extension configs with Meta Data.
        Passes "lines" through unchanged.
        
        Run as a preprocessor because must run after the 
        MetaPreprocessor runs and only needs to run once.
        '''
        if hasattr(self.md, 'Meta'):
            if self.md.Meta.has_key('wiki_base_url'):
                self.md.wiki_config['base_url'][0] = self.md.Meta['wiki_base_url'][0]
            if self.md.Meta.has_key('wiki_end_url'):
                self.md.wiki_config['end_url'][0] = self.md.Meta['wiki_end_url'][0]
            if self.md.Meta.has_key('wiki_html_class'):
                self.md.wiki_config['html_class'][0] = self.md.Meta['wiki_html_class'][0]
        
        return lines

def makeExtension(configs=None) :
    return WikiLinkExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
