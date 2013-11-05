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
        alpha- 
    '''

