"""distutils setup.py for InVEST 3.0 framework and models"""

from distutils.core import setup
from distutils.extension import Extension
import platform
import os
import datetime

import numpy as np
from Cython.Distutils import build_ext
VERSION = '2.3.0a1'

CYTHON_SOURCE_FILES = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

console = []
data_files = []
py2exe_args = {}


#This makes a destination directory with the name invest_version_datetime.
#Will make it easy to see the difference between different builds of the 
#same version.
DIST_DIR = 'invest_'+VERSION.replace('.','_') + '_' + \
    datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")

#If it's windows assume we're going the py2exe route.
if platform.system() == 'Windows':
    import py2exe
    py2exe_args['options'] = \
        {'py2exe':{
            #Sometimes if I don't include 'sip' it doesn't build, found
            #this on a stackoverflow thread that I've now lost
            'includes': ['sip',
                         'invest_natcap'],
            'dist_dir': DIST_DIR,
            'packages': ['invest_natcap',
                        'invest_natcap.carbon',
                        'invest_natcap.dbfpy',
                        'invest_natcap.hydropower',
                        'invest_natcap.invest_core',
                        'invest_natcap.iui',
                        'invest_natcap.iui.dbfpy',
                        'invest_natcap.sediment',
                        'invest_natcap.timber',
                        'invest_natcap.validator_core',
                        'invest_natcap.wave_energy',
                        'invest_natcap.pollination',
                        'invest_natcap.finfish_aquaculture',
                        'invest_natcap.marine_water_quality'],
            #http://www.py2exe.org/index.cgi/ListOfOptions
            'skip_archive': True
            }
         }

    #These are the exes that will get built
    py2exe_args['console'] = \
        ['invest_carbon_biophysical.py',
         'invest_carbon_valuation.py',
         'invest_wave_energy_biophysical.py',
         'invest_wave_energy_valuation.py',
         'invest_timber.py',
         'invest_water_yield.py',
         'invest_hydropower_valuation.py',
         'invest_water_scarcity.py',
         'invest_marine_water_quality_biophysical.py']

    #Need to manually bring along the json configuration files to
    #the current build directory
    py2exe_args['data_files'] = \
        [('.',['invest_natcap/iui/carbon_biophysical.json',
               'invest_natcap/iui/carbon_valuation.json',
               'invest_natcap/iui/timber.json',
               'invest_natcap/iui/wave_energy_biophysical.json',
               'invest_natcap/iui/wave_energy_valuation.json',
               'invest_natcap/iui/water_yield.json',
               'invest_natcap/iui/water_scarcity.json',
               'invest_natcap/iui/hydropower_valuation.json',
               'invest_natcap/iui/pollination_biophysical.json',
               'invest_natcap/iui/marine_water_quality_biophysical.json']),
        ('invest_natcap/iui',
              ['invest_natcap/iui/dialog-close.png',
               'invest_natcap/iui/dialog-ok.png',
               'invest_natcap/iui/document-open.png',
               'invest_natcap/iui/edit-undo.png',
               'invest_natcap/iui/info.png',
               'invest_natcap/iui/natcap_logo.png',
               'invest_natcap/iui/validate-pass.png',
               'invest_natcap/iui/validate-fail.png'])]
#The standard distutils setup command
setup(name='invest_natcap',
      version=VERSION,
      packages=['invest_natcap',
                'invest_natcap.carbon',
                'invest_natcap.dbfpy',
                'invest_natcap.hydropower',
                'invest_natcap.invest_core',
                'invest_natcap.iui',
                'invest_natcap.iui.dbfpy',
                'invest_natcap.sediment',
                'invest_natcap.timber',
                'invest_natcap.validator_core',
                'invest_natcap.wave_energy',
                'invest_natcap.pollination',
                'invest_natcap.finfish_aquaculture',
                'invest_natcap.marine_water_quality'],
      cmdclass={'build_ext': build_ext},
      include_dirs = [np.get_include()],
      ext_modules=[Extension(name="invest_cython_core",
                             sources = CYTHON_SOURCE_FILES)],
      **py2exe_args)
