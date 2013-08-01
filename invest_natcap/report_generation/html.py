import collections
import re

BEACH_STYLE = 0

_TOC_MARKER = '<---TOC MARKER--->'

class HTMLWriter(object):
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
        
    def __init__(self, uri, title, header):
        self.uri = uri
        self.title = title
        self.header = header
        self.body = ''
        self.style = ''
        self.id_counter = 0
        self.has_toc = False
        self.toc = collections.OrderedDict()

    def set_style(self, style_const):
        self.style = _get_style_css(style_const)

    def insert_table_of_contents(self, max_header_level=2):
        if self.has_toc:
            raise Exception('This page already has a table of contents.')
        self.body += _TOC_MARKER
        self.has_toc = True
        self.toc_max_header_level = max_header_level

    def write_header(self, text, level=2):
        elem_id = 'id_%d' % self.id_counter
        self.id_counter += 1
        self.body += _elem(('h%d' % level), text, id=elem_id)
        self.toc[elem_id] = (level, text)

    def write_paragraph(self, text):
        self.body += _elem('p', text)

    def start_table(self):
        self.body += '<table>'

    def end_table(self):
        self.body += '</table>'

    def write_row(self, cells, is_header=False, cell_attr=[]):
        '''Writes a table row with the given cell data.

        cell_attr - attributes for each cell. If provided, it must be the 
            same length as cells. Each entry should be a dictionary mapping
            attribute key to value.
        '''
        self.body += '<tr>'
        cell_tag = 'th' if is_header else 'td'
        for i, cell in enumerate(cells):
            attr = cell_attr[i] if cell_attr else {}
            self.body += _elem(cell_tag, str(cell), **attr)
        self.body += '</tr>'

    def add_image(self, src):
        self.body += ('<img src="%s">' % src)

    def start_collapsible_element(self, summary_content=None):
        self.body += '<details>'
        if summary_content:
            self.body += _elem('summary', summary_content)

    def end_collapsible_element(self):
        self.body += '</details>'

    def flush(self):
        '''Creates and writes to an HTML file.'''
        f = open(self.uri, 'w')

        f.write('<html>')

        f.write('<head>')
        f.write(_elem('title', self.title))
        if self.style:
            f.write(_elem('style', self.style, type="text/css"))
        f.write('</head>')

        f.write('<body>')
        f.write('<center><h1>%s</h1></center>' % self.header)
        if self.has_toc:
            self.body = re.sub(_TOC_MARKER, self._make_toc(), self.body)
        f.write(self.body)
        f.write('</body>')
        f.write('</html>')

        f.close()

    def _make_toc(self):
        '''Returns the HTML to generate the Table of Contents for the page.'''
        toc_html = ''
        toc_html += _elem('h2', 'Table of Contents')
        toc_html += '<ul>'
        for elem_id, (level, text) in self.toc.items():
            if level > self.toc_max_header_level:
                continue
            toc_html += '<li>'
            toc_html += _elem('a', text, href=('#%s' % elem_id))
            toc_html += '</li>'
        toc_html += '</ul>'
        return toc_html

def _elem(tag, content, **attr):
    if attr:
        attr_str = ' ' + ' '.join(
            '%s="%s"' % (key, val) for key, val in attr.items())
    else:
        attr_str = ''
    return ('<%s%s>%s</%s>' % (tag, attr_str, content, tag))


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
