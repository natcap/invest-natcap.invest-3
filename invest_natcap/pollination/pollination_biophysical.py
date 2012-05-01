"""InVEST Pollination model file handler module"""

from osgeo import gdal

import pollination_core
import invest_natcap.iui.fileio

import logging
logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    """Open files necessary for the biophysical portion of the pollination
        model.

        args - a python dictionary with at least the following components:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation (required)
        args['landuse_uri'] - a uri to an input land use/land cover raster
        args['landuse_attributes_uri'] - a uri to an input CSV containing data
            on each class in the land use/land cover map (required).
        args['guilds_uri'] - a uri to an input CSV table containing data on each
            species or guild of pollinator to be modeled.
        args['ag_classes'] - a python string of space-separated integers
            representing land cover classes in the input land use/land cover
            map where each class specified is agricultural. (optional)

        returns nothing."""

    gdal.AllRegister()

    biophysical_args = {}
    workspace = args['workspace_dir']

    # Open the landcover raster
    biophysical_args['landuse'] = gdal.Open(str(args['landuse_uri']),
                                           gdal.GA_ReadOnly)

    # Open a Table Handler for the land use attributes table
    att_table_handler = fileio.TableHandler(args['landuse_attributes_uri'])

    # Retrieve a list of row dictionaries as a representation of the input
    # attributes table.
    biophysical_args['landuse_attributes'] = att_table_handler.get_table_list()



