from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import platform
import os

import numpy as np

cython_source_files = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

options = {}
console = []
data_files = []
py2exe_args = {}
if platform.system() == 'Windows':
    import py2exe
    options = {"py2exe":{"includes":["sip"]}}
    py2exe_args['console'] = \
        ['invest_carbon_biophysical.py',
         'invest_carbon_valuation.py',
         'invest_wave_energy_biophysical.py',
         'invest_wave_energy_valuation.py',
         'invest_timber.py',
         'invest_hydropower_valuation.py',
         'invest_water_scarcity.py']
    py2exe_args['data_files'] = \
        [('.',['invest_natcap/iui/carbon_biophysical.json',
               'invest_natcap/iui/carbon_valuation.json',
               'invest_natcap/iui/wave_energy_valuation.json',
               'invest_natcap/iui/wave_energy_biophysical.json',
               'invest_natcap/iui/hydropower_valuation.json',
               'invest_natcap/iui/water_scarcity.json',
               'invest_natcap/iui/water_yield.json',
               'invest_natcap/iui/timber.json'])]

    for root, subFolders, files in os.walk('invest_natcap'):
        local_files = (root,[os.path.join(root,x) for x in files if not x.endswith('pyc')])
        py2exe_args['data_files'].append(local_files)

setup(name='invest_natcap',
      version='tip',
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
                'invest_natcap.pollination'],
      cmdclass={'build_ext': build_ext},
      include_dirs = [np.get_include()],
      ext_modules=[Extension(name="invest_cython_core",
                             sources = cython_source_files)],
      **py2exe_args)
