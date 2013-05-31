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

    def write_import(self):
        self.write('import invest_natcap.testing')

    def write_test_class(self, classname):
        self.write(self._class_string(classname))

    def write_archive_regression_test(self, test_name, module, input_archive,
            output_archive, start_dir):
        input_archive = os.path.relpath(input_archive, start_dir)
        output_archive = os.path.relpath(output_archive, start_dir)
        self.write('    @invest_natcap.testing.regression(')
        self.write('        input_archive="%s",' % input_archive)
        self.write('        workspace_archive="%s")' % output_archive)
        self.write('    def %s(self):' % test_name)
        self.write('        %s.execute(self.args)' % module)
        self.write('')

    def class_exists(self, test_class_name):
        cls_string = self._class_string(test_class_name) + '\n'
        different_classtype = ''
        for line in self.test_file:
            if line == cls_string:
                self.test_file.seek(0)
                return (True, 'invest_natcap.testing.GISTest')
            elif 'class %s' % test_class_name in line:
                in_paren = False
                for char in line:
                    if in_paren:
                        different_classtype += char
                    elif char == '(':
                        in_paren = True
                    elif char == ')':
                        self.test_file.seek(0)
                        return (False, different_classtype)
        self.test_file.seek(0)
        return (False, None)

def add_test_to_class(file_uri, test_class_name, test_func_name, in_archive_uri,
        out_archive_uri, module):

    test_file = TestWriter(file_uri, 'r')
    temp_file_uri = raster_utils.temporary_filename()
    new_file = TestWriter(temp_file_uri, 'w+')

    cls_exists = test_file.class_exists(test_class_name)
    if cls_exists[0] == False:
        for line in test_file.test_file:
            new_file.write(line.rstrip())

        new_file.write('\n')
        new_file.write_import()
        new_file.write_test_class(test_class_name)
        new_file.write_archive_regression_test(test_func_name, module,
            in_archive_uri, out_archive_uri, os.path.dirname(file_uri))
    else:
        for line in test_file.test_file:
            new_file.write(line.rstrip())
            if 'class %s(' % test_class_name in line:
                new_file.write_archive_regression_test(test_func_name, module,
                    in_archive_uri, out_archive_uri, os.path.dirname(file_uri))

    test_file = None
    new_file = None

    # delete the old file
    os.remove(file_uri)
    print 'removed %s' % file_uri

    # copy the new file over the old one.
    shutil.copyfile(temp_file_uri, file_uri)
    print 'copying %s to %s' % (temp_file_uri, file_uri)
