"""Entry point for the Habitat Risk Assessment module"""

import re
import csv
import os
import glob
import logging
from invest_natcap.habitat_risk_assessment import hra

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')

def execute(args):
    """Want to read in multiple hab/stressors directories, in addition to named
    criteria, and make an appropriate csv file.

    Input:
        args['workspace_dir'] - The directory to dump the output CSV files to.
        args['habitat_dir'] - A directory of shapefiles that are habitats.
        args['species_dir']- Directory which holds all species shapefiles, but
            may or may not actually exist within args.
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors
        args['criteria_dir']- Directory which holds the criteria shapefiles.
            This needs to be in a VERY specific format, which shall be described
            in the user's guide.
        Criteria....dictionary....thing? Would somehow be organized by which
        subcategory they were in, and whether or not they were checked.

    Output:
        hra_args[

        - JSON file containing vars that need to be passed on to hra non-core
            when that gets run. Should live inside the preprocessor folder.
    Returns nothing.
    """

    hra_args = {}

    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #Get the names of all potential habs
    hab_list = []
    for ele in ('habitat_dir', 'species_dir'):
        if ele in args:
            hab_list.append(glob.glob(os.path.join(args[ele], '*.shp')))
            hab_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], hab_list)
    
    #And all potential stressors
    stress_list = []
    stress_list.append(glob.glob(os.path.join(args['stressor_dir'], '*.shp')))
    stress_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], stress_list)


    '''Want to pull the shapefile criteria from the folder structure specified.
    this function will return a dictionary with the following form:
        {'h-s':
            {('HabA', 'Stress1'):
                {'CritName': "Shapefile URI", ...}
            },
         's':
            {'Stress1':
                {'CritName': "Shapefile URI", ...}
            },
         'h':
            {'HabA':
                {'CritName': "Shapefile URI", ...}
        }
    '''
    crit_shapes = hra.make_crit_shape_dict(args['criteria_dir'])
    
    crit_descriptions = {
        'change in area rating': '<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'change in structure rating': '<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'temporal overlap rating': '<enter (3) co-occur 8-12 mo/year, (2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>',
        
        'frequency of disturbance': '<enter (3) Annually or less often, (2) Several times per year, (1) Weekly or more often, (0) no score>',
        'intensity Rating:': '<enter (3) high, (2) medium, (1) low, (0) no score>',
        'management effectiveness:': '<enter (3) not effective, (2) somewhat effective, (1) very effective, (0) no score>',
        'natural mortality': '<enter (3) 0-20%, (2) 20-50%, (1) >80% mortality, or (0) no score>',
        'recruitment rate': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, (1) every <1 yrs, or (0) no score>',
        'recovery time': '<enter (3) >10 yrs, (2) 1-10 yrs, (1) <1 yr, or (0) no score>',
        'connectivity rate': '<enter (3) <10km, (2) 10-100km, (1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited, or (0) unknown>'
    default_weight_message = '<enter (3) more important, (2) equal importance, (1) less important>'
    default_headers = ['', 'Rating', 'DQ', 'Weight']
    default_row = [default_dq_message, default_weight_message]

    #Create habitat-centric output csv's.
    for habitat_name in hab_list:

        csv_filename = os.path.join(output_dir, habitat_name + '_overlap_ratings.csv')
        
        with open(csv_filename, 'wb') as habitat_csv_file:
            habitat_csv_writer = csv.writer(habitat_csv_file)
            #Write the habitat name
            habitat_csv_writer.writerow(['HABITAT NAME', habitat_name])
            habitat_csv_writer.writerow(['HABITAT ONLY PROPERTIES'])
            habitat_csv_writer.writerow(['Habitat Data Quality:', default_dq_message])
            habitat_csv_writer.writerow([])

            habitat_csv_writer.writerow(default_table_headers)

            ##### HERE WILL BE WHERE USER INPUT HABITAT CRITERIA GO.####


            ##### HERE WILL BE WHERE ALL THE H-S USER INPUT CRITERIA GO.####

    #Making stressor specific tables. 
    for stressor_name in name_lookup['stressor']:
        csv_filename = os.path.join(output_dir, stressor_name + '_stressor_ratings.csv')
        with open(csv_filename, 'wb') as stressor_csv_file:
            stressor_csv_writer = csv.writer(stressor_csv_file)
            stressor_csv_writer.writerow(['STRESSOR NAME', stressor_name])
            stressor_csv_writer.writerow(['Stressor Data Quality:', default_dq_message])
            stressor_csv_writer.writerow(['Stressor Buffer (m):', '<enter a buffer region in meters>'])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(default_table_headers)
    
            #### HERE IS WHERE STRESSOR SPECIFIC USER INPUT CRITERIA GO. ####

def parse_hra_tables(worskapce_uri):
    '''This takes in the directory containing the criteria rating csv's, 
    and returns a coherent set of dictionaries that can be used to do EVERYTHING
    in core.

    It will return a massive dictionary containing all of the subdictionaries
    needed by non core. It will be of the following form:

    {'buffer_dict':
        {'Stressor 1': 50,
        'Stressor 2': ...,
        },
    'h-s':
        {(Habitat A, Stressor 1): 
            {'Crit_Ratings': 
                {'CritName': 
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                },
            'Crit_Rasters': 
                {'CritName':
                    {'Weight': 1.0, 'DQ': 1.0}
                },
            }
        },
     'stressors':
        {Stressor 1: 
            {'Crit_Ratings': 
                {'CritName': 
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                },
            'Crit_Rasters': 
                {'CritName':
                    {'Weight': 1.0, 'DQ': 1.0}
                },
            }
        },
     'habitats':
        {Habitat A: 
            {'Crit_Ratings': 
                {'CritName': 
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                },
            'Crit_Rasters': 
                {'CritName':
                    {'Weight': 1.0, 'DQ': 1.0}
                },
            }
        }
    }
    '''

    habitat_paths = os.path.join(uri_to_workspace, '*_overlap_ratings.csv')
    stressor_paths = os.path.join(uri_to_workspace, '*_stressor_ratings.csv')

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

        #Since each habitat CSV has both habitat individual ratings and habitat
        #overlap ratings, need to subdivide them within the return dictionary
        habitat_parse_dictionary = parse_habitat_overlap(habitat_uri)
        habitat_dict[habitat_name] = habitat_parse_dictionary['hab_only']
    
        #For all of the overlaps pertaining to this particular habitat
        for hab_stress_overlap in habitat_parse_dictionary['overlap']:
            h_s_dict[hab_stress_overlap] = habitat_parse_dictionary['overlap'][hab_stress_overlap]

    parse_dictionary = {}
    parse_dictionary['habitats'] = habitat_dict
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
           {'Crit_Ratings':
                {
                  'Intensity Rating:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                  'Management Effectiveness:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                }
            'Crit_Rasters':
                {'Intensity Rating:':
                    {'DQ': 1.0, 'Weight': 1.0},
                  'Management Effectiveness:':
                    {'DQ': 1.0, 'Weight': 1.0}
                }
           }
    """
    stressor_dict = {'Crit_Ratings': {}, 'Crit_Rasters': {}}

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
        
    Input:
        uri - path to the habitat stressor overlap csv table.

    Returns a dictionary of the following form, where any individually named
        stressors actually represent the overlap between the overarching habitat
        and that particular stressor:
        
        {'hab_only':
           {'Crit_Ratings':
                {'Intensity Rating:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0},
                  'Management Effectiveness:':
                    {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                }
            'Crit_Rasters':
                {'Intensity Rating:':
                    {'DQ': 1.0, 'Weight': 1.0},
                  'Management Effectiveness:':
                    {'DQ': 1.0, 'Weight': 1.0}
                }
           },
       'overlap':
            {'stressorName':
               {'Crit_Ratings':
                    {'Intensity Rating:':
                        {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                    }
                'Crit_Rasters':
                    {'Intensity Rating:':
                        {'DQ': 1.0, 'Weight': 1.0}
                    }
               },
            'stressorName2':
               {'Crit_Ratings':
                    {'Intensity Rating:':
                        {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                    }
                'Crit_Rasters':
                    {'Intensity Rating:':
                        {'DQ': 1.0, 'Weight': 1.0}
                    }
               }
            }
        }
    """

    habitat_overlap_dict = {}
    habitat_dict = {}
    with open(uri,'rU') as habitat_file:
        csv_reader = csv.reader(habitat_file)
        hab_name = csv_reader.next()[1]

        #Drain the next two lines
        for _ in range(2): csv_reader.next()
        
        #Get the headers
        headers = csv_reader.next()[1:]
        line = csv_reader.next()
        #Drain the habitat dictionary
        habitat_dict['Crit_Rating'] = {}
        while line[0] != '':
            if line[1] == 'SHAPE':
                habitat_dict['Crit_Rasters'][line[0]] = dict(zip(headers[1:2], map(int, line[2:3]))) 
            else:
                habitat_dict['Crit_Rating'][line[0]] = dict(zip(headers, map(int,line[1:3])))
            line = csv_reader.next()

        #Drain the next two lines
        for _ in range(2): csv_reader.next()
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
                    habitat_overlap_dict[(hab_name, stressor)][stressor_type][line[0]] = dict(zip(headers, map(int,line[2:5])))
                    line = csv_reader.next()
            except StopIteration:
                break

    return {
        'hab_only': habitat_dict,
        'overlap': habitat_overlap_dict
        }
