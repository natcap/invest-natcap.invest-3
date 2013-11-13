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
    '''

