import sys
import glob
import re
import os
import csv

def get_lookup_from_csv(csv_table_uri, key_field):
    """Creates a python dictionary to look up the rest of the fields in a
        csv table indexed by the given key_field

        csv_table_uri - a URI to a csv file containing at
            least the header key_field

        returns a dictionary of the form {key_field_0:
            {header_1: val_1_0, header_2: val_2_0, etc.}
            depending on the values of those fields"""

    def smart_cast(value):
        """Attempts to cat value to a float, int, or leave it as string"""
        cast_functions = [int, float]
        for fn in cast_functions:
            try:
                return fn(value)
            except ValueError:
                pass
        return value

    with open(csv_table_uri, 'rU') as csv_file:
        csv_reader = csv.reader(csv_file)
        header_row = csv_reader.next()
        key_index = header_row.index(key_field)
        #This makes a dictionary that maps the headers to the indexes they
        #represent in the soon to be read lines
        index_to_field = dict(zip(range(len(header_row)), header_row))

        lookup_dict = {}
        for line in csv_reader:
            key_value = smart_cast(line[key_index])
            #Map an entire row to its lookup values
            lookup_dict[key_value] = (
                dict([(index_to_field[index], smart_cast(value))
                      for index, value in zip(range(len(line)), line)]))
        return lookup_dict



for state_directory in ['globio_mgds_output', 'globio_mg_output']:
    print state_directory
    csv_filenames = [
        x for x in glob.glob('%s/*.csv' % state_directory) if not 'pixel_count' in x]

    print csv_filenames
    csv_header = open(csv_filenames[0], 'rb').readline()

    ecoregions = set([
        re.match('[^-]*- ([^(]*)', x).group(1)[0:-1] for x in csv_header.split(',')[4::]])

    print ecoregions

    scenario_lookup = {}

    for csv_uri in csv_filenames:
        scenario_name = os.path.splitext(os.path.basename(csv_uri))[0]
        print csv_uri, scenario_name
        scenario_lookup[scenario_name] = get_lookup_from_csv(csv_uri, 'Percent Soy Expansion in Forest Core Expansion Scenario')

    out_dir = state_directory + '_by_ecoregion'
    try:
        os.makedirs(out_dir)
    except OSError as exception:
            #It's okay if the directory already exists, if it fails for
            #some other reason, raise that exception
        if exception.errno != errno.EEXIST:
            raise



    for msa_type in ['MSA Species - ', 'MSA Endemic - ']:
        for ecoregion in ecoregions:
            outfile_name = os.path.join(out_dir, msa_type[0:-3] + '_' + ecoregion + '.csv')
            print outfile_name
            outfile = open(outfile_name, 'wb')
            

            header_lookups = []
            for tail_type in [' (median)', ' (lower)', ' (upper)']:
                header_lookups.append(msa_type + ecoregion + tail_type)

#            for scenario_name in sorted(scenario_lookup):
#            for header, s in header_lookups:


            outfile.write('Percent')
            for scenario_name in sorted(scenario_lookup):
                for header in header_lookups:
                    outfile.write(',' + scenario_name + ' ' + header)
            outfile.write('\n')

            for percent in range(201):
                outfile.write(str(percent))
                for scenario_name in sorted(scenario_lookup):
                    for header in header_lookups:
                        #outfile.write(',' + scenario_name + ' ' + header)
                        outfile.write(',' + str(scenario_lookup[scenario_name][percent][header]))
                outfile.write('\n')
                


#            print header_lookups


