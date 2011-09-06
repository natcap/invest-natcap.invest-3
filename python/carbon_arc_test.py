import os, sys, subprocess
import arcgisscripting

os.chdir(os.path.dirname(os.path.realpath(__file__)) + "\\invest_core\\")

process = subprocess.Popen(['..\\..\\OSGeo4W\\gdal_python_exec_test.bat',
                            'carbon_test_suite.py'])

