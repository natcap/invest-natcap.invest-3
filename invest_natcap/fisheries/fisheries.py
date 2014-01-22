'''This will be the entry point for the fisheries tier 1 model. It will pass
any calculation onto fisheries_core.py.'''

import logging
import os
import shutil
import csv

from osgeo import ogr
from invest_natcap.fisheries import fisheries_core

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class ImproperStageParameter(Exception):
    '''This exception will occur if the stage-specific headings in the main 
    parameter CSV are not included in the set of known parameters.'''
    pass
class ImproperAreaParameter(Exception):
    '''This exception will occur if the area-specific headings in the main 
    parameter CSV are not included in the set of known parameters.'''
    pass
class MissingRecruitmentParameter(Exception):
    '''This should be raised if the dropdown equation does not match the
    parameters provided, and additional information is needed. That might
    be in the form of alpha/beta, the CSV, or a numerical recruitment number.
    '''
    pass
class MissingVulnFishingParameter(Exception):
    '''This should be raised if the species main parameter CSV is missing a
    VulnFishing column. It is a required input for the survival equation.'''
    pass
class MissingExpFracParameter(Exception):
    '''Exception should be raised if the species main parameter CSV is missing
    a ExploitationFraction for each AOI subregion included. It is a required
    input for the survival equation.'''
    pass
class MissingMaturityParameter(Exception):
    '''Exception should be raised if the species main parameter CSV is missing
    a Maturity parameter for ages/stages. It is a required paramater if the
    recruitment equation being used is B-H, Ricker, or Fecundity.'''
    pass

def execute(args):
    '''This function will prepare files to be passed to the fisheries core
    module.
    
    Inputs:
        workspace_uri- Location into which all intermediate and output files
            should be placed.
        aoi_uri- Location of shapefile which will be used as subregions for
            calculation. Each region must conatin a 'name' attribute which will
            be used for any parameters that vary by area.
        class_params_uri- Location of the parameters csv. This will contain all
            age and stage specific parameters.
        maturity_type- String specifying whether the model is age-specific or
            stage-specific. Options will be either "Age Specific" or
            "Stage Specific" and will change which equation is used in modeling
            growth.
        num_classes- The number of maturity classes that the user will be
            providing within the main parameter csv.
        is_gendered- Boolean for whether or not the age and stage classes are
            separated by gender.
        rec_eq- The equation to be used in calculation of recruitment. Choices
            are strings, and will be one of "Beverton-Holt", "Ricker", 
            "Fecundity", or "Fixed."
        alpha(*)- Must exist within args if rec_eq == "Beverton-Holt" or 
            "Ricker" . Parameter that will be used in calculation of
            recruitment.
        beta(*)- Must exist within args if rec_eq == "Beverton-Holt" or 
            "Ricker" . Parameter that will be used in calculation of
            recruitment.
        fec_params_uri(*)- Must exist within args if rec_eq == "Fecundity".
            Location of the csv conatining parameters to be used in calculation
            of recruitment.
        fix_param(*)- Must exist within args if rec_eq == "Fixed". Parameter
            that will be used in calculation of recruitment. 
        init_recruits- Int which represents the initial number of recruits that
            will be used in calculation of population on a per area basis. 
        mig_params_uri(*)- If this parameter exists, it means migration is
            desired. This is  the location of the parameters folder containing
            files for migration. There should be one for every age class which
            migrates.
        frac_post_process(*)- This will exist only if valuation is desired for
            the particular species. A double representing the fraction of the
            animal remaining after processing of the whole carcass is complete.
        unit_price(*)- This will exist only if valuation is desired. Double 
            which represents the price for a single unit of that animal.
        duration- Int representing the number of time steps that the user
            desires the model to run.
    '''
    core_args = {}

    #Create folders that will be used for the rest of the model run.
    for folder in ['Intermediate', 'Output']:
        
        out_dir = os.path.join(args['workspace_uri'], folder)
        
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        os.makedirs(out_dir)

    #Do all error checking for the different recruitment equations, since
    #we can't continue if we don't have data.
    if args['rec_eq'] == 'Beverton-Holt' or args['rec_eq'] == 'Ricker':
        if 'alpha' not in args or 'beta' not in args:
            raise MissingRecruitmentParameter("For the recruitment equation \
                        chosen, there are missing parameters. Both an alpha \
                        and a beta parameter are necessary. Please look at \
                        the help text provided next to the recruitment equation\
                        selection, and add the necessary additional information.")
    if args['rec_eq'] == 'Fecundity' and 'fec_params_uri' not in args:
        raise MissingRecruitmentParameter("For the recruitment equation \
                    chosen, there are missing parameters.  A CSV for fecundity\
                    by AOI zone is necessary. Please look at the help text \
                    provided next to the recruitment equation selection, and \
                    add the necessary additional information.")
    if args['rec_eq'] == 'Fixed' and 'fix_param' not in args:
        raise MissingRecruitmentParameter("For the recruitment equation \
                    chosen, there are missing parameters.  A fixed recruitment\
                    number is necessary. Please look at the help text \
                    provided next to the recruitment equation selection, and \
                    add the necessary additional information.")

    #Want to know how many areas we're dealing with
    aoi_ds = ogr.Open(args['aoi_uri'])
    aoi_layer = aoi_ds.GetLayer()
    area_count = aoi_layer.GetFeatureCount()

    #Calculate the classes main param info, and add it to the core args dict
    classes_dict, ordered_stages = parse_main_csv(args['class_params_uri'], area_count,
                                args['rec_eq'])
    core_args['params_dict'] = classes_dict
    core_args['ordered_stages'] = ordered_stages

    #If migration is desired, get all the info, and add to the core args dict
    if 'mig_params_uri' in args:
        migration_dict = parse_migration_tables(args['mig_params_uri'])
        core_args['migrate_dict'] = migration_dict

    #Recruitment- already know that the correct params exist
    '''Want to make a single dictionary to pass with the correct arguments.
    Dictionary will look like one of the following:
        {'Beverton-Holt': {'alpha': 0.02, 'beta': 3}}
        {'Ricker': {'alpha': 0.02, 'beta': 3}}
        {'Fecundity': {FECUNDITY DICT}}
        {'Fixed': 0.5}
   ''' 
    if args['rec_eq'] == 'Beverton-Holt' or args['rec_eq'] == 'Ricker':
        key = 'Ricker' if args['rec_eq'] == 'Ricker' else 'Beverton-Holt'
        rec_dict = {key: {'alpha': args['alpha'], 'beta': args['beta']}}
    elif args['rec_eq'] == 'Fecundity':
        rec_dict = {'Fecundity': args['fec_params_dict']}
    else:
        rec_dict = {'Fixed': args['fix_param']}
    
    LOGGER.debug(rec_dict)
    core_args['rec_dict'] = rec_dict


    #Direct pass all these variables
    core_args['workspace_uri'] = args['workspace_uri']
    core_args['maturity_type'] = args['maturity_type']
    core_args['is_gendered'] = args['is_gendered']
    core_args['init_recruits'] = args['init_recruits']
    core_args['duration'] = args['duration']

    possible_vars = ['frac_post_process', 'unit_price']
    for var in possible_vars:
        if var in args:
            core_args[var] = args[var]

    fisheries_core.execute(core_args)

def parse_fec_csv(fec_uri):
    '''This function will be used if the recruitment equation of choice is 
    fecundity. The CSV passed in will contain all parameters relevant to
    fecundity.
    
    Input:
        fec_uri- The location of the CSV file containing all pertinent
            information for fecundity.
    '''
    return

def parse_migration_tables(mig_folder_uri):
    '''Want to take all of the files within the migration parameter folder, and
    glean relavant information from them. Should return a single dictionary
    containing all migration data for all applicable age/stages.
    
    Input:
        mig_folder_uri- The location of the outer folder containing all
            source/sink migration information for any age/stages which migrate.

    Returns:
        mig_dict- Migration dictionary which will contain all source/sink
            percentage information for each age/stage which is capable of
            migration. The outermost numerical key is the source, and the
            keys of the dictionary that points to are the sinks.

            {'egg': {'1': {'1': 98.66, '2': 1.31, ...},
                    '2': {'1': 0.13, '2': 98.06, ...}
            }
    '''
    mig_dict = {}

    mig_files = listdir(mig_folder_uri)

    for mig_table_uri in mig_files:
        
        basename = os.path.splitext(os.path.basename(mig_table_uri))[0]
        stage_name = basename.split('migration_').pop()
        mig_dict[stage_name] = {}

        #Now, the actual file reading
        with open(mig_table_uri, 'rU') as mig_file:

            csv_reader = csv.reader(mig_file)

            headers = csv_reader.next()
            #First cell of the headers is a blank
            headers.pop(0)

            for source in headers:
                mig_dict[stage_name][source] = {}

            while True:
                try:
                    line = csv_reader.next()
                    sink = line.pop(0)
                    
                    for i, source in enumerate(headers):
                        mig_dict[stage_name][source][sink] = line[i]
                
                except StopIteration:
                    break

    return mig_dict

def parse_main_csv(params_uri, area_count, rec_eq):
    '''Want to create the dictionary to store all information for age/stages
    and areas.

    Input:
        params_uri- Contains a string location of the main parameter csv file.

    Returns:
        params_dict- Dictionary containing all information from the csv file.
            Should have age/stage specific information, as well as area-specific
            information. NOT ALL KEYS ARE REQUIRED TO EXIST. The keys which are
            present are determined by what equations/additional information the
            user is trying to model.

            {'Stage_Params':
                {'Age_A':
                    {'survival': {'Area_1': 0.653, 'Area_2': 0.23', ...},
                     'maturity': 0.0007, 'vuln_fishing': 0.993, 
                     'weight': 4.42, 'duration': 16},
                     ...
                }
             'Area_Params':
                {'Area_1':
                    {'exploit_frac': 0.309, 'larval_disp': 0.023},
                    ...
                }
            }
        ordered_stages- A list containing all the ages/stages that are being
            used within the model, in the order they were listed in the CSV,
            which is presumed to be the order in which they occur.
   '''
    #Create a container list to hold all the line lists
    hybrid_lines = []
    area_lines = []

    with open(params_uri, 'rU') as param_file:

        csv_reader = csv.reader(param_file)

        #In some cases, line[0] may contain the name of the model 
        #(as with Jodie data). And in some cases, line[1] reads 'Survival'.
        line = csv_reader.next()
        while line[0] == '' or line[1] == '':
            line = csv_reader.next()
        
        #Once we get here, know that we're into the area/age vars.
        #Should continue until we hit a blank line, which is the cue
        #to switch over to area specific stuff.
        
        while line[0] != '':
            hybrid_lines.append(line)
            line = csv_reader.next()

        #Once we get here, know that we've hit the space between hybrid vars
        #and area specific vars. Run until we hit the end.
        while True:
            try:
                area_lines.append(csv_reader.next())
            except StopIteration:
                break

    main_dict = {'Stage_Params':{}, 'Area_Params':{}}

    headers = hybrid_lines.pop(0)

    #Know that for headers, the first is actually just a notation that areas are
    #on top, and stages are below. Want to ignore.
    headers.pop(0)

    #Since these are lists, they should be in the same order as in the line
    #itself. We know that len(area_names) + len(age_params) = len(line) - 1
    area_names = headers[:area_count]
    age_params = headers[area_count:]

    #Sometimes, people do weird capitalizations. So lower everything.
    age_params = map(lambda x: x.lower(), age_params)
    
    #Want to make sure that the headers are in the acceptable set.
    for param in age_params:

        if param not in ['duration', 'vulnfishing', 'weight', 'maturity']:
            
            LOGGER.debug("The problematic parameter is %s." % param)
            raise ImproperStageParameter("Improper parameter name given. \
                    Acceptable age/stage-specific parameters include \
                    'duration', 'vulnfishing', 'weight', and 'maturity'.")

    #Want to make sure that all required parameters exist
    #Looks like 'VulnFishing' is really the only required one from this set.
    if 'vulnfishing' not in age_params:
        raise MissingVulnFishingParameter("The main parameter CSV for this \
                species is missing a VulnFishing parameter. Please make sure \
                that each age/stage for the species has a corresponding \
                proportion that is vulnerable to fishing.")
    if 'maturity' not in age_params and \
                        rec_eq in ['Beverton-Holt', 'Ricker', 'Fecundity']:
        raise MissingMaturityParameter("The main parameter CSV for this \
                species is missing a Maturity parameter. Please make sure \
                that each age/stage for the species is assigned a proportion \
                between 0 and 1 (inclusive) which would be considered mature.")

    #Want a list of the stages in order
    ordered_stages = []

    for i in range(len(hybrid_lines)):
        line = hybrid_lines[i]
        stage_name = line.pop(0)
        ordered_stages.append(stage_name)

        #Initialize stage subdictionary with survival subdictionary inside
        main_dict['Stage_Params'][stage_name] = {'survival':{}}
        
        #Do the survival params first
        for j in range(len(area_names)):
           
            #If there is only one area, user may instead choose to not write an
            #area name, but instead just put "Survival". If that's the case, 
            #replace it with 'AOI'. Because 'Survival'['Survival'] is confusing.
            curr_area_name = area_names[j]
            if curr_area_name.lower() == 'survival':
                curr_area_name = 'AOI'

            area_surv = line[j]

            main_dict['Stage_Params'][stage_name]['survival'][curr_area_name] = float(area_surv)

        #The rest of the age-specific params.
        for k in range(len(age_params)):
            
            param_name = age_params[k]
            #The first part of line will contain the area names. Want index
            #relative to the end of that set.
            param_value = line[k+len(area_names)] 

            main_dict['Stage_Params'][stage_name][param_name] = float(param_value)

    area_param_short = {'exploitationfraction': 'exploit_frac', 
                        'larvaldispersal': 'larv_disp'}
    #pre-populate with area names
    for area_name in area_names:
        if area_name.lower() == 'survival':
            area_name = 'AOI'
        main_dict['Area_Params'][area_name] = {}

    exp_frac_exists = False

    #The area-specific parameters.
    for m in range(len(area_lines)):
        line = area_lines[m]
        param_name = line.pop(0).lower()
        
        if param_name == 'exploitationfraction':
            exp_frac_exists = True

        try:
            short_param_name = area_param_short[param_name]
        except KeyError:
            raise ImproperAreaParameter("Improper area-specific parameter name.\
                    Acceptable parameters include 'ExploitationFraction', and \
                    'LarvalDispersal'.")

        for n in range(len(area_names)):
            curr_area_name = area_names[n]
            if curr_area_name.lower() == 'survival':
                curr_area_name = 'AOI'
            
            param_value = line[n]
       
            main_dict['Area_Params'][curr_area_name][short_param_name] = float(param_value)


    if not exp_frac_exists:
        raise MissingExpFracParameter("The main parameter CSV for this species \
                is missing an ExplotationFraction parameter. Please make sure \
                that each area provided within the AOI(s) has a corresponding \
                explotation fraction.")

    return main_dict, ordered_stages

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
