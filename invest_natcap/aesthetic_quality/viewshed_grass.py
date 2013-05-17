import sys, os, numpy, argparse

sys.path.append("/usr/lib/grass64/etc")
sys.path.append("/usr/lib/grass64/etc/python")
sys.path.append("/usr/lib/grass64/lib")
sys.path.append("/usr/lib/grass64/bin")
#sys.path.append("/usr/lib/grass64/extralib")
#sys.path.append("/usr/lib/grass64/msys/bin")

os.putenv("GISBASE","/usr/lib/grass64")

import grass.script as g
import grass.script.setup as gsetup

class grasswrapper():
        def __init__(self, dbBase="", location="", mapset="PERMANENT"):
                '''
                Wrapper of "python.setup.init" defined in GRASS python.
                Initialize system variables to run scripts without starting GRASS explicitly.
                
                @param dbBase: path to GRASS database (default: '').
                @param location: location name (default: '').
                @param mapset: mapset within given location (default: 'PERMANENT')

                @return: Path to gisrc file.
                '''
                self.gisbase = os.environ['GISBASE']
                self.gisdb = dbBase
                self.loc = location
                self.mapset = mapset
                gsetup.init(self.gisbase, self.gisdb, self.loc, self.mapset)
                
g.run_command('r.resample',
              input="/home/mlacayo/Desktop/test_out/pop_vs.tif",
##              "211084.959353,372584.959353,5356029.35524,5495529.35524",
##              1000,
              output="/home/mlacayo/Desktop/resample.tif")
