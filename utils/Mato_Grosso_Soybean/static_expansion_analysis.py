"""This script analyzes the static LULC change maps to report statistics
    about the kinds of lucodes that are changed on each step."""

import gdal
import numpy
import scipy.ndimage
import scipy
import scipy.stats
import csv
import os


def analyze_premade_lulc_scenarios(args):
    """This function loads scenarios from disk and calculates stats like
        how many pixels of each types change per step.

        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['scenario_path'] - the path to the directory that holds the
            scenarios
        args['scenario_file_pattern'] - the filename pattern to load the
            scenarios, a string of the form xxxxx%nxxxx, where %n is the
            simulation step integer.
        args['lucode_to_description'] - a dictionary that maps lucodes
            to their texual descriptions.  it will also define what columns
            are output in the analysis CSV table
        """

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')

    lucode_header = ''
    for lucode in sorted(args['lucode_to_description'].keys()):
        lucode_header += "%s (%d)," % (
            args['lucode_to_description'][lucode], lucode)
    output_table.write('percent change,%s\n' % lucode_header)

    #Load the first scenario
    scenario_base_filename = os.path.join(
            args['scenario_path'],
            args['scenario_file_pattern'].replace('%n', str(0)))
    scenario_dataset = gdal.Open(scenario_base_filename)
    scenario_prev_lulc_array = (
        scenario_dataset.GetRasterBand(1).ReadAsArray())

    for percent in range(1, args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for expansion step %s' % percent

        scenario_filename = os.path.join(
            args['scenario_path'],
            args['scenario_file_pattern'].replace('%n', str(percent)))
        scenario_dataset = gdal.Open(scenario_filename)
        scenario_lulc_array = (
            scenario_dataset.GetRasterBand(1).
            ReadAsArray())
        pixel_change_mask = numpy.where(
            scenario_lulc_array != scenario_prev_lulc_array)

        changed_lucodes = scenario_prev_lulc_array[pixel_change_mask]
        output_table.write('%d,' % percent)
        for lucode in sorted(args['lucode_to_description'].keys()):
            output_table.write('%d,' % numpy.count_nonzero(
                changed_lucodes == lucode))
        output_table.write('\n')
        output_table.flush()
        scenario_prev_lulc_array = scenario_lulc_array


if __name__ == '__main__':
    ARGS = {
        'scenario_conversion_steps': 400,
    }

    #Set up the args for the disk based scenario
    ARGS['scenario_path'] = './MG_Soy_Exp_07122013/'
    ARGS['scenario_file_pattern'] = 'mg_lulc%n'
    ARGS['output_table_filename'] = (
        'pre_calculated_scenarios_pixel_change.csv')

    ARGS['lucode_to_description'] = {
        0: 'Water',
        1: 'Evergreen Needleleaf forest',
        2: 'Evergreen Broadleaf forest',
        3: 'Deciduous Needleleaf forest',
        4: 'Deciduous Broadleaf forest',
        5: 'Mixed forest',
        6: 'Closed shrublands/ Cerrado',
        7: 'Open shrublands',
        8: 'Woody savannas',
        9: 'Savannas',
        10: 'Grasslands',
        12: 'Croplands/Perennial',
        13: 'Urban and built-up',
        16: 'Barren or sparsely vegetated',
        120: 'Soybean Croplands',
    }


    analyze_premade_lulc_scenarios(ARGS)
