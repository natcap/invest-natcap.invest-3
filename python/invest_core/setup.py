from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

simpleQueue = Extension('libsimplequeue', sources=['simplequeue.c'])
queueModule = Extension('queue', ['queue.pyx'], include_dirs=["."],
                        library_dirs = ['.'],
                        libraries=['simplequeue'])
investCythonCore = Extension("invest_cython_core", ["invest_cython_core.pyx"])

setup(
    cmdclass={'build_ext': build_ext},
    ext_modules=[simpleQueue, queueModule, investCythonCore]
)
