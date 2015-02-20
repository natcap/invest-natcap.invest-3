"""
(About Blue Carbon)
"""

import logging
import pprint as pp

import blue_carbon_io as io
import blue_carbon_model as model

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('blue_carbon')


def execute(args):
    """
    Entry point for the blue carbon model.

    Args:
        workspace_dir (string): the directory to hold output from a particular
            model run
        lulc_uri_1 (string): the land use land cover raster for time 1.
        year_1 (int): the year for the land use land cover raster for time 1.
        lulc_uri_2 (string): the land use land cover raster for time 2.
        year_2 (int): the year for the land use land cover raster for time 2.
        lulc_uri_3 (string): the year for the land use land cover raster for
            time 3.
        year_3 (int): the year for the land use land cover raster for time 3.
        lulc_uri_4 (string): the year for the land use land cover raster for
            time 4.
        year_4 (int): the year for the land use land cover raster for time 4.
        lulc_uri_5 (string): the year for the land use land cover raster for
            time 5.
        year_5 (int): the year for the land use land cover raster for time 5.
        analysis_year (int): analysis end year
        soil_disturbance_csv_uri (string): soil disturbance csv file
        biomass_disturbance_csv_uri (string): biomass disturbance csv file
        carbon_pools_uri (string): Carbon in Metric Tons per Hectacre
            (t ha-1) stored in each of the four fundamental pools for
            each land-use/land-cover class.
        half_life_csv_uri (string): carbon half-lives csv file
        transition_matrix_uri (string): Coefficients for the carbon storage
            rates for the transtion between each of the land-use/land-cover
            classes. Values above 1 indicate an increase, values below 1
            indicate a decrease. Absent transitions are assigned a value
            of 1, representing no change.
        snapshots (boolean): enable snapshots
        start (int): start year
        step (int): years between snapshots
        stop (int): stop year
        do_private_valuation (boolean): enable private valuation
        discount_rate (int): the discount rate as an integer percent.
        price_table (boolean): enable price table
        carbon_schedule (string): the social cost of carbon table.
        carbon_value (float): the price per unit ton of carbon or C02 as
            defined in the carbon price units.
        rate_change (float): the integer percent increase of the price of
            carbon per year.

    Example Args::

        args = {
            'workspace_dir': '/path/to/workspace_dir/',
            'lulc_uri_1': '/path/to/lulc_uri_1',
            'year_1': 2004,
            'lulc_uri_2': '/path/to/lulc_uri_2',
            'year_2': 2050,
            'lulc_uri_3': '/path/to/lulc_uri_3',
            'year_3': 2100,
            'lulc_uri_4': '/path/to/lulc_uri_4',
            'analysis_year': 2150,
            'soil_disturbance_csv_uri': '/path/to/csv',
            'biomass_disturbance_csv_uri': '/path/to/csv',
            'carbon_pools_uri': '/path/to/csv',
            'half_life_csv_uri': '/path/to/csv',
            'transition_matrix_uri': '/path/to/csv',
            'do_private_valuation': True,
            'discount_rate': 5,
            'do_price_table': True,
            'carbon_schedule': '/path/to/csv',
            'carbon_value': 43.00,
            'rate_change': 0,
        }

    """
    vars_dict = io.fetch_args(args)

    # with open('output.txt', 'wt') as out:
    #     pp.pprint(vars_dict, stream=out)
    # return

    # Biophysical Component
    vars_dict = model.run_biophysical(vars_dict)

    # Valuation Component
    if args["do_private_valuation"]:
        model.run_valuation(vars_dict)
