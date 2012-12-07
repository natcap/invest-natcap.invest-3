"""InVEST Wind Energy model file handler module"""
import logging
import os

from invest_natcap.wind_energy import wind_energy_biophysical
from invest_natcap.wind_energy import wind_energy_valuation
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_uri_handler')

def execute(args):
    # Run the biophysical uri module
    LOGGER.debug('Stepping into Biophysical URI Handler')
    wind_energy_biophysical.execute(args)
    
    # Check to see if one of the valuation arguments is active. If the checkbox
    # was not selected then the following key will not be in the arguments.
    if 'number_of_machines' in args:
        # Run the valuation uri module
        LOGGER.debug('Stepping into Valuation URI Handler')
        wind_energy_valuation.execute(args)
   
    LOGGER.debug('Leaving wind_energy_uri_handler')
