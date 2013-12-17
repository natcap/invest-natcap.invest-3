'''The core functionality for the fisheries model. This will take the
arguments from non-core and do the calculation side of the model.'''
import logging
import os

LOGGER = logging.getLogger('FISHERIES_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):

