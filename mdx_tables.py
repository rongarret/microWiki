"""
Wrapped Tables extension for Markdown Python

2007-09-27

brian_jaress@gna.org

"Wrapped" means that you can wrap lines inside a cell.
It's inspired by another extension I found at

https://libprs500.kovidgoyal.net/browser/trunk/src/libprs500/ebooks/markdown/mdx_tables.py?format=txt

but that extension didn't have wrapping and is implemented in a very
different way.

An example of the syntax is:

|*heading*|*heading*|cell|
|cell a|cell b| cell c
    still cell c
    blah blah blah
    still cell c|
|third row|cell|cell|

That gives you a three by three table with two headings (top left and
top center) and one cell with a lot of text (mid right).

"""

from os import linesep
from csv import reader, QUOTE_NONE
from markdown import Preprocessor, Extension

class TableExtension(Extension):
    def __init__(self, configs):
        self.configs = {
                'delim': '|',
                'wrap': 4 * ' ',
                'header': '*'
                }
        self.configs.update(configs)

    def extendMarkdown(self, md, md_globals):
        md.preprocessors.append(TablePre(**self.configs))

class TablePre(Preprocessor):
    def __init__(self, delim, wrap, header):
        self.delim = delim
        self.wrap = wrap
        self.header = header

    def run(self, lines):
        table_lines = []
        #Group contiguous table lines and convert each group to a table
        for l in lines:
            if l.startswith(self.delim) or (len(table_lines) > 0 and
                    l.startswith(self.wrap)):
                table_lines.append(l)
            else:
                if len(table_lines) > 0:
                    for new_line in self.table(table_lines):
                        yield new_line
                    table_lines = []
                yield l

    def clean(self, cells):
        """Remove the empty cells at the beginning and end."""
        return cells[1:-1]

    def table(self, lines):
        yield "<table>"
        for r in self.parse(lines):
            yield self.row(r)
        yield "</table>"

    def parse(self, lines):
        """Generate table rows as lists of cell strings."""
        read = reader(lines,
                delimiter=self.delim,
                quoting=QUOTE_NONE,
                escapechar='\\',
                lineterminator=linesep
                )

        accumulated = []
        for line in read:
            if not line[0].startswith(self.wrap):
                #Start new row
                if len(accumulated) > 0:
                    yield self.clean(accumulated)
                accumulated = line
            else:
                #Continue existing cell
                accumulated[-1] = accumulated[-1] + '\n' + line[0].lstrip()
                accumulated.extend(line[1:])
        yield self.clean(accumulated)

    def row(self, data):
        return self.tag(''.join(map(self.cell, data)), "tr")

    def cell(self, data):
        if (data.startswith(self.header) and data.endswith(self.header) and
                len(data) > 1):
            data = data[len(self.header):-len(self.header)]
            tag = "th"
        else:
            tag = "td"
        return self.tag(data, tag)

    def tag(self, data, tag):
        return "<%s>%s</%s>" % (tag, data, tag)

def makeExtension(configs={}) :
    return TableExtension(configs)
