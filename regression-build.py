import invest_natcap.testing
import sys
import os
import shutil

json_file = sys.argv[1]

#CONFIG_DATA = {
#    'Input archive': '',
#    'Output archive': '',
#}

def _set_archive_name(keyword):
    input_archive_name = raw_input('Path to the %s archive: ' % keyword)

    if os.path.exists(input_archive_name):
        confirm_overwrite = raw_input('%s exists.  Overwrite? (y/n)' %
            input_archive_name)

        while confirm_overwrite not in ['y', 'n']:
            confirm_overwrite = raw_input('Confirm overwrite? (y/n)')

        if input_archive_name == 'n':
            return ''
    else:
        dirname = os.path.dirname(input_archive_name)
        if not os.path.exists(dirname):
            confirm_create_folder = raw_input(('%s does not exist.  '
                'Create path? (y/n) ') % dirname)
            while confirm_create_folder not in ['y', 'n']:
                confirm_create_folder = raw_input('Create path? (y/n)')

            if confirm_create_folder == 'y':
                os.makedirs(dirname)
    return input_archive_name


def set_input_archive_name():
    CONFIG_DATA['Input archive']['path'] = _set_archive_name('input')

def set_output_archive_name():
    CONFIG_DATA['Output archive']['path'] = _set_archive_name('output')

CONFIG_DATA = {
    'Input archive': {
        'path': '',
        'function': set_input_archive_name,
    },
    'Output archive': {
        'path': '',
        'function': set_output_archive_name
    },
}

def configure_settings():
    settings = list(sorted(CONFIG_DATA.iteritems(), key=lambda x: x[0]))

    for item_no, (label, data) in enumerate(settings):
        if data['path'] == '':
            path = '(not set)'
        else:
            path = data['path']

        print '[%s] %-15s: %s' % (item_no, label, path)

    input_selection = raw_input('Select an item to configure: ')

    while int(input_selection) not in range(len(settings)):
        input_selection = raw_input('Input must be an option above: ')

    input_selection = int(input_selection)
    settings[input_selection][1]['function']()




def main():
    finished = False
    while not finished:
        configure_settings()

if __name__ == '__main__':
    main()


#TEST_DIR = 'test'
#MANAGED_DATA = os.path.join(TEST_DIR, 'data', 'managed_data')
#MANAGED_INPUT = os.path.join(MANAGED_DATA, 'input')
#MANAGED_OUTPUT = os.path.join(MANAGED_DATA, 'output')
#
#test_file = raw_input('Test file to use: ')
#test_file = os.path.basename(test_file)
#
#test_class_name = raw_input('Name of the new test class: ')
#test_func_name = raw_input('Name of the new test_function: ')
#
#test_file = open(os.path.join(TEST_DIR, test_file), "a")
#
#input_archive = os.path.join(MANAGED_INPUT, '-'.join([test_class_name,
#    test_func_name]))
#output_archive = os.path.join(MANAGED_OUTPUT, '-'.join([test_class_name,
#    test_func_name]))
#
#invest_natcap.testing.build_regression_archives(json_file, input_archive,
#    output_archive)

#TAB = '    '
#lines_to_write = [
#    'class %s(invest_natcap.testing.GISTest):' % test_class_name,
#    '    def %s(self):' % test_func_name,
#    '        
#test_file._write(

