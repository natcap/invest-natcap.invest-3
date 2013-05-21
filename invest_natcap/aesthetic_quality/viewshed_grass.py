import sys, os, numpy, argparse

#sys.path.append("/usr/lib/grass64/etc")
sys.path.append("/usr/lib/grass64/etc/python")
#sys.path.append("/usr/lib/grass64/lib")
#sys.path.append("/usr/lib/grass64/bin")
#sys.path.append("/usr/lib/grass64/extralib")
#sys.path.append("/usr/lib/grass64/msys/bin")

#os.putenv("GISBASE","/usr/lib/grass64")

import grass.script
import grass.script.setup

class grasswrapper():
        def __init__(self, dbBase="", location="/home/mlacayo/workspace/newLocation", mapset="PERMANENT"):
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
                grass.script.setup.init(self.gisbase, self.gisdb, self.loc, self.mapset)

def execute(args):

def viewshed(input, output, coordinate, obs_elev=1.75, tgt_elev=0.0, memory=4098, overwrite=True, quiet=True):
    g.run_command('r.in.gdal',
                  'o', #overide projection
                  input=args["in_raster"],
                  output='dem')

    g.run_command('v.in.ogr',
                  'o', #overide projection
                  input=args["in_observer_features"],
                  output='features')
                  
                  

    print "\n\n\tList Rasters"
    rast_list = grass.script.parse_command('g.list',
                                            type='rast')

    print rast_list

    print "\n\n\tRegion Settings"
    grass.script.run_command('g.region',
                  'pec')

    #change the rsolution
    print "\n\n\tSet Region Resolution"
    grass.script.run_command('g.region',
                  res='15')
    print "\n\n\tRegion Settings"
    grass.script.run_command('g.region',
                  'pec')


    ##g.run_command('g.copy',
    ##              rast="pop_vs,pop_vs2")
                    
    ##g.run_command('r.resample',
    ##              input="/home/mlacayo/Desktop/test_out/pop_vs.tif",
    ####              "211084.959353,372584.959353,5356029.35524,5495529.35524",
    ####              1000,
    ##              output="/home/mlacayo/Desktop/resample.tif")

    ##g.run_command('r.viewshed',
    ##              input='/home/mlacayo/Desktop/aq_sample/Input/claybark_dem.tif',
    ##              output='/home/mlacayo/Desktop/viewshed.tif',
    ##              coordinate=[295844, 5459791],
    ##              obs_elev=1.75,
    ##              tgt_elev=0.0,
    ##              'c', #earth curvature
    ##              memory=4098,
    ##              overwrite=True,
    ##              quiet=True)

    ##g.run_command('r.out.tiff'

if __name__ == "__main__":
         
    execute()
