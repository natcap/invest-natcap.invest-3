#carbon_arc.py
#
#Extract the arguments of the Geoprocessing Object to a Python Dictionary
import os, sys
import arcgisscripting
#os.chdir('Z:\projects\invest3x\python')
sys.path.append('Z:\\projects\\invest3x\\python')
#os.chdir('Z:\\')
os.chdir('Z:\\projects\\invest3x\\python')
import invest_core

os.chdir('C:\\')



gp = arcgisscripting.create()
gp.addmessage(sys.path)

def carbon_arc(gp):
    lulc_uri = gp.GetParameterAsText(0)
    pool_uri = gp.GetParameterAsText(1)
    output_uri = gp.GetParameterAsText(2)

    lulc_dictionary = {'uri'  : lulc_uri,
                       'type' :'gdal',
                       'input': True}

    pool_dictionary = {'uri'  : pool_uri,
                       'type': 'dbf',
                       'input': True}

    output_dictionary = {'uri'  : output_uri,
                         'type' : 'gdal',
                         'input': False}

    arguments = {'lulc': lulc_dictionary,
                 'carbon_pools' : pool_dictionary,
                 'output' : output_dictionary}
    gp.addmessage('Processing')

    invest_core.invest.execute('carbon', arguments)

carbon_arc(gp)