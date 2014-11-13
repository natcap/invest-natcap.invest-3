'''
The Fisheries IO module contains functions for handling inputs and outputs
'''

import logging
import os
import csv

from osgeo import ogr
import numpy as np

from invest_natcap import raster_utils
from invest_natcap import reporting

LOGGER = logging.getLogger('FISHERIES')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')


class MissingParameter(Exception):
    '''
    A broad exception class that is raised when a necessary parameter is not
        provided.
    '''
    def __init__(self, msg):
        self.msg = msg


# Fetch and Verify Arguments
def fetch_verify_args(args):
    '''
    Fetches input arguments from the user, verifies for correctness and
    completeness, and returns a dictionary of variables

    This function receives an unmodified 'args' dictionary from the user

    Args:
        args (dictionary): arguments from the user

    Returns:
        vars_dict (dictionary)

    Example Returned Dictionary of Verified Arguments::

        {
            'workspace_dir': 'path/to/workspace_dir',
            'output_dir': 'path/to/output_dir',
            'aoi_uri': 'path/to/aoi_uri',
            'total_timesteps': 100,
            'population_type': 'Stage-Based',
            'sexsp': 2,
            'spawn_units': 'Weight',
            'total_init_recruits': 100.0,
            'recruitment_type': 'Ricker',
            'alpha': 32.4,
            'beta': 54.2,
            'total_recur_recruits': 92.1,
            'migr_cont': True,
            'harv_cont': True,
            'harvest_units': 'Individuals',
            'frac_post_process': 0.5,
            'unit_price': 5.0,

            # Pop Params
            'population_csv_uri': 'path/to/csv_uri',
            'Survnaturalfrac': np.array([[[...], [...]], [[...], [...]], ...]),
            'Classes': np.array([...]),
            'Vulnfishing': np.array([...], [...]),
            'Maturity': np.array([...], [...]),
            'Duration': np.array([...], [...]),
            'Weight': np.array([...], [...]),
            'Fecundity': np.array([...], [...]),
            'Regions': np.array([...]),
            'Exploitationfraction': np.array([...]),
            'Larvaldispersal': np.array([...]),

            # Mig Params
            'migration_dir': 'path/to/mig_dir',
            'Migration': [np.matrix, np.matrix, ...]
        }

    '''
    if args['sexsp'] == 'Yes':
        args['sexsp'] = 2
    else:
        args['sexsp'] = 1

    pop_dict = _verify_population_csv(args)

    mig_dict = _verify_migration_tables(
        args, pop_dict['Classes'], pop_dict['Regions'])

    params_dict = _verify_single_params(args)

    vars_dict = dict(pop_dict.items() + mig_dict.items() + params_dict.items())

    return vars_dict


def _verify_population_csv(args):
    '''Parses and verifies the population arributes file

    Parses and verifies inputs from the population attributes csv file.
        If not all necessary vectors are included, the function will raise a
        MissingParameter exception. Survival matrix will be arranged by
        class-elements, 2nd dim: sex, and 3rd dim: region. Class vectors will
        be arranged by class-elements, 2nd dim: sex (depending on whether model
        is sex-specific) Region vectors will be arraged by region-elements,
        sex-agnostic.

    Args:
        args (dictionary): arguments provided by user

    Returns:
        pop_dict (dictionary): verified population arguments

    Example Returned Population Dictionary::

        {
            'Survnaturalfrac': np.array([[...], [...]], [[...], [...]], ...),

            # Class Vectors
            'Classes': np.array([...]),
            'Vulnfishing': np.array([...], [...]),
            'Maturity': np.array([...], [...]),
            'Duration': np.array([...], [...]),
            'Weight': np.array([...], [...]),
            'Fecundity': np.array([...], [...]),

            # Region Vectors
            'Regions': np.array([...]),
            'Exploitationfraction': np.array([...]),
            'Larvaldispersal': np.array([...]),
        }
    '''
    population_csv_uri = args['population_csv_uri']
    pop_dict = _parse_population_csv(population_csv_uri, args['sexsp'])

    # Check that required information exists
    Necessary_Params = ['Classes', 'Exploitationfraction', 'Regions',
                        'Survnaturalfrac', 'Vulnfishing']
    Matching_Params = [i for i in pop_dict.keys() if i in Necessary_Params]
    if len(Matching_Params) != len(Necessary_Params):
        LOGGER.error("Population Attributes File does not contain all necessary parameters")
        raise MissingParameter("Population Attributes File does not contain all necessary parameters")

    if (args['recruitment_type'] != 'Fixed') and ('Maturity' not in pop_dict.keys()):
        LOGGER.error("Population Attributes File must contain a 'Maturity' vector when running the given recruitment function")
        raise MissingParameter("Population Attributes File must contain a 'Maturity' vector when running the given recruitment function")

    if (args['population_type'] == 'Stage-Based') and ('Duration' not in pop_dict.keys()):
        LOGGER.error("Population Attributes File must contain a 'Duration' vector when running Stage-Based models")
        raise MissingParameter("Population Attributes File must contain a 'Duration' vector when running Stage-Based models")

    if (args['recruitment_type'] in ['Beverton-Holt', 'Ricker']) and args['spawn_units'] == 'Weight' and 'Weight' not in pop_dict.keys():
        LOGGER.error("Population Attributes File must contain a 'Weight' vector when Spawners are calulated by weight using the Beverton-Holt or Ricker recruitment functions")
        raise MissingParameter("Population Attributes File must contain a 'Weight' vector when Spawners are calulated by weight using the Beverton-Holt or Ricker recruitment functions")

    if (args['harvest_units'] == 'Weight') and ('Weight' not in pop_dict.keys()):
        LOGGER.error("Population Attributes File must contain a 'Weight' vector when 'Harvest by Weight' is selected")
        raise MissingParameter("Population Attributes File must contain a 'Weight' vector when 'Harvest by Weight' is selected")

    if (args['recruitment_type'] == 'Fecundity' and 'Fecundity' not in pop_dict.keys()):
        LOGGER.error("Population Attributes File must contain a 'Fecundity' vector when using the Fecundity recruitment function")
        raise MissingParameter("Population Attributes File must contain a 'Fecundity' vector when using the Fecundity recruitment function")

    # Make sure parameters are initialized even when user does not enter data
    if 'Larvaldispersal' not in pop_dict.keys():
        num_regions = len(pop_dict['Regions'])
        pop_dict['Larvaldispersal'] = np.ndarray(np.ones(num_regions) / num_regions)

    # Check that similar vectors have same shapes (NOTE: checks region vectors)
    if not (pop_dict['Larvaldispersal'].shape == pop_dict[
            'Exploitationfraction'].shape):
        LOGGER.error("Region vector shapes do not match")
        raise ValueError

    # Check that information is correct
    if not np.allclose(pop_dict['Larvaldispersal'], 1):
        LOGGER.warning("The Larvaldisperal vector does not sum exactly to one")

    # Check that certain attributes have fraction elements
    Frac_Vectors = ['Survnaturalfrac', 'Vulnfishing',
                    'Exploitationfraction']
    if args['recruitment_type'] != 'Fixed':
        Frac_Vectors.append('Maturity')
    for attr in Frac_Vectors:
        a = pop_dict[attr]
        if np.any(a > 1) or np.any(a < 0):
            LOGGER.warning("The %s vector has elements that are not decimal fractions", attr)

    # Make duration vector of type integer
    if args['population_type'] == 'Stage-Based':
        pop_dict['Duration'] = np.array(
            pop_dict['Duration'], dtype=int)

    # Fill in unused keys with null values
    All_Parameters = ['Classes', 'Duration', 'Exploitationfraction',
                      'Fecundity', 'Larvaldispersal', 'Maturity', 'Regions',
                      'Survnaturalfrac', 'Weight', 'Vulnfishing']
    for parameter in All_Parameters:
        if parameter not in pop_dict.keys():
            pop_dict[parameter] = None

    return pop_dict


def _parse_population_csv(uri, sexsp):
    '''
    Parses the given population attributes csv file and returns a dictionary
        of lists, arrays, and matrices

    Dictionary items containing lists, arrays or matrices are capitalized,
    while single variables are lowercase.

    Keys: Survnaturalfrac, Vulnfishing, Maturity, Duration, Weight, Fecundity,
            Exploitationfraction, Larvaldispersal, Classes, Regions

    Example:
        pop_dict = {{'Survnaturalfrac': np.array([[...], [...]], [[...], [...]], ...)},
                    {'Vulnfishing': np.array([...], [...]), ...},
    '''
    csv_data = []
    pop_dict = {}

    with open(uri, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            csv_data.append(line)

    start_rows = _get_table_row_start_indexes(csv_data)
    start_cols = _get_table_col_start_indexes(csv_data, start_rows[0])
    end_rows = _get_table_row_end_indexes(csv_data)
    end_cols = _get_table_col_end_indexes(csv_data, start_rows[0])

    classes = _get_col(
        csv_data, start_rows[0])[0:end_rows[0]+1]

    pop_dict["Classes"] = map(lambda x: x.lower(), classes[1:])
    if sexsp == 2:
        pop_dict["Classes"] = pop_dict["Classes"][0:len(pop_dict["Classes"])/2]

    regions = _get_row(csv_data, start_cols[0])[0: end_cols[0]+1]

    pop_dict["Regions"] = regions[1:]

    surv_table = _get_table(csv_data, start_rows[0]+1, start_cols[0]+1)
    class_attributes_table = _get_table(
        csv_data, start_rows[0], start_cols[1])
    region_attributes_table = _get_table(
        csv_data, start_rows[1], start_cols[0])

    if sexsp == 1:
        # Sex Neutral
        pop_dict['Survnaturalfrac'] = np.array(
            [surv_table], dtype=np.float_).swapaxes(1, 2).swapaxes(0, 1)

    elif sexsp == 2:
        # Sex Specific
        female = np.array(surv_table[0:len(surv_table)/sexsp], dtype=np.float_)
        male = np.array(surv_table[len(surv_table)/sexsp:], dtype=np.float_)
        pop_dict['Survnaturalfrac'] = np.array(
            [female, male]).swapaxes(1, 2).swapaxes(0, 1)

    else:
        # Throw exception about sex-specific conflict or formatting issue
        LOGGER.error("Could not parse table given Sex-Specific inputs")
        raise Exception

    for col in range(0, len(class_attributes_table[0])):
        pop_dict.update(_vectorize_attribute(
            _get_col(class_attributes_table, col), sexsp))

    for row in range(0, len(region_attributes_table)):
        pop_dict.update(_vectorize_reg_attribute(
            _get_row(region_attributes_table, row)))

    return pop_dict


def _verify_migration_tables(args, class_list, region_list):
    '''Parses, verifies and orders list of migration matrices necessary for
    program.

    If migration matrices are not provided for all classes, the function will
    generate identity matrices for missing classes

    Example:

        mig_dict = {'Migration': [np.matrix, np.matrix, ...]}
    '''
    migration_dict = {}

    # If Migration:
    mig_dict = _parse_migration_tables(args, class_list)

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


def _parse_migration_tables(args, class_list):
    '''Parses the migration tables given by user

    Parses all files in the given directory as migration matrices and returns a
    dictionary of stages and their corresponding migration numpy matrix. If
    extra files are provided that do not match the class names, an exception
    will be thrown.

    Args:
        uri (string): filepath to the directory of migration tables

    Returns:
        mig_dict (dictionary)

    Example::

        mig_dict = {{'stage1': np.matrix}, {'stage2': np.matrix}, ...}
    '''
    mig_dict = {}

    if args['migr_cont']:
        uri = args['migration_dir']
        if not os.path.isdir(uri):
            LOGGER.error("Migration directory does not exist")
            raise OSError
        try:
            for mig_csv in _listdir(uri):
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
                else:
                    # Warn user if possible mig matrix isn't being added
                    LOGGER.warning("The %s class in the Migration Directory did not match any class in the Population Attributes File. This could result in no migration for a class with expected migration.", class_name.capitalize())

        except:
            LOGGER.warning("Issue parsing at least one migration table")

    return mig_dict


def _verify_single_params(args):
    '''
    Example Returned Parameters Dictionary::

        {
            'workspace_dir': 'path/to/workspace_dir',
            'population_csv_uri': 'path/to/csv_uri',
            'migration_dir': 'path/to/mig_dir',
            'aoi_uri': 'path/to/aoi_uri',
            'total_timesteps': 100,
            'population_type': 'Stage-Based',
            'sexsp': 2,
            'spawn_units': 'Weight',
            'total_init_recruits': 100.0,
            'recruitment_type': 'Ricker',
            'alpha': 32.4,
            'beta': 54.2,
            'total_recur_recruits': 92.1,
            'migr_cont': True,
            'harv_cont': True,
            'harvest_units': 'Individuals',
            'frac_post_process': 0.5,
            'unit_price': 5.0,
            # ...
            'output_dir': 'path/to/output_dir',
        }
    '''
    params_dict = args

    # Check that workspace directory exists, if not, try to create directory
    if not os.path.isdir(args['workspace_dir']):
        try:
            os.makedirs(args['workspace_dir'])
        except:
            LOGGER.error("Cannot create Workspace Directory")
            raise OSError

    # Create output directory
    output_dir = os.path.join(args['workspace_dir'], 'output')
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            LOGGER.error("Cannot create Output Directory")
            raise OSError
    params_dict['output_dir'] = output_dir

    # Create output directory
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    if not os.path.isdir(intermediate_dir):
        try:
            os.makedirs(intermediate_dir)
        except:
            LOGGER.error("Cannot create Intermediate Directory")
            raise OSError
    params_dict['intermediate_dir'] = intermediate_dir

    # Check that timesteps is positive integer
    total_timesteps = args['total_timesteps']
    if type(total_timesteps) != int or total_timesteps < 1:
        LOGGER.error("Total Time Steps value must be positive integer")
        raise ValueError
    params_dict['total_timesteps'] = total_timesteps + 1

    # Check total_init_recruits for non-negative float
    total_init_recruits = args['total_init_recruits']
    if type(total_init_recruits) != float or total_init_recruits < 0:
        LOGGER.error("Total Initial Recruits value must be non-negative float")
        raise ValueError

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
                "Total Recruits per Time Step must be non-negative float")
            raise ValueError

    # If Harvest:
    if args['harv_cont']:
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

    return params_dict


# Helper function for Migration directory
def _listdir(path):
    '''A replacement for the standar os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Args:
        path (string): the location container from which we want to
            gather all files

    Returns:
        uris (list): A list of full URIs contained within 'path'
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris


# Helper functions for navigating CSV files
def _get_col(lsts, col):
    # print "LSTS"
    # print lsts
    # print "Column:", col
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


def _get_table_row_end_indexes(lsts):
    indexes = []
    for i in range(1, len(lsts)):
        if (lsts[i][0] == '' and lsts[i-1][0] != ''):
            indexes.append(i-1)
    if lsts[-1] != '':
        indexes.append(len(lsts)-1)

    return indexes


def _get_table_col_end_indexes(lsts, top):
    indexes = []
    for i in range(1, len(lsts[top])):
        if (lsts[top][i] == '' and lsts[top][i-1] != ''):
            indexes.append(i-1)
    if lsts[top][-1] != '':
        indexes.append(len(lsts[top])-1)

    return indexes


def _vectorize_attribute(lst, rows):
    d = {}
    a = np.array(lst[1:], dtype=np.float_)
    a = np.reshape(a, (rows, a.shape[0] / rows))
    d[lst[0].strip().capitalize()] = a
    return d


def _vectorize_reg_attribute(lst):
    d = {}
    a = np.array(lst[1:], dtype=np.float_)
    d[lst[0].strip().capitalize()] = a
    return d


# Generate Outputs
def generate_outputs(vars_dict):
    '''
    '''
    # CSV results page
    _generate_intermediate_csv(vars_dict)
    _generate_results_csv(vars_dict)
    # HTML results page
    _generate_results_html(vars_dict)
    # Append Results to Shapefile
    if vars_dict['aoi_uri']:
        _generate_results_aoi(vars_dict)


def _generate_results_csv(vars_dict):
    '''Generates a CSV file that contains a summary of all harvest totals
    for each subregion.
    '''
    uri = os.path.join(vars_dict['output_dir'], 'Results_Table.csv')
    Spawners_t = vars_dict['Spawners_t']
    H_tx = vars_dict['H_tx']
    V_tx = vars_dict['V_tx']
    equilibrate_timestep = int(vars_dict['equilibrate_timestep'])
    Regions = vars_dict['Regions']

    with open(uri, 'wb') as csv_file:
        csv_writer = csv.writer(csv_file)

        total_timesteps = vars_dict['total_timesteps']

        #Header for final results table
        csv_writer.writerow(
            ['Final Harvest by Subregion after ' + str(total_timesteps-1) +
                ' Time Steps'])
        csv_writer.writerow([])

        # Breakdown Harvest and Valuation for each Region of Final Cycle
        sum_headers_row = ['Subregion', 'Harvest', 'Valuation']
        csv_writer.writerow(sum_headers_row)
        for i in range(0, len(H_tx[-1])):  # i is a cycle
            line = [Regions[i], "%.2f" % H_tx[-1, i], "%.2f" % V_tx[-1, i]]
            csv_writer.writerow(line)
        line = ['Total', "%.2f" % H_tx[-1].sum(), "%.2f" % V_tx[-1].sum()]
        csv_writer.writerow(line)

        # Give Total Harvest for Each Cycle
        csv_writer.writerow([])
        csv_writer.writerow(['Time Step Breakdown'])
        csv_writer.writerow([])
        csv_writer.writerow(['Time Step', 'Spawners', 'Harvest', 'Equilibrated?'])

        for i in range(0, len(H_tx)):  # i is a cycle
            line = [i, "%.2f" % Spawners_t[i], "%.2f" % H_tx[i].sum()]
            # This can be more rigorously checked
            if equilibrate_timestep and i >= equilibrate_timestep:
                line.append('Y')
            else:
                line.append('N')
            csv_writer.writerow(line)


def _generate_intermediate_csv(vars_dict):
    '''Creates an intermediate output that gives the number of
    individuals within each area for each time step for each age/stage.
    '''
    uri = os.path.join(
        vars_dict['intermediate_dir'], 'Population_by_Time_Step.csv')
    Regions = vars_dict['Regions']
    Classes = vars_dict['Classes']
    N_tasx = vars_dict['N_tasx']
    N_txsa = N_tasx.swapaxes(1, 3)
    sexsp = vars_dict['sexsp']
    Sexes = ['Female', 'Male']

    with open(uri, 'wb') as c_file:
        # c_writer = csv.writer(c_file)
        if sexsp == 2:
            line = "Time Step, Region, Class, Sex, Numbers\n"
            c_file.write(line)
        else:
            line = "Time Step, Region, Class, Numbers\n"
            c_file.write(line)

        for t in range(0, len(N_txsa)):
            for x in range(0, len(Regions)):
                for a in range(0, len(Classes)):
                    if sexsp == 2:
                        for s in range(0, 2):
                            line = "%i, %s, %s, %s, %f\n" % (
                                t, Regions[x], Classes[a], Sexes[s], N_txsa[t, x, s, a])
                            c_file.write(line)
                    else:
                        line = "%i, %s, %s, %f\n" % (
                                t, Regions[x], Classes[a], N_txsa[t, x, 0, a])
                        c_file.write(line)


def _generate_results_html(vars_dict):
    '''Creates an HTML file that contains a summary of all harvest totals
    for each subregion.
    '''
    uri = os.path.join(vars_dict['output_dir'], 'Results_Page.html')
    recruitment_type = vars_dict['recruitment_type']
    Spawners_t = vars_dict['Spawners_t']
    H_tx = vars_dict['H_tx']
    V_tx = vars_dict['V_tx']
    equilibrate_timestep = int(vars_dict['equilibrate_timestep'])
    Regions = vars_dict['Regions']

    # Set Reporting Arguments
    rep_args = {}
    rep_args['title'] = "Fishieries Results Page"
    rep_args['out_uri'] = uri
    rep_args['sortable'] = True  # JS Functionality
    rep_args['totals'] = True  # JS Functionality

    total_timesteps = len(H_tx)

    # Create Model Run Overview Table
    overview_columns = [{'name': 'Attribute', 'total': False},
                        {'name': 'Value', 'total': False}]

    overview_body = [
        {'Attribute': 'Model Type', 'Value': vars_dict['population_type']},
        {'Attribute': 'Recruitment Type', 'Value': vars_dict['recruitment_type']},
        {'Attribute': 'Sex-Specific?', 'Value': (
            'Yes' if vars_dict['sexsp'] == 2 else 'No')},
        {'Attribute': 'Classes', 'Value': str(len(vars_dict['Classes']))},
        {'Attribute': 'Regions', 'Value': str(len(Regions))},
    ]

    # Create Final Cycle Harvest Summary Table
    final_cycle_columns = [{'name': 'Subregion', 'total': False},
                           {'name': 'Harvest', 'total': True},
                           {'name': 'Valuation', 'total': True}]

    final_timestep_body = []
    for i in range(0, len(H_tx[-1])):  # i is a cycle
        sub_dict = {}
        sub_dict['Subregion'] = Regions[i]
        sub_dict['Harvest'] = "%.2f" % H_tx[-1, i]
        sub_dict['Valuation'] = "%.2f" % V_tx[-1, i]
        final_timestep_body.append(sub_dict)

    # Create Harvest Time Step Table
    timestep_breakdown_columns = [{'name': 'Time Step', 'total': False},
                               {'name': 'Spawners', 'total': True},
                               {'name': 'Harvest', 'total': True},
                               {'name': 'Equilibrated?', 'total': False}]

    timestep_breakdown_body = []
    for i in range(0, total_timesteps):
        sub_dict = {}
        sub_dict['Time Step'] = str(i)
        if i == 0:
            sub_dict['Spawners'] = "(none)"
        elif recruitment_type == 'Fixed':
            sub_dict['Spawners'] = "(fixed recruitment)"
        else:
            sub_dict['Spawners'] = "%.2f" % Spawners_t[i]
        sub_dict['Harvest'] = "%.2f" % H_tx[i].sum()
        # This can be more rigorously checked
        if equilibrate_timestep and i >= equilibrate_timestep:
            sub_dict['Equilibrated?'] = 'Y'
        else:
            sub_dict['Equilibrated?'] = 'N'
        timestep_breakdown_body.append(sub_dict)

    # Generate Report
    css = """body { background-color: #EFECCA; color: #002F2F; }
         h1 { text-align: center }
         h1, h2, h3, h4, strong, th { color: #046380 }
         h2 { border-bottom: 1px solid #A7A37E }
         table { border: 5px solid #A7A37E; margin-bottom: 50px; background-color: #E6E2AF; }
         table.sortable thead:hover { border: 5px solid #A7A37E; margin-bottom: 50px; background-color: #E6E2AF; }
         td, th { margin-left: 0px; margin-right: 0px; padding-left: 8px; padding-right: 8px; padding-bottom: 2px; padding-top: 2px; text-align: left; }
         td { border-top: 5px solid #EFECCA }
         img { margin: 20px }"""

    elements = [{
                'type': 'text',
                'section': 'body',
                'text': '<h2>Model Run Overview</h2>'
                },
                {
                    'type': 'table',
                    'section': 'body',
                    'sortable': True,
                    'checkbox': False,
                    'total': False,
                    'data_type': 'dictionary',
                    'columns': overview_columns,
                    'data': overview_body
                },
                {
                    'type': 'text',
                    'section': 'body',
                    'text': '<h2>Final Harvest by Subregion After ' +
                            str(total_timesteps-1) + ' Time Steps</h2>'},
                {
                    'type': 'table',
                    'section': 'body',
                    'sortable': True,
                    'checkbox': False,
                    'total': True,
                    'data_type': 'dictionary',
                    'columns': final_cycle_columns,
                    'data': final_timestep_body
                },
                {
                    'type': 'text',
                    'section': 'body',
                    'text': '<h2>Time Step Breakdown</h2>'
                },
                {
                    'type': 'table',
                    'section': 'body',
                    'sortable': True,
                    'checkbox': False,
                    'total': False,
                    'data_type': 'dictionary',
                    'columns': timestep_breakdown_columns,
                    'data': timestep_breakdown_body
                },
                {
                    'type': 'head',
                    'section': 'head',
                    'format': 'style',
                    'data_src': css,
                    'input_type': 'Text'
                }]

    rep_args['elements'] = elements

    reporting.generate_report(rep_args)


def _generate_results_aoi(vars_dict):
    '''Appends the final harvest and valuation values for each region to an
    input shapefile.  The 'NAME' attributes of each region in the input
    shapefile must exactly match the names of each region in the population
    parameters file.

    '''
    aoi_uri = vars_dict['aoi_uri']
    Regions = vars_dict['Regions']
    H_tx = vars_dict['H_tx']
    V_tx = vars_dict['V_tx']
    basename = os.path.splitext(os.path.basename(aoi_uri))[0]
    output_aoi_uri = os.path.join(
        vars_dict['output_dir'], basename + '_Results.shp')

    # Copy AOI file to outputs directory
    raster_utils.copy_datasource_uri(aoi_uri, output_aoi_uri)

    # Append attributes to Shapefile
    ds = ogr.Open(output_aoi_uri, update=1)
    layer = ds.GetLayer()

    # Set Harvest
    harvest_field = ogr.FieldDefn('Hrv_Total', ogr.OFTReal)
    layer.CreateField(harvest_field)

    harv_reg_dict = {}
    for i in range(0, len(Regions)):
        harv_reg_dict[Regions[i]] = H_tx[-1][i]

    # Set Valuation
    val_field = ogr.FieldDefn('Val_Total', ogr.OFTReal)
    layer.CreateField(val_field)

    val_reg_dict = {}
    for i in range(0, len(Regions)):
        val_reg_dict[Regions[i]] = V_tx[-1][i]

    # Add Information to Shapefile
    for feature in layer:
        region_name = str(feature.items()['NAME'])
        feature.SetField('Hrv_Total', "%.2f" % harv_reg_dict[region_name])
        feature.SetField('Val_Total', "%.2f" % val_reg_dict[region_name])
        layer.SetFeature(feature)

    layer.ResetReading()
