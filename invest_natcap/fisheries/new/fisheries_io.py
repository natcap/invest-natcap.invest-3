import logging
import os
import shutil
import csv

from osgeo import ogr
import numpy as np

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
    pass


def fetch_verify_args(args):
    '''Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a dictionary of variables

    :param dictionary args: arguments from the user
    :return: vars_dict
    :rtype: dictionary
    '''
    pop_dict = _verify_population_csv(args)

    mig_dict = _verify_migration_tables(args)

    params_dict = _verify_single_params(args, pop_dict, mig_dict)

    vars_dict = dict(pop_dict.items() + mig_dict.items() + params_dict.items())

    return vars_dict


def _verify_population_csv(args):
    '''
    '''
    population_csv_uri = args['population_csv_uri']
    sexsp = args['sexsp']
    pop_dict = _parse_population_csv(population_csv_uri)

    # Check that required information exists
    pass


def _parse_population_csv(uri, sexsp):
    '''Parses the given population parameters csv file and returns a dictionary
    of matrices and vectors

    **Example**
    pop_dict = {{'SurvNaturalFrac': [np.ndarrays]},
                {'VulnFishing': np.ndarray}, ...}
    '''
    csv_data = []
    params_dict = {}

    with open(uri, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            csv_data.append(line)

    start_rows = _get_table_row_start_indexes(csv_data)
    start_cols = _get_table_col_start_indexes(csv_data, start_rows[0])

    classes = _get_col(
        csv_data, start_rows[0])[0:len(_get_col(csv_data, start_rows[1]))]
    params_dict["classes"] = classes[1:]

    regions = _get_row(
        csv_data, start_cols[0])[0:len(_get_row(csv_data, start_rows[1]))]
    params_dict["regions"] = regions[1:]

    surv_table = _get_table(csv_data, start_rows[0] + 1, start_cols[0] + 1)
    class_attributes_table = _get_table(
        csv_data, start_rows[0], start_cols[1])
    region_attributes_table = _get_table(
        csv_data, start_rows[1], start_cols[0])

    if sexsp == 1:
        # Sex Neutral
        params_dict['SurvNaturalFrac'] = [np.array(surv_table, dtype=np.float_)]

    elif sexsp == 2:
        # Sex Specific
        female = np.array(surv_table[0:len(surv_table)/sexsp], dtype=np.float_)
        male = np.array(surv_table[len(surv_table)/sexsp:], dtype=np.float_)
        params_dict['SurvNaturalFrac'] = [female, male]

    else:
        # Throw exception about sex-specific conflict or formatting issue
        pass

    for col in range(0, len(class_attributes_table[0])):
        params_dict.update(_vectorize_attribute(
            _get_col(class_attributes_table, col), sexsp))

    for row in range(0, len(region_attributes_table)):
        params_dict.update(_vectorize_attribute(
            _get_row(region_attributes_table, row), 1))

    return params_dict


def _verify_migration_tables(args):
    '''
    '''
    mig_dict = {}

    # If Migration:
    migration_dir = args['migration_dir']
    mig_dict = _parse_migration_tables(migration_dir)

    # Check migration CSV files match areas.
    # Check columns approximately sum to one? (maybe throw warning rather than error)

    pass


def _parse_migration_tables(uri):
    '''Parses all files in the given directory as migration matrices
    and returns a dictionary of stages and their corresponding migration
    numpy matrix.

    :param string uri: filepath to the directory of migration tables

    :returns: mig_dict
    :rtype: dictionary

    **Example**
    mig_dict = {{'stage1': np.matrix}, {'stage2': np.matrix}, ...}
    '''
    mig_dict = {}

    for mig_csv in listdir(uri):
        basename = os.path.splitext(os.path.basename(mig_csv))[0]
        class_name = basename.split('_').pop().lower()

        with open(mig_csv, 'rU') as param_file:
            csv_reader = csv.reader(param_file)
            lines = []
            for row in csv_reader:
                lines.append(row)
            
            matrix = []
            for row in range(1, len(lines)):
                if lines[row][0] == '': break
                array = []
                for entry in range (1, len(lines[row])):
                    array.append(float(lines[row][entry]))
                matrix.append(array)
            
            Migration = np.matrix(matrix)

        mig_dict[class_name] = Migration
    
    return mig_dict


def _verify_single_params(args, pop_dict, mig_dict):
    # Check that path exists and user has read/write permissions along path
    workspace_dir = args['workspace_dir']

    # Check file extension? (maybe try / except would be better)
    # Check shapefile subregions match regions in population parameters file
    aoi_uri = args['aoi_uri']

    # Check positive number
    total_timesteps = args['total_timesteps']

    # If stage-based: Check that Duration vector exists in parameters file
    population_type = args['population_type']

    # If sex-specific: Check for male and female matrices in parameters file
    sexsp = args['sexsp']

    # Check for non-negative float
    total_init_recruits = args['total_init_recruits']

    # Check that corresponding parameters exist
    recruitment_type = args['recruitment_type']

    # If BH or Ricker and 'spawners by weight' selected: Check that Weight vector exists in parameters file
    spawn_units = args['spawn_units']

    # If BH or Ricker: Check positive number
    alpha = args['alpha']

    # Check positive float
    beta = args['beta']

    # If Fixed: Check non-negative number, check for sum approximately equal to one
    # Special Case: 1 sub-region --> vector equals 1
    total_recur_recruits = args['total_recur_recruits']

    # If Harvest: Check that Weight vector exists in population parameters file
    harvest_units = args['harvest_units']

    # If Harvest: Check float between [0,1]
    frac_post_process = args['frac_post_process']

    # If Harvest: Check non-negative float
    unit_price = args['unit_price']

    pass


def initialize_vars(vars_dict):
    '''Initializes variables
    '''

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
    d[lst[0]] = a
    return d
