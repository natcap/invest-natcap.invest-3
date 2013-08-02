import collections
import re

BEACH_STYLE = 0

class HTMLDocument(object):
    '''Utility class for creating simple HTML files.

    Usage:
        writer = html.HTMLWriter('myfile.html', 'My Page', 'A Page About Me')
        writer.set_style(html.BEACH_STYLE)
        writer.write_section_header('My Early Life')
        writer.write_paragraph('I lived in a small barn.')
        writer.write_section_header('My Later Life')
        writer.write_paragraph('I lived in a bigger barn.')
        writer.flush()

    Once writing is complete, flush() must be called in order to
    actually create the file.
    '''
        
    def __init__(self, uri, title, header, style_const=BEACH_STYLE):
        self.uri = uri

        self.html_elem = Element('html')

        head = Element('head')
        head.add(Element('title', title))
        head.add(Element('style', _get_style_css(style_const), type='text/css'))
        self.html_elem.add(head)

        self.body = Element('body')
        self.body.add(Element('h1', ('<center>%s</center>' % header)))
        self.html_elem.add(self.body)

        self.id_counter = 0
        self.toc = collections.OrderedDict()

    def add(self, elem):
        self.body.add(elem)
        return elem

    def insert_table_of_contents(self, max_header_level=2):
        self.body.add(TableOfContents(self.toc, max_header_level))

    def write_header(self, text, level=2):
        elem_id = 'id_%d' % self.id_counter
        self.id_counter += 1
        self.body.add(Element(('h%d' % level), text, id=elem_id))
        self.toc[elem_id] = (level, text)

    def write_paragraph(self, text):
        self.body.add(Element('p', text))

    def flush(self):
        '''Creates and writes to an HTML file.'''
        f = open(self.uri, 'w')
        f.write(self.html_elem.html())
        f.close()

class TableOfContents(object):
    def __init__(self, toc, max_header_level):
        self.toc = toc
        self.max_header_level = max_header_level

    def html(self):
        header = Element('h2', 'Table of Contents')

        link_list = Element('ul')
        for elem_id, (level, text) in self.toc.items():
            if level > self.max_header_level:
                continue
            list_elem = Element('li')
            list_elem.add(Element('a', text, href=('#%s' % elem_id)))
            link_list.add(list_elem)

        return header.html() + link_list.html()

class Element(object):
    def __init__(self, tag, content='', end_tag=True, **attr):
        self.tag = tag
        self.content = content
        self.end_tag = end_tag
        if attr:
            self.attr_str = ' ' + ' '.join(
                '%s="%s"' % (key, val) for key, val in attr.items())
        else:
            self.attr_str = ''
        self.elems = []

    def add(self, elem):
        self.elems.append(elem)
        return elem

    def html(self):
        html_str = '<%s%s>%s' % (self.tag, self.attr_str, self.content)
        for elem in self.elems:
            html_str += elem.html()
        if self.end_tag:
            html_str += ('</%s>' % self.tag)
        return html_str

class Table(object):
    def __init__(self):
        self.table_elem = Element('table')

    def add_row(self, cells, is_header=False, cell_attr=[]):
        '''Writes a table row with the given cell data.

        cell_attr - attributes for each cell. If provided, it must be the 
            same length as cells. Each entry should be a dictionary mapping
            attribute key to value.
        '''
        row = Element('tr')
        cell_tag = 'th' if is_header else 'td'
        for i, cell in enumerate(cells):
            attr = cell_attr[i] if cell_attr else {}
            row.add(Element(cell_tag, str(cell), **attr))
        self.table_elem.add(row)

    def html(self):
        return self.table_elem.html()

def _get_style_css(style_const):
    if style_const == BEACH_STYLE:
        return '''
      body {
          background-color: #EFECCA;
          color: #002F2F
      }
      h1, h2, h3, h4, strong, th {
          color: #046380;
      }
      h2 {
          border-bottom: 1px solid #A7A37E;
      }
      table {
          border: 5px solid #A7A37E;
          margin-bottom: 50px; 
          background-color: #E6E2AF;
      }
      td, th { 
          margin-left: 0px;
          margin-right: 0px;
          padding-left: 8px;
          padding-right: 8px;
          padding-bottom: 2px;
          padding-top: 2px;
          text-align:left;
      }
      td { 
          border-top: 5px solid #EFECCA;
      }
      img {
          margin: 20px;
      }
      '''
    else:
        raise Exception('Unsupported style constant %d' % style_const)
