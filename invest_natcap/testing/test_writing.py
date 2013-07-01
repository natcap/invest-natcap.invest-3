import codecs
import os
import shutil
import imp

import invest_natcap.testing
from invest_natcap import raster_utils


def file_has_class(test_file_uri, test_class_name):
    test_file = codecs.open(test_file_uri, mode='r', encoding='utf-8')
    module = imp.load_source('model', test_file_uri)
    try:
        cls_attr = getattr(module, test_class_name)
        return True
    except AttributeError:
        return False

def class_has_test(test_file_uri, test_class_name, test_func_name):
    test_file = codecs.open(test_file_uri, mode='r', encoding='utf-8')
    module = imp.load_source('model', test_file_uri)
    try:
        cls_attr = getattr(module, test_class_name)
        func_attr = getattr(cls_attr, test_func_name)
        return True
    except AttributeError:
        return False


def add_test_to_class(file_uri, test_class_name, test_func_name,
        in_archive_uri, out_archive_uri, module):
    test_file = codecs.open(file_uri, 'r', encoding='utf-8')

    temp_file_uri = raster_utils.temporary_filename()
    new_file = codecs.open(temp_file_uri, 'w+', encoding='utf-8')

    cls_exists = file_has_class(file_uri, test_class_name)
    test_exists = class_has_test(file_uri, test_class_name, test_func_name)

    if test_exists:
        print ('WARNING: %s.%s exists.  Not writing a new test.' %
            (test_class_name, test_func_name))
        return

    def _import():
        return 'import invest_natcap.testing\n'

    def _test_class(test_class):
        return 'class %s(invest_natcap.testing.GISTest):\n' % test_class

    def _archive_reg_test(test_name, module, in_archive, out_archive, cur_dir):
        in_archive = os.path.relpath(in_archive, cur_dir)
        out_archive = os.path.relpath(out_archive, cur_dir)
        return('    @invest_natcap.testing.regression(\n' +\
               '        input_archive="%s",\n' % in_archive +\
               '        workspace_archive="%s")\n' % out_archive +\
               '    def %s(self):\n' % test_name +\
               '        %s.execute(self.args)\n' % module +\
               '\n')

    if cls_exists == False:
        for line in test_file:
            new_file.write(line.rstrip() + '\n')

        new_file.write('\n')
        new_file.write(_import())
        new_file.write(_test_class(test_class_name))
        new_file.write(_archive_reg_test(test_func_name, module,
            in_archive_uri, out_archive_uri, os.path.dirname(file_uri)))
    else:
        import_written = False
        for line in test_file:
            if (not(line.startswith('import') or line.startswith('from')) and not
                import_written):
                new_file.write(_import())
                import_written = True

            new_file.write(line.rstrip() + '\n')
            if 'class %s(' % test_class_name in line:
                new_file.write(_archive_reg_test(test_func_name, module,
                    in_archive_uri, out_archive_uri, os.path.dirname(file_uri)))

    test_file = None
    new_file = None

    # delete the old file
    os.remove(file_uri)
    print 'removed %s' % file_uri

    # copy the new file over the old one.
    shutil.copyfile(temp_file_uri, file_uri)
    print 'copying %s to %s' % (temp_file_uri, file_uri)

