import invest_natcap.testing
import sys
import os

json_file = sys.argv[1]

INPUT_ARCHIVE = ''
OUTPUT_ARCHIVE = ''

def _set_archive_name(keyword):
    input_archive_name = raw_input('Path to the %s archive: ' % keyword)

    if os.path.exists(input_archive_name):
        confirm_overwrite = raw_input('%s exists.  Overwrite? (y/n)' %
            input_archive_name)

        while confirm_overwrite not in ['y', 'n']:
            confirm_overwrite = raw_input('Confirm overwrite? (y/n)')

        if input_archive_name == 'n'
            return ''
    else:
        if not os.path.exists(os.path.dirname(input_archive_name)):
            confirm_create_folder = raw_input(('%s does not exist.  '
                'Create path? (y/n) ')
            while confirm_create_folder not in ['y', 'n']:
                confirm_create_folder = raw_input('Create path? (y/n)')

            if confirm_create_folder == 'y':
                os.mkdirs(os.path.dirname(input_archive_name))
    return input_archive_name


def set_input_archive_name():
    INPUT_ARCHIVE = _set_archive_name('input')

def set_output_archive_name():
    OUTPUT_ARCHIVE = _set_archive_name('output')


TEST_DIR = 'test'
MANAGED_DATA = os.path.join(TEST_DIR, 'data', 'managed_data')
MANAGED_INPUT = os.path.join(MANAGED_DATA, 'input')
MANAGED_OUTPUT = os.path.join(MANAGED_DATA, 'output')

test_file = raw_input('Test file to use: ')
test_file = os.path.basename(test_file)

test_class_name = raw_input('Name of the new test class: ')
test_func_name = raw_input('Name of the new test_function: ')

test_file = open(os.path.join(TEST_DIR, test_file), "a")

input_archive = os.path.join(MANAGED_INPUT, '-'.join([test_class_name,
    test_func_name]))
output_archive = os.path.join(MANAGED_OUTPUT, '-'.join([test_class_name,
    test_func_name]))

invest_natcap.testing.build_regression_archives(json_file, input_archive,
    output_archive)

#TAB = '    '
#lines_to_write = [
#    'class %s(invest_natcap.testing.GISTest):' % test_class_name,
#    '    def %s(self):' % test_func_name,
#    '        
#test_file._write(

