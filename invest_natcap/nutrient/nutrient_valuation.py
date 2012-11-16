
from osgeo import ogr

from invest_natcap.nutrient import nutrient_core
from invest_natcap.invest_core import fileio as fileio

def execute(args):
    print args

    valuation_args = {}
    watersheds = ogr.Open(args['watersheds_uri'])

    # Check to see if the watersheds shapefile has the nut_value field.  If not,
    # add it.
    new_field = ogr.FieldDefn('nut_value', ogr.OFTReal)
    watersheds.GetLayer(0).CreateField(new_field)
    valuation_args['watersheds'] = watersheds

    valuation_table = fileio.TableHandler(args['valuation_table_uri'])
    valuation_args['valuation_table'] = valuation_table

    nutrient_core.valuation(valuation_args)
