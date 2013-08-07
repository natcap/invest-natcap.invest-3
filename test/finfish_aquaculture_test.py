"""URI level tests for the aquaculture biophysical and valuation module"""

import os
import sys
import shutil
import unittest
import filecmp
import re

from osgeo import ogr
import numpy as np

from invest_natcap.finfish_aquaculture import finfish_aquaculture
from invest_natcap.report_generation import html
import invest_test_core
import html_test_utils

class TestFinfishAquaculture(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = './invest-data/test/data/test_out/Aquaculture'
        self.output_dir = os.path.join(self.workspace_dir, 'Output')

        # Get rid of old output files before each test run.
        if os.path.exists(self.output_dir):
            for out_file in os.listdir(self.output_dir):
                uri = os.path.join(self.output_dir, out_file)
                try:
                    # Try removing it as a file.
                    os.remove(uri)
                except OSError:
                    # Try removing it as a directory (e.g. the 'images' dir).
                    shutil.rmtree(uri)

    def get_args(self, do_valuation=False, use_uncertainty=False):
        args = {}
        args['workspace_dir'] = self.workspace_dir
        args['ff_farm_loc'] = './invest-data/test/data/aquaculture_data/Test_Data/Finfish_Netpens_Reg_Test.shp'
        args['farm_ID'] = 'FarmID'
        args['g_param_a'] = 0.038
        args['g_param_b'] = 0.6667
        args['water_temp_tbl'] = './invest-data/test/data/aquaculture_data/Test_Data/Temp_Daily_Reg_Test.csv'
        args['farm_op_tbl'] = './invest-data/test/data/aquaculture_data/Test_Data/Farm_Operations_Reg_Test.csv'
        args['outplant_buffer'] = 3

        if use_uncertainty:
            args['use_uncertainty'] = True
            args['g_param_a_sd'] = 0.005
            args['g_param_b_sd'] = 0.05
            args['num_monte_carlo_runs'] = 100

            # Seed the numpy random number generator for predictable results.
            np.random.seed(1)
        else:
            args['use_uncertainty'] = False

        if do_valuation:
            args['do_valuation'] = True
            args['p_per_kg']= 2.25
            args['frac_p'] = .3
            args['discount'] = 0.000192
        else:
            args['do_valuation'] = False

        return args

    def test_format_ops_table(self):
        expected_ops_table = {'1': {'weight of fish at start (kg)' : '0.06',
                                    'target weight of fish at harvest (kg)' : '5.4',
                                    'number of fish in farm' : '600000',
                                    'start day for growing' : '1',
                                    'Length of Fallowing period' : '30'},
                              '4': {'weight of fish at start (kg)' : '0.08',
                                    'target weight of fish at harvest (kg)' : '6',
                                    'number of fish in farm' : '500000',
                                    'start day for growing' : '20',
                                    'Length of Fallowing period' : '0'}}

        args = self.get_args()
        finfish_aquaculture.format_ops_table(args['farm_op_tbl'], "Farm #:", args)
        norm_ops_table = args['farm_op_dict']
        self.assertEqual(expected_ops_table, norm_ops_table)

    def test_format_temp_table(self):
        args = self.get_args()
        finfish_aquaculture.format_temp_table(args['water_temp_tbl'], args)
        norm_temp_table = args['water_temp_dict']

        self.maxDiff = None
        self.assertEqual(_get_expected_temp_table(), norm_temp_table)

    def assert_files_equal(self, ref_filename, output_filename=None, comp_type='shape'):
        if not output_filename:
            output_filename = ref_filename

        output_uri = os.path.join(self.output_dir, output_filename)
        ref_uri = os.path.join('./invest-data/test/data/aquaculture_data/Expected_Output',
                               ref_filename)

        if comp_type == 'shape':
            invest_test_core.assertTwoShapesEqualURI(self, ref_uri, output_uri)
        elif comp_type == 'file':
            self.assertTrue(filecmp.cmp(ref_uri, output_uri, shallow=False))
        else:
            raise Exception("This method doesn't support file comparison type '%s'"  %
                            comp_type)

    def test_finfish_model(self):
        finfish_aquaculture.execute(self.get_args())
        self.check_html_report()

        finfish_aquaculture.execute(self.get_args(do_valuation=True))
        self.assert_files_equal('Finfish_Harvest.shp')
        self.check_html_report(do_valuation=True)

    def test_finfish_model_with_uncertainty(self):
        finfish_aquaculture.execute(self.get_args(use_uncertainty=True))
        self.check_html_report(use_uncertainty=True)

        finfish_aquaculture.execute(self.get_args(do_valuation=True,
                                                  use_uncertainty=True))
        self.assert_files_equal('Finfish_Harvest.shp')
        self.check_html_report(do_valuation=True, use_uncertainty=True)

    def check_html_report(self, do_valuation=False, use_uncertainty=False):
        '''Tests a few rows in the HTML report for the expected values.'''
        # Find the file.
        for filename in os.listdir(self.output_dir):
            if re.match(r'Harvest_Results[_0-9\[\]\-]+\.html', filename):
                html_uri = os.path.join(self.output_dir, filename)
                break
        else:
            self.fail("Didn't find a Harvest Results HTML file in the output folder.")

        # Check the farm operations table.
        html_test_utils.assert_table_contains_rows_uri(
            self, html_uri, 'farm_ops_table',
            [[1, 0.06, 5.4, 600000, 1, 30],
             [4, 0.08, 6, 500000, 20, 0]])

        # Check the farm harvesting table.
        if do_valuation:
            harvest_rows = [
                [1, 1, 617, 616, 2531362.01225, 3986.89516929, 3541.53463533, 1, 1],
                [1, 2, 1344, 616, 2531362.01225, 3986.89516929, 3080.18464345, 363, 2]]
        else:
            harvest_rows = [
                [1, 1, 617, 616, 2531362.01225, '(no valuation)', '(no valuation)', 1, 1],
                [1, 2, 1344, 616, 2531362.01225, '(no valuation)', '(no valuation)', 363, 2]]
        html_test_utils.assert_table_contains_rows_uri(
            self, html_uri, 'harvest_table', harvest_rows)

        # Check the farm result totals table.
        if do_valuation:
            totals_rows = [
                [1, 6621.7193, 2, 5062724.0245],
                [4, 6198.587, 2, 4722863.6745]]
        else:
            totals_rows = [
                [1, '(no valuation)', 2, 5062724.0245],
                [4, '(no valuation)', 2, 4722863.6745]]
        html_test_utils.assert_table_contains_rows_uri(
            self, html_uri, 'totals_table', totals_rows)

        if not use_uncertainty:
            return

        # Check the uncertainty table.
        uncertainty_rows = [
            ['Total (all farms)', 9407678.16305, 4360554.97538,
             12430.5918386, 5696.36013219],
            ['Farm 1', 4698976.86064, 2163202.13865,
             6215.76470719, 2824.16194289]]
        if not do_valuation:
            for row in range(2):
                for col in range(3, 5):
                    uncertainty_rows[row][col] = '(no valuation)'
        html_test_utils.assert_table_contains_rows_uri(
            self, html_uri, 'uncertainty_table', uncertainty_rows)

        # Check the histogram images.
        image_paths = self.expected_image_paths(do_valuation)

        # Make sure the image files exist.
        for image_path in image_paths:
            self.assertTrue(os.path.isfile(
                    os.path.join(self.output_dir, image_path)))

        # Make sure the image files are embedded in the HTML report.
        image_elems = [html.Element('img', src=path) for path in image_paths]
        html_test_utils.assert_contains_matching_elems(self, html_uri, image_elems)

    def expected_image_paths(self, do_valuation):
        plot_types = ['weight', 'cycles']
        if do_valuation:
            plot_types.append('value')

        filenames = []
        for plot_type in plot_types:
            for farm in ['1', '4']:
                filenames.append('farm_%s_%s.png' % (farm, plot_type))
            if plot_type != 'cycles':
                filenames.append('total_%s.png' % plot_type)

        return [os.path.join('images', name) for name in filenames]

def _get_expected_temp_table():
    '''Return a formatted temperature table to compare against for testing.'''
    return {'344': {'1': '7', '4': '8'}, '0': {'1': '7', '4': '8'},
            '346': {'1': '7', '4': '8'}, '347': {'1': '7', '4': '8'},
            '340': {'1': '7', '4': '8'}, '341': {'1': '7', '4': '8'},
            '342': {'1': '7', '4': '8'}, '343': {'1': '7', '4': '8'},
            '348': {'1': '7', '4': '8'}, '349': {'1': '7', '4': '8'},
            '298': {'1': '7', '4': '8'}, '299': {'1': '7', '4': '8'},
            '296': {'1': '7', '4': '8'}, '297': {'1': '7', '4': '8'}, '294': {'1': '7', '4': '8'}, '295': {'1': '7', '4': '8'}, '292': {'1': '7', '4': '8'}, '293': {'1': '7', '4': '8'}, '290': {'1': '7', '4': '8'}, '291': {'1': '7', '4': '8'}, '199': {'1': '7', '4': '8'},
            '198': {'1': '7', '4': '8'}, '195': {'1': '7', '4': '8'}, '194': {'1': '7', '4': '8'}, '197': {'1': '7', '4': '8'}, '196': {'1': '7', '4': '8'}, '191': {'1': '7', '4': '8'}, '190': {'1': '7', '4': '8'}, '193': {'1': '7', '4': '8'}, '192': {'1': '7', '4': '8'},
            '270': {'1': '7', '4': '8'}, '271': {'1': '7', '4': '8'}, '272': {'1': '7', '4': '8'}, '273': {'1': '7', '4': '8'}, '274': {'1': '7', '4': '8'}, '275': {'1': '7', '4': '8'}, '276': {'1': '7', '4': '8'}, '277': {'1': '7', '4': '8'}, '278': {'1': '7', '4': '8'},
            '279': {'1': '7', '4': '8'}, '108': {'1': '7', '4': '8'}, '109': {'1': '7', '4': '8'}, '102': {'1': '7', '4': '8'}, '103': {'1': '7', '4': '8'}, '100': {'1': '7', '4': '8'}, '101': {'1': '7', '4': '8'}, '106': {'1': '7', '4': '8'}, '107': {'1': '7', '4': '8'},
            '104': {'1': '7', '4': '8'}, '105': {'1': '7', '4': '8'}, '39': {'1': '7', '4': '8'}, '38': {'1': '7', '4': '8'}, '33': {'1': '7', '4': '8'}, '32': {'1': '7', '4': '8'}, '31': {'1': '7', '4': '8'}, '30': {'1': '7', '4': '8'}, '37': {'1': '7', '4': '8'},
            '36': {'1': '7', '4': '8'}, '35': {'1': '7', '4': '8'}, '34': {'1': '7', '4': '8'}, '339': {'1': '7', '4': '8'}, '338': {'1': '7', '4': '8'}, '335': {'1': '7', '4': '8'}, '334': {'1': '7', '4': '8'}, '337': {'1': '7', '4': '8'}, '336': {'1': '7', '4': '8'},
            '331': {'1': '7', '4': '8'}, '330': {'1': '7', '4': '8'}, '333': {'1': '7', '4': '8'}, '332': {'1': '7', '4': '8'}, '345': {'1': '7', '4': '8'}, '6': {'1': '7', '4': '8'}, '99': {'1': '7', '4': '8'}, '98': {'1': '7', '4': '8'}, '91': {'1': '7', '4': '8'},
            '90': {'1': '7', '4': '8'}, '93': {'1': '7', '4': '8'}, '92': {'1': '7', '4': '8'}, '95': {'1': '7', '4': '8'}, '94': {'1': '7', '4': '8'}, '97': {'1': '7', '4': '8'}, '96': {'1': '7', '4': '8'}, '238': {'1': '7', '4': '8'}, '239': {'1': '7', '4': '8'}, '234': {'1': '7', '4': '8'},
            '235': {'1': '7', '4': '8'}, '236': {'1': '7', '4': '8'}, '237': {'1': '7', '4': '8'}, '230': {'1': '7', '4': '8'}, '231': {'1': '7', '4': '8'}, '232': {'1': '7', '4': '8'}, '233': {'1': '7', '4': '8'}, '1': {'1': '7', '4': '8'}, '146': {'1': '7', '4': '8'}, '147': {'1': '7', '4': '8'},
            '144': {'1': '7', '4': '8'}, '145': {'1': '7', '4': '8'}, '142': {'1': '7', '4': '8'}, '143': {'1': '7', '4': '8'}, '140': {'1': '7', '4': '8'}, '141': {'1': '7', '4': '8'}, '148': {'1': '7', '4': '8'}, '149': {'1': '7', '4': '8'}, '133': {'1': '7', '4': '8'},
            '132': {'1': '7', '4': '8'}, '131': {'1': '7', '4': '8'}, '130': {'1': '7', '4': '8'}, '137': {'1': '7', '4': '8'}, '136': {'1': '7', '4': '8'}, '135': {'1': '7', '4': '8'}, '134': {'1': '7', '4': '8'}, '139': {'1': '7', '4': '8'}, '138': {'1': '7', '4': '8'}, '24': {'1': '7', '4': '8'},
            '25': {'1': '7', '4': '8'}, '26': {'1': '7', '4': '8'}, '27': {'1': '7', '4': '8'}, '20': {'1': '7', '4': '8'}, '21': {'1': '7', '4': '8'}, '22': {'1': '7', '4': '8'}, '23': {'1': '7', '4': '8'}, '28': {'1': '7', '4': '8'}, '29': {'1': '7', '4': '8'}, '88': {'1': '7', '4': '8'}, '89': {'1': '7', '4': '8'},
            '82': {'1': '7', '4': '8'}, '83': {'1': '7', '4': '8'}, '80': {'1': '7', '4': '8'}, '81': {'1': '7', '4': '8'}, '86': {'1': '7', '4': '8'}, '87': {'1': '7', '4': '8'}, '84': {'1': '7', '4': '8'}, '85': {'1': '7', '4': '8'}, '7': {'1': '7', '4': '8'}, '245': {'1': '7', '4': '8'}, '244': {'1': '7', '4': '8'}, '247': {'1': '7', '4': '8'},
            '246': {'1': '7', '4': '8'}, '241': {'1': '7', '4': '8'}, '240': {'1': '7', '4': '8'}, '243': {'1': '7', '4': '8'}, '242': {'1': '7', '4': '8'}, '249': {'1': '7', '4': '8'}, '248': {'1': '7', '4': '8'}, '179': {'1': '7', '4': '8'}, '178': {'1': '7', '4': '8'}, '177': {'1': '7', '4': '8'}, '176': {'1': '7', '4': '8'}, '175': {'1': '7', '4': '8'},
            '174': {'1': '7', '4': '8'}, '173': {'1': '7', '4': '8'}, '172': {'1': '7', '4': '8'}, '171': {'1': '7', '4': '8'}, '170': {'1': '7', '4': '8'}, '253': {'1': '7', '4': '8'}, '182': {'1': '7', '4': '8'}, '183': {'1': '7', '4': '8'}, '180': {'1': '7', '4': '8'}, '181': {'1': '7', '4': '8'},
            '186': {'1': '7', '4': '8'}, '187': {'1': '7', '4': '8'}, '184': {'1': '7', '4': '8'}, '185': {'1': '7', '4': '8'}, '188': {'1': '7', '4': '8'}, '189': {'1': '7', '4': '8'}, '11': {'1': '7', '4': '8'}, '10': {'1': '7', '4': '8'}, '13': {'1': '7', '4': '8'}, '12': {'1': '7', '4': '8'}, '15': {'1': '7', '4': '8'},
            '14': {'1': '7', '4': '8'}, '17': {'1': '7', '4': '8'}, '16': {'1': '7', '4': '8'}, '19': {'1': '7', '4': '8'}, '18': {'1': '7', '4': '8'}, '62': {'1': '7', '4': '8'}, '322': {'1': '7', '4': '8'}, '323': {'1': '7', '4': '8'}, '320': {'1': '7', '4': '8'}, '321': {'1': '7', '4': '8'}, '326': {'1': '7', '4': '8'}, '327': {'1': '7', '4': '8'},
            '324': {'1': '7', '4': '8'}, '325': {'1': '7', '4': '8'}, '328': {'1': '7', '4': '8'}, '329': {'1': '7', '4': '8'}, '201': {'1': '7', '4': '8'}, '200': {'1': '7', '4': '8'}, '203': {'1': '7', '4': '8'}, '202': {'1': '7', '4': '8'}, '205': {'1': '7', '4': '8'}, '204': {'1': '7', '4': '8'}, '207': {'1': '7', '4': '8'}, '206': {'1': '7', '4': '8'}, '209': {'1': '7', '4': '8'},
            '208': {'1': '7', '4': '8'}, '77': {'1': '7', '4': '8'}, '76': {'1': '7', '4': '8'}, '75': {'1': '7', '4': '8'}, '74': {'1': '7', '4': '8'}, '73': {'1': '7', '4': '8'}, '72': {'1': '7', '4': '8'}, '71': {'1': '7', '4': '8'}, '70': {'1': '7', '4': '8'}, '79': {'1': '7', '4': '8'},
            '78': {'1': '7', '4': '8'}, '2': {'1': '7', '4': '8'}, '8': {'1': '7', '4': '8'}, '68': {'1': '7', '4': '8'}, '120': {'1': '7', '4': '8'}, '121': {'1': '7', '4': '8'}, '122': {'1': '7', '4': '8'}, '123': {'1': '7', '4': '8'}, '124': {'1': '7', '4': '8'}, '125': {'1': '7', '4': '8'}, '126': {'1': '7', '4': '8'},
            '127': {'1': '7', '4': '8'}, '128': {'1': '7', '4': '8'}, '129': {'1': '7', '4': '8'}, '319': {'1': '7', '4': '8'}, '318': {'1': '7', '4': '8'}, '313': {'1': '7', '4': '8'}, '312': {'1': '7', '4': '8'}, '311': {'1': '7', '4': '8'}, '310': {'1': '7', '4': '8'}, '317': {'1': '7', '4': '8'}, '316': {'1': '7', '4': '8'}, '315': {'1': '7', '4': '8'},
            '314': {'1': '7', '4': '8'}, '3': {'1': '7', '4': '8'}, '362': {'1': '7', '4': '8'}, '363': {'1': '7', '4': '8'}, '360': {'1': '7', '4': '8'}, '361': {'1': '7', '4': '8'}, '60': {'1': '7', '4': '8'}, '61': {'1': '7', '4': '8'}, '258': {'1': '7', '4': '8'}, '259': {'1': '7', '4': '8'}, '64': {'1': '7', '4': '8'},
            '65': {'1': '7', '4': '8'}, '66': {'1': '7', '4': '8'}, '67': {'1': '7', '4': '8'}, '252': {'1': '7', '4': '8'}, '69': {'1': '7', '4': '8'}, '250': {'1': '7', '4': '8'}, '251': {'1': '7', '4': '8'}, '256': {'1': '7', '4': '8'}, '257': {'1': '7', '4': '8'}, '254': {'1': '7', '4': '8'}, '255': {'1': '7', '4': '8'}, '168': {'1': '7', '4': '8'},
            '169': {'1': '7', '4': '8'}, '164': {'1': '7', '4': '8'}, '165': {'1': '7', '4': '8'}, '166': {'1': '7', '4': '8'},
            '167': {'1': '7', '4': '8'}, '160': {'1': '7', '4': '8'}, '161': {'1': '7', '4': '8'}, '162': {'1': '7', '4': '8'}, '163': {'1': '7', '4': '8'}, '9': {'1': '7', '4': '8'}, '357': {'1': '7', '4': '8'}, '356': {'1': '7', '4': '8'}, '355': {'1': '7', '4': '8'}, '354': {'1': '7', '4': '8'}, '353': {'1': '7', '4': '8'}, '352': {'1': '7', '4': '8'},
            '351': {'1': '7', '4': '8'}, '350': {'1': '7', '4': '8'}, '359': {'1': '7', '4': '8'}, '358': {'1': '7', '4': '8'}, '216': {'1': '7', '4': '8'}, '217': {'1': '7', '4': '8'}, '214': {'1': '7', '4': '8'}, '215': {'1': '7', '4': '8'}, '212': {'1': '7', '4': '8'}, '213': {'1': '7', '4': '8'}, '210': {'1': '7', '4': '8'}, '211': {'1': '7', '4': '8'},
            '218': {'1': '7', '4': '8'}, '219': {'1': '7', '4': '8'}, '289': {'1': '7', '4': '8'}, '288': {'1': '7', '4': '8'}, '4': {'1': '7', '4': '8'}, '281': {'1': '7', '4': '8'}, '280': {'1': '7', '4': '8'}, '283': {'1': '7', '4': '8'}, '282': {'1': '7', '4': '8'}, '285': {'1': '7', '4': '8'}, '284': {'1': '7', '4': '8'}, '287': {'1': '7', '4': '8'},
            '286': {'1': '7', '4': '8'}, '263': {'1': '7', '4': '8'}, '262': {'1': '7', '4': '8'}, '261': {'1': '7', '4': '8'}, '260': {'1': '7', '4': '8'}, '267': {'1': '7', '4': '8'}, '266': {'1': '7', '4': '8'}, '265': {'1': '7', '4': '8'}, '264': {'1': '7', '4': '8'}, '269': {'1': '7', '4': '8'}, '268': {'1': '7', '4': '8'}, '59': {'1': '7', '4': '8'}, '58': {'1': '7', '4': '8'},
            '55': {'1': '7', '4': '8'}, '54': {'1': '7', '4': '8'}, '57': {'1': '7', '4': '8'}, '56': {'1': '7', '4': '8'}, '51': {'1': '7', '4': '8'}, '50': {'1': '7', '4': '8'}, '53': {'1': '7', '4': '8'}, '52': {'1': '7', '4': '8'}, '63': {'1': '7', '4': '8'}, '115': {'1': '7', '4': '8'}, '114': {'1': '7', '4': '8'}, '117': {'1': '7', '4': '8'},
            '116': {'1': '7', '4': '8'}, '111': {'1': '7', '4': '8'}, '110': {'1': '7', '4': '8'}, '113': {'1': '7', '4': '8'}, '112': {'1': '7', '4': '8'}, '119': {'1': '7', '4': '8'}, '118': {'1': '7', '4': '8'}, '308': {'1': '7', '4': '8'}, '309': {'1': '7', '4': '8'}, '300': {'1': '7', '4': '8'}, '301': {'1': '7', '4': '8'}, '302': {'1': '7', '4': '8'},
            '303': {'1': '7', '4': '8'}, '304': {'1': '7', '4': '8'}, '305': {'1': '7', '4': '8'}, '306': {'1': '7', '4': '8'}, '307': {'1': '7', '4': '8'}, '229': {'1': '7', '4': '8'}, '228': {'1': '7', '4': '8'}, '227': {'1': '7', '4': '8'}, '226': {'1': '7', '4': '8'}, '225': {'1': '7', '4': '8'}, '224': {'1': '7', '4': '8'}, '223': {'1': '7', '4': '8'},
            '222': {'1': '7', '4': '8'}, '221': {'1': '7', '4': '8'}, '220': {'1': '7', '4': '8'}, '151': {'1': '7', '4': '8'}, '150': {'1': '7', '4': '8'}, '153': {'1': '7', '4': '8'}, '152': {'1': '7', '4': '8'}, '155': {'1': '7', '4': '8'}, '154': {'1': '7', '4': '8'}, '157': {'1': '7', '4': '8'}, '156': {'1': '7', '4': '8'}, '159': {'1': '7', '4': '8'}, '158': {'1': '7', '4': '8'},
            '48': {'1': '7', '4': '8'}, '49': {'1': '7', '4': '8'}, '46': {'1': '7', '4': '8'}, '47': {'1': '7', '4': '8'}, '44': {'1': '7', '4': '8'}, '45': {'1': '7', '4': '8'}, '42': {'1': '7', '4': '8'}, '43': {'1': '7', '4': '8'}, '40': {'1': '7', '4': '8'}, '41': {'1': '7', '4': '8'}, '5': {'1': '7', '4': '8'}, '364': {'1': '7', '4': '8'}}
