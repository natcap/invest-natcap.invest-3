from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

simpleQueue = Extension('libsimplequeue', sources=['simplequeue.c'])
investCythonCore = Extension("invest_cython_core", ["invest_cython_core.pyx"],
                                include_dirs=["."],
                                library_dirs=['.'],
                                libraries=['simplequeue'])
queuetest = Extension("queuetest", ["queuetest.pyx"],
                                include_dirs=["."],
                                library_dirs=['.'],
                                libraries=['simplequeue'])

setup(
    cmdclass={'build_ext': build_ext},
    ext_modules=[simpleQueue, investCythonCore, queuetest]
)
