'''
The Fisheries Preprocessor module contains the high-level code for
generating a new Population Parameters CSV File based on habitat area
change and the dependencies that particular classes of the given species
have on particular habitats.
'''
import pprint
import logging

import numpy as np

import fisheries_preprocessor_io as io


pp = pprint.PrettyPrinter(indent=4)

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


def execute(args):
    '''
    Entry point into the Fisheries Preprocessor

    The Fisheries Preprocessor generates a new Population Parameters CSV File
    with modified survival attributes across classes and regions based on
    habitat area changes and class-level dependencies on those habitats.

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

    Returns:
        None

    Example Args::

        args = {
            'workspace_dir': 'path/to/workspace_dir/',
            'sexsp': 'Yes',
            'population_csv_uri': 'path/to/csv',
            'habitat_csv_uri': 'path/to/csv',
            'gamma': 0.5,
        }

    Note:

        Modified Population Parameters CSV File saved to
        'workspace_dir/output/'
    '''

    # Parse, Verify Inputs
    vars_dict = io.fetch_args(args)

    # Convert Data
    vars_dict = convert_survival_matrix(vars_dict)

    # Generate Modified Population Parameters CSV File
    io.generate_outputs(vars_dict)


def convert_survival_matrix(vars_dict):
    '''
    Creates a new survival matrix based on the information provided by
    the user related to habitat area changes and class-level dependencies
    on those habitats.

    Args:
        vars_dict (dictionary): see fisheries_preprocessor_io.fetch_args for
            example

    Returns:
        vars_dict (dictionary): modified vars_dict with new Survival matrix
            accessible using the key 'Surv_nat_xsa_mod' with element values
            that exist between [0,1]

    Example Returns::

        ret = {
            # Other Variables...

            'Surv_nat_xsa_mod': np.ndarray([...])
        }
    '''
    # Fetch original survival matrix
    S_sxa = vars_dict['Surv_nat_xsa'].swapaxes(0, 1)

    # Fetch conversion parameters
    gamma = vars_dict['gamma']
    H_chg_hx = vars_dict['Hab_chg_hx']      # H_hx
    D_ha = vars_dict['Hab_dep_ha']          # d_ah
    t_a = vars_dict['Hab_class_mvmt_a']     # T_a
    n_a = vars_dict['Hab_dep_num_a']        # n_h
    n_a[n_a == 0] = 1
    num_habitats = len(vars_dict['Habitats'])
    num_classes = len(vars_dict['Classes'])
    num_regions = len(vars_dict['Regions'])

    # Apply function
    Mod_elements_xha = np.ones([num_regions, num_habitats, num_classes])
    A = Mod_elements_xha * D_ha
    A[A != 0] = 1
    Mod_elements_xha = A
    Exp_xha = Mod_elements_xha * D_ha * gamma

    pp.pprint(Exp_xha)
    Mod_elements_ahx = Mod_elements_xha.swapaxes(0, 2)
    print "Mod_elements_ahx"
    pp.pprint(Mod_elements_ahx)
    H_chg_all_ahx = (Mod_elements_ahx * H_chg_hx)
    print "H_chg_all_ahx"
    pp.pprint(H_chg_all_ahx)
    H_chg_all_xha = H_chg_all_ahx.swapaxes(0, 2)
    print "H_chg_all_xha"
    pp.pprint(H_chg_all_xha)
    H_xha = (H_chg_all_xha ** Exp_xha)
    print "H_xha"
    pp.pprint(H_xha)
    H_xa = H_xha.sum(axis=1)
    print "H_xa"
    pp.pprint(H_xa)
    # Add in one so that original S values are weighed properly
    H_xa_weighted = H_xa + 1
    print "H_xa_weighted"
    pp.pprint(H_xa_weighted)


    # Multiply by original S elements

    # Filter and correct for elements outside [0, 1]

    # Return
    S_mod = None
    vars_dict['Surv_nat_xsa_mod'] = S_mod

    return vars_dict
