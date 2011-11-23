'''Wrapper for transform.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_trans.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/transform.h -o trans.py

Do not modify this file.
'''

__docformat__ =  'restructuredtext'


_libs = {}
_libdirs = []

from ctypes_preamble import *
from ctypes_preamble import _variadic_function
from ctypes_loader import *

add_library_search_dirs([])

# Begin libraries

_libs["grass_trans.6.4.2RC2"] = load_library("grass_trans.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 11
if hasattr(_libs['grass_trans.6.4.2RC2'], 'inverse'):
    inverse = _libs['grass_trans.6.4.2RC2'].inverse
    inverse.restype = c_int
    inverse.argtypes = [(c_double * 3) * 3]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 12
if hasattr(_libs['grass_trans.6.4.2RC2'], 'isnull'):
    isnull = _libs['grass_trans.6.4.2RC2'].isnull
    isnull.restype = c_int
    isnull.argtypes = [(c_double * 3) * 3]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 15
if hasattr(_libs['grass_trans.6.4.2RC2'], 'm_mult'):
    m_mult = _libs['grass_trans.6.4.2RC2'].m_mult
    m_mult.restype = c_int
    m_mult.argtypes = [(c_double * 3) * 3, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 18
if hasattr(_libs['grass_trans.6.4.2RC2'], 'compute_transformation_coef'):
    compute_transformation_coef = _libs['grass_trans.6.4.2RC2'].compute_transformation_coef
    compute_transformation_coef.restype = c_int
    compute_transformation_coef.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 20
if hasattr(_libs['grass_trans.6.4.2RC2'], 'transform_a_into_b'):
    transform_a_into_b = _libs['grass_trans.6.4.2RC2'].transform_a_into_b
    transform_a_into_b.restype = c_int
    transform_a_into_b.argtypes = [c_double, c_double, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 21
if hasattr(_libs['grass_trans.6.4.2RC2'], 'transform_b_into_a'):
    transform_b_into_a = _libs['grass_trans.6.4.2RC2'].transform_b_into_a
    transform_b_into_a.restype = c_int
    transform_b_into_a.argtypes = [c_double, c_double, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 22
if hasattr(_libs['grass_trans.6.4.2RC2'], 'residuals_a_predicts_b'):
    residuals_a_predicts_b = _libs['grass_trans.6.4.2RC2'].residuals_a_predicts_b
    residuals_a_predicts_b.restype = c_int
    residuals_a_predicts_b.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int), c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 24
if hasattr(_libs['grass_trans.6.4.2RC2'], 'residuals_b_predicts_a'):
    residuals_b_predicts_a = _libs['grass_trans.6.4.2RC2'].residuals_b_predicts_a
    residuals_b_predicts_a.restype = c_int
    residuals_b_predicts_a.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int), c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\transform.h: 8
try:
    DIM_matrix = 3
except:
    pass

# No inserted files

