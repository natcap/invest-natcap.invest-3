"""Entry point for the Habitat Risk Assessment module"""

import csv
import os
import glob
import logging

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('hra_preprocessor')


def execute(args):
    """Read two directories for habitat and stressor layers and make
        appropriate output csv files

        args['workspace_dir'] - The directory to dump the output CSV files to
        args['habitat_dir'] - A directory of ArcGIS shapefiles that are habitats
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors

        returns nothing"""

    habitats_stressors = {
        'Change in area rating': '<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'Change in structure rating': '(3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>',
        'Overlap Time Rating': '<enter (3) co-occur 8-12 mo/year, (2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>',
        'Frequency of disturbance': '<enter (3) Annually or less often, (2) Several times per year, (1) Weekly or more often, (0) no score>'
        }
    stressors = {
        'Intensity Rating:': '<enter (3) high, (2) medium, (1) low, (0) no score>',
        'Management Effectiveness:': '<enter (3) not effective, (2) somewhat effective, (1) very effective, (0) no score>',
        }
    habitats = {
        'Natural Mortality Rate': '<enter (3) 0-20%, (2) 20-50%, (1) >80% mortality, or (0) no score>',
        'Recruitment Rating': '<enter (3) every 2+ yrs, (2) every 1-2 yrs, (1) every <1 yrs, or (0) no score>',
        'Age at maturity': '<enter (3) >10 yrs, (2) 1-10 yrs, (1) <1 yr, or (0) no score>',
        'Connectivity Rating': '<enter (3) <10km, (2) 10-100km, (1) >100km, or (0) no score>'
        }

    default_dq_message = '<enter (3) best, (2) adequate, (1) limited, or (0) unknown>'
    default_weight_message = '<enter (3) more important, (2) equal importance, (1) less important>'
    default_table_headers = ['', 'Rating', 'Data Quality', 'Weight']
    default_table_row = [default_dq_message, default_weight_message]

    #Make the workspace directory if it doesn't exist
    output_dir = os.path.join(args['workspace_dir'], 'habitat_stressor_ratings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #Pick up all the habitat and stressor names
    name_lookup = {}
    for layer_type in ['habitat', 'stressor']:
        name_lookup[layer_type] = [
            os.path.basename(f.split('.')[0]) for f in 
            glob.glob(os.path.join(args[layer_type + '_dir'], '*.shp'))]


    #Create output csvs so that they are habitat centric
    default_fill_in_message = '<enter 1 (low), 2 (med) 3 (high), or 0 (no data)>'
    for habitat_name in name_lookup['habitat']:
        csv_filename = os.path.join(
            output_dir, habitat_name + '_overlap_ratings.csv')
        with open(csv_filename, 'wb') as habitat_csv_file:
            habitat_csv_writer = csv.writer(habitat_csv_file)
            #Write the habitat name
            habitat_csv_writer.writerow(['HABITAT NAME', habitat_name])
            habitat_csv_writer.writerow(['HABITAT ONLY PROPERTIES'])
            habitat_csv_writer.writerow(['Habitat Data Quality:', default_fill_in_message])
            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(default_table_headers)
            for habitat_property, default_message in habitats.iteritems():
                habitat_csv_writer.writerow([habitat_property, default_message] + default_table_row)

            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT STRESSOR OVERLAP PROPERTIES'])
            for stressor_name in name_lookup['stressor']:
                habitat_csv_writer.writerow([])
                habitat_csv_writer.writerow([habitat_name + '/' + stressor_name + ' OVERLAP'])
                habitat_csv_writer.writerow(['', 'Rating', 'Data Quality', 'Weight'])
                for overlap_property, default_message in habitats_stressors.iteritems():
                    habitat_csv_writer.writerow([overlap_property, default_message] + default_table_row)

    #Make stressor specific tables
    for stressor_name in name_lookup['stressor']:
        csv_filename = os.path.join(
            output_dir, stressor_name + '_stressor_ratings.csv')
        with open(csv_filename, 'wb') as stressor_csv_file:
            stressor_csv_writer = csv.writer(stressor_csv_file)
            stressor_csv_writer.writerow(['STRESSOR NAME', stressor_name])
            stressor_csv_writer.writerow(['Stressor Data Quality:', default_dq_message])
            stressor_csv_writer.writerow(['Stressor Buffer (m):', '<enter a buffer region in meters>'])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(default_table_headers)
            for stressor_property, default_message in stressors.iteritems():
                stressor_csv_writer.writerow([stressor_property, default_message] + default_table_row)
