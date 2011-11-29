from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

queueModule = Extension('queue', sources=['queue.pyx', 'cqueue.pxd',
                                          'simplequeue.c'])
investCythonCore = Extension("invest_cython_core", ["invest_cython_core.pyx"])

setup(
    cmdclass={'build_ext': build_ext},
    ext_modules = [queueModule, investCythonCore]
)
