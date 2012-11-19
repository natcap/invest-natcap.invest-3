
import os
import logging

from osgeo import ogr

from invest_natcap.nutrient import nutrient_biophysical
from invest_natcap.nutrient import nutrient_core
from invest_natcap.invest_core import fileio as fileio

LOGGER = logging.getLogger('nutrient_valuation')

def execute(args):
    print args

    valuation_args = {}
    watersheds = ogr.Open(args['watersheds_uri'], 1)

    ogr_driver = ogr.GetDriverByName('ESRI Shapefile')
    shapefile_folder = os.path.join(args['workspace_dir'], 'watersheds_value')
    nutrient_biophysical.make_folder(shapefile_folder)

    copy_uri = os.path.join(args['workspace_dir'], 'watersheds_value')
    watersheds_copy = ogr_driver.CopyDataSource(watersheds, copy_uri)

    # Check to see if the watersheds shapefile has the nut_value field.  If not,
    # add it.
    value_index = watersheds_copy.GetLayer(0).GetFeature(0).GetFieldIndex('nut_value')
    if value_index == -1:
        # Value_index will be -1 if the field does not yet exist.  If it already
        # exists, we should just use that one field.
        LOGGER.debug('Making a new nut_value field in the new watersheds .shp')
        new_field = ogr.FieldDefn('nut_value', ogr.OFTReal)
        watersheds_copy.GetLayer(0).CreateField(new_field)
        watersheds_copy.GetLayer(0).SyncToDisk()

    valuation_args['watersheds'] = watersheds_copy

    LOGGER.debug('Opening the valuation table')
    valuation_table = fileio.TableHandler(args['valuation_table_uri'])
    valuation_args['valuation_table'] = valuation_table

    nutrient_core.valuation(valuation_args)
