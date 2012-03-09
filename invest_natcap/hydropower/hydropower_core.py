"""Module that contains the core computational components for the hydropower
    model including the water yield, water scarcity , and valuation functions"""

import logging

import numpy as np
from osgeo import gdal

import invest_cython_core
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('sediment_core')

def water_yield(args):
    #water yield functionality goes here
    LOGGER.info('Starting Water Yield Calculation')
    
def water_scarcity(args):
    #water yield functionality goes here    
    LOGGER.info('Starting Water Scarcity Calculation')
        
def valuation(args):
    #water yield functionality goes here
    LOGGER.info('Starting Valuation Calculation')