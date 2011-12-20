'''Wrapper for gmath.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_gmath.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gmath.h -o gmath.py

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

_libs["grass_gmath.6.4.2RC2"] = load_library("grass_gmath.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 35
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'fft'):
    fft = _libs['grass_gmath.6.4.2RC2'].fft
    fft.restype = c_int
    fft.argtypes = [c_int, POINTER(c_double) * 2, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 36
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'fft2'):
    fft2 = _libs['grass_gmath.6.4.2RC2'].fft2
    fft2.restype = c_int
    fft2.argtypes = [c_int, POINTER(c_double * 2), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 39
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_math_rand_gauss'):
    G_math_rand_gauss = _libs['grass_gmath.6.4.2RC2'].G_math_rand_gauss
    G_math_rand_gauss.restype = c_double
    G_math_rand_gauss.argtypes = [c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 42
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_math_max_pow2'):
    G_math_max_pow2 = _libs['grass_gmath.6.4.2RC2'].G_math_max_pow2
    G_math_max_pow2.restype = c_long
    G_math_max_pow2.argtypes = [c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 43
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_math_min_pow2'):
    G_math_min_pow2 = _libs['grass_gmath.6.4.2RC2'].G_math_min_pow2
    G_math_min_pow2.restype = c_long
    G_math_min_pow2.argtypes = [c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 46
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_math_rand'):
    G_math_rand = _libs['grass_gmath.6.4.2RC2'].G_math_rand
    G_math_rand.restype = c_float
    G_math_rand.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 49
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'del2g'):
    del2g = _libs['grass_gmath.6.4.2RC2'].del2g
    del2g.restype = c_int
    del2g.argtypes = [POINTER(c_double) * 2, c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 52
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_math_findzc'):
    G_math_findzc = _libs['grass_gmath.6.4.2RC2'].G_math_findzc
    G_math_findzc.restype = c_int
    G_math_findzc.argtypes = [POINTER(c_double), c_int, POINTER(c_double), c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 55
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'getg'):
    getg = _libs['grass_gmath.6.4.2RC2'].getg
    getg.restype = c_int
    getg.argtypes = [c_double, POINTER(c_double) * 2, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 58
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'eigen'):
    eigen = _libs['grass_gmath.6.4.2RC2'].eigen
    eigen.restype = c_int
    eigen.argtypes = [POINTER(POINTER(c_double)), POINTER(POINTER(c_double)), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 59
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'egvorder2'):
    egvorder2 = _libs['grass_gmath.6.4.2RC2'].egvorder2
    egvorder2.restype = c_int
    egvorder2.argtypes = [POINTER(c_double), POINTER(POINTER(c_double)), c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 60
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'transpose2'):
    transpose2 = _libs['grass_gmath.6.4.2RC2'].transpose2
    transpose2.restype = c_int
    transpose2.argtypes = [POINTER(POINTER(c_double)), c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 64
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'jacobi'):
    jacobi = _libs['grass_gmath.6.4.2RC2'].jacobi
    jacobi.restype = c_int
    jacobi.argtypes = [(c_double * 9) * 9, c_long, c_double * 9, (c_double * 9) * 9]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 65
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'egvorder'):
    egvorder = _libs['grass_gmath.6.4.2RC2'].egvorder
    egvorder.restype = c_int
    egvorder.argtypes = [c_double * 9, (c_double * 9) * 9, c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 66
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'transpose'):
    transpose = _libs['grass_gmath.6.4.2RC2'].transpose
    transpose.restype = c_int
    transpose.argtypes = [(c_double * 9) * 9, c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 69
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'mult'):
    mult = _libs['grass_gmath.6.4.2RC2'].mult
    mult.restype = c_int
    mult.argtypes = [POINTER(c_double) * 2, c_int, POINTER(c_double) * 2, c_int, POINTER(c_double) * 2, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 73
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_vector'):
    G_alloc_vector = _libs['grass_gmath.6.4.2RC2'].G_alloc_vector
    G_alloc_vector.restype = POINTER(c_double)
    G_alloc_vector.argtypes = [c_size_t]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 74
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_matrix'):
    G_alloc_matrix = _libs['grass_gmath.6.4.2RC2'].G_alloc_matrix
    G_alloc_matrix.restype = POINTER(POINTER(c_double))
    G_alloc_matrix.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 75
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_fvector'):
    G_alloc_fvector = _libs['grass_gmath.6.4.2RC2'].G_alloc_fvector
    G_alloc_fvector.restype = POINTER(c_float)
    G_alloc_fvector.argtypes = [c_size_t]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 76
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_fmatrix'):
    G_alloc_fmatrix = _libs['grass_gmath.6.4.2RC2'].G_alloc_fmatrix
    G_alloc_fmatrix.restype = POINTER(POINTER(c_float))
    G_alloc_fmatrix.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 77
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_vector'):
    G_free_vector = _libs['grass_gmath.6.4.2RC2'].G_free_vector
    G_free_vector.restype = None
    G_free_vector.argtypes = [POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 78
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_matrix'):
    G_free_matrix = _libs['grass_gmath.6.4.2RC2'].G_free_matrix
    G_free_matrix.restype = None
    G_free_matrix.argtypes = [POINTER(POINTER(c_double))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 79
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_fvector'):
    G_free_fvector = _libs['grass_gmath.6.4.2RC2'].G_free_fvector
    G_free_fvector.restype = None
    G_free_fvector.argtypes = [POINTER(c_float)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 80
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_fmatrix'):
    G_free_fmatrix = _libs['grass_gmath.6.4.2RC2'].G_free_fmatrix
    G_free_fmatrix.restype = None
    G_free_fmatrix.argtypes = [POINTER(POINTER(c_float))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 83
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_tqli'):
    G_tqli = _libs['grass_gmath.6.4.2RC2'].G_tqli
    G_tqli.restype = c_int
    G_tqli.argtypes = [POINTER(c_double), POINTER(c_double), c_int, POINTER(POINTER(c_double))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 84
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_tred2'):
    G_tred2 = _libs['grass_gmath.6.4.2RC2'].G_tred2
    G_tred2.restype = None
    G_tred2.argtypes = [POINTER(POINTER(c_double)), c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 87
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_ivector'):
    G_alloc_ivector = _libs['grass_gmath.6.4.2RC2'].G_alloc_ivector
    G_alloc_ivector.restype = POINTER(c_int)
    G_alloc_ivector.argtypes = [c_size_t]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 88
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_alloc_imatrix'):
    G_alloc_imatrix = _libs['grass_gmath.6.4.2RC2'].G_alloc_imatrix
    G_alloc_imatrix.restype = POINTER(POINTER(c_int))
    G_alloc_imatrix.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 89
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_ivector'):
    G_free_ivector = _libs['grass_gmath.6.4.2RC2'].G_free_ivector
    G_free_ivector.restype = None
    G_free_ivector.argtypes = [POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 90
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_free_imatrix'):
    G_free_imatrix = _libs['grass_gmath.6.4.2RC2'].G_free_imatrix
    G_free_imatrix.restype = None
    G_free_imatrix.argtypes = [POINTER(POINTER(c_int))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 93
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_ludcmp'):
    G_ludcmp = _libs['grass_gmath.6.4.2RC2'].G_ludcmp
    G_ludcmp.restype = c_int
    G_ludcmp.argtypes = [POINTER(POINTER(c_double)), c_int, POINTER(c_int), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 94
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_lubksb'):
    G_lubksb = _libs['grass_gmath.6.4.2RC2'].G_lubksb
    G_lubksb.restype = None
    G_lubksb.argtypes = [POINTER(POINTER(c_double)), c_int, POINTER(c_int), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 97
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_svdcmp'):
    G_svdcmp = _libs['grass_gmath.6.4.2RC2'].G_svdcmp
    G_svdcmp.restype = c_int
    G_svdcmp.argtypes = [POINTER(POINTER(c_double)), c_int, c_int, POINTER(c_double), POINTER(POINTER(c_double))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 98
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_svbksb'):
    G_svbksb = _libs['grass_gmath.6.4.2RC2'].G_svbksb
    G_svbksb.restype = c_int
    G_svbksb.argtypes = [POINTER(POINTER(c_double)), POINTER(c_double), POINTER(POINTER(c_double)), c_int, c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 99
if hasattr(_libs['grass_gmath.6.4.2RC2'], 'G_svelim'):
    G_svelim = _libs['grass_gmath.6.4.2RC2'].G_svelim
    G_svelim.restype = c_int
    G_svelim.argtypes = [POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gmath.h: 63
try:
    MX = 9
except:
    pass

# No inserted files

