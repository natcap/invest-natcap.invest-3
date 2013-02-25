"""Entry point for the Habitat Risk Assessment module"""

import re
import csv
import os
import glob
import logging
import hra
#from invest_natcap.habitat_risk_assessment import hra

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')

class MissingHabitatsOrSpecies(Exception):
    '''An exception to pass if the hra_preprocessor args dictionary being
    passed is missing a habitats directory or a species directory.'''
    pass

class NotEnoughCriteria(Exception):
    '''An exception for hra_preprocessor which can be passed if the number of
    criteria in the resiliance, exposure, and sensitivity categories all sums
    to less than 4.'''
    pass

class ImproperCriteriaSpread(Exception):
    '''An exception for hra_preprocessor which can be passed if there are not
    one or more criteria in each of the 3 criteria categories: resiliance,
    exposure, and sensitivity.'''
    pass

def execute(args):
    """Want to read in multiple hab/stressors directories, in addition to named
    criteria, and make an appropriate csv file.

    Input:
        args['workspace_dir'] - The directory to dump the output CSV files to.
        args['do_habitats']- Boolean indicating whether or not purely habitat
            inputs are desired within this model.
        args['habitat_dir'] - A directory of shapefiles that are habitats.
        args['do_species']- Boolean indication whether species should be used as
            input to this model run.
        args['species_dir']- Directory which holds all species shapefiles, but
            may or may not actually exist within args if 'do_species' is false.
        args['stressors_dir'] - A directory of ArcGIS shapefiles that are stressors
        args['exposure_crits']- List containing string names of exposure
            (stressor-specific) criteria.
        args['sensitivity-crits']- List containing string names of sensitivity
            (habitat-stressor overlap specific) criteria.
        args['resiliance_crits']- List containing string names of resiliance
            (habitat or species-specific) criteria.
        args['do_shapes']- Boolean to specify whether or not shapefile criteria
            should be used in this run of the model.
        args['criteria_dir']- Directory which holds the criteria shapefiles.
            This needs to be in a VERY specific format, which shall be described
            in the user's guide.

    Output:
        Creation of a series of CSVs within workspace_dir. There will be one CSV
            for every stressor, and one for every habitat/species. These files
            will contain information relevant to each stresor or habitat, 
            including a stressor buffer, as well as criteria names that apply to
            each overlap or individual.

        JSON file containing vars that need to be passed on to hra non-core
          when that gets run. Should live inside the preprocessor folder which
          will be created in 'workspace_dir'. 

    Returns nothing.
    """
    #First, want to raise two exceptions if things are wrong.
    #1. Shouldn't be able to run with no species or habitats.
    if not args['do_species'] and not args['do_habitats']:
    
        raise MissingHabitatsOrSpecies("This model requires you to provide \
                either habitat or species information for comparison against \
                potential stressors.")

    #2. There should be criteria of each type (exposure, sensitivity,
    # resiliance).
    if len(args['exposure_crits']) == 0 or len(args['resiliance_crits']) == 0 \
            or len(args['sensitivity_crits']) == 0:

        raise ImproperCriteriaSpread("This model requires there to be one \
                criteria in each of the following catagories: Exposure, \
                Sensitivity, and Resiliance.")
    
    #3. There should be > 4 criteria total.
    total_crits = len(args['exposure_crits']) + len(args['resiliance_crits']) \
                + len(args['sensitivity_crits'])
   
    if total_crits < 4:
        
        raise NotEnoughCriteria("This model requires you to use at least 4 \
                criteria in order to display an accurate picture of habitat \
                risk.")

    #Now we can run the meat of the model. 
    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    #Get the names of all potential habs
    hab_list = []
    for ele in ('habitat_dir', 'species_dir'):
        if ele in args:
            hab_list = hab_list + glob.glob(os.path.join(args[ele], '*.shp'))
            hab_list = \
                map(lambda uri: os.path.splitext(os.path.basename(uri))[0], 
                            hab_list)
    
    #And all potential stressors
    stress_list = []
    stress_list = stress_list + glob.glob(os.path.join(args['stressors_dir'], '*.shp'))
    stress_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], 
                        stress_list)

    #Clean up the incoming criteria name strings coming in from the IUI
    exposure_crits = map(lambda name: name.replace('_', ' ').lower(), \
                    args['exposure_crits'])
    resiliance_crits = map(lambda name: name.replace('_', ' ').lower(), \
                    args['resiliance_crits'])
    sensitivity_crits = map(lambda name: name.replace('_', ' ').lower(), \
                    args['sensitivity_crits'])
    
    '''If shapefile criteria are desired, want to pull the shapefile criteria 
    from the folder structure specified. This function will return a dictionary
    with the following form:
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
    if args['do_shapes']:
        crit_shapes = hra.make_crit_shape_dict(args['criteria_dir'])
    
    crit_descriptions = {
        'change in area rating': '<enter (3) 50-100% loss, ' + 
            '(2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'change in structure rating': '<enter (3) 50-100% loss, ' + 
            '(2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'temporal overlap rating': '<enter (3) co-occur 8-12 mo/year, ' + 
            '(2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>',
        'frequency of disturbance': '<enter (3) Annually or less often, ' +
            '(2) Several times per year, (1) Weekly or more often, ' + \
            '(0) no score>',
        'intensity rating': '<enter (3) high, (2) medium, ' +
            '(1) low, (0) no score>',
        'management effectiveness': '<enter (3) not effective, ' +
            '(2) somewhat effective, (1) very effective, (0) no score>',
        'natural mortality': '<enter (3) 0-20%, (2) 20-50%, ' +
            '(1) >80% mortality, or (0) no score>',
        'recruitment rate': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, ' +
            '(1) every <1 yrs, or (0) no score>',
        'recovery time': '<enter (3) >10 yrs, (2) 1-10 yrs, ' + 
            '(1) <1 yr, or (0) no score>',
        'connectivity rate': '<enter (3) <10km, (2) 10-100km, ' +
            '(1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited, '  + \
        'or (0) unknown>'
    default_weight_message = '<enter (3) more important, ' + \
        '(2) equal importance, (1) less important>'
    default_table_headers = ['', 'Rating', 'DQ', 'Weight']
    default_row = [default_dq_message, default_weight_message]
    default_rating = ['<enter (3) high, (2) medium, (1) low, (0) no score>']

    #Create habitat-centric output csv's.
    for habitat_name in hab_list:

        csv_filename = os.path.join(output_dir, habitat_name + \
            '_overlap_ratings.csv')
        
        with open(csv_filename, 'wb') as habitat_csv_file:
            habitat_csv_writer = csv.writer(habitat_csv_file)
            #Write the habitat name
            habitat_csv_writer.writerow(['HABITAT NAME', habitat_name])
            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT ONLY PROPERTIES'])
            habitat_csv_writer.writerow([])

            habitat_csv_writer.writerow(default_table_headers)

            ##### HERE WILL BE WHERE USER INPUT HABITAT CRITERIA GO.####
            for c_name in resiliance_crits:

                curr_row = default_row

                #Need to first check to make sure that crit_shapes 
                #was instantiated when 
                if 'crit_shapes' in locals() and \
                                    c_name in crit_shapes['h'][habitat_name]:
                    curr_row = [c_name] + ['SHAPE'] + curr_row
                elif c_name in crit_descriptions:
                    curr_row = [c_name] + [crit_descriptions[c_name]] + curr_row
                else:
                    curr_row = [c_name] + default_rating + curr_row

                habitat_csv_writer.writerow(curr_row)

            ##### HERE WILL BE WHERE ALL THE H-S USER INPUT CRITERIA GO.####
            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT STRESSOR OVERLAP PROPERTIES'])
            
            for stressor_name in stress_list:
                
                habitat_csv_writer.writerow([])
                habitat_csv_writer.writerow([habitat_name + '/' + \
                        stressor_name + ' OVERLAP'])
                habitat_csv_writer.writerow(default_table_headers)

                for c_name in sensitivity_crits:
                
                    curr_row = default_row

                    if 'crit_shapes' in locals() and \
                        c_name in crit_shapes['h-s'][(habitat_name, stressor_name)]:

                        curr_row = [c_name] + ['SHAPE'] + curr_row
                    elif c_name in crit_descriptions:

                        curr_row = [c_name] + [crit_descriptions[c_name]] + curr_row
                    else:
                        curr_row = [c_name] + default_rating + curr_row

                    habitat_csv_writer.writerow(curr_row)
    
    #Making stressor specific tables. 
    for stressor_name in stress_list:

        csv_filename = os.path.join(output_dir, stressor_name + \
                        '_stressor_ratings.csv')
    
        with open(csv_filename, 'wb') as stressor_csv_file:
            stressor_csv_writer = csv.writer(stressor_csv_file)
            stressor_csv_writer.writerow(['STRESSOR NAME', stressor_name])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(['Stressor Buffer (m):', \
                    '<enter a buffer region in meters>'])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(default_table_headers)

            #### HERE IS WHERE STRESSOR SPECIFIC USER INPUT CRITERIA GO. ####
            for c_name in exposure_crits:
            
                curr_row = default_row

                if 'crit_shapes' in locals() and \
                            c_name in crit_shapes['s'][stressor_name]:

                    curr_row = [c_name] + ['SHAPE'] + curr_row
                elif c_name in crit_descriptions:
                    curr_row = [c_name] + [crit_descriptions[c_name]] + curr_row
                else:
                    curr_row = [c_name] + default_rating + curr_row

                stressor_csv_writer.writerow(curr_row)
            
def parse_hra_tables(workspace_uri):
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

    habitat_paths = os.path.join(workspace_uri, '*_overlap_ratings.csv')
    stressor_paths = os.path.join(workspace_uri, '*_stressor_ratings.csv')

    habitat_csvs = glob.glob(habitat_paths)
    stressor_csvs = glob.glob(stressor_paths)
    
    stressor_dict = {}
    for stressor_uri in stressor_csvs:
        
        stressor_name = re.search('(.*)_stressor_ratings\.csv', 
                                os.path.basename(stressor_uri)).group(1)
        stressor_dict[stressor_name] = parse_stressor(stressor_uri)

    habitat_dict = {}
    h_s_dict = {}

    for habitat_uri in habitat_csvs:
        
        habitat_name = re.search('(.*)_overlap_ratings\.csv', 
                                os.path.basename(habitat_uri)).group(1)

        #Since each habitat CSV has both habitat individual ratings and habitat
        #overlap ratings, need to subdivide them within the return dictionary
        habitat_parse_dictionary = parse_habitat_overlap(habitat_uri)
        habitat_dict[habitat_name] = habitat_parse_dictionary['hab_only']
    
        #For all of the overlaps pertaining to this particular habitat,
        #hab_stress_overlap is a stressor name which overlaps our habitat
        for hab_stress_overlap in habitat_parse_dictionary['overlap']:
            h_s_dict[(habitat_name, hab_stress_overlap)] = \
                        habitat_parse_dictionary['overlap'][hab_stress_overlap]

    parse_dictionary = {}
    parse_dictionary['habitats'] = habitat_dict
    parse_dictionary['h-s'] = h_s_dict
    parse_dictionary['stressors'] = stressor_dict
    
    LOGGER.debug(parse_dictionary)

    #At this point, we want to check for 0 or null values in any of the
    #subdictionaries subpieces, and if we find any, remove that whole criteria
    #from the assessment for that subdictionary.
    for subdict in parse_dictionary.values():
        for indivs in subdict.values():
            for kind in indivs.values():
                for crit_name, crit_dict in kind.iteritems():
                    for value in crit_dict.values():
                        if value in [0, '']:
                            del(kind[crit_name])
                            #Breaking because crit_dict won't contain crit_name
                            break

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
      
        #Skip first two lines
        for _ in range(2): 
            csv_reader.next()

        #pull the stressor buffer from the second part of the third line
        stressor_buffer = float(csv_reader.next()[1])
        stressor_dict['buffer'] = stressor_buffer

        #Ignore the next blank line
        csv_reader.next()
        #Get the headers
        headers = csv_reader.next()[1:]
        
        #Drain the rest of the table
        for row in csv_reader:
            key = row[0]
            
            if row[1] == 'SHAPE':
                stressor_dict['Crit_Rasters'][key] = \
                        dict(zip(headers[1:3],map(int,row[2:4])))
            else:
                stressor_dict['Crit_Ratings'][key] = \
                        dict(zip(headers,map(int,row[1:])))
                
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
    habitat_dict = {'Crit_Rasters': {}, 'Crit_Ratings':{}}
    with open(uri,'rU') as habitat_file:
        csv_reader = csv.reader(habitat_file)
        hab_name = csv_reader.next()[1]

        #Drain the next two lines
        for _ in range(2): 
            csv_reader.next()
        
        #Get the headers
        headers = csv_reader.next()[1:]
        line = csv_reader.next()

        #Drain the habitat dictionary
        while line[0] != '':
            LOGGER.debug(line)        
            key = line[0]

            if line[1] == 'SHAPE':
                #If we are dealing with a shapefile criteria, we only want  to
                #add the DQ and the W, and we will add a rasterized version of
                #the shapefile later.
                habitat_dict['Crit_Rasters'][key] = \
                        dict(zip(headers[1:3], map(int, line[2:4]))) 
            else:
                habitat_dict['Crit_Ratings'][key] = \
                        dict(zip(headers, map(int,line[1:4])))
            line = csv_reader.next()

        #Drain the next two lines
        for _ in range(2): 
            csv_reader.next()
        
        #Drain the overlap dictionaries
        #This is the overlap header
        while True:
            try:
                line = csv_reader.next()
                LOGGER.debug(line)
                stressor = (line[0].split(hab_name+'/')[1]).split(' ')[0]
                headers = csv_reader.next()[1:]
                LOGGER.debug(headers)
                #Drain the overlap table
                line = csv_reader.next()
                LOGGER.debug(line)
                #Drain the habitat dictionary is the first character of the
                #type field
                habitat_overlap_dict[stressor] = {'Crit_Ratings': {}, \
                        'Crit_Rasters': {}}
                while line[0] != '':
                    if line[1] == 'SHAPE':
                        #Only include DQ and W headers
                        habitat_overlap_dict[stressor]['Crit_Rasters'][line[0]] = \
                                dict(zip(headers[1:3], map(int,line[2:4])))
                    else:
                        habitat_overlap_dict[stressor]['Crit_Ratings'][line[0]] = \
                                dict(zip(headers, map(int,line[1:4])))
                    line = csv_reader.next()
            except StopIteration:
                break

    return {
        'hab_only': habitat_dict,
        'overlap': habitat_overlap_dict
        }
