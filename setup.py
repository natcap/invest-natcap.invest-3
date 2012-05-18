from distutils.core import setup
from distutils.extension import Extension
import platform
import os

import numpy as np

cython_source_files = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

console = []
data_files = []
py2exe_args = {}
if platform.system() == 'Windows':
    import py2exe
    py2exe_args['options'] = {"py2exe":{"includes":["sip"]}}
    py2exe_args['console'] = \
        ['invest_carbon_biophysical.py']
    py2exe_args['data_files'] = \
        [('.',['invest_natcap/iui/carbon_biophysical.json'])]

    for root, subFolders, files in os.walk('invest_natcap'):
        local_files = (root,[os.path.join(root,x) for x in files if not x.endswith('pyc')])
        py2exe_args['data_files'].append(local_files)

setup(name='invest_natcap',
      version='2.3.0',
      packages=['invest_natcap',
                'invest_natcap.invest_core',
                'invest_natcap.carbon',
                'invest_natcap.dbfpy',
                'invest_natcap.iui',
                'invest_natcap.iui.dbfpy'],
      include_dirs = [np.get_include()],
      **py2exe_args)
