import codecs
import os
import shutil
import imp

import invest_natcap.testing
from invest_natcap import raster_utils

class TestWriter(object):
    def __init__(self, file_uri, mode='a', encoding='utf-8'):
        self.file_uri = file_uri
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

    def has_class(self, test_class_name):
        try:
            module = imp.load_source('model', self.file_uri)
            try:
                return (True, getattr(module, test_class_name).__bases__)
            except AttributeError:
                return (False, None)
        except ImportError:
            # Occurs when there's a problem importing, like with
            # invest_test_core.  In this case, we loop line by line through the
            # file and check whether the class exists and, if so, get the class
            # base(s).
            for line in self.test_file:
                if 'class %s(' % test_class_name in line:
                    cls_base = ''
                    started_base_cls = False
                    for char in line:
                        if char == '(' and not started_base_cls:
                            started_base_cls == True
                        elif char == ')':
                            self.test_file.seek(0)
                            return(True, [cls_base])
                        else:
                            cls_base += char
            self.test_file.seek(0)
            return (False, None)

    def class_has_test(self, test_class_name, test_func_name):
        try:
            module = imp.load_source('model', self.file_uri)
            try:
                cls_instance = getattr(module, test_class_name)
                function = getattr(cls_instance, test_func_name)
                return True
            except AttributeError:
                return False
        except ImportError:
            # Occurs when there's a problem importing, like with
            # invest_test_core.  In this case, we loop line by line through the
            # file and check whether theres is the target function in the class
            # given.
            in_test_class = False
            for line in self.test_file:
                if 'class %s(' in line:
                    in_test_class = True
                elif in_test_class:
                    if 'def %s(self):' in line:
                        self.test_file.seek(0)
                        return True
                    elif line[0:6] == 'class ':
                        # we've ended the active class, have not found the
                        # target test.
                        self.test_file.seek(0)
                        return False
                    else:
                        # We're still in the target class but have not found the
                        # test yet.  Keep going.
                        pass
            # If we reach the end of the file, we haven't found the class or the
            # target function in the class, return False.
            return False


def add_test_to_class(file_uri, test_class_name, test_func_name, in_archive_uri,
        out_archive_uri, module):

    test_file = TestWriter(file_uri, 'r')
    temp_file_uri = raster_utils.temporary_filename()
    new_file = TestWriter(temp_file_uri, 'w+')

    cls_exists = test_file.has_class(test_class_name)
    test_exists = test_file.class_has_test(test_class_name, test_func_name)

    if test_exists:
        print ('WARNING: %s.%s exists.  Not writing a new test.' %
            (test_class_name, test_func_name))
        return

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
