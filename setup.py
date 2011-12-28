from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

cython_source_files = ['invest_cython_core/invest_cython_core.pyx',
                       'invest_cython_core/simplequeue.c']

#setup(name='invest_cython_core', 
#      )

setup(name='invest_natcap',
      version='tip',
      modules = ['invest_natcap.postprocessing'],
      packages = ['invest_natcap',
                'invest_natcap.carbon',
                'invest_natcap.dbfpy',
                'invest_natcap.invest_core',
                'invest_natcap.iui',
                'invest_natcap.sediment',
                'invest_natcap.timber',
                'invest_natcap.validator_core',
                'invest_natcap.wave_energy'],
      cmdclass={'build_ext': build_ext},
      ext_modules=[Extension(name="invest_cython_core",
                             sources=cython_source_files)]
      )
