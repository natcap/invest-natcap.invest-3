"""Entry point for the Habitat Risk Assessment module"""

import re
import csv
import os
import glob
import logging
from invest_natcap.habitat_risk_assessment import hra

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')

def execute(args):
    """Want to read in multiple hab/stressors directories, in addition to named
    criteria, and make an appropriate csv file.

    Input:
        args['workspace_dir'] - The directory to dump the output CSV files to.
        args['habitat_dir'] - A directory of shapefiles that are habitats.
        args['species_dir']- Directory which holds all species shapefiles, but
            may or may not actually exist within args.
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors
        args['criteria_dir']- Directory which holds the criteria shapefiles.
            This needs to be in a VERY specific format, which shall be described
            in the user's guide.
        Criteria....dictionary....thing? Would somehow be organized by which
        subcategory they were in, and whether or not they were checked.

    Output:
        hra_args[

        - JSON file containing vars that need to be passed on to hra non-core
            when that gets run. Should live inside the preprocessor folder.
    Returns nothing.
    """

    hra_args = {}

    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #Get the names of all potential habs
    hab_list = []
    for ele in ('habitat_dir', 'species_dir'):
        if ele in args:
            hab_list.append(glob.glob(os.path.join(args[ele], '*.shp')))
            hab_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], hab_list)
    
    #And all potential stressors
    stress_list = []
    stress_list.append(glob.glob(os.path.join(args['stressor_dir'], '*.shp')))
    stress_list = map(lambda uri: os.path.splitext(os.path.basename(uri))[0], stress_list)


    '''Want to pull the shapefile criteria from the folder structure specified.
    this function will return a dictionary with the following form:
        {'h-s':
            {('HabA', 'Stress1'):
                {'CritName': "Shapefile URI", ...}
            },
         's':
            {'Stress1':
                {'CritName': "Shapefile URI", ...}
            },
         'h':
            {'HabA':
                {'CritName': "Shapefile URI", ...}
        }
    '''
    crit_shapes = hra.make_crit_shape_dict(args['criteria_dir'])
    
    crit_descriptions = {
        'change in area rating': '<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'change in structure rating': '<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'temporal overlap rating': '<enter (3) co-occur 8-12 mo/year, (2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>',
        
        'frequency of disturbance': '<enter (3) Annually or less often, (2) Several times per year, (1) Weekly or more often, (0) no score>',
        'intensity Rating:': '<enter (3) high, (2) medium, (1) low, (0) no score>',
        'management effectiveness:': '<enter (3) not effective, (2) somewhat effective, (1) very effective, (0) no score>',
        'natural mortality': '<enter (3) 0-20%, (2) 20-50%, (1) >80% mortality, or (0) no score>',
        'recruitment rate': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, (1) every <1 yrs, or (0) no score>',
        'recovery time': '<enter (3) >10 yrs, (2) 1-10 yrs, (1) <1 yr, or (0) no score>',
        'connectivity rate': '<enter (3) <10km, (2) 10-100km, (1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited, or (0) unknown>'
    default_weight_message = '<enter (3) more important, (2) equal importance, (1) less important>'
    default_headers = ['', 'Rating', 'DQ', 'Weight']
    default_row = [default_dq_message, default_weight_message]
