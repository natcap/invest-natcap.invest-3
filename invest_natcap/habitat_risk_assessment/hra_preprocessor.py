"""Entry point for the Habitat Risk Assessment module"""

import re
import csv
import os
import logging
import json
import fnmatch
import shutil

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')

class MissingHabitatsOrSpecies(Exception):
    '''An exception to pass if the hra_preprocessor args dictionary being
    passed is missing a habitats directory or a species directory.'''
    pass

class NotEnoughCriteria(Exception):
    '''An exception for hra_preprocessor which can be passed if the number of
    criteria in the resilience, exposure, and sensitivity categories all sums
    to less than 4.'''
    pass

class ImproperCriteriaSpread(Exception):
    '''An exception for hra_preprocessor which can be passed if there are not
    one or more criteria in each of the 3 criteria categories: resilience,
    exposure, and sensitivity.'''
    pass

class ZeroDQWeightValue(Exception):
    '''An exception specifically for the parsing of the preprocessor tables in
    which the model shoudl break loudly if a user tries to enter a zero value
    for either a data quality or a weight. However, we should confirm that it
    will only break if the rating is not also zero. If they're removing the
    criteria entirely from that H-S overlap, it should be allowed.'''
    pass

class UnexpectedString(Exception):
    '''An exception for hra_preprocessor that should catch any strings that are
    left over in the CSVs. Since everything from the CSV's are being cast to
    floats, this will be a hook off of python's ValueError, which will re-raise 
    our exception with a more accurate message. '''
    pass

def execute(args):
    """Want to read in multiple hab/stressors directories, in addition to named
    criteria, and make an appropriate csv file.

    Input:
        args['workspace_dir'] - The directory to dump the output CSV files to.
        args['habitats_dir'] - A directory of shapefiles that are habitats. This
            is not required, and may not exist if there is a species layer
            directory.
        args['species_dir']- Directory which holds all species shapefiles, but
            may or may not exist if there is a habitats layer directory.
        args['stressors_dir'] - A directory of ArcGIS shapefiles that are stressors
        args['exposure_crits']- List containing string names of exposure
            (stressor-specific) criteria.
        args['sensitivity-crits']- List containing string names of sensitivity
            (habitat-stressor overlap specific) criteria.
        args['resilience_crits']- List containing string names of resilience
            (habitat or species-specific) criteria.
        args['criteria_dir']- Directory which holds the criteria shapefiles.
            May not exist if the user does not desire criteria shapefiles. This
            needs to be in a VERY specific format, which shall be described in
            the user's guide.

    Output:
        Creation of a series of CSVs within workspace_dir. There will be one CSV
            for every stressor, and one for every habitat/species. These files
            will contain information relevant to each stresor or habitat, 
            including a stressor buffer, as well as criteria names that apply to
            each overlap or individual.

        JSON file containing vars that need to be passed on to hra non-core
          when that gets run. Should live inside the preprocessor folder which
          will be created in 'workspace_dir'. It will contain habitats_dir,
          species_dir, stressors_dir, and criteria_dir.

    Returns nothing.
    """
    #Create two booleans to indicate which of the layers we should be using in
    #this model run.
    do_habs = 'habitats_dir' in args
    do_species = 'species_dir' in args

    #First, want to raise two exceptions if things are wrong.
    #1. Shouldn't be able to run with no species or habitats.
    if not do_species and not do_habs:
    
        raise MissingHabitatsOrSpecies("This model requires you to provide \
                either habitat or species information for comparison against \
                potential stressors.")

    #2. There should be criteria of each type (exposure, sensitivity,
    # resilience).
    if len(args['exposure_crits']) == 0 or len(args['resilience_crits']) == 0 \
            or len(args['sensitivity_crits']) == 0:

        raise ImproperCriteriaSpread("This model requires there to be one \
                criteria in each of the following catagories: Exposure, \
                Sensitivity, and Resilience.")
    
    #3. There should be > 4 criteria total.
    total_crits = len(args['exposure_crits']) + len(args['resilience_crits']) \
                + len(args['sensitivity_crits'])
   
    if total_crits < 4:
        
        raise NotEnoughCriteria("This model requires you to use at least 4 \
                criteria in order to display an accurate picture of habitat \
                risk.")

    #Now we can run the meat of the model. 
    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if os.path.exists(output_dir):
       shutil.rmtree(output_dir)
 
    os.makedirs(output_dir)
   
    #Make the dictionary first, then write the JSON file with the directory
    #pathnames if they exist in args
    json_uri = os.path.join(output_dir, 'dir_names.txt')

    json_dict = {'stressors_dir': args['stressors_dir']}
    for var in ('criteria_dir', 'habitats_dir', 'species_dir'):
        if var in args:
            json_dict[var] = args[var]

    with open(json_uri, 'w') as outfile:

        json.dump(json_dict, outfile)

    #Get the names of all potential habs
    hab_list = []
    for ele in ('habitats_dir', 'species_dir'):
        if ele in args:
            names = listdir(args[ele])
            hab_list = fnmatch.filter(names, '*.shp')
            hab_list = \
                map(lambda uri: os.path.splitext(os.path.basename(uri))[0], 
                            hab_list)
    
    #And all potential stressors
    names = listdir(args['stressors_dir'])
    stress_list = fnmatch.filter(names, '*.shp')
    stress_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], 
                        stress_list)
    
    #Clean up the incoming criteria name strings coming in from the IUI
    exposure_crits = map(lambda name: name.replace('_', ' ').lower(), \
                    args['exposure_crits'])
    resilience_crits = map(lambda name: name.replace('_', ' ').lower(), \
                    args['resilience_crits'])
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
    if 'criteria_dir' in args:
        crit_shapes = make_crit_shape_dict(args['criteria_dir'])
    
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
        'natural mortality rate': '<enter (3) 0-20%, (2) 20-50%, ' +
            '(1) >80% mortality, or (0) no score>',
        'recruitment rate': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, ' +
            '(1) every <1 yrs, or (0) no score>',
        'recovery time': '<enter (3) >10 yrs, (2) 1-10 yrs, ' + 
            '(1) <1 yr, or (0) no score>',
        'connectivity rate': '<enter (3) <10km, (2) 10-100km, ' +
            '(1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited>'
    default_weight_message = '<enter (3) more important, ' + \
        '(2) equal importance, (1) less important>'
    default_table_headers = ['', 'Rating', 'DQ', 'Weight']
    default_row = [default_dq_message, default_weight_message]
    default_rating = ['<enter (3) high, (2) medium, (1) low, (0) no score>']

    #Create habitat-centric output csv's.
    for habitat_name in hab_list:

        csv_filename = os.path.join(output_dir, habitat_name + \
            '_ratings.csv')
        
        with open(csv_filename, 'wb') as habitat_csv_file:
            habitat_csv_writer = csv.writer(habitat_csv_file)
            #Write the habitat name
            habitat_csv_writer.writerow(['HABITAT NAME', habitat_name])
            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT ONLY PROPERTIES'])

            habitat_csv_writer.writerow(default_table_headers)

            ##### HERE WILL BE WHERE USER INPUT HABITAT CRITERIA GO.####
            for c_name in resilience_crits:

                curr_row = default_row

                #Need to first check to make sure that crit_shapes 
                #was instantiated when 
                if 'crit_shapes' in locals() and \
                                (habitat_name in crit_shapes['h'] and \
                                c_name in crit_shapes['h'][habitat_name]):
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
                            ((habitat_name, stressor_name) in crit_shapes['h-s'] and \
                            c_name in crit_shapes['h-s'][(habitat_name, stressor_name)]):

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
                            (stressor_name in crit_shapes['s'] and \
                            c_name in crit_shapes['s'][stressor_name]):

                    curr_row = [c_name] + ['SHAPE'] + curr_row
                elif c_name in crit_descriptions:
                    curr_row = [c_name] + [crit_descriptions[c_name]] + curr_row
                else:
                    curr_row = [c_name] + default_rating + curr_row

                stressor_csv_writer.writerow(curr_row)

def listdir(path):
    '''A replacement for the standar os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Input:
        path- The location container from which we want to gather all files.

    Returns:
        A list of full URIs contained within 'path'.
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris

def parse_hra_tables(workspace_uri):
    #It should be noted here that workspace_uri isn't actually the workspace
    #URI, but is actually the location of the CSV and JSON files that we need
    #to parse through.
    '''This takes in the directory containing the criteria rating csv's, 
    and returns a coherent set of dictionaries that can be used to do EVERYTHING
    in non-core and core.

    It will return a massive dictionary containing all of the subdictionaries
    needed by non core, as well as directory URI's. It will be of the following 
    form:

    {'habitats_dir': 'Habitat Directory URI',
    'species_dir': 'Species Directory URI',
    'stressors_dir': 'Stressors Directory URI',
    'criteria_dir': 'Criteria Directory URI',
    'buffer_dict':
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
    #Create the dictionary in which everything will be stored.
    parse_dictionary = {}

    #Get the arguments out of the json file.
    json_uri = os.path.join(workspace_uri, 'dir_names.txt')

    with open(json_uri, 'rb') as infile:
        parse_dictionary = json.load(infile)
    
    #Now we can compile and add the other dictionaries
    dir_names = listdir(workspace_uri)
    
    all_csvs = [f for f in dir_names if f.endswith('_ratings.csv')]
    stressor_csvs = fnmatch.filter(dir_names, '*_stressor_ratings.csv')
    habitat_csvs = set(all_csvs) - set(stressor_csvs)

    stressor_dict = {}
    for stressor_uri in stressor_csvs:
      
        stressor_name = re.search('(.*)_stressor_ratings\.csv', 
                                os.path.basename(stressor_uri)).group(1)
        stressor_dict[stressor_name] = parse_stressor(stressor_uri)

    habitat_dict = {}
    h_s_dict = {}

    for habitat_uri in habitat_csvs:
        
        base_hab_name = os.path.basename(habitat_uri)
        habitat_name = re.search('(.*)_ratings\.csv', base_hab_name).group(1)

        #Since each habitat CSV has both habitat individual ratings and habitat
        #overlap ratings, need to subdivide them within the return dictionary
        habitat_parse_dictionary = parse_habitat_overlap(habitat_uri)
        habitat_dict[habitat_name] = habitat_parse_dictionary['hab_only']
    
        #For all of the overlaps pertaining to this particular habitat,
        #hab_stress_overlap is a stressor name which overlaps our habitat
        for hab_stress_overlap in habitat_parse_dictionary['overlap']:
            h_s_dict[(habitat_name, hab_stress_overlap)] = \
                        habitat_parse_dictionary['overlap'][hab_stress_overlap]

    #Should note: these are references to the dictionaries. If we change the
    #properties of them, they will change within parse_dictionary.
    parse_dictionary['habitats'] = habitat_dict
    parse_dictionary['h-s'] = h_s_dict
    parse_dictionary['stressors'] = stressor_dict
       
    #Add the stressors in after to make the dictionary traversal easier before
    #this. We already know that the values in here are floats, since we checked 
    #them as they were placed in there.
    stressor_buf_dict = {}
    for stressor, stressor_properties in stressor_dict.iteritems():
        stressor_buf_dict[stressor] = stressor_properties['buffer']
        del(stressor_properties['buffer'])

    parse_dictionary['buffer_dict'] = stressor_buf_dict

    #At this point, we want to check for 0 or null values in any of the
    #subdictionaries subpieces, and if we find any, remove that whole criteria
    #from the assessment for that subdictionary. Abstracting this to a new function.
    zero_null_val_check(parse_dictionary)

    return parse_dictionary

def zero_null_val_check(parse_dictionary):
    '''Helper function to remove criteria whose ratings is a 0, or raise an
    exception if the DQ or Weight is 0.

        {'habitats_dir': 'Habitat Directory URI',
        'species_dir': 'Species Directory URI',
        'stressors_dir': 'Stressors Directory URI',
        'criteria_dir': 'Criteria Directory URI',
        'buffer_dict':
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
    for subdict_lvl1 in parse_dictionary.values():
        
        #Sometimes will find strings here that are coming from the JSON object
        #URIs being passed in. Just skip them.
        try:
            for subdict_lvl2 in subdict_lvl1.values():
                #Sometimes will find floats here that are coming from the buffer
                #subdictionary. Skip them.
                try:
                    for subdict_lvl3 in subdict_lvl2.values():

                        #This is an actual list copy of the resulting dictionary.
                        for key4, subdict_lvl4 in subdict_lvl3.items():
                            
                            #If they have listed the rating as 0, they do not
                            #want that to be an applicable criteria. Need to first
                            #check that it has a 'Rating' spot, instead of nothing
                            #if it was listed as SHAPE
                            if 'Rating' in subdict_lvl4 and subdict_lvl4['Rating'] in [0, 0.0]:
                                
                                del subdict_lvl3[key4]
                            
                            else:
                                #Now that we know that they want this criteria, we
                                #need to make sure their DQ and W have been entered
                                #properly
                                for val in subdict_lvl4['DQ'], subdict_lvl4['Weight']:
                                    #We already know that it's not null, since that
                                    #was checked as it was added to the dictionary,
                                    #so we can just check for 0's.
                                    if val in [0, 0.0]:
                                        
                                        raise ZeroDQWeightValue("Individual criteria \
                                            data qualities and weights may not be 0.")

                except AttributeError:
                    #If we can't iterrate into it, it's not a subdictionary,
                    #can skip.
                    pass

        except AttributeError:
            #If we can't iterrate into it, it's not a subdictionary, and we're
            #safe to ignore it.
            pass

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
                },
           'buffer': StressBuffNum
           }
    """
    stressor_dict = {'Crit_Ratings': {}, 'Crit_Rasters': {}}
    with open(uri,'rU') as stressor_file:
        csv_reader = csv.reader(stressor_file)
      
        s_name = csv_reader.next()[1]

        #Skip the blank line
        csv_reader.next()

        #pull the stressor buffer from the second part of the third line
        try:
            stressor_buffer = float(csv_reader.next()[1])
        except ValueError:
            raise UnexpectedString("Entries in CSV table may not be \
                strings, and may not be left blank. Check your " + s_name + " CSV \
                for any leftover strings or spaces within Buffer, Rating, \
                Data Quality or Weight columns.")
        
        stressor_dict['buffer'] = stressor_buffer

        #Ignore the next blank line
        csv_reader.next()
        #Get the headers
        headers = csv_reader.next()[1:]
        
        #Drain the rest of the table
        for row in csv_reader:
            key = row[0]
            
            if row[1] == 'SHAPE':
                #Guarding against strings or null values being passed.
                try:
                    stressor_dict['Crit_Rasters'][key] = \
                        dict(zip(headers[1:3],map(float,row[2:4])))
                except ValueError:
                    raise UnexpectedString("Entries in CSV table may not be \
                        strings, and may not be left blank. Check your %s CSV \
                        for any leftover strings or spaces within Buffer, Rating, \
                        Data Quality or Weight columns.", s_name)
            #This should catch any instances where the rating is a string, but
            #is not SHAPE (aka- is leftover from the user's guide population)
            else:
                try:
                    stressor_dict['Crit_Ratings'][key] = \
                        dict(zip(headers,map(float,row[1:])))
                except ValueError:
                    raise UnexpectedString("Entries in CSV table may not be \
                        strings, and may not be left blank. Check your %s CSV \
                        for any leftover strings or spaces within Buffer, Rating, \
                        Data Quality or Weight columns.", s_name)
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
            
            key = line[0]

            #If we are dealing with a shapefile criteria, we only want  to
            #add the DQ and the W, and we will add a rasterized version of
            #the shapefile later.
            if line[1] == 'SHAPE':
                try:
                    habitat_dict['Crit_Rasters'][key] = \
                        dict(zip(headers[1:3], map(float, line[2:4])))
                except ValueError:
                    raise UnexpectedString("Entries in CSV table may not be \
                        strings, and may not be left blank. Check your %s CSV \
                        for any leftover strings or spaces within Rating, \
                        Data Quality or Weight columns.", hab_name)
            #Should catch any leftovers from the autopopulation of the helptext        
            else:
                try:
                    habitat_dict['Crit_Ratings'][key] = \
                        dict(zip(headers, map(float,line[1:4])))
                except ValueError:
                    raise UnexpectedString("Entries in CSV table may not be \
                        strings, and may not be left blank. Check your %s CSV \
                        for any leftover strings or spaces within Rating, \
                        Data Quality or Weight columns.", hab_name)
            
            line = csv_reader.next()

        #Drain the next two lines
        for _ in range(2): 
            csv_reader.next()
        
        #Drain the overlap dictionaries
        #This is the overlap header
        while True:
            try:
                line = csv_reader.next()
                stressor = (line[0].split(hab_name+'/')[1]).split(' ')[0]
                headers = csv_reader.next()[1:]
                
                #Drain the overlap table
                line = csv_reader.next()
                
                #Drain the habitat dictionary is the first character of the
                #type field
                habitat_overlap_dict[stressor] = {'Crit_Ratings': {}, \
                        'Crit_Rasters': {}}
                while line[0] != '':
                    if line[1] == 'SHAPE':
                        #Going to do some custom error checking for null values or strings.
                        try:                    
                        #Only include DQ and W headers, since 'rating' will come
                        #in the form of a shapefile.
                            habitat_overlap_dict[stressor]['Crit_Rasters'][line[0]] = \
                                dict(zip(headers[1:3], map(float,line[2:4])))
                        except ValueError:
                            raise UnexpectedString("Entries in CSV table may not be \
                                strings, and may not be left blank. Check your %s CSV \
                                for any leftover strings or spaces within Rating, \
                                Data Quality or Weight columns." % hab_name)
                    else:
                        #Going to do some custom error checking for null values or strings.
                        try:
                            habitat_overlap_dict[stressor]['Crit_Ratings'][line[0]] = \
                                dict(zip(headers, map(float,line[1:4])))
                        except ValueError:
                            raise UnexpectedString("Entries in CSV table may not be \
                                strings, and may not be left blank. Check your %s CSV \
                                for any leftover strings or spaces within Rating, \
                                Data Quality or Weight columns." % hab_name)

                    line = csv_reader.next()

            except StopIteration:
                break

    return {
        'hab_only': habitat_dict,
        'overlap': habitat_overlap_dict
        }

def make_crit_shape_dict(crit_uri):
    '''This will take in the location of the file structure, and will return
    a dictionary containing all the shapefiles that we find. Hypothetically, we
    should be able to parse easily through the files, since it should be
    EXACTLY of the specs that we laid out.
    
    Input:
        crit_uri- Location of the file structure containing all of the shapefile
            criteria.


    Returns:
        A dictionary containing shapefile URI's, indexed by their criteria name,
        in addition to which dictionaries and h-s pairs they apply to. The
        structure will be as follows:
        
        {'h-s':
            {('HabA', 'Stress1'):
                {'CriteriaName': "Shapefile Datasource URI", ...}, ...
            },
         'h':
            {'HabA':
                {'CriteriaName: "Shapefile Datasource URI"...}, ...
            },
         's':
            {'Stress1':
                {'CriteriaName: "Shapefile Datasource URI", ...}, ...
            }
        }
    '''
    c_shape_dict = {'h-s':{}, 'h': {}, 's':{}}
    
    res_dir = os.path.join(crit_uri, 'Resilience')
    exps_dir = os.path.join(crit_uri, 'Exposure')
    sens_dir = os.path.join(crit_uri, 'Sensitivity')
 
    for folder in [res_dir, exps_dir, sens_dir]:
        if not os.path.isdir(folder):
    
            raise IOError("Using spatically explicit critiera requires you to \
                    have subfolders named \"Resilience\", \"Exposure\", and \
                    \"Sensitivity\". Check that all these folders exist, and \
                    that your criteria are placed properly.")
    
    #First, want to get the things that are either habitat specific or 
    #species specific. These should all be in the 'Resilience subfolder
    #of raster_criteria.
    res_names = listdir(os.path.join(crit_uri, 'Resilience'))
    res_shps = fnmatch.filter(res_names, '*.shp')   
    
    #Now we have a list of all habitat specific shapefile criteria. Now we need
    #to parse them out.
    for path in res_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the second part to all be one piece
        parts = filename.split('_', 1)
        hab_name = parts[0]
        crit_name = parts[1].replace('_', ' ').lower()

        if hab_name not in c_shape_dict['h']:
            c_shape_dict['h'][hab_name] = {}
        
        c_shape_dict['h'][hab_name][crit_name] = path
                   
    
    #Now, want to move on to stressor-centric criteria, but will do much the
    #same thing. 
    exps_names = listdir(os.path.join(crit_uri, 'Exposure'))
    exps_shps = fnmatch.filter(exps_names, '*.shp')   
   
    #Now we have a list of all stressor specific shapefile criteria. 
    #Now we need to parse them out.
    for path in exps_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the second part to all be one piece
        parts = filename.split('_', 1)
        stress_name = parts[0]
        crit_name = parts[1].replace('_', ' ')

        if stress_name not in c_shape_dict['s']:
            c_shape_dict['s'][stress_name] = {}
        
        c_shape_dict['s'][stress_name][crit_name] = path
    
    #Finally, want to get all of our pair-centric shape criteria. 
    sens_names = listdir(os.path.join(crit_uri, 'Sensitivity'))
    sens_shps = fnmatch.filter(sens_names, '*.shp')   
   
    #Now we have a list of all pair specific shapefile criteria. 
    #Now we need to parse them out.
    for path in sens_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the first and second part to be separate, since they are the
        #habitatName and the stressorName, but want the criteria name to be
        #self contained.
        parts = filename.split('_', 2)
        hab_name = parts[0]
        stress_name = parts[1]
        crit_name = parts[2].replace('_', ' ')

        if (hab_name, stress_name) not in c_shape_dict['h-s']:
            c_shape_dict['h-s'][(hab_name, stress_name)] = {}
        
        c_shape_dict['h-s'][(hab_name, stress_name)][crit_name] = path

    #Et, voila! C'est parfait.
    return c_shape_dict
