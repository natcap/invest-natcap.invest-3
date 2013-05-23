"""
GRASS Python script examples.
"""
import sys
import os

import random, string

def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))

#add the path to GRASS
sys.path.append("/usr/lib/grass64/etc/python")

import grass.script
import grass.script.setup

class grasswrapper():
    def __init__(self,
                 dbBase="",
                 location="",
                 mapset=""):
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


if __name__ == "__main__":
    dataset_uri = "/home/mlacayo/Desktop/aq_sample/Input/claybark_dem.tif"
    name = randomword(6)
    grass.script.run_command('g.proj',
                             'c',
                             georef = dataset_uri,
                             location = name)
    grass.script.run_command('r.in.gdal',
                             input = dataset_uri,
                             output = 'dem')
    grass.script.run_command('r.out.tiff',
                             input = 'dem',
                             output = os.path.join(os.path.split(dataset_uri)[0],
                                                   name+".tif"))

