DEFAULT_PALETTE = 0
BEACH_PALETTE = 1

class HTMLWriter(object):
    def __init__(self, uri, title, header):
        self.uri = uri
        self.title = title
        self.header = header
        self.body = ''
        self.style = ''

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
