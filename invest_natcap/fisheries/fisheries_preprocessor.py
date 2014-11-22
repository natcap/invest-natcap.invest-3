'''
The Fisheries Preprocessor module contains the high-level code for
generating a new Population Parameters CSV File based on habitat area
change and the dependencies that particular classes of the given species
have on particular habitats.
'''

import fisheries_preprocessor_io as io

import logging

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args):
    '''
    Entry point into the Fisheries Preprocessor

    Args:
        workspace_dir (string): location into which the resultant modified
            Population Parameters CSV file should be placed.

        sexsp (string): specifies whether or not the age and stage
            classes are distinguished by sex. Options: 'Yes' or 'No'

        population_csv_uri (string): location of the population parameters csv
            file. This file contains all age and stage specific parameters.

        habitat_csv_uri (string): location of the habitat parameters csv file.
            This file contains habitat-class dependency and habitat area
            change information.

        gamma (float): (desc)

    Example Args Dictionary::

        args = {
            'workspace_dir': 'path/to/workspace_dir/',
            'sexsp': 'Yes',
            'population_csv_uri': 'path/to/csv',
            'habitat_csv_uri': 'path/to/csv',
            'gamma': 0.5,
        }

    Output:

        + Modified Population Parameters CSV file saved to 'workspace_dir/output/'
    '''

    # Parse, Verify Inputs
    vars_dict = io.fetch_args(args)

    # Convert Data
    vars_dict = convert_data(vars_dict)

    # Generate Modified Population Parameters CSV File
    io.generate_outputs(vars_dict)


def convert_data(vars_dict):
    '''


    resultant survival matrix has values that exist between [0,1]
    '''
    pass
