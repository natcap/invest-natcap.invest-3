import invest_natcap.testing
import sys
import os

json_file = sys.argv[1]

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

