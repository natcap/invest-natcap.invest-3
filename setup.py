"""distutils setup.py for InVEST 3.0 framework and models"""

from distutils.core import setup
from distutils.extension import Extension
from distutils.core import Command
import platform
import os
import sys
import datetime
import time
import glob
import subprocess
import matplotlib
import zipfile
import re


import numpy as np
from Cython.Distutils import build_ext
from Cython.Build import cythonize

from invest_natcap import build_utils
VERSION = build_utils.invest_version(uri='invest_version.py',
    force_new=True)
# sanitize the version tag for distutils.
VERSION = VERSION.replace(':', '_').replace(' ', '_')
from invest_natcap import invest_version
ARCHITECTURE = invest_version.py_arch
CYTHON_SOURCE_FILES = ['invest_natcap/cython_modules/invest_cython_core.pyx',
                       'invest_natcap/cython_modules/simplequeue.c']

#This makes a destination directory with the name invest_version_datetime.
#Will make it easy to see the difference between different builds of the 
#same version.
DIST_DIR = 'invest_%s_%s' % (VERSION.replace('.','_').replace(':', '_'),
    ARCHITECTURE)

class ZipCommand(Command):
    description = 'Custom command to recurseively zip a folder'
    user_options = [
        ('zip-dir=', None, 'Folder to be zipped up'),
        ('zip-file=', None, 'Output zip file path')]

    def initialize_options(self):
        self.zip_dir = DIST_DIR
        self.zip_file = str(self.zip_dir + '.zip')

    def finalize_options(self):
        """This function, though empty, is requred to exist in subclasses of
        Command."""
        pass

    def run(self):
        zip = zipfile.ZipFile(self.zip_file, 'w',
            compression=zipfile.ZIP_DEFLATED)
        dir = self.zip_dir
        root_len = len(os.path.abspath(dir))
        print dir
        for root, dirs, files in os.walk(dir):
            for f in files:
                fullpath = os.path.join(root, f)
                print(fullpath)
                zip.write(fullpath, fullpath, zipfile.ZIP_DEFLATED)
        zip.close()

console = []
py2exe_args = {}
data_files = []
lib_path = ''
CMD_CLASSES = {
    'build_ext': build_ext,
    'zip': ZipCommand,
}

packages = ['invest_natcap',
            'invest_natcap.carbon',
            'invest_natcap.dbfpy',
            'invest_natcap.hydropower',
            'invest_natcap.invest_core',
            'invest_natcap.iui',
            'invest_natcap.iui.dbfpy',
            'invest_natcap.recreation',
            'invest_natcap.sediment',
            'invest_natcap.malaria',
            'invest_natcap.testing',
            'invest_natcap.optimization',
            'invest_natcap.timber',
            'invest_natcap.nutrient',
            'invest_natcap.wave_energy',
            'invest_natcap.pollination',
            'invest_natcap.finfish_aquaculture',
            'invest_natcap.marine_water_quality',
            'invest_natcap.monthly_water_yield',
            'invest_natcap.biodiversity',
            'invest_natcap.coastal_vulnerability',
            'invest_natcap.overlap_analysis',
            'invest_natcap.wind_energy',
            'invest_natcap.aesthetic_quality',
            'invest_natcap.habitat_risk_assessment',
            'invest_natcap.report_generation',
            'invest_natcap.routing',
            'invest_natcap.flood_mitigation',
            'invest_natcap.fisheries',
            'invest_natcap.ntfp',
            ]

def get_iui_resource_data_files(lib_path):
    """Returns a list of tuples for all the files to be added to iui_resources.
     Use the input virtualenv site-packages path to add all files in the
     IUI resources directory to our setup.py data files.
    """
    data_list = []
    directory = 'invest_natcap/iui/iui_resources'
    for root_dir, sub_folders, file_list in os.walk(directory):
        data_list.append((os.path.join(lib_path, root_dir), map(lambda x:
            os.path.join(root_dir, x), file_list)))
    return data_list

#If it's windows assume we're going the py2exe route.
if platform.system() == 'Windows':
    py2exe_args['options'] = \
        {'py2exe':{
            'includes': ['sip',
                         'invest_natcap',
                         'scipy.io.matlab.streams',
                         'ctypes',
                         'shapely.geos',
                         'matplotlib.backends.backend_qt4agg',
                         'invest_natcap.invest_version'],
            'dist_dir': DIST_DIR,
            'packages': packages,
            'skip_archive': True,
            'dll_excludes': ['POWRPROF.dll', 'Secur32.dll', 'SHFOLDER.dll',
                'msvcp90.dll']
            }
         }

    #These are the exes that will get built
    py2exe_args['console'] = \
        ['invest_carbon.py',
         'invest_wave_energy.py',
         'invest_hra.py',
         'invest_hra_preprocessor.py',
         'invest_timber.py',
         'invest_hydropower_water_yield.py',
         'invest_marine_water_quality_biophysical.py',
         'invest_recreation_client_init.py',
         'invest_recreation_client_scenario.py',
         'invest_finfish_aquaculture.py',
         'invest_biodiversity_biophysical.py',
         'invest_overlap_analysis.py',
         'invest_overlap_analysis_mz.py',
         'invest_coastal_vulnerability.py',
         'invest_sediment.py',
         'invest_nutrient.py',
         'invest_wind_energy.py',
         'invest_fisheries.py',
         'invest_ntfp.py',
         'invest_test_all.py']

    py2exe_args['windows'] = [
        'invest_pollination.py',
    ]
    from py2exe.build_exe import py2exe as py2exeCommand

    class CustomPy2exe(py2exeCommand):
        """This is a custom Py2exe command that allows us to define data files
        that are only used for the built executeables.  This is especially
        important now that we include 30MB or so of GDAL DLLs that we don't need
        for any other distribution scheme."""

        def create_binaries(self, py_files, extensions, dlls):
            if self.distribution.data_files == None:
                self.distribution.data_files = []

            # This block defines the data files that only apply to the Py2exe distribution
            # of InVEST.  These are files that are really only needed for the standalone
            # executeables and otherwise muck up our other distributions.
            self.distribution.data_files += [
                ('invest_natcap/iui', glob.glob('invest_natcap/iui/*.json')),
                ('.', ['geos_c.dll', 'libgcc_s_dw2-1.dll', 'libstdc++-6.dll']),
                ('invest_natcap/recreation',
                    ['invest_natcap/recreation/recreation_client_config.json']),
                ('invest_natcap/iui', glob.glob('invest_natcap/iui/*.png')),
                ('installer', glob.glob('installer/*')),
            ] + matplotlib.get_py2exe_datafiles()

            # These are the GDAL DLLs.  They are absolutely required for running the
            # Windows executeables on XP.  For whatever reason, they do not appear to be
            # required for running GDAL stuff on Windows 7.  Not sure why that is.
            # I'm only including them here for the 32-bit windows build.
            if platform.architecture()[0] == '32bit':
                self.distribution.data_files.append(('.', glob.glob('gdal_dlls/*.dll')))


            self.distribution.data_files.extend(get_iui_resource_data_files(''))

            # If we're building InVEST on 64-bit Windows, we need to also include the
            # 64-bit GEOS DLL.  See issue 2027.
            if platform.architecture()[0] == '64bit':
                self.distribution.data_files.append(
                    ('shapely', ['x64_build/geos_c.dll']))

            # After we've defined all our custom data files, we can now add on
            # the data files provided by default in setup.py.
            py2exeCommand.create_binaries(self, py_files, extensions, dlls)

    from distutils.command.bdist_wininst import bdist_wininst
    class CustomBdistWininst(bdist_wininst):
        """A custom distutils command class for placing the correct stdlib c and
        c++ dlls in the correct place for the binary distribution for Windows.
        We only need this for bdist_wininst, so that's why we have the custom
        command."""
        def run(self):
            if self.distribution.data_files == None:
                self.distribution.data_files = []

            # Put the c/c++ libraries where we need them, in lib/site-packages and lib.
            # Only necessary for binary package installer.
            self.distribution.data_files.append(('lib/site-packages',
                ['libgcc_s_dw2-1.dll', 'libstdc++-6.dll']))
            self.distribution.data_files.append(('lib',
                ['libgcc_s_dw2-1.dll', 'libstdc++-6.dll']))
            bdist_wininst.run(self)

    # Now the we've declared our custom Py2exe command, we need to let the
    # Setup() function know that we want to use it in place of the normal py2exe
    # command.
    CMD_CLASSES['py2exe'] = CustomPy2exe
    CMD_CLASSES['bdist_wininst'] = CustomBdistWininst
else:
    # this is not running on windows
    # We need to add certain IUI resources to the virtualenv site-packages
    # folder for certain things (including certain tests) to work correctly.
    python_version = 'python%s' % '.'.join([str(r) for r in
        sys.version_info[:2]])
    lib_path = os.path.join('lib', python_version, 'site-packages')
    data_files.extend(get_iui_resource_data_files(lib_path))

#The standard distutils setup command
setup(name='invest_natcap',
      version=VERSION,
      packages=packages,
      cmdclass=CMD_CLASSES,
      requires=['cython (>=0.19.1)', 'scipy (>=0.12.0)', 'nose (>=1.2.1)', 'osgeo (>=1.9.2)'],
      include_dirs = [np.get_include()],
      data_files=data_files,
      ext_modules=cythonize([Extension(name="invest_cython_core",
                             sources = CYTHON_SOURCE_FILES),
                   Extension(name="hydropower_cython_core",
                             sources = ['invest_natcap/hydropower/hydropower_cython_core.pyx']),
                   Extension(name="raster_cython_utils",
                             sources = ['invest_natcap/raster_cython_utils.pyx'],
                             language="c++"),
                   Extension(name="routing_cython_core",
                             sources = ['invest_natcap/routing/routing_cython_core.pyx'],
                             language="c++"),
                   Extension(name="sediment_cython_core",
                             sources = ['invest_natcap/sediment/sediment_cython_core.pyx'],
                             language="c++"),
                   Extension(name="flood_mitigation_cython_core",
                             sources = ['invest_natcap/flood_mitigation/flood_mitigation_cython_core.pyx'],
                             language="c++"),
                   Extension(name="monthly_water_yield_cython_core",
                             sources = ['invest_natcap/monthly_water_yield/monthly_water_yield_cython_core.pyx'],
                             language="c++")]),
      **py2exe_args)

# Since we wrote the invest version module to a file that needed to be taken
# along with the other invest_version stuff, remove those files so we aren't
# confused later on.
for file_name in glob.glob('invest_natcap/invest_version.py*'):
    print ('Removing %s' % file_name)
    os.remove(file_name)
