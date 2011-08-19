import os
os.environ['PATH'] = 'C:\\OSGeo4W\\bin;' + os.environ['PATH']

import arcgisscripting
gp = arcgisscripting.create()
import subprocess

gp.AddMessage('Starting subprocess')
#p = subprocess.Popen(['C:\OSGeo4W\gdal_python_exec.bat', 'X:\\local\\workspace\\invest-natcap.invest-3\python\import_tests.py'])
os.system('C:\OSGeo4W\gdal_python_exec.bat X:\\local\\workspace\\invest-natcap.invest-3\python\import_tests.py')
