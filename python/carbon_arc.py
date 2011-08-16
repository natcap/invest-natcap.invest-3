#carbon_arc.py
#
#Extract the arguments of the Geoprocessing Object to a Python Dictionary
import sys, arcgisscripting
sys.path.append('Z:\projects\invest3x\python\invest_core\\')
#sys.path.append('C:\Python26\ArcGIS10.0\lib\site-packages\osgeo\\')

gp = arcgisscripting.create()
gp.addmessage(sys.path)
import carbon_uri

def carbon_arc(gp):
    lulc_uri = gp.GetParameterAsText(0)
    pool_uri = gp.GetParameterAsText(1)
    output_uri = gp.GetParameterAsText(2)

    lulc_dictionary = {'uri'  : lulc_uri,
                         'type' :'gdal',
                         'input': True}

    pool_dictionary = {'uri'  : pool_uri}

    output_dictionary = {'uri'  : output_uri,
                         'type' : 'gdal',
                         'input': False}


    arguments = {'lulc': lulc_dictionary,
                 'carbon_pools' : pool_dictionary,
                 'output' : output_dictionary}
    gp.addmessage('Processing')

    carbon_uri.carbon_uri(arguments)

carbon_arc(gp)
