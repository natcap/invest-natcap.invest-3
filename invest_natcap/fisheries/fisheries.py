'''This will be the entry point for the fisheries tier 1 model. It will pass
any calculation onto fisheries_core.py.'''

import logging
import os
import shutil
import csv

from osgeo import ogr

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
    classes_dict, ordered_classes = parse_main_csv(args['class_params_uri'], area_count)
    core_args['classes_dict'] = classes_dict

    #If migration is desired, get all the info, and add to the core args dict
    migration_dict = parse_migration_tables(mig_params_uri)


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
            migration.

            {'2'
    
    '''

def parse_main_csv(params_uri, area_count):
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

    main_dict = {'stage_params':{}, 'area_params':{}}

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

            raise ImproperStageParameter("Improper parameter name given. \
                    Acceptable age/stage-specific parameters include \
                    'duration', 'vulnfishing', 'weight', and 'maturity'.")

    #Want a list of the stages in order
    ordered_stages = []

    for i in range(len(hybrid_lines)):
        line = hybrid_lines[i]
        stage_name = line.pop(0)
        ordered_stages.append(stage_name)

        #Initialize stage subdictionary with survival subdictionary inside
        main_dict['stage_params'][stage_name] = {'survival':{}}
        
        #Do the survival params first
        for j in range(len(area_names)):
           
            #If there is only one area, user may instead choose to not write an
            #area name, but instead just put "Survival". If that's the case, 
            #replace it with '1'. Because 'Survival'['Survival'] is confusing.
            curr_area_name = area_names[j]
            if curr_area_name.lower() == 'survival':
                curr_area_name = '1'

            area_surv = line[j]

            main_dict['stage_params'][stage_name]['survival'][curr_area_name] = area_surv

        #The rest of the age-specific params.
        for k in range(len(age_params)):
            
            param_name = age_params[k]
            #The first part of line will contain the area names. Want index
            #relative to the end of that set.
            param_value = line[k+len(area_names)] 

            main_dict['stage_params'][stage_name][param_name] = param_value

    area_param_short = {'exploitationfraction': 'exploit_frac', 
                        'larvaldispersal': 'larv_disp'}
    #pre-populate with area names
    for area_name in area_names:
        if area_name.lower() == 'survival':
            area_name = '1'
        main_dict['area_params'][area_name] = {}

    #The area-specific parameters.
    for m in range(len(area_lines)):
        line = area_lines[m]
        param_name = line.pop(0).lower()
        
        try:
            short_param_name = area_param_short[param_name]
        except KeyError:
            raise ImproperAreaParameter("Improper area-specific parameter name.\
                    Acceptable parameters include 'ExploitationFraction', and \
                    'LarvalDispersal'.")

        for n in range(len(area_names)):
            curr_area_name = area_names[n]
            if curr_area_name.lower() == 'survival':
                curr_area_name = '1'
            
            param_value = line[n]
       
            main_dict['area_params'][curr_area_name][short_param_name] = param_value

    return main_dict, ordered_stages
