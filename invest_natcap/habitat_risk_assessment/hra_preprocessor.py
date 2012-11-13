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
            habitat_csv_writer.writerow(['', 'Rating', 'Data Quality'])
            for habitat_property in ['Mortality:', 'Recruitment:', 'Connectivity:', 'Recovery Time:']:
                habitat_csv_writer.writerow([habitat_property] + [default_fill_in_message]*2)

            habitat_csv_writer.writerow([])
            habitat_csv_writer.writerow(['HABITAT STRESSOR OVERLAP PROPERTIES'])
            for stressor_name in name_lookup['stressor']:
                habitat_csv_writer.writerow([])
                habitat_csv_writer.writerow([habitat_name + '/' + stressor_name + ' OVERLAP'])
                habitat_csv_writer.writerow(['', 'Rating', 'Data Quality'])
                for overlap_property in [
                    'Temporal Overlap:', 'Area Change:', 'Structure Change:',
                    'Disurbance Rating:']:
                    habitat_csv_writer.writerow([overlap_property] + [default_fill_in_message]*2)

    #Make stressor specific tables
    for stressor_name in name_lookup['stressor']:
        csv_filename = os.path.join(
            output_dir, stressor_name + '_stressor_ratings.csv')
        with open(csv_filename, 'wb') as stressor_csv_file:
            stressor_csv_writer = csv.writer(stressor_csv_file)
            stressor_csv_writer.writerow(['STRESSOR NAME', stressor_name])
            stressor_csv_writer.writerow(['Stressor Data Quality:', default_fill_in_message])
            stressor_csv_writer.writerow(['Stressor Buffer (m):', '<enter a buffer region in meters>'])
            stressor_csv_writer.writerow([])
            stressor_csv_writer.writerow(['', 'Rating', 'Data Quality'])
            for stressor_property in ['Intensity:', 'Management:',]:
                stressor_csv_writer.writerow([stressor_property] + [default_fill_in_message]*2)
