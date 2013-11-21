'''This will be the entry point for the fisheries tier 1 model. It will pass
any calculation onto fisheries_core.py.'''

import logging

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

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
            desired. This is  the location of the parameters file for migration.
        frac_post_process(*)- This will exist only if valuation is desired for
            the particular species. A double representing the fraction of the
            animal remaining after processing of the whole carcass is complete.
        unit_price(*)- This will exist only if valuation is desired. Double 
            which represents the price for a single unit of that animal.
        duration- Int representing the number of time steps that the user
            desires the model to run.
    '''

    #Create folders that will be used for the rest of the model run.
    for folder in ['Intermediate', 'Output']:
        
        out_dir = os.path.join(workspace_uri, folder)
        
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        os.makedirs(out_dir)

    classes_dict = parse_main_csv(args['class_params_uri'])

def parse_main_csv(params_uri)
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

    csv_reader = csv.reader(params_uri)







