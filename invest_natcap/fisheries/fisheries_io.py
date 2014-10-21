import logging
import os
import shutil
import csv

from osgeo import ogr
import numpy as np
from numpy import testing as nptest

from invest_natcap import raster_utils

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class ImproperStageParameter(Exception):
    '''This exception will occur if the stage-specific headings in the main
    parameter CSV are not included in the set of known parameters.'''
    pass


class ImproperAreaParameter(Exception):
    '''This exception will occur if the area-specific headings in the main
    parameter CSV are not included in the set of known parameters.'''
    pass


class MissingParameter(Exception):
    '''This is a broad exception which can be raised if the any of the
    parameters required for a specific model run type are missing. This
    can include recruitment parameters, vulnerability, exploitation fraction,
    maturity, weight, or duration.
    '''
    def __init__(self, msg):
        self.msg = msg


def fetch_verify_args(args):
    '''Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a dictionary of variables

    :param dictionary args: arguments from the user
    :return: vars_dict
    :rtype: dictionary
    '''
    pop_dict = _verify_population_csv(args)

    mig_dict = _verify_migration_tables(
        args, pop_dict['Classes'], pop_dict['Regions'])

    params_dict = _verify_single_params(args)

    vars_dict = dict(pop_dict.items() + mig_dict.items() + params_dict.items())

    return vars_dict


def _verify_population_csv(args):
    '''Parses and verifies inputs from the population parameters csv file.
    If not all necessary vectors are included, the function will raise a
    MissingParameter exception

    **Notes**
    See _parse_population_csv function for notes for list of dictionary keys
        in returned pop_dict
    '''
    population_csv_uri = args['population_csv_uri']
    pop_dict = _parse_population_csv(population_csv_uri, args['sexsp'])

    # Check that required information exists
    Necessary_Params = ['Classes', 'Exploitationfraction', 'Maturity',
                        'Regions', 'Survnaturalfrac', 'Vulnfishing']
    Matching_Params = [i for i in pop_dict.keys() if i in Necessary_Params]
    if len(Matching_Params) != len(Necessary_Params):
        LOGGER.error("Population Parameters File does not contain all necessary parameters")
        raise MissingParameter('')

    if (args['population_type'] == 'Stage-Based') and ('Duration' not in pop_dict.keys()):
        LOGGER.error("Population Parameters File must contain a 'Duration' vector when running Stage-Based models")
        raise MissingParameter("Population Parameters File must contain a 'Duration' vector when running Stage-Based models")

    if (args['recruitment_type'] in ['Beverton-Holt', 'Ricker']) and args['spawn_units'] == 'Weight' and 'Weight' not in pop_dict.keys():
        LOGGER.error("Population Parameters File must contain a 'Weight' vector when Spawners are calulated by weight using the Beverton-Holt or Ricker recruitment functions")
        raise MissingParameter('')

    if (args['harvest_units'] == 'Weight') and ('Weight' not in pop_dict.keys()):
        LOGGER.error("Population Parameters File must contain a 'Weight' vector when 'Harvest by Weight' is selected")
        raise MissingParameter('')

    if (args['recruitment_type'] == 'Fecundity' and 'Fecundity' not in pop_dict.keys()):
        LOGGER.error("Population Parameters File must contain a 'Fecundity' vector when using the Fecundity recruitment function")
        raise MissingParameter('')

    # Check that similar vectors have same shapes (NOTE: checks region vectors)
    if not (pop_dict['Larvaldispersal'].shape == pop_dict[
            'Exploitationfraction'].shape):
        LOGGER.error("Region vector shapes do not match")
        raise ValueError

    # Check that information is correct
    if not np.allclose(pop_dict['Larvaldispersal'], 1):
        LOGGER.warning("The LarvalDisperal vector does not sum exactly to one")

    # Check that certain attributes have fraction elements
    Frac_Vectors = ['Survnaturalfrac', 'Vulnfishing', 'Maturity',
                    'Exploitationfraction']
    for attr in Frac_Vectors:
        a = pop_dict[attr]
        if np.any(a > 1) or np.any(a < 0):
            LOGGER.warning("The %s vector has elements that are not \
                decimal fractions", attr)

    # Make sure parameters are initialized even when user does not enter data
    if 'Larvaldispersal' not in pop_dict.keys():
        num_regions = len(pop_dict['regions'])
        pop_dict['Larvaldispersal'] = np.ones(num_regions) / num_regions

    # Make duration vector of type integer
    pop_dict['Duration'] = np.array(
        pop_dict['Duration'], dtype=int)

    pass


def _parse_population_csv(uri, sexsp):
    '''Parses the given population parameters csv file and returns a dictionary
    of lists, arrays, and matrices

    **Notes**
    Dictionary items containing lists, arrays or matrices are capitalized,
    while single variables are lowercase.

    Keys: Survnaturalfrac, Vulnfishing, Maturity, Duration, Weight, Fecundity,
            Exploitationfraction, Larvaldispersal, Classes, Regions

    **Example**
    pop_dict = {{'Survnaturalfrac': [np.ndarrays]},
                {'Vulnfishing': np.ndarray}, ...},
    '''
    csv_data = []
    pop_dict = {}

    with open(uri, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            csv_data.append(line)

    start_rows = _get_table_row_start_indexes(csv_data)
    start_cols = _get_table_col_start_indexes(csv_data, start_rows[0])

    classes = _get_col(
        csv_data, start_rows[0])[0:len(_get_col(csv_data, start_rows[1]))]
    pop_dict["Classes"] = map(lambda x: x.lower(), classes[1:])

    regions = _get_row(
        csv_data, start_cols[0])[0:len(_get_row(csv_data, start_rows[1]))]
    pop_dict["Regions"] = map(lambda x: x.lower(), regions[1:])

    surv_table = _get_table(csv_data, start_rows[0] + 1, start_cols[0] + 1)
    class_attributes_table = _get_table(
        csv_data, start_rows[0], start_cols[1])
    region_attributes_table = _get_table(
        csv_data, start_rows[1], start_cols[0])

    if sexsp == 1:
        # Sex Neutral
        pop_dict['Survnaturalfrac'] = [np.array(surv_table, dtype=np.float_)]

    elif sexsp == 2:
        # Sex Specific
        female = np.array(surv_table[0:len(surv_table)/sexsp], dtype=np.float_)
        male = np.array(surv_table[len(surv_table)/sexsp:], dtype=np.float_)
        pop_dict['Survnaturalfrac'] = [female, male]

    else:
        # Throw exception about sex-specific conflict or formatting issue
        pass

    for col in range(0, len(class_attributes_table[0])):
        pop_dict.update(_vectorize_attribute(
            _get_col(class_attributes_table, col), sexsp))

    for row in range(0, len(region_attributes_table)):
        pop_dict.update(_vectorize_attribute(
            _get_row(region_attributes_table, row), 1))

    return pop_dict


def _verify_migration_tables(args, class_list, region_list):
    '''Parses, verifies and orders list of migration matrices necessary for
    program.

    If migration matrices are not provided for all classes, the function will
    generate identity matrices for missing classes

    **Example**
    mig_dict = {'Migration': [np.matrix, np.matrix, ...]}
    '''
    migration_dict = {}

    # If Migration:
    migration_dir = args['migration_dir']
    mig_dict = _parse_migration_tables(migration_dir, class_list)

    # Create indexed list
    matrix_list = map(lambda x: None, class_list)

    # Map np.matrices to indices in list
    for i in range(0, len(class_list)):
        if class_list[i] in mig_dict.keys():
            matrix_list[i] = mig_dict[class_list[i]]

    # Fill in rest with identity matrices
    for i in range(0, len(matrix_list)):
        if matrix_list[i] is None:
            matrix_list[i] = np.matrix(np.identity(len(region_list)))

    # Check migration regions are equal across matrices
    if not all(map(lambda x: x.shape == matrix_list[0].shape, matrix_list)):
        LOGGER.error("Shape of migration matrices are not equal across lifecycle classes")
        raise ValueError

    # Check that all migration vectors approximately sum to one
    if not all([np.allclose(vector.sum(), 1) for matrix in matrix_list for vector in matrix]):
        LOGGER.warning("Elements in at least one migration matrices source vector do not sum to one")

    migration_dict['Migration'] = matrix_list
    return migration_dict


def _parse_migration_tables(uri, class_list):
    '''Parses all files in the given directory as migration matrices
    and returns a dictionary of stages and their corresponding migration
    numpy matrix.

    If extra files are provided that do not match the class names, an exception
    will be thrown

    :param string uri: filepath to the directory of migration tables

    :returns: mig_dict
    :rtype: dictionary

    **Example**
    mig_dict = {{'stage1': np.matrix}, {'stage2': np.matrix}, ...}
    '''
    mig_dict = {}

    try:
        for mig_csv in listdir(uri):
            basename = os.path.splitext(os.path.basename(mig_csv))[0]
            class_name = basename.split('_').pop().lower()
            if class_name.lower() in class_list:
                with open(mig_csv, 'rU') as param_file:
                    csv_reader = csv.reader(param_file)
                    lines = []
                    for row in csv_reader:
                        lines.append(row)

                    matrix = []
                    for row in range(1, len(lines)):
                        if lines[row][0] == '':
                            break
                        array = []
                        for entry in range(1, len(lines[row])):
                            array.append(float(lines[row][entry]))
                        matrix.append(array)

                    Migration = np.matrix(matrix)

                mig_dict[class_name] = Migration

    except:
        pass

    return mig_dict


def _verify_single_params(args):
    '''
    '''
    # Check that directory exists, if not, try to create directory
    if not os.path.isdir(args['workspace_dir']):
        try:
            os.makedirs(args['workspace_dir'])
        except:
            LOGGER.error("Cannot create Workspace Directory")
            raise OSError

    # Check that timesteps is positive integer
    total_timesteps = args['total_timesteps']
    if type(total_timesteps) != int or total_timesteps < 1:
        LOGGER.error("Total Timesteps value must be positive integer")
        raise ValueError

    # Check total_init_recruits for non-negative float
    total_init_recruits = args['total_init_recruits']
    if type(total_init_recruits) != float or total_init_recruits < 0:
        LOGGER.error("Total Initial Recruits value must be non-negative float")

    # Check that corresponding recruitment parameters exist
    recruitment_type = args['recruitment_type']
    if recruitment_type in ['Beverton-Holt', 'Ricker']:
        if args['alpha'] is None or args['beta'] is None:
            LOGGER.error("Not all required recruitment parameters provided")
            raise ValueError
        if args['alpha'] <= 0 or args['beta'] <= 0:
            LOGGER.error("Alpha and Beta parameters must be positive")
            raise ValueError
    if recruitment_type is 'Fixed':
        if args['total_recur_recruits'] is None:
            LOGGER.error("Not all required recruitment parameters provided")
            raise ValueError
        if args['total_recur_recruits'] < 0:
            LOGGER.error(
                "Total Recruits per Timestep must be non-negative float")
            raise ValueError

    # If Harvest:
    if args['harvest_cont']:
        frac_post_process = args['frac_post_process']
        unit_price = args['unit_price']
        if frac_post_process is None or unit_price is None:
            LOGGER.error("Not all required harvest parameters are provided")
            raise ValueError
        # Check frac_post_process float between [0,1]
        if frac_post_process < 0 or frac_post_process > 1:
            LOGGER.error("The fraction of harvest kept after processing must be a float between 0 and 1 (inclusive)")
            raise ValueError
        # Check unit_price non-negative float
        if unit_price < 0:
            LOGGER.error("Unit price of harvest must be non-negative float")
            raise ValueError

    # If shapefile exists
    # Check file extension? (maybe try / except would be better)
    # Check shapefile subregions match regions in population parameters file
    aoi_uri = args['aoi_uri']

    pass


def initialize_vars(vars_dict):
    '''Initializes variables
    '''
    # Initialize derived parameters
        # Survtotalfrac, P_survtotalfrac, G_survtotalfrac, N_all,
        # Harvest, Valuation

    pass


def generate_outputs(vars_dict):
    '''
    '''
    # Append Results to Shapefile
    # HTML results page
    # CSV results page
    pass


def listdir(path):
    '''A replacement for the standar os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Input:
        :param string path: the location container from which we want to
            gather all files

    Returns:
        :return: A list of full URIs contained within 'path'.
        :rtype: list
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris


# Helper functions for navigating CSV files
def _get_col(lsts, col):
    l = []
    for row in range(0, len(lsts)):
        if lsts[row][col] != '':
            l.append(lsts[row][col])
    return l


def _get_row(lsts, row):
    l = []
    for entry in range(0, len(lsts[row])):
        if lsts[row][entry] != '':
            l.append(lsts[row][entry])
    return l


def _get_table(lsts, row, col):
    table = []

    end_col = col
    while end_col + 1 < len(lsts[0]) and lsts[0][end_col + 1] != '':
        end_col += 1

    end_row = row
    while end_row + 1 < len(lsts) and lsts[end_row + 1][0] != '':
        end_row += 1

    for line in range(row, end_row + 1):
        table.append(lsts[line][col:end_col + 1])
    return table


def _get_table_row_start_indexes(lsts):
    indexes = []
    if lsts[0][0] != '':
        indexes.append(0)
    for line in range(1, len(lsts)):
        if lsts[line - 1][0] == '' and lsts[line][0] != '':
            indexes.append(line)
    return indexes


def _get_table_col_start_indexes(lsts, top):
    indexes = []
    if lsts[top][0] != '':
        indexes.append(0)
    for col in range(1, len(lsts[top])):
        if lsts[top][col - 1] == '' and lsts[top][col] != '':
            indexes.append(col)
    return indexes


def _vectorize_attribute(lst, rows):
    d = {}
    a = np.array(lst[1:], dtype=np.float_)
    a = np.reshape(a, (rows, a.shape[0] / rows))
    d[lst[0].capitalize()] = a
    return d
