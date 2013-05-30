import codecs

class TestWriter(object):
    def __init__(self, file_uri, mode='a', encoding='utf-8'):
        self.test_file = codecs.Open(file_uri, mode, encoding)

    def __del__(self):
        self.test_file.close()

    def write(self, line):
        self.test_file.write(line + '\n')

def write_import(file_uri):
    test_file = TestWriter(file_uri)
    test_file.write('import invest_natcap.testing')

def write_test_class(file_uri, classname):
    test_file = TestWriter(file_uri)
    test_file.write('class %s(invest_natcap.testing.GISTest):')
