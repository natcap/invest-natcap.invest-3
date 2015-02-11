'''
The Crop Production IO module contains functions for handling inputs and
outputs
'''

import logging

from invest_natcap import raster_utils as ru

LOGGER = logging.getLogger('CROP_PRODUCTION')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class MissingParameter(StandardError):
    '''
    An exception class that may be raised when a necessary parameter is not
    provided by the user.
    '''
    def __init__(self, msg):
        self.msg = msg


# Fetch and Verify Arguments
def fetch_args(args, create_outputs=True):
    '''
    Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a list of variables dictionaries

    Args:
        args (dictionary): arguments from the user

    Returns:
        vars_dict (dictionary): dictionary of variables to be used in the model

    Example Returns::

        vars_dict = {
            'workspace_dir': 'path/to/workspace_dir',
            'output_dir': 'path/to/output_dir',
            'results_suffix': '',
            '': '',
            '': '',
            '': '',
            '': '',
            '': '',
            '': '',
            '': '',
            '': '',
            '': '',
        }

    '''
    pass
