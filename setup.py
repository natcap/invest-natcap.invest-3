from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

cython_source_files = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

setup(name='invest',
      version='tip',
      packages=['invest',
                'invest.carbon',
                'invest.dbfpy',
                'invest.invest_core',
                'invest.iui',
                'invest.sediment',
                'invest.simplejson',
                'invest.timber',
                'invest.validator_core',
                'invest.wave_energy'],
      cmdclass={'build_ext': build_ext},
      ext_package='invest_cython_core',
      ext_modules=[Extension(name="invest_cython_core",
                             sources=cython_source_files)]
      )
