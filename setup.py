"""distutils setup.py for InVEST 3.0 framework and models"""

from distutils.core import setup
from distutils.extension import Extension
import platform
import os
import sys
import datetime
import time
import glob
import subprocess

import numpy as np
from Cython.Distutils import build_ext
from Cython.Build import cythonize


def write_version_file(filepath):
    """Write the version number to the file designated by filepath.  Returns
    nothing."""
    comments = [
        'The version noted below is used throughout InVEST as a static version',
        'that differs only from build to build.  Its value is determined by ',
        'setup.py and is based off of the time and date of the last revision.',
        '',
        'This file is programmatically generated when invest_natcap is built. ',
    ]

    # Open the version file for writing
    fp = open(filepath, 'w')

    # Write the comments as comments to the file and write the version to the
    # file as well.
    for comment in comments:
        fp.write('# %s\n' % comment)
    fp.write('version = \'%s\'\n' % get_version())

    # Close the file.
    fp.close()

def get_version():
    cmd = 'hg log -r . --config ui.report_untrusted=False --template "v{latesttag}-{latesttagdistance} [{node|short}]"'
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.read()

# __version__ is set in invest_natcap/__init__.py, in accordance with PEP
# 396:http://www.python.org/dev/peps/pep-0396/. 
write_version_file('invest_natcap/invest_version.py')


import invest_natcap
VERSION = invest_natcap.__version__
CYTHON_SOURCE_FILES = ['invest_natcap/cython_modules/invest_cython_core.pyx',
                       'invest_natcap/cython_modules/simplequeue.c']

console = []
py2exe_args = {}
data_files = []
lib_path = ''


packages = ['invest_natcap',
            'invest_natcap.carbon',
            'invest_natcap.dbfpy',
            'invest_natcap.hydropower',
            'invest_natcap.invest_core',
            'invest_natcap.iui',
            'invest_natcap.iui.dbfpy',
            'invest_natcap.recreation',
            'invest_natcap.sediment',
            'invest_natcap.timber',
            'invest_natcap.nutrient',
            'invest_natcap.validator_core',
            'invest_natcap.wave_energy',
            'invest_natcap.pollination',
            'invest_natcap.finfish_aquaculture',
            'invest_natcap.marine_water_quality',
            'invest_natcap.biodiversity',
            'invest_natcap.coastal_vulnerability',
            'invest_natcap.overlap_analysis',
            'invest_natcap.wind_energy',
            'invest_natcap.habitat_risk_assessment']

#This makes a destination directory with the name invest_version_datetime.
#Will make it easy to see the difference between different builds of the 
#same version.
DIST_DIR = 'invest_'+VERSION.replace('.','_')

#If it's windows assume we're going the py2exe route.
if platform.system() == 'Windows':
    import py2exe
    py2exe_args['options'] = \
        {'py2exe':{
            #Sometimes if I don't include 'sip' it doesn't build, found
            #this on a stackoverflow thread that I've now lost
            'includes': ['sip',
                         'invest_natcap',
                         'scipy.io.matlab.streams'],
            'dist_dir': DIST_DIR,
            'packages': packages,
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
         'invest_marine_water_quality_biophysical.py',
         'invest_pollination_biophysical.py',
         'invest_pollination_valuation.py',
         'invest_finfish_aquaculture.py',
         'invest_biodiversity_biophysical.py',
         'invest_overlap_analysis.py',
         'invest_overlap_analysis_mz.py',
         'invest_sediment_biophysical.py',
         'invest_habitat_risk_assessment.py']

    #Need to manually bring along the json configuration files to
    #the current build directory
    data_files.append(
        ('.',['invest_natcap/iui/carbon_biophysical.json',
               'invest_natcap/iui/carbon_valuation.json',
               'invest_natcap/iui/timber.json',
               'invest_natcap/iui/wave_energy_biophysical.json',
               'invest_natcap/iui/wave_energy_valuation.json',
               'invest_natcap/iui/water_yield.json',
               'invest_natcap/iui/water_scarcity.json',
               'invest_natcap/iui/hydropower_valuation.json',
               'invest_natcap/iui/pollination_biophysical.json',
               'invest_natcap/iui/pollination_valuation.json',
               'invest_natcap/iui/finfish_aquaculture.json',
               'invest_natcap/iui/marine_water_quality_biophysical.json',
               'invest_natcap/iui/biodiversity_biophysical.json',
               'invest_natcap/iui/overlap_analysis.json',
               'invest_natcap/iui/overlap_analysis_mz.json',
               'invest_natcap/iui/sediment_biophysical.json']))
    data_files.append(
        ('invest_natcap/iui', glob.glob('invest_natcap/iui/*.png')))
    data_files.append(('installer', glob.glob('installer/*')))
else:
    # this is not running on windows
    # We need to add certain IUI resources to the virtualenv site-packages
    # folder for certain things (including certain tests) to work correctly.
    python_version = 'python%s' % '.'.join([str(r) for r in
        sys.version_info[:2]])
    lib_path = os.path.join('lib', python_version, 'site-packages')

# Use the determined virtualenv site-packages path to add all files in the
# IUI resources directory to our setup.py data files.
directory = 'invest_natcap/iui/iui_resources'
for root_dir, sub_folders, file_list in os.walk(directory):
    data_files.append((os.path.join(lib_path, root_dir), map(lambda x:
        os.path.join(root_dir, x), file_list)))

#The standard distutils setup command
setup(name='invest_natcap',
      version=VERSION,
      packages=packages,
      cmdclass={'build_ext': build_ext},
      include_dirs = [np.get_include()],
      data_files=data_files,
      ext_modules=cythonize([Extension(name="invest_cython_core",
                             sources = CYTHON_SOURCE_FILES),
                   Extension(name="coastal_vulnerability_cython_core",
                             sources = ['invest_natcap/coastal_vulnerability/coastal_vulnerability_cython_core.pyx']),
                   Extension(name="hydropower_cython_core",
                             sources = ['invest_natcap/hydropower/hydropower_cython_core.pyx']),
                   Extension(name="raster_cython_utils",
                             sources = ['invest_natcap/raster_cython_utils.pyx'],
                             language="c++")]),
      **py2exe_args)
