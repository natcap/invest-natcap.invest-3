"""Entry point for the Habitat Risk Assessment module"""

import os

def execute(args):
    """Read two directories for habitat and stressor layers and make
        appropriate output csv files

        args['workspace_dir'] - The directory to dump the output CSV files to
        args['habitat_dir'] - A directory of ArcGIS shapefiles that are habitats
        args['stressor_dir'] - A directory of ArcGIS shapefiles that are stressors

        returns nothing"""

    #Make the workspace directory if it doesn't exist
    if not os.path.exists(args['workspace_dir']):
        os.makedirs(args['workspace_dir'])

        
