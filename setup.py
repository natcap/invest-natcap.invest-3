from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

cython_source_files = ['invest/invest_core/invest_cython_core.pyx']

cqueue_source_files = ['invest/invest_core/simplequeue.c',
                       'invest/invest_core/cqueue.pxd']

setup(name='invest',
      version='tip',
      cmdclass={'build_ext': build_ext},
      ext_modules=[Extension('invest.invest_core.cqueue', cqueue_source_files),
                   Extension("invest.invest_core.invest_cython_core", cython_source_files)],
      packages=['invest', 'invest.dbfpy', 'invest.invest_core', 'invest.iui',
                  'invest.carbon',
                  'invest.sediment', 'invest.timber', 'invest.validator_core',
                  'invest.wave_energy'],
      )
