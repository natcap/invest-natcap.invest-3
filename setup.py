from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import platform

import numpy as np

cython_source_files = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

options = {}
console = []
if platform.system() == 'Windows':
    import py2exe
    options = {"py2exe":{"includes":["sip"]}}
    console = ['invest_carbon.py']


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
                'invest_natcap.wave_energy'],
      cmdclass={'build_ext': build_ext},
      include_dirs = [np.get_include()],
      ext_modules=[Extension(name="invest_cython_core",
                             sources = cython_source_files)],
      console = console,
      options = options
      )
