'''This will be the entry point for the fisheries tier 1 model. It will pass
any calculation onto fisheries_core.py.'''

import logging

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This function will prepare files to be passed to the fisheries core
    module.'''

