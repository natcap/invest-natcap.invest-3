BEACH_STYLE = 0

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

    def set_style(self, style_const):
        self.style = _get_style_css(style_const)

    def write_header(self, text, level=2):
        self.body += _elem(('h%d' % level), text)

    def write_paragraph(self, text):
        self.body += _elem('p', text)

    def start_table(self):
        self.body += '<table>'

    def end_table(self):
        self.body += '</table>'

    def write_row(self, cells, is_header=False):
        self.body += '<tr>'
        cell_tag = 'th' if is_header else 'td'
        for cell in cells:
            self.body += '<%s>%s</%s>' % (cell_tag, str(cell), cell_tag)
        self.body += '</tr>'

    def add_image(self, src):
        self.body += ('<img src="%s">' % src)

    def flush(self):
        '''Creates and writes to an HTML file.'''
        f = open(self.uri, 'w')

        def write_elem(tag, text, attr=''):
            if attr:
                attr = ' ' + attr
            f.write('<%s%s>%s</%s>' % (tag, attr, text, tag))

        f.write('<html>')

        f.write('<head>')
        write_elem('title', self.title)
        if self.style:
            write_elem('style', self.style, 'type="text/css"')
        f.write('<head>')

        f.write('<body>')
        f.write('<center><h1>%s</h1></center>' % self.header)
        f.write(self.body)
        f.write('</body>')
        f.write('</html>')

        f.close()

def _elem(tag, content, attr=''):
    if attr:
        attr = ' ' + attr
    return ('<%s%s>%s</%s>' % (tag, attr, content, tag))


def _get_style_css(style_const):
    if style_const == BEACH_STYLE:
        return '''
      body {
          background-color: #EFECCA;
          color: #002F2F
      }
      h1, h2, h3, strong, th {
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
      '''
    else:
        raise Exception('Unsupported style constant %d' % style_const)
