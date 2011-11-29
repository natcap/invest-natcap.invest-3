from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    cmdclass={'build_ext': build_ext},
    ext_modules = [Extension("queue", ["queue.pyx, cqueue.pxd"],
                             libraries=["queue"]),
                 Extension("invest_cython_core", ["invest_cython_core.pyx"])]
)
