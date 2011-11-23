'''Wrapper for arraystats.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_arraystats.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/arraystats.h -o arraystats.py

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

_libs["grass_arraystats.6.4.2RC2"] = load_library("grass_arraystats.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 8
class struct_GASTATS(Structure):
    pass

struct_GASTATS.__slots__ = [
    'count',
    'min',
    'max',
    'sum',
    'sumsq',
    'sumabs',
    'mean',
    'meanabs',
    'var',
    'stdev',
]
struct_GASTATS._fields_ = [
    ('count', c_double),
    ('min', c_double),
    ('max', c_double),
    ('sum', c_double),
    ('sumsq', c_double),
    ('sumabs', c_double),
    ('mean', c_double),
    ('meanabs', c_double),
    ('var', c_double),
    ('stdev', c_double),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 22
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_apply_algorithm'):
    class_apply_algorithm = _libs['grass_arraystats.6.4.2RC2'].class_apply_algorithm
    class_apply_algorithm.restype = c_double
    class_apply_algorithm.argtypes = [String, POINTER(c_double), c_int, POINTER(c_int), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 23
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_interval'):
    class_interval = _libs['grass_arraystats.6.4.2RC2'].class_interval
    class_interval.restype = c_int
    class_interval.argtypes = [POINTER(c_double), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 24
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_quant'):
    class_quant = _libs['grass_arraystats.6.4.2RC2'].class_quant
    class_quant.restype = c_int
    class_quant.argtypes = [POINTER(c_double), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 25
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_discont'):
    class_discont = _libs['grass_arraystats.6.4.2RC2'].class_discont
    class_discont.restype = c_double
    class_discont.argtypes = [POINTER(c_double), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 26
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_stdev'):
    class_stdev = _libs['grass_arraystats.6.4.2RC2'].class_stdev
    class_stdev.restype = c_double
    class_stdev.argtypes = [POINTER(c_double), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 27
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_equiprob'):
    class_equiprob = _libs['grass_arraystats.6.4.2RC2'].class_equiprob
    class_equiprob.restype = c_int
    class_equiprob.argtypes = [POINTER(c_double), c_int, POINTER(c_int), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 29
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'class_frequencies'):
    class_frequencies = _libs['grass_arraystats.6.4.2RC2'].class_frequencies
    class_frequencies.restype = c_int
    class_frequencies.argtypes = [POINTER(c_double), c_int, c_int, POINTER(c_double), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 31
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'eqdrt'):
    eqdrt = _libs['grass_arraystats.6.4.2RC2'].eqdrt
    eqdrt.restype = None
    eqdrt.argtypes = [POINTER(c_double), POINTER(c_double), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 32
if hasattr(_libs['grass_arraystats.6.4.2RC2'], 'basic_stats'):
    basic_stats = _libs['grass_arraystats.6.4.2RC2'].basic_stats
    basic_stats.restype = None
    basic_stats.argtypes = [POINTER(c_double), c_int, POINTER(struct_GASTATS)]

GASTATS = struct_GASTATS # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\arraystats.h: 8

# No inserted files

