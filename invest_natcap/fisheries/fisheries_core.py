'''The core functionality for the fisheries model. This will take the
arguments from non-core and do the calculation side of the model.'''
import logging
import os

LOGGER = logging.getLogger('FISHERIES_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''
    Input:
        workspace_uri- Location into which all intermediate and output files
            should be placed.
        maturity_type- String specifying whether the model is age-specific or
            stage-specific. Options will be either "Age Specific" or
            "Stage Specific" and will change which equation is used in modeling
            growth.
        is_gendered- Boolean for whether or not the age and stage classes are
            separated by gender.
        rec_eq- The equation to be used in calculation of recruitment. Choices
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
            used within this run of the model, in the order in which they
            should occur naturally.
        alpha(*)- Must exist within args if rec_eq == "Beverton-Holt" or 
            "Ricker" . Parameter that will be used in calculation of
            recruitment.
        beta(*)- Must exist within args if rec_eq == "Beverton-Holt" or 
            "Ricker" . Parameter that will be used in calculation of
            recruitment.
        fecundity_dict- Must exist within args if rec_eq == "Fecundity".
            Dictionary containing all relevant fecundity information for this
            run of the model.
        fix_param(*)- Must exist within args if rec_eq == "Fixed". Parameter
            that will be used in calculation of recruitment. 
        init_recruits- Int which represents the initial number of recruits that
            will be used in calculation of population on a per area basis. 
        migration_dict(*)- Migration dictionary which will contain all source/sink
            percentage information for each age/stage which is capable of
            migration. The outermost numerical key is the source, and the
            keys of the dictionary that points to are the sinks.

            {'egg': {'1': {'1': 98.66, '2': 1.31, ...},
                    '2': {'1': 0.13, '2': 98.06, ...}
            }
        frac_post_process(*)- This will exist only if valuation is desired for
            the particular species. A double representing the fraction of the
            animal remaining after processing of the whole carcass is complete.
        unit_price(*)- This will exist only if valuation is desired. Double 
            which represents the price for a single unit of that animal.
        duration- Int representing the number of time steps that the user
            desires the model to run.
    '''

    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Going to start cycling here. 
    #Three possible stages: age = 0, age<maxAge, age=maxAge.
    
    '''This dictionary will contain all counts of individuals for each
    combination of cycle, age/stage, and area. The final dictionary will look
    like the following:
    
    {Cycle_#:
        {'Area_1':
            {'Age_A': 1000,
                ...
            },
        }
    }
    '''
    #Initialize the first cycle, since we know we will start at least one.
    cycle_dict = {1:{}}

    initialize_pop(args['maturity_type'], args['params_dict'], 
        args['ordered_stages'], args['init_recruits'], cycle_dict)

def initialize_pop(maturity_type, params_dict, order, init_recruits, 
                    cycle_dict):
    '''Set the initial population numbers within cycling dictionary.

    Input:
        maturity_type- String specifying whether the model is age-specific or
            stage-specific. Options will be either "Age Specific" or
            "Stage Specific" and will change which equation is used in modeling
            growth.
        params_dict- Dictionary containing all information from the csv file.
            Should have age/stage specific information, as well as area-specific
            information.

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
            used within this run of the model, in the order in which they
            should occur naturally.
        init_recruits- Int which represents the initial number of recruits that
            will be used in calculation of population on a per area basis. 
        cycle_dict- Contains all counts of individuals for each combination of 
            cycle, age/stage, and area.
            
            {Cycle_#:
                {'Area_1':
                    {'Age_A': 1000}
                }
            }
        Returns:
            Modified version of cycle_dict which contains initial pop counts by
            area and age group.
    '''

    if maturity_type == 'Stage Specific':
        
        for area in params_dict['Area_Params'].keys():
            #The first one should be set to the initial recruits, the rest should
            #be 1.
            cycle_dict[1][area] = {order[0]:init_recruits}

            for stage in order[1::]

                cycle_dict[1][area][stage] = init_recruits



