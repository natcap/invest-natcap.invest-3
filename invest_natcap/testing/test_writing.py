import codecs
import os
import shutil

from invest_natcap import raster_utils

class TestWriter(object):
    def __init__(self, file_uri, mode='a', encoding='utf-8'):
        self.test_file = codecs.open(file_uri, mode, encoding)

    def __del__(self):
        self.test_file.close()

    def _class_string(self, classname):
        return 'class %s(invest_natcap.testing.GISTest):' % classname

    def write(self, line):
        self.test_file.write(line + '\n')

    def write_import(self, ):
        self.write('import invest_natcap.testing')

    def write_test_class(self, classname):
        self.write(self._class_string(classname))

    def write_archive_regression_test(self, test_name, module, input_archive,
            output_archive):
        self.write('    @invest_natcap.testing.regression(')
        self.write('        input_archive="%s",' % input_archive)
        self.write('        workspace_archive="%s")' % output_archive)
        self.write('    def %s(self):' % test_name)
        self.write('        %s.execute(self.args)')
        self.write('')

    def class_exists(self, test_class_name):
        cls_string = self._class_string(test_class_name) + '\n'
        different_classtype = ''
        for line in self.test_file:
            if line == cls_string:
                return (True, 'invest_natcap.testing.GISTest')
            elif 'class %s' % test_class_name in line:
                in_paren = False
                for char in line:
                    if in_paren:
                        different_classtype += char
                    elif char == '(':
                        in_paren = True
                    elif char == ')':
                        return (False, different_classtype)
        return (False, None)



#def write_import(file_uri):
#    test_file = TestWriter(file_uri)
#    test_file.write('import invest_natcap.testing')

#def _class_string(classname):
#    test_file.write('class %s(invest_natcap.testing.GISTest):')

#def write_test_class(file_uri, classname):
#    test_file = TestWriter(file_uri)
#    test_file.write(_class_string(classname))

#def write_archive_test(test_name, module, input_archive, output_archive):
#    test_file = TestWriter(file_uri)
#    test_file.write('    @invest_natcap.testing.regression(')
#    test_file.write('        input_archive="%s",' % input_archive)
#    test_file.write('        workspace_archive="%s")' % output_archive)
#    test_file.write('    def %s(self):' % test_name)
#    test_file.write('        %s.execute(self.args)')
#    test_file.write('')
#
## function to see if a test class is in the test file
#def class_exists(file_uri, test_class_name):
#    """Check to see if the target classname exists in the given file.
#
#        file_uri - a URI to the target test file
#        test_class_name - the name of the test class to check
#
#    Returns a tuple.  The first element is whether the classname is present.
#    The second element is the string classtype of the class found, or None if
#    the class was not found at all in the file."""
#
#    test_file = TestWriter(file_uri)
#
#    cls_string = _class_string(classname) + '\n'
#    different_classtype = ''
#    for line in test_file:
#        if line == cls_string:
#            return (True, 'invest_natcap.testing.GISTest')
#        elif 'class %s' % classname in line:
#            in_paren = False
#            for char in line:
#                if in_paren:
#                    different_classtype.append(char)
#                elif char == '(':
#                    in_paren = True
#                elif_char == ')':
#                    return (False, different_classtype)
#
#    return (False, None)

# function to insert test functions into an existing test class.
def add_test_to_class(file_uri, test_class_name, test_func_name, in_archive_uri,
        out_archive_uri, module):
    test_file = TestWriter(file_uri, 'r')
    temp_file = raster_utils.temporary_filename()
    new_file = TestWriter(temp_file, 'w')

    for line in test_file.test_file:
        new_file.write(line.rstrip())
        if 'class %s(' % test_class_name in line:
            new_file.write_archive_regression_test(test_func_name, module,
                in_archive_uri, out_archive_uri)

    test_file = None
    new_file = None

    # delete the old file
    os.remove(test_file)

    # copy the new file over the old one.
    shutil.copyfile(new_file, test_file)
