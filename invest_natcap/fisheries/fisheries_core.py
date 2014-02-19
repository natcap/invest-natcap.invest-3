'''The core functionality for the fisheries model. This will take the
arguments from non-core and do the calculation side of the model.'''
import logging
import os
import copy
import cmath

from osgeo import ogr
from invest_natcap import reporting
from invest_natcap import raster_utils

LOGGER = logging.getLogger('FISHERIES_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''
    Input:
        workspace_dir- Location into which all intermediate and output files
            should be placed.
        aoi_uri- Location of the AOI containing all areas the user is
            interested in using for this model run.
        maturity_type- String specifying whether the model is age-specific or
            stage-specific. Options will be either "Age Specific" or
            "Stage Specific" and will change which equation is used in modeling
            growth.
        is_gendered- Boolean for whether or not the age and stage classes are
            separated by gender.
        do_weight- Boolean for whether harvesting and biomass should be done by
            weight or not. If weight is desired, there will be a 'weight' 
            parameter in the params_dict['Stage_Params'] subdictionary.
        params_dict- Dictionary containing all information from the csv file.
            Should have age/stage specific information, as well as area-specific
            information. NOT ALL KEYS ARE REQUIRED TO EXIST. The keys which are
            present are determined by what equations/additional information the
            user is trying to model.

            {'Stage_Params':
                {'Age_A':
                    {'survival': {'Area_1': 0.653, 'Area_2': 0.23', ...},
                     'maturity': 0.0007, 'vulnfishing': 0.993, 
                     'weight': 4.42, 'duration': 16},
                     ...
                }
             'Area_Params':
                {'Area_1':
                    {'exploit_frac': 0.309, 'larv_disp': 0.023},
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
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Initialize the first cycle, since we know we will start at least one.
    cycle_dict = {}

    initialize_pop(args['maturity_type'], args['params_dict'], 
        args['ordered_stages'], args['is_gendered'], args['init_recruits'], 
        cycle_dict)

    migration_dict = args['migration_dict'] if 'migration_dict' in args else None

    if args['maturity_type'] == "Age Specific":
        age_structured_cycle(args['params_dict'], args['is_gendered'],
                    args['ordered_stages'], args['rec_dict'], cycle_dict, 
                    migration_dict, args['duration'], args['do_weight'])
    else:
        stage_structured_cycle(args['params_dict'], args['is_gendered'],
                    args['ordered_stages'], args['rec_dict'], cycle_dict, 
                    migration_dict, args['duration'], args['do_weight'])

    hrv_dict, equil_pt = calc_harvest(cycle_dict, args['params_dict'])
   
    #If either of the two valuation variables exist, know that valuation is desired
    if 'unit_price' in args:
        #passing a subdictionary that is only the equilibrated final cycle 
        #to get the value
        val_dict = calc_valuation(hrv_dict[len(hrv_dict)-1], args['unit_price'], 
                                                    args['frac_post_process'])

    #Here be outputs
    val_var = val_dict if 'unit_price' in args else None
    append_results_to_aoi(args['aoi_uri'], hrv_dict[len(hrv_dict)-1], val_var)

    html_page_uri = os.path.join(output_dir, 'Results_Page.html')
    create_results_page(html_page_uri, hrv_dict, equil_pt, val_var)


def create_results_page(uri, hrv_dict, equil_pt, val_var):
    '''Will output an HTML file that contains a summary of all harvest totals
    for each subregion.
    
    Inputs:
        uri- Location at which the HTML file shoudl be saved. 
        val_var*- Dictionary which maps each area to the total value returned
            from all harvesting.
            {'Area_1': 300000.50,
            'Area_2': 40000.62}
        hrv_dict- Dictionary containing all harvest information on a per area
            per cycle basis. This will have the following structure.
            {Cycle #:
                {'Area_1': 3001},
                'Area_2': ...,
                'Cycle_Total: SUM(Area_1, Area_2, ...)}
            }
        equil_pt- The cycle on which the harvest was equilibrated. If it never
            equilibrated, this will be -1.
    '''
    rep_args = {}
    rep_args['title'] = "Fishieries Results Page"
    rep_args['out_uri'] = uri

    num_cycles = len(hrv_dict.keys())
    
    t_body = []

    final_cycle = hrv_dict[num_cycles-1]

    for area in final_cycle:
        if area != 'Cycle_Total':
            inner_dict = {}
            inner_dict['Subregion'] = area
            inner_dict['Harvest'] = final_cycle[area]
            inner_dict['Value'] = '-' if val_var is None else val_var[area]
    
            t_body.append(inner_dict)

    t_columns =  [{'name': 'Subregion', 'total': False},
                {'name': 'Harvest', 'total': True},
                {'name': 'Value', 'total': True}]

    c_body = []
    for cycle in hrv_dict:
        inner_dict = {}
        inner_dict['Cycle'] = cycle
        inner_dict['Harvest'] = hrv_dict[cycle]['Cycle_Total']

        if cycle == equil_pt: 
            inner_dict['Equilibrated?'] = 'Y'
        else:
            inner_dict['Equilibrated?'] = 'N'
        
        c_body.append(inner_dict)

    c_columns = [{'name': 'Cycle', 'total': False},
                {'name': 'Harvest', 'total': True},
                {'name': 'Equilibrated?', 'total': False}]

    elements = [{
                'type': 'text',
                'section': 'body',
                'text': '<h2>Final Harvest by Subregion After ' + str(num_cycles) + ' Cycles</h2>'},
                {
                'type': 'table',
                'section': 'body',
                'sortable': True,
                'checkbox': False,
                'total': True,
                'data_type': 'dictionary',
                'columns': t_columns,
                'data': t_body},
                {
                'type': 'text',
                'section': 'body',
                'text': '<h2>Cycle Breakdown</h2>'},
                {
                'type': 'table',
                'section': 'body',
                'sortable': True,
                'checkbox': False,
                'total': True,
                'data_type': 'dictionary',
                'columns': c_columns,
                'data': c_body},
                {
                'type':'head',
                'section':'head',
                'format': 'script',
                'data_src': '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/reporting_data/sorttable.js',
                'input_type': 'File'},
                {
                'type':'head',
                'section':'head',
                'format': 'script',
                'data_src': '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/reporting_data/jquery-1.10.2.min.js',
                'input_type': 'File'},
                {
                'type':'head',
                'section':'head',
                'format': 'script',
                'data_src': '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/reporting_data/total_functions.js',
                'input_type': 'File'},
                {
                'type':'head',
                'section':'head',
                'format': 'style',
                'data_src': '/home/kathryn/workspace/invest-natcap.invest-3/test/invest-data/test/data/reporting_data/table_style.css',
                'input_type': 'File'}
                ]

    rep_args['elements'] = elements

    reporting.generate_report(rep_args)

def append_results_to_aoi(aoi_uri, final_cycle, val_dict):
    '''Want to add the relevant data to the correct AOI as attributes.'''

    ds = ogr.Open(aoi_uri, update=1)
    layer = ds.GetLayer()

    harvest_field = ogr.FieldDefn('Hrv_Total', ogr.OFTReal)
    layer.CreateField(harvest_field)
    
    if val_dict is not None:
        val_field = ogr.FieldDefn('Val_Total', ogr.OFTReal)
        layer.CreateField(val_field)
    
    for feature in layer:

        #Since we now know for sure there will be a name attribute lower case,
        #can just call it directly.
        subregion_name = feature.items()['name']
        feature.SetField('Hrv_Total', final_cycle[subregion_name])

        if val_dict is not None:
            feature.SetField('Val_Total', val_dict[subregion_name])

        layer.SetFeature(feature)

    layer.ResetReading()

def calc_valuation(final_cycle, price, frac):
    '''If the user wants valuation, want to output a dictionary that maps area
    to total value of harvest across all areas.
    
    Returns:
        val_dict- Dictionary which maps each area to the total value returned
            from all harvesting.
            {'Area_1': 300000.50,
            'Area_2': 40000.62}
    '''
    
    value_dict = {}

    for area, totals in final_cycle.items():
        
        #There's an extra key that's a running total. Don't get a value for it
        if area != 'Cycle_Total':
            val = totals * price * frac
            value_dict[area] = val

    return value_dict

def calc_harvest(cycle_dict, params_dict):
    '''Function to calculate harvest of an area on a cycle basis. If do_weight
    is True, then this will be done on the basis of biomass, otherwise the
    results represent the number of individuals.
    
    Returns:
        hrv_dict- Dictionary containing all harvest information on a per area
            per cycle basis. This will have the following structure.
            {Cycle #:
                {'Area_1': 3001,
                'Area_2': ...,
                'Cycle_Total: SUM(Area_1, Area_2, ...)}
            }
            '''
    hrv_dict = {}
    equil_pt = len(cycle_dict)-1
    mov_tot = 0

    #Want to be sure that we're looking at the harvests in order so that all
    #prior harvest information will exist.
    for cycle in range(0, len(cycle_dict)):
        
        areas_dict = cycle_dict[cycle]
        
        hrv_dict[cycle] = {}
        hrv_dict[cycle]['Cycle_Total'] = 0

        for area, stages_dict in areas_dict.items():
            exploit_frac = params_dict['Area_Params'][area]['exploit_frac']

            hrv_total = 0
            for stage, indivs in stages_dict.items():
                
                vuln = params_dict['Stage_Params'][stage]['vulnfishing']
                curr_ax_hrv = indivs * exploit_frac * vuln

                #Adding to the total for that area
                hrv_total += curr_ax_hrv

            hrv_dict[cycle][area] = hrv_total
            hrv_dict[cycle]['Cycle_Total'] += hrv_total
        
        mov_tot += hrv_dict[cycle]['Cycle_Total']

        #Equilibration checks.
        if cycle > 9:

            mov_avg = mov_total / 10
            frac = mov_avg / hrv_dict[cycle]['Cycle_Total']

            #If we reach equilibrium before the total duration, record what
            #cycle it happened at, and we can break.
            if .999 < frac < 1.001:
                equil_pt = cycle
                break

        mov_tot -= hrv_dict[cycle-9]['Cycle_Total']

    return hrv_dict, equil_pt
    
def age_structured_cycle(params_dict, is_gendered, order, rec_dict, cycle_dict,
                    migration_dict, duration, do_weight):
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
                     'maturity': 0.0007, 'vulnfishing': 0.993, 
                     'weight': 4.42, 'duration': 16},
                     ...
                }
             'Area_Params':
                {'Area_1':
                    {'exploit_frac': 0.309, 'larv_disp': 0.023},
                    ...
                }
            }
    '''
    #Need to know if we're using gendered ages, b/c it changes the age
    #specific initialization equation. We need to know the two last stages
    #that we have to look out for to switch the EQ that we use.
    if is_gendered:
        first_age = [order[0], order[len(order)/2]]
        final_age = [order[len(order)/2-1], order[len(order)-1]]
    else:
        first_age = [order[0]]
        final_age = [order[len(order)-1]]
   
    gender_var = 2 if is_gendered else 1

    #Want to pre-run it for extra cycles, on the off-chance that it does not
    #equilibrate within the given time. 
    for cycle in range(1, duration+100):

        #Initialize this current cycle
        cycle_dict[cycle] = {}

        #This will be used for each 0 age in the cycle. 
        rec_sans_disp = area_indifferent_rec(cycle_dict, params_dict,
                                            rec_dict, gender_var, cycle, do_weight)
                            
        for area in params_dict['Area_Params'].keys():

            #Initialize current area within cycle.
            cycle_dict[cycle][area] = {}

            area_params = params_dict['Area_Params'][area]
            larval_disp = area_params['larv_disp'] if 'larv_disp' in area_params else 1 

            for i, age in enumerate(order):
    
                #If a = 0
                if age in first_age:
                    #LOGGER.debug("(%s, %s) Rec=%s, Larval_Disp=%s" % (cycle, area, rec_sans_disp, larval_disp))
                    cycle_dict[cycle][area][age] = rec_sans_disp * larval_disp
                #If a = maxAge
                elif age in final_age:
                    prev_age = order[i-1] 
                
                    prev_survival = calc_survival_mortal(params_dict, area, prev_age)
                    prev_num_indivs = \
                        calc_indiv_count(cycle_dict, migration_dict, area, 
                                                prev_age, cycle)

                    survival = calc_survival_mortal(params_dict, area, age)
                    num_indivs = \
                        calc_indiv_count(cycle_dict, migration_dict, area, age,
                                            cycle)
                    cycle_dict[cycle][area][age] = (prev_num_indivs * prev_survival) + \
                                            (num_indivs * survival)
                else:
                    prev_age = order[i-1] 
                
                    prev_survival = calc_survival_mortal(params_dict, area, prev_age)
                    prev_num_indivs = \
                        calc_indiv_count(cycle_dict, migration_dict, area, 
                                                prev_age, cycle)

                    cycle_dict[cycle][area][age] = prev_num_indivs * prev_survival

    for cycle in cycle_dict:
        for area in cycle_dict[cycle]:
            if area == '1':
                for age in cycle_dict[cycle][area]:
                    #LOGGER.debug("Cycle %s: Age %s: %s" % (cycle, age, cycle_dict[cycle][area][age]))
                    pass

def stage_structured_cycle(params_dict, is_gendered, order, rec_dict, cycle_dict,
                    migration_dict, duration, do_weight):
    
    gender_var = 2 if is_gendered else 1
    
    if is_gendered:
        first_stage = [order[0], order[len(order)/2]]
    else:
        first_stage = [order[0]]
    
    #Want to pre-run it for extra cycles, on the off-chance that it does not
    #equilibrate within the given time. 
    for cycle in range(1, duration+100):

        #Initialize this current cycle
        cycle_dict[cycle] = {}

        #This will be used for each 0 stage in the cycle. 
        total_recruits = area_indifferent_rec(cycle_dict, params_dict,
                                            rec_dict, gender_var, cycle, do_weight)
   
        for area in params_dict['Area_Params'].keys():

            #Initialize current area within cycle.
            cycle_dict[cycle][area] = {}

            area_params = params_dict['Area_Params'][area]
            larval_disp = area_params['larv_disp'] if 'larv_disp' in area_params else 1 

            for i, stage in enumerate(order):
               
                #a = 0
                if stage in first_stage:
                    area_rec = larval_disp * total_recruits 
                    
                    num_indivs = calc_indiv_count(cycle_dict, migration_dict, area, stage, cycle)
                    prob_surv_stay = calc_prob_surv_stay(params_dict, stage, area) 
               
                    cycle_dict[cycle][area][stage] = (num_indivs * prob_surv_stay) + area_rec

                # 1 <= a
                else:
                    prev_stage = order[i-1] 
                    
                    prev_num_indivs = \
                        calc_indiv_count(cycle_dict, migration_dict, area, 
                                                prev_stage, cycle)
                    curr_num_indivs = \
                        calc_indiv_count(cycle_dict, migration_dict, area, stage,
                                            cycle)
                    prob_surv_stay = calc_prob_surv_stay(params_dict, prev_stage, area) 
                    prob_surv_grow = calc_prob_surv_grow(params_dict, prev_stage, area)

                    cycle_dict[cycle][area][stage] = (prev_num_indivs * prob_surv_grow) + \
                                                    (curr_num_indivs * prob_surv_stay)

    print cycle_dict

def calc_indiv_count(cycle_dict, mig_dict, area, age, cycle):
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
    prev_indiv_in_area = cycle_dict[cycle-1][area][age]
    prev_mig_in_area = 1 if mig_dict == None else mig_dict[age][area][area]

    indivs_in_area = prev_indiv_in_area * prev_mig_in_area

    incoming_pop = 0

    #For the individuals incoming from other areas.
    #Couldn't think of anything better to call this. Refers to x != x'
    for area_prime in cycle_dict[cycle].keys():
        if area_prime is not area:
            prev_indivs_prime =  cycle_dict[cycle-1][area_prime][age]

            if mig_dict is not None and age in mig_dict:
                mig_prime_to_area = mig_dict[age][area_prime][area]
            else:
                mig_prime_to_area = 0

            incoming_pop += prev_indivs_prime * mig_prime_to_area
    
    return indivs_in_area + incoming_pop

def area_indifferent_rec(cycle_dict, params_dict, rec_dict, gender_var, cycle, do_weight):
    '''This is is the portion of the recruitment equiation which does not include
    the larval dispersal. Since L_D is multiplied against everything else for
    all recruitment equations, we can calculate a location independent portion
    of recruitment first, then just multiply it against larval dispersal for
    each area with the cycle.'''

    #We know there's only the one key, value pair within the dictionary.
    rec_eq, add_info = next(rec_dict.iteritems())

    if rec_eq in ['Beverton-Holt', 'Ricker']:
        #If weight is a parameter in params_dict, spawners will be biomass, not
        #number of spawners. Otherwise, just a count.
        spawners = spawner_count(cycle_dict, params_dict, cycle, do_weight)

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

def spawner_count(cycle_dict, params_dict, cycle, do_weight):
    '''For a given cycle, does a SUMPRODUCT of the individuals and the maturity
    for a given pairing of age, area.'''

    spawner_sum = 0

    for ages_dict in cycle_dict[cycle-1].values():
        for age, indiv_count in ages_dict.items():

            weight = params_dict['Stage_Params'][age]['weight'] if do_weight else 1
            maturity = params_dict['Stage_Params'][age]['maturity']
            product = indiv_count * maturity * weight

            spawner_sum += product

    return spawner_sum

def initialize_pop(maturity_type, params_dict, order, is_gendered, init_recruits, 
                    cycle_dict):
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
    #Since we know this is the initialization cycle.
    cycle_dict[0] = {}
    revised_order = copy.copy(order)

    #Need to know if we're using gendered ages, b/c it changes the age
    #specific initialization equation. We need to know the two last stages
    #that we have to look out for to switch the EQ that we use.
    if is_gendered == True:
        first_stage = [order[0], order[len(order)/2]]
        final_stage = [order[len(order)/2-1], order[len(order)-1]]
        #Want to make sure that the order we will use for later iteration does
        #contain the two first ages.
        revised_order.pop(len(order)/2)
        revised_order.pop(0)
    else:
        first_stage = [order[0]]
        final_stage = [order[len(order)-1]]
        #Want to remove the first age from the order through which we will cycle
        revised_order.pop(0)

    gender_var = 2 if is_gendered else 1

    if maturity_type == 'Stage Specific':
        
        for area in params_dict['Area_Params'].keys():

            cycle_dict[0][area] = {}

            area_params = params_dict['Area_Params'][area]
            larval_disp = area_params['larv_disp'] if 'larv_disp' in area_params else 1 
            
            #The first stage should be set to the initial recruits equation, the
            #rest should be 1.
            for stage in first_stage:
                initial_pop = init_recruits * larval_disp / gender_var
                cycle_dict[0][area][stage] = initial_pop

            for stage in revised_order:
                cycle_dict[0][area][stage] = 1

    elif maturity_type == 'Age Specific':
       
        for area in params_dict['Area_Params'].keys():

            cycle_dict[0][area] = {}

            area_params = params_dict['Area_Params'][area]
            larval_disp = area_params['larv_disp'] if 'larv_disp' in area_params else 1 

            #For age = 0, count = init_recruits
            for age in first_stage:
                initial_pop = init_recruits * larval_disp / gender_var
                cycle_dict[0][area][age] = initial_pop
            
            #For age = maxAge, count = (count{A-1} * SURV) / (1- SURV)
            for age in revised_order:
                #Can use order to check previous, since we know we will not be
                #getting the first of any age group.
                prev_age = order[order.index(age)-1]
                prev_count = cycle_dict[0][area][prev_age]
                
                prev_surv = calc_survival_mortal(params_dict, area, prev_age)
                surv = calc_survival_mortal(params_dict, area, age)

                if age in final_stage:
                    count = (prev_count * surv)/ (1- surv)
                else:
                    count = prev_count * prev_surv
                    #LOGGER.debug("For %s,%s we're using N=%s, Surv=%s" % (area, age, prev_count, prev_surv))

                cycle_dict[0][area][age] = count

def calc_prob_surv_stay(params_dict, stage, area):
    
    surv = calc_survival_mortal(params_dict, area, stage)
    duration = params_dict['Stage_Params'][stage]['duration']

    numerator = surv * (1 - (surv ** (duration-1)))
    denom = 1 - (surv ** duration)

    return numerator / denom

def calc_prob_surv_grow(params_dict, stage, area):

    surv = calc_survival_mortal(params_dict, area, stage)
    duration = params_dict['Stage_Params'][stage]['duration']

    numerator = (surv ** duration) * (1 - surv)
    denom = 1 - (surv ** duration)

    return numerator / denom

def calc_survival_mortal(params_dict, area, stage):
    '''Calculate survival from natural and fishing mortality

    Input:
        params_dict- Dictionary which we will use to get survival values,
            exploitation fraction, and vulnerability to fishing.

            {'Stage_Params':
                {'Age_A':
                    {'survival': {'Area_1': 0.653, 'Area_2': 0.23', ...},
                     'maturity': 0.0007, 'vulnfishing': 0.993, 
                     'weight': 4.42, 'duration': 16},
                     ...
                }
             'Area_Params':
                {'Area_1':
                    {'exploit_frac': 0.309, 'larv_disp': 0.023},
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
    vuln = params_dict['Stage_Params'][stage]['vulnfishing']

    surv_mort = surv_frac * (1 - exp_frac * vuln)

    return surv_mort
