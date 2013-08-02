import collections

BEACH_STYLE = 0  # constant to select a nice beach (tan and blue) palette

class HTMLDocument(object):
    '''Utility class for creating simple HTML files.

    Example usage:
        # Create the document object.
        doc = html.HTMLDocument('myfile.html', 'My Page', 'A Page About Me')

        # Add some text.
        doc.write_header('My Early Life')
        doc.write_paragraph('I lived in a small barn.')

        # Add a table.
        table = doc.add(html.Table())
        table.add_row(['Age', 'Weight'], is_header=True)
        table.add_row(['1 year', '20 pounds'])
        table.add_row(['2 years', '40 pounds'])

        # Add an arbitrary HTML element. 
        # Note that the HTML 'img' element doesn't have an end tag.
        doc.add(html.Element('img', src='images/my_pic.png', end_tag=False))

        # Create the file.
        doc.flush()
    '''
        
    def __init__(self, uri, title, header, style_const=BEACH_STYLE):
        self.uri = uri

        self.html_elem = Element('html')

        head = self.html_elem.add(Element('head'))
        head.add(Element('title', title))
        head.add(Element('style', _get_style_css(style_const), type='text/css'))

        self.body = self.html_elem.add(Element('body'))
        self.body.add(Element('h1', ('<center>%s</center>' % header)))

        self.id_counter = 0  # keep track of allocated IDs
        self.headers = collections.OrderedDict()

    def add(self, elem):
        '''Add an arbitrary element to the body of the document.

        elem - any object that has a method html() to output HTML markup

        Return the added element for convenience.
        '''
        return self.body.add(elem)

    def insert_table_of_contents(self, max_header_level=2):
        '''Insert an auto-generated table of contents.

        The table of contents is based on the headers in the document.
        '''
        self.body.add(_TableOfContents(self.headers, max_header_level))

    def write_header(self, text, level=2):
        '''Convenience method to write a header.'''
        elem_id = 'id_%d' % self.id_counter
        self.id_counter += 1
        self.body.add(Element(('h%d' % level), text, id=elem_id))
        self.headers[elem_id] = (level, text)

    def write_paragraph(self, text):
        '''Convenience method to write a paragraph.'''
        self.body.add(Element('p', text))

    def flush(self):
        '''Create a file with the contents of this document.'''
        f = open(self.uri, 'w')
        f.write(self.html_elem.html())
        f.close()


class Element(object):
    '''Represents a generic HTML element.

    Any Element object can be passed to HTMLDocument.add()

    Example:
        doc = html.HTMLDocument(...)
        details_elem = doc.add(html.Element('details'))
        details_elem.add(
            html.Element('img', src='images/my_pic.png', end_tag=False))
    '''
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
    '''Represents and renders HTML tables.'''

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

class _TableOfContents(object):
    '''Represents a Table of Contents for the document.'''

    def __init__(self, headers, max_header_level):
        self.headers = headers
        self.max_header_level = max_header_level

    def html(self):
        # Generate a header.
        header = Element('h2', 'Table of Contents')

        # Generate a list with links to each major header.
        link_list = Element('ul')
        for elem_id, (level, text) in self.headers.items():
            if level > self.max_header_level:
                continue
            list_elem = Element('li')
            list_elem.add(Element('a', text, href=('#%s' % elem_id)))
            link_list.add(list_elem)

        return header.html() + link_list.html()

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
