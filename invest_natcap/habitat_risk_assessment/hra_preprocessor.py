"""Entry point for the Habitat Risk Assessment module"""

import re
import csv
import os
import glob
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')

def execute(args):
    """Read two directories for habitat and stressor layers and make
        appropriate output csv files

        args['workspace_dir'] - The directory to dump the output CSV files to
        args['habitat_dir'] - A directory of ArcGIS shapefiles that are habitats
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors

        returns nothing"""

    habitats_stressors = {
        'Change in area rating': ('Consequence','<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>'),
        'Change in structure rating': ('Consequence','<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>'),
        'Overlap Time Rating': ('Exposure','<enter (3) co-occur 8-12 mo/year, (2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>'),
        'Frequency of disturbance': ('Consequence','<enter (3) Annually or less often, (2) Several times per year, (1) Weekly or more often, (0) no score>')
        }

    stressors = {
        'Intensity Rating:': '<enter (3) high, (2) medium, (1) low, (0) no score>',
        'Management Effectiveness:': '<enter (3) not effective, (2) somewhat effective, (1) very effective, (0) no score>',
        }

    #These keys come directly from hra.py's execute docstring.
    habitats = {
        'Natural Mortality': '<enter (3) 0-20%, (2) 20-50%, (1) >80% mortality, or (0) no score>',
        'Recruitment Rate': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, (1) every <1 yrs, or (0) no score>',
        'Recovery Time': '<enter (3) >10 yrs, (2) 1-10 yrs, (1) <1 yr, or (0) no score>',
        'Connectivity Rate': '<enter (3) <10km, (2) 10-100km, (1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited, or (0) unknown>'
    default_weight_message = '<enter (3) more important, (2) equal importance, (1) less important>'
    default_table_headers = ['', 'Rating', 'DQ', 'Weight']
    default_overlap_table_headers = ['', 'Type','Rating', 'DQ', 'Weight']
    default_table_row = [default_dq_message, default_weight_message]

    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #Pick up all the habitat and stressor names
    name_lookup = {}
    for layer_type in ['habitat', 'stressor']:
        name_lookup[layer_type] = [
            os.path.basename(f.split('.')[0]) for f in 
            glob.glob(os.path.join(args[layer_type + '_dir'], '*.shp'))]


    #Create output csvs so that they are habitat centric
    for habitat_name in name_lookup['habitat']:
        csv_filename = os.path.join(
            output_dir, habitat_name + '_overlap_ratings.csv')
        with open(csv_filename, 'wb') as habitat_csv_file:
            habitat_csv_writer = csv.writer(habitat_csv_file)
            #Write the habitat name
            habitat_csv_writer.writerow(['HABITAT NAME', habitat_name])
            habitat_csv_writer.writerow(['HABITAT ONLY PROPERTIES'])
            habitat_csv_writer.writerow(['Habitat Data Quality:', default_dq_message])
            habitat_csv_writer.writerow([])

            #Build the habitat property table
            habitat_csv_writer.writerow(default_table_headers)
            for habitat_property, default_message in habitats.iteritems():
                habitat_csv_writer.writerow([habitat_property, default_message] + default_table_row)

            #Build the habitat stressor ratings table
            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT STRESSOR OVERLAP PROPERTIES'])
            for stressor_name in name_lookup['stressor']:
                habitat_csv_writer.writerow([])
                habitat_csv_writer.writerow([habitat_name + '/' + stressor_name + ' OVERLAP'])
                habitat_csv_writer.writerow(default_overlap_table_headers)
                for overlap_property, default_message in habitats_stressors.iteritems():
                    habitat_csv_writer.writerow([overlap_property] + list(default_message) + default_table_row)

    #Make stressor specific tables
    for stressor_name in name_lookup['stressor']:
        csv_filename = os.path.join(
            output_dir, stressor_name + '_stressor_ratings.csv')
        with open(csv_filename, 'wb') as stressor_csv_file:
            stressor_csv_writer = csv.writer(stressor_csv_file)
            stressor_csv_writer.writerow(['STRESSOR NAME', stressor_name])
            stressor_csv_writer.writerow(['Stressor Data Quality:', default_dq_message])
            stressor_csv_writer.writerow(['Stressor Buffer (m):', '<enter a buffer region in meters>'])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(default_table_headers)
            for stressor_property, default_message in stressors.iteritems():
                stressor_csv_writer.writerow([stressor_property, default_message] + default_table_row)

def parse_hra_tables(uri_to_workspace):
    """Digests CSV tables on disk and generates data structures specified by 
       invest_natcap.habitat_risk_assessment.hra.execute

       uri_to_workspace - the root directory that contains the CSV tables
           generated by hra_preprocessor.execute (args['workspace_dir'] in
           that function

       returns a dictionary of the form:
               'buffer_dict': 
                   {
                    {'Stressor 1': 50,
                     'Stressor 2': ...,
                    },
               'h-s':
                   {('Habitat A', 'Stressor 1'):
                       {
                         'E':
                             {
                             'Overlap Time Rating':
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                             },
                         'C':
                             {
                             'Change in area rating':,
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                             'Change in structure rating':
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                             'Frequency of disturbance':
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                             }
                        }
                      ('Habitat B', 'Stressor 1'): {}...
                    }
,
               'habitats': 
                 {'Habitat A':
                        {
                        'DQ': 1.0,
                        'C': 
                            {
                            'Natural Mortality':
                                {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                            'Recruitment Rate':
                                {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                            'Recovery Time':
                                {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                            'Connectivity Rate':
                                {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                            }
                        },
                 'Habitat B': ...
                 }

               'stressors':
                    {'Stressor 1':
                            {
                            'DQ': 1.0,
                            'E':
                                {
                                  'Intensity Rating:':
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                                  'Management Effectiveness:':
                                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                                }
                            },
                     'Stressor 2': ...
                     }
           }"""
    habitat_paths = os.path.join(uri_to_workspace, 'habitat_stressor_ratings', '*_overlap_ratings.csv')
    stressor_paths = os.path.join(uri_to_workspace, 'habitat_stressor_ratings', '*_stressor_ratings.csv')

    habitat_csvs = glob.glob(habitat_paths)
    stressor_csvs = glob.glob(stressor_paths)

    #Parse out stressor names
    LOGGER.debug(stressor_paths)
    stressor_names = [re.search('(.*)_stressor_ratings\.csv', os.path.basename(x)).group(1) for x in stressor_csvs]
    #Parse out habitat names
    habitat_names = [re.search('(.*)_overlap_ratings\.csv', os.path.basename(x)).group(1) for x in habitat_csvs]

    stressor_dict = {}

    for stressor_uri in stressor_csvs:
        LOGGER.debug(stressor_uri)
        stressor_name = re.search('(.*)_stressor_ratings\.csv', os.path.basename(stressor_uri)).group(1)
        stressor_dict[stressor_name] = parse_stressor(stressor_uri)

    habitat_dict = {}
    h_s_dict = {}
    for habitat_uri in habitat_csvs:
        LOGGER.debug(habitat_uri)
        habitat_name = re.search('(.*)_overlap_ratings\.csv', os.path.basename(habitat_uri)).group(1)

        habitat_parse_dictionary = parse_habitat_overlap(habitat_uri)
        habitat_dict[habitat_name] = habitat_parse_dictionary['hab_only']
        for hab_stress_overlap in habitat_parse_dictionary['overlap']:
            h_s_dict[hab_stress_overlap] = habitat_parse_dictionary['overlap'][hab_stress_overlap]

    parse_dictionary = {}
    parse_dictionary['habitat'] = habitat_dict
    parse_dictionary['h-s'] = h_s_dict
    parse_dictionary['stressors'] = stressor_dict

    stressor_buf_dict = {}
    for stressor, stressor_properties in stressor_dict.iteritems():
        stressor_buf_dict[stressor] = stressor_properties['buffer']
        del(stressor_properties['buffer'])

    parse_dictionary['buffer_dict'] = stressor_buf_dict

    return parse_dictionary

def parse_stressor(uri):
    """Helper function to parse out a stressor csv file

        uri - path to the csv file

        returns a dictionary with the stressor information in it as:
           {
            'DQ': 1.0,
            'E':
                {
                  'Intensity Rating:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                  'Management Effectiveness:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                }
           }"""

    stressor_dict = {}
    with open(uri,'rU') as stressor_file:
        csv_reader = csv.reader(stressor_file)
        stressor_name = csv_reader.next()[1]
        data_quality = int(csv_reader.next()[1])
        stressor_dict['DQ'] = data_quality
        stressor_buffer = float(csv_reader.next()[1])
        stressor_dict['buffer'] = stressor_buffer

        #Ignore the next blank line
        csv_reader.next()
        #Get the headers
        headers = csv_reader.next()[1:]
        #Drain the rest of the table
        stressor_dict['E'] = {}
        for row in csv_reader:
            key = row[0]
            properties = dict(zip(headers,map(int,row[1:])))
            stressor_dict['E'][key] = properties

    return stressor_dict

def parse_habitat_overlap(uri):
    """Helper function to parse out the habitat stressor table

        uri - path to the habitat stressor overlap csv table

        returns big ass dictionary"""

    habitat_overlap_dict = {}
    habitat_dict = {}
    with open(uri,'rU') as habitat_file:
        csv_reader = csv.reader(habitat_file)
        hab_name = csv_reader.next()[1]
        #Ignore blank line
        csv_reader.next()
        data_quality = int(csv_reader.next()[1])
        habitat_dict['DQ'] = data_quality
        #Ignore blank line
        csv_reader.next()
        #Get the headers
        headers = csv_reader.next()[1:]
        line = csv_reader.next()
        #Drain the habitat dictionary
        habitat_dict['C'] = {}
        while line[0] != '':
            habitat_dict['C'][line[0]] = dict(zip(headers, map(int,line[1:4])))
            line = csv_reader.next()

        #Drain the next two lines
        for i in range(2): csv_reader.next()
        #Drain the overlap dictionaries
        #This is the overlap header
        while True:
            try:
                line = csv_reader.next()
                LOGGER.debug(line)
                stressor = (line[0].split(hab_name+'/')[1]).split(' ')[0]
                headers = csv_reader.next()[2:]
                #Drain the overlap table
                line = csv_reader.next()
                #Drain the habitat dictionary is the first character of the type field
                habitat_overlap_dict[(hab_name,stressor)] = {'C': {}, 'E': {}}
                while line[0] != '':
                    stressor_type = line[1][0]
                    habitat_overlap_dict[(hab_name,stressor)][stressor_type][line[0]] = dict(zip(headers, map(int,line[2:5])))
                    line = csv_reader.next()
            except StopIteration:
                break

    return {
        'hab_only': habitat_dict,
        'overlap': habitat_overlap_dict
        }
