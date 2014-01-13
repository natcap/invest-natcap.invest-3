'''The core functionality for the fisheries model. This will take the
arguments from non-core and do the calculation side of the model.'''
import logging
import os
import copy
import cmath

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
        rec_dict- A dictionary containing the chosen recruitment equation and
            the parameters that are needed to use that equation. Dictionary will
            look like one of the following:
            {'Beverton-Holt': {'alpha': 0.02, 'beta': 3}}
            {'Ricker': {'alpha': 0.02, 'beta': 3}}
            {'Fecundity': {FECUNDITY DICT}}
            {'Fixed': 0.5}
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
    cycle_dict = {}

    initialize_pop(args['maturity_type'], args['params_dict'], 
        args['ordered_stages'], args['is_gendered'], args['init_recruits'], 
        cycle_dict, 0)

    migration_dict = args['migration_dict'] if 'migration_dict' in args else None

    if args['maturity_type'] == "Age Specific":
        age_structured_cycle(args['params_dict'], args['is_gendered'],
                    args['ordered_stages'], args['rec_dict'], cycle_dict, 
                    migration_dict, args['duration'])
    else:
        stage_structured_cycle(args['params_dict'], args['is_gendered'],
                    args['ordered_stages'], args['rec_dict'], cycle_dict, 
                    migration_dict, args['duration'])

def age_structured_cycle(params_dict, is_gendered, order, rec_dict, cycle_dict,
                    migration_dict, duration):
    '''cycle_dict- Contains all counts of individuals for each combination of 
            cycle, age/stage, and area.
            
            {Cycle_#:
                {'Area_1':
                    {'Age_A': 1000}
                }
            }
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
    #Need to know if we're using gendered ages, b/c it changes the age
    #specific initialization equation. We need to know the two last stages
    #that we have to look out for to switch the EQ that we use.
    if is_gendered == True:
        first_age = [order[0], order[len(order)/2]]
        final_age = [order[len(order)/2-1], order[len(order)-1]]
    else:
        first_age = [order[0]]
        final_age = [order[len(order)-1]]
   
    revised_order = copy.copy(order)
    do_migration = False if migration_dict is None else True
    gender_var = 2 if is_gendered else 1

    for cycle in range(1, duration):

        #This will be used for each 0 age in the cycle. 
        rec_sans_disp = area_indifferent_rec(cycle_dict, params_dict,
                                                rec_dict, gender_var, cycle)
                            
        for area in params_dict['Area_Params'].keys():

            larval_disp = params_dict['Area_Params'][area]['larval_disp']

            for age in params_dict['Stage_Params'].keys():

                #If a = 0
                if age in first_age:
                    cycle_dict[cycle][area][age] = rec_sans_disp * larval_disp
                #If a = maxAge
                elif age in final_age:
                    pass
                else:
                    survival = calc_survival_mortal(params_dict, area, stage)
                    num_indivs = \
                        calc_prev_indiv_count(cycle_dict, migration_dict, area, 
                                                age, cycle)

                    cycle_dict[cycle][area][age] = num_indivs * survival

def  calc_prev_indiv_count(cycle_dict, mig_dict, area, age):
    '''Want to get the indiviual count for the previous cycle, including the 
    amount of incoming migration.
    
    N{a} = (N{a-1,x,t} * Mig{stays X} + SUM{x!=x'}(N{a-1, x'} * Mig{a-1, x->x'})
    
    migration_dict(*)- Contains source/sink info for each age/stage
        capable of migration. Outer key is source, inner is sink.

        {'egg': {'1': {'1': 98.66, '2': 1.31, ...},
                '2': {'1': 0.13, '2': 98.06, ...}
        }
    cycle_dict- Contains all counts of individuals for each combination of 
            cycle, age/stage, and area.
            
            {Cycle_#:
                {'Area_1':
                    {'Age_A': 1000}
                }
            }
    '''
    

def area_indifferent_rec(cycle_dict, params_dict, rec_dict, gender_var, cycle):
    '''This is is the portion of the recruitment equiation which does not include
    the larval dispersal. Since L_D is multiplied against everything else for
    all recruitment equations, we can calculate a location independent portion
    of recruitment first, then just multiply it against larval dispersal for
    each area with the cycle.'''

    #We know there's only the one key, value pair within the dictionary.
    rec_eq, add_info = rec_dict.popitem()

    if rec_eq in ['Beverton-Holt', 'Ricker']:
        #If weight is a parameter in params_dict, spawners will be biomass, not
        #number of spawners. Otherwise, just a count.
        spawners = spawner_count(cycle_dict, params_dict, cycle)

    #Now, run equation for each of the recruitment equation possibilities.
    if rec_eq == 'Beverton-Holt':
        rec = add_info['alpha'] * spawners / \
                    (add_info['beta'] + spawners) / gender_var
    elif rec_eq == 'Ricker':
        rec = add_info['alpha'] * spawners * \
                    (cmath.e ** (-add_info['beta']*spawners)) / gender_var
    elif rec_eq == 'Fecundity':
        pass
    elif rec_eq == 'Fixed':
        #In this case, add_info is a fixed recruitment
        rec = add_info / gender_var

    return rec

def spawner_count(cycle_dict, params_dict, cycle):
    '''For a given cycle, does a SUMPRODUCT of the individuals and the maturity
    for a given pairing of age, area.'''

    spawner_sum = 0

    for area, ages_dict in cycle_dict[cycle-1].items():
        for age, indiv_count in ages_dict.items():

            maturity = params_dict['Stage_Params'][age]['maturity']
            product = indiv_count * maturity

            spawner_sum += product

    return spawner_sum

def stage_structured_cycle(params_dict, is_gendered, order, rec_dict, cycle_dict,
                    migration_dict, duration):
    pass


def initialize_pop(maturity_type, params_dict, order, is_gendered, init_recruits, 
                    cycle_dict, cycle_count):
    '''Set the initial population numbers within cycling dictionary.

    Input:
        maturity_type- String specifying whether the model is age-specific or
            stage-specific. Options will be either "Age Specific" or
            "Stage Specific" and will change which equation is used in modeling
            growth.
        params_dict- Dictionary containing all information from the csv file.
            Contains  age/stage specific information, as well as area-specific
            information.
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
    #Need to know if we're using gendered ages, b/c it changes the age
    #specific initialization equation. We need to know the two last stages
    #that we have to look out for to switch the EQ that we use.
    if is_gendered == True:
        first_stage = [order[0], order[len(order)/2]]
        final_stage = [order[len(order)/2-1], order[len(order)-1]]
    else:
        first_stage = [order[0]]
        final_stage = [order[len(order)-1]]

    revised_order = copy.copy(order)
    gender_var = 2 if is_gendered else 1

    if maturity_type == 'Stage Specific':
        
        for area in params_dict['Area_Params'].keys():

            larval_disp = params_dict['Area_Params'][area]['larval_disp']
            
            #The first stage should be set to the initial recruits equation, the
            #rest should be 1.
            for stage in first_stage:
                initial_pop = init_recruits * larval_disp / gender_var
                cycle_dict[cycle_count][area] = {stage:initial_pop}
                revised_order.remove(stage)

            for stage in revised_order:
                cycle_dict[cycle_count][area][stage] = 1

    elif maturity_type == 'Age Specific':
        
        for area in params_dict['Area_Params'].keys():

            larval_disp = params_dict['Area_Params'][area]['larval_disp']

            #For age = 0, count = init_recruits
            for age in first_stage:
                initial_pop = init_recruits * larval_disp / gender_var
                cycle_dict[cycle_count][area] = {age:initial_pop}
                revised_order.remove(age)
            
            #For age = maxAge, count = (count{A-1} * SURV) / (1- SURV)
            for age in revised_order:
                #Can use order to check previous, since we know we will not be
                #getting the first of any age group.
                prev_age = order[order.index(age)-1]
                prev_count = cycle_dict[cycle_count][area][prev_age]
                
                surv = calc_survival_mortal(params_dict, area, age)

                if age in final_stage:
                    count = (prev_count * surv)/ (1- surv)
                else:
                    count = prev_count * surv
                
                cycle_dict[cycle_count][area][age] = count

def calc_survival_mortal(params_dict, area, stage):
    '''Calculate survival from natural and fishing mortality

    Input:
        params_dict- Dictionary which we will use to get survival values,
            exploitation fraction, and vulnerability to fishing.

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
        area- A string that can be used to index into params_dict describing
            the area that we are calculating for.
        stage- A string that can be used to index into params_dict describing
            the age/stage that we're calculating for.

    Returns:
        The survival fraction, which is described by the equation
        S = surv{a,s,x} * (1-exp{x} * vuln{a,s})
    '''

    surv_frac = params_dict['Stage_Params'][stage]['survival'][area]
    exp_frac = params_dict['Area_Params'][area]['exploit_frac']
    vuln = params_dict['Stage_Params'][stage]['vuln_fishing']

    surv_mort = surv_frac * (1 - exp_frac * vuln)

    return surv_mort
