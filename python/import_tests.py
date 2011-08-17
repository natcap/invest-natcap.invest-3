import arcgisscripting
#import osgeo #works

import subprocess
import os

#import import_test_gdal.py
gp = arcgisscripting.create()

#p = os.system('C:\Python266\python.exe Z:\projects\invest3x\python\import_test_gdal.py')
p = subprocess.Popen('C:\Python266\python.exe' + ' Z:\projects\invest3x\python\import_test_gdal.py', stdout=open('stdout.txt', 'w'), stderr=open('stderr.txt', 'w'), cwd='C:\Users\jadoug06')
p.wait()
gp.addmessage(p)

#from osgeo import gdal

#import osgeo.gdal #fails on its own
#from osgeo import gdal #fails on its own
