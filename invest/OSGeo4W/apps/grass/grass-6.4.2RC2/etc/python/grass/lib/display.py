'''Wrapper for display.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_display.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/display.h -o display.py

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

_libs["grass_display.6.4.2RC2"] = load_library("grass_display.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

CELL = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 256

DCELL = c_double # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 257

FCELL = c_float # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 258

RASTER_MAP_TYPE = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 260

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 265
class struct_Cell_head(Structure):
    pass

struct_Cell_head.__slots__ = [
    'format',
    'compressed',
    'rows',
    'rows3',
    'cols',
    'cols3',
    'depths',
    'proj',
    'zone',
    'ew_res',
    'ew_res3',
    'ns_res',
    'ns_res3',
    'tb_res',
    'north',
    'south',
    'east',
    'west',
    'top',
    'bottom',
]
struct_Cell_head._fields_ = [
    ('format', c_int),
    ('compressed', c_int),
    ('rows', c_int),
    ('rows3', c_int),
    ('cols', c_int),
    ('cols3', c_int),
    ('depths', c_int),
    ('proj', c_int),
    ('zone', c_int),
    ('ew_res', c_double),
    ('ew_res3', c_double),
    ('ns_res', c_double),
    ('ns_res3', c_double),
    ('tb_res', c_double),
    ('north', c_double),
    ('south', c_double),
    ('east', c_double),
    ('west', c_double),
    ('top', c_double),
    ('bottom', c_double),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 289
class struct__Color_Value_(Structure):
    pass

struct__Color_Value_.__slots__ = [
    'value',
    'red',
    'grn',
    'blu',
]
struct__Color_Value_._fields_ = [
    ('value', DCELL),
    ('red', c_ubyte),
    ('grn', c_ubyte),
    ('blu', c_ubyte),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 297
class struct__Color_Rule_(Structure):
    pass

struct__Color_Rule_.__slots__ = [
    'low',
    'high',
    'next',
    'prev',
]
struct__Color_Rule_._fields_ = [
    ('low', struct__Color_Value_),
    ('high', struct__Color_Value_),
    ('next', POINTER(struct__Color_Rule_)),
    ('prev', POINTER(struct__Color_Rule_)),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 309
class struct_anon_4(Structure):
    pass

struct_anon_4.__slots__ = [
    'red',
    'grn',
    'blu',
    'set',
    'nalloc',
    'active',
]
struct_anon_4._fields_ = [
    ('red', POINTER(c_ubyte)),
    ('grn', POINTER(c_ubyte)),
    ('blu', POINTER(c_ubyte)),
    ('set', POINTER(c_ubyte)),
    ('nalloc', c_int),
    ('active', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 319
class struct_anon_5(Structure):
    pass

struct_anon_5.__slots__ = [
    'vals',
    'rules',
    'nalloc',
    'active',
]
struct_anon_5._fields_ = [
    ('vals', POINTER(DCELL)),
    ('rules', POINTER(POINTER(struct__Color_Rule_))),
    ('nalloc', c_int),
    ('active', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 304
class struct__Color_Info_(Structure):
    pass

struct__Color_Info_.__slots__ = [
    'rules',
    'n_rules',
    'lookup',
    'fp_lookup',
    'min',
    'max',
]
struct__Color_Info_._fields_ = [
    ('rules', POINTER(struct__Color_Rule_)),
    ('n_rules', c_int),
    ('lookup', struct_anon_4),
    ('fp_lookup', struct_anon_5),
    ('min', DCELL),
    ('max', DCELL),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 331
class struct_Colors(Structure):
    pass

struct_Colors.__slots__ = [
    'version',
    'shift',
    'invert',
    'is_float',
    'null_set',
    'null_red',
    'null_grn',
    'null_blu',
    'undef_set',
    'undef_red',
    'undef_grn',
    'undef_blu',
    'fixed',
    'modular',
    'cmin',
    'cmax',
]
struct_Colors._fields_ = [
    ('version', c_int),
    ('shift', DCELL),
    ('invert', c_int),
    ('is_float', c_int),
    ('null_set', c_int),
    ('null_red', c_ubyte),
    ('null_grn', c_ubyte),
    ('null_blu', c_ubyte),
    ('undef_set', c_int),
    ('undef_red', c_ubyte),
    ('undef_grn', c_ubyte),
    ('undef_blu', c_ubyte),
    ('fixed', struct__Color_Info_),
    ('modular', struct__Color_Info_),
    ('cmin', DCELL),
    ('cmax', DCELL),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 355
class struct_anon_6(Structure):
    pass

struct_anon_6.__slots__ = [
    'r',
    'g',
    'b',
    'a',
]
struct_anon_6._fields_ = [
    ('r', c_ubyte),
    ('g', c_ubyte),
    ('b', c_ubyte),
    ('a', c_ubyte),
]

RGBA_Color = struct_anon_6 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 355

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 27
class struct_anon_8(Structure):
    pass

struct_anon_8.__slots__ = [
    'color',
    'r',
    'g',
    'b',
    'fr',
    'fg',
    'fb',
]
struct_anon_8._fields_ = [
    ('color', c_int),
    ('r', c_int),
    ('g', c_int),
    ('b', c_int),
    ('fr', c_double),
    ('fg', c_double),
    ('fb', c_double),
]

SYMBCOLOR = struct_anon_8 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 27

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 35
class struct_anon_9(Structure):
    pass

struct_anon_9.__slots__ = [
    'count',
    'alloc',
    'x',
    'y',
]
struct_anon_9._fields_ = [
    ('count', c_int),
    ('alloc', c_int),
    ('x', POINTER(c_double)),
    ('y', POINTER(c_double)),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 40
class struct_anon_10(Structure):
    pass

struct_anon_10.__slots__ = [
    'clock',
    'x',
    'y',
    'r',
    'a1',
    'a2',
]
struct_anon_10._fields_ = [
    ('clock', c_int),
    ('x', c_double),
    ('y', c_double),
    ('r', c_double),
    ('a1', c_double),
    ('a2', c_double),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 33
class union_anon_11(Union):
    pass

union_anon_11.__slots__ = [
    'line',
    'arc',
]
union_anon_11._fields_ = [
    ('line', struct_anon_9),
    ('arc', struct_anon_10),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 46
class struct_anon_12(Structure):
    pass

struct_anon_12.__slots__ = [
    'type',
    'coor',
]
struct_anon_12._fields_ = [
    ('type', c_int),
    ('coor', union_anon_11),
]

SYMBEL = struct_anon_12 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 46

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 55
class struct_anon_13(Structure):
    pass

struct_anon_13.__slots__ = [
    'count',
    'alloc',
    'elem',
    'scount',
    'salloc',
    'sx',
    'sy',
]
struct_anon_13._fields_ = [
    ('count', c_int),
    ('alloc', c_int),
    ('elem', POINTER(POINTER(SYMBEL))),
    ('scount', c_int),
    ('salloc', c_int),
    ('sx', POINTER(c_int)),
    ('sy', POINTER(c_int)),
]

SYMBCHAIN = struct_anon_13 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 55

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 65
class struct_anon_14(Structure):
    pass

struct_anon_14.__slots__ = [
    'type',
    'color',
    'fcolor',
    'count',
    'alloc',
    'chain',
]
struct_anon_14._fields_ = [
    ('type', c_int),
    ('color', SYMBCOLOR),
    ('fcolor', SYMBCOLOR),
    ('count', c_int),
    ('alloc', c_int),
    ('chain', POINTER(POINTER(SYMBCHAIN))),
]

SYMBPART = struct_anon_14 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 65

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 72
class struct_anon_15(Structure):
    pass

struct_anon_15.__slots__ = [
    'scale',
    'count',
    'alloc',
    'part',
]
struct_anon_15._fields_ = [
    ('scale', c_double),
    ('count', c_int),
    ('alloc', c_int),
    ('part', POINTER(POINTER(SYMBPART))),
]

SYMBOL = struct_anon_15 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/symbol.h: 72

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 8
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_do_conversions'):
    D_do_conversions = _libs['grass_display.6.4.2RC2'].D_do_conversions
    D_do_conversions.restype = c_int
    D_do_conversions.argtypes = [POINTER(struct_Cell_head), c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 9
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_is_lat_lon'):
    D_is_lat_lon = _libs['grass_display.6.4.2RC2'].D_is_lat_lon
    D_is_lat_lon.restype = c_int
    D_is_lat_lon.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 10
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_to_d_xconv'):
    D_get_u_to_d_xconv = _libs['grass_display.6.4.2RC2'].D_get_u_to_d_xconv
    D_get_u_to_d_xconv.restype = c_double
    D_get_u_to_d_xconv.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 11
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_to_d_yconv'):
    D_get_u_to_d_yconv = _libs['grass_display.6.4.2RC2'].D_get_u_to_d_yconv
    D_get_u_to_d_yconv.restype = c_double
    D_get_u_to_d_yconv.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 12
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_west'):
    D_get_u_west = _libs['grass_display.6.4.2RC2'].D_get_u_west
    D_get_u_west.restype = c_double
    D_get_u_west.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 13
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_east'):
    D_get_u_east = _libs['grass_display.6.4.2RC2'].D_get_u_east
    D_get_u_east.restype = c_double
    D_get_u_east.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 14
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_north'):
    D_get_u_north = _libs['grass_display.6.4.2RC2'].D_get_u_north
    D_get_u_north.restype = c_double
    D_get_u_north.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 15
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u_south'):
    D_get_u_south = _libs['grass_display.6.4.2RC2'].D_get_u_south
    D_get_u_south.restype = c_double
    D_get_u_south.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 16
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_a_west'):
    D_get_a_west = _libs['grass_display.6.4.2RC2'].D_get_a_west
    D_get_a_west.restype = c_double
    D_get_a_west.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 17
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_a_east'):
    D_get_a_east = _libs['grass_display.6.4.2RC2'].D_get_a_east
    D_get_a_east.restype = c_double
    D_get_a_east.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 18
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_a_north'):
    D_get_a_north = _libs['grass_display.6.4.2RC2'].D_get_a_north
    D_get_a_north.restype = c_double
    D_get_a_north.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 19
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_a_south'):
    D_get_a_south = _libs['grass_display.6.4.2RC2'].D_get_a_south
    D_get_a_south.restype = c_double
    D_get_a_south.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 20
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_d_west'):
    D_get_d_west = _libs['grass_display.6.4.2RC2'].D_get_d_west
    D_get_d_west.restype = c_double
    D_get_d_west.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 21
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_d_east'):
    D_get_d_east = _libs['grass_display.6.4.2RC2'].D_get_d_east
    D_get_d_east.restype = c_double
    D_get_d_east.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 22
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_d_north'):
    D_get_d_north = _libs['grass_display.6.4.2RC2'].D_get_d_north
    D_get_d_north.restype = c_double
    D_get_d_north.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 23
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_d_south'):
    D_get_d_south = _libs['grass_display.6.4.2RC2'].D_get_d_south
    D_get_d_south.restype = c_double
    D_get_d_south.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 24
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_u_to_a_row'):
    D_u_to_a_row = _libs['grass_display.6.4.2RC2'].D_u_to_a_row
    D_u_to_a_row.restype = c_double
    D_u_to_a_row.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 25
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_u_to_a_col'):
    D_u_to_a_col = _libs['grass_display.6.4.2RC2'].D_u_to_a_col
    D_u_to_a_col.restype = c_double
    D_u_to_a_col.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 26
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_a_to_d_row'):
    D_a_to_d_row = _libs['grass_display.6.4.2RC2'].D_a_to_d_row
    D_a_to_d_row.restype = c_double
    D_a_to_d_row.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 27
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_a_to_d_col'):
    D_a_to_d_col = _libs['grass_display.6.4.2RC2'].D_a_to_d_col
    D_a_to_d_col.restype = c_double
    D_a_to_d_col.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 28
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_u_to_d_row'):
    D_u_to_d_row = _libs['grass_display.6.4.2RC2'].D_u_to_d_row
    D_u_to_d_row.restype = c_double
    D_u_to_d_row.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 29
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_u_to_d_col'):
    D_u_to_d_col = _libs['grass_display.6.4.2RC2'].D_u_to_d_col
    D_u_to_d_col.restype = c_double
    D_u_to_d_col.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 30
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_d_to_u_row'):
    D_d_to_u_row = _libs['grass_display.6.4.2RC2'].D_d_to_u_row
    D_d_to_u_row.restype = c_double
    D_d_to_u_row.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 31
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_d_to_u_col'):
    D_d_to_u_col = _libs['grass_display.6.4.2RC2'].D_d_to_u_col
    D_d_to_u_col.restype = c_double
    D_d_to_u_col.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 32
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_d_to_a_row'):
    D_d_to_a_row = _libs['grass_display.6.4.2RC2'].D_d_to_a_row
    D_d_to_a_row.restype = c_double
    D_d_to_a_row.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 33
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_d_to_a_col'):
    D_d_to_a_col = _libs['grass_display.6.4.2RC2'].D_d_to_a_col
    D_d_to_a_col.restype = c_double
    D_d_to_a_col.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 34
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_ns_resolution'):
    D_get_ns_resolution = _libs['grass_display.6.4.2RC2'].D_get_ns_resolution
    D_get_ns_resolution.restype = c_double
    D_get_ns_resolution.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 35
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_ew_resolution'):
    D_get_ew_resolution = _libs['grass_display.6.4.2RC2'].D_get_ew_resolution
    D_get_ew_resolution.restype = c_double
    D_get_ew_resolution.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 36
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_u'):
    D_get_u = _libs['grass_display.6.4.2RC2'].D_get_u
    D_get_u.restype = None
    D_get_u.argtypes = [(c_double * 2) * 2]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 37
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_a'):
    D_get_a = _libs['grass_display.6.4.2RC2'].D_get_a
    D_get_a.restype = None
    D_get_a.argtypes = [(c_int * 2) * 2]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 38
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_d'):
    D_get_d = _libs['grass_display.6.4.2RC2'].D_get_d
    D_get_d.restype = None
    D_get_d.argtypes = [(c_int * 2) * 2]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 41
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_color_list'):
    D_color_list = _libs['grass_display.6.4.2RC2'].D_color_list
    D_color_list.restype = ReturnString
    D_color_list.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 44
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_clip_window'):
    D_set_clip_window = _libs['grass_display.6.4.2RC2'].D_set_clip_window
    D_set_clip_window.restype = c_int
    D_set_clip_window.argtypes = [c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 45
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_clip_window_to_map_window'):
    D_set_clip_window_to_map_window = _libs['grass_display.6.4.2RC2'].D_set_clip_window_to_map_window
    D_set_clip_window_to_map_window.restype = c_int
    D_set_clip_window_to_map_window.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 46
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_clip_window_to_screen_window'):
    D_set_clip_window_to_screen_window = _libs['grass_display.6.4.2RC2'].D_set_clip_window_to_screen_window
    D_set_clip_window_to_screen_window.restype = c_int
    D_set_clip_window_to_screen_window.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 47
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cont_abs'):
    D_cont_abs = _libs['grass_display.6.4.2RC2'].D_cont_abs
    D_cont_abs.restype = c_int
    D_cont_abs.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 48
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cont_rel'):
    D_cont_rel = _libs['grass_display.6.4.2RC2'].D_cont_rel
    D_cont_rel.restype = c_int
    D_cont_rel.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 49
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_move_abs'):
    D_move_abs = _libs['grass_display.6.4.2RC2'].D_move_abs
    D_move_abs.restype = c_int
    D_move_abs.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 50
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_move_rel'):
    D_move_rel = _libs['grass_display.6.4.2RC2'].D_move_rel
    D_move_rel.restype = c_int
    D_move_rel.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 53
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_clip'):
    D_set_clip = _libs['grass_display.6.4.2RC2'].D_set_clip
    D_set_clip.restype = None
    D_set_clip.argtypes = [c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 54
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_clip_to_map'):
    D_clip_to_map = _libs['grass_display.6.4.2RC2'].D_clip_to_map
    D_clip_to_map.restype = None
    D_clip_to_map.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 55
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_move_clip'):
    D_move_clip = _libs['grass_display.6.4.2RC2'].D_move_clip
    D_move_clip.restype = None
    D_move_clip.argtypes = [c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 56
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cont_clip'):
    D_cont_clip = _libs['grass_display.6.4.2RC2'].D_cont_clip
    D_cont_clip.restype = c_int
    D_cont_clip.argtypes = [c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 57
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polydots_clip'):
    D_polydots_clip = _libs['grass_display.6.4.2RC2'].D_polydots_clip
    D_polydots_clip.restype = None
    D_polydots_clip.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 58
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polyline_cull'):
    D_polyline_cull = _libs['grass_display.6.4.2RC2'].D_polyline_cull
    D_polyline_cull.restype = None
    D_polyline_cull.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 59
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polyline_clip'):
    D_polyline_clip = _libs['grass_display.6.4.2RC2'].D_polyline_clip
    D_polyline_clip.restype = None
    D_polyline_clip.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 60
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polygon_cull'):
    D_polygon_cull = _libs['grass_display.6.4.2RC2'].D_polygon_cull
    D_polygon_cull.restype = None
    D_polygon_cull.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 61
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polygon_clip'):
    D_polygon_clip = _libs['grass_display.6.4.2RC2'].D_polygon_clip
    D_polygon_clip.restype = None
    D_polygon_clip.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 62
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_box_clip'):
    D_box_clip = _libs['grass_display.6.4.2RC2'].D_box_clip
    D_box_clip.restype = None
    D_box_clip.argtypes = [c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 63
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_move'):
    D_move = _libs['grass_display.6.4.2RC2'].D_move
    D_move.restype = None
    D_move.argtypes = [c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 64
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cont'):
    D_cont = _libs['grass_display.6.4.2RC2'].D_cont
    D_cont.restype = None
    D_cont.argtypes = [c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 65
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polydots'):
    D_polydots = _libs['grass_display.6.4.2RC2'].D_polydots
    D_polydots.restype = None
    D_polydots.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 66
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polyline'):
    D_polyline = _libs['grass_display.6.4.2RC2'].D_polyline
    D_polyline.restype = None
    D_polyline.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 67
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_polygon'):
    D_polygon = _libs['grass_display.6.4.2RC2'].D_polygon
    D_polygon.restype = None
    D_polygon.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 68
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_box'):
    D_box = _libs['grass_display.6.4.2RC2'].D_box
    D_box.restype = None
    D_box.argtypes = [c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 69
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_line_width'):
    D_line_width = _libs['grass_display.6.4.2RC2'].D_line_width
    D_line_width.restype = None
    D_line_width.argtypes = [c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 72
if hasattr(_libs['grass_display.6.4.2RC2'], 'get_win_w_mouse'):
    get_win_w_mouse = _libs['grass_display.6.4.2RC2'].get_win_w_mouse
    get_win_w_mouse.restype = c_int
    get_win_w_mouse.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 75
if hasattr(_libs['grass_display.6.4.2RC2'], 'ident_win'):
    ident_win = _libs['grass_display.6.4.2RC2'].ident_win
    ident_win.restype = c_int
    ident_win.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 78
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_cell_name'):
    D_set_cell_name = _libs['grass_display.6.4.2RC2'].D_set_cell_name
    D_set_cell_name.restype = c_int
    D_set_cell_name.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 79
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_cell_name'):
    D_get_cell_name = _libs['grass_display.6.4.2RC2'].D_get_cell_name
    D_get_cell_name.restype = c_int
    D_get_cell_name.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 80
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_dig_name'):
    D_set_dig_name = _libs['grass_display.6.4.2RC2'].D_set_dig_name
    D_set_dig_name.restype = c_int
    D_set_dig_name.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 81
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_dig_name'):
    D_get_dig_name = _libs['grass_display.6.4.2RC2'].D_get_dig_name
    D_get_dig_name.restype = c_int
    D_get_dig_name.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 82
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_add_to_cell_list'):
    D_add_to_cell_list = _libs['grass_display.6.4.2RC2'].D_add_to_cell_list
    D_add_to_cell_list.restype = c_int
    D_add_to_cell_list.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 83
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_cell_list'):
    D_get_cell_list = _libs['grass_display.6.4.2RC2'].D_get_cell_list
    D_get_cell_list.restype = c_int
    D_get_cell_list.argtypes = [POINTER(POINTER(POINTER(c_char))), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 84
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_add_to_dig_list'):
    D_add_to_dig_list = _libs['grass_display.6.4.2RC2'].D_add_to_dig_list
    D_add_to_dig_list.restype = c_int
    D_add_to_dig_list.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 85
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_dig_list'):
    D_get_dig_list = _libs['grass_display.6.4.2RC2'].D_get_dig_list
    D_get_dig_list.restype = c_int
    D_get_dig_list.argtypes = [POINTER(POINTER(POINTER(c_char))), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 86
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_add_to_list'):
    D_add_to_list = _libs['grass_display.6.4.2RC2'].D_add_to_list
    D_add_to_list.restype = c_int
    D_add_to_list.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 87
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_list'):
    D_get_list = _libs['grass_display.6.4.2RC2'].D_get_list
    D_get_list.restype = c_int
    D_get_list.argtypes = [POINTER(POINTER(POINTER(c_char))), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 88
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_clear_window'):
    D_clear_window = _libs['grass_display.6.4.2RC2'].D_clear_window
    D_clear_window.restype = c_int
    D_clear_window.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 89
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_erase_color'):
    D_set_erase_color = _libs['grass_display.6.4.2RC2'].D_set_erase_color
    D_set_erase_color.restype = c_int
    D_set_erase_color.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 90
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_erase_color'):
    D_get_erase_color = _libs['grass_display.6.4.2RC2'].D_get_erase_color
    D_get_erase_color.restype = c_int
    D_get_erase_color.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 93
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_popup'):
    D_popup = _libs['grass_display.6.4.2RC2'].D_popup
    D_popup.restype = c_int
    D_popup.argtypes = [c_int, c_int, c_int, c_int, c_int, c_int, POINTER(POINTER(c_char))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 96
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_raster'):
    D_draw_raster = _libs['grass_display.6.4.2RC2'].D_draw_raster
    D_draw_raster.restype = c_int
    D_draw_raster.argtypes = [c_int, POINTER(None), POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 97
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_d_raster'):
    D_draw_d_raster = _libs['grass_display.6.4.2RC2'].D_draw_d_raster
    D_draw_d_raster.restype = c_int
    D_draw_d_raster.argtypes = [c_int, POINTER(DCELL), POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 98
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_f_raster'):
    D_draw_f_raster = _libs['grass_display.6.4.2RC2'].D_draw_f_raster
    D_draw_f_raster.restype = c_int
    D_draw_f_raster.argtypes = [c_int, POINTER(FCELL), POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 99
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_c_raster'):
    D_draw_c_raster = _libs['grass_display.6.4.2RC2'].D_draw_c_raster
    D_draw_c_raster.restype = c_int
    D_draw_c_raster.argtypes = [c_int, POINTER(CELL), POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 100
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_cell'):
    D_draw_cell = _libs['grass_display.6.4.2RC2'].D_draw_cell
    D_draw_cell.restype = c_int
    D_draw_cell.argtypes = [c_int, POINTER(CELL), POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 101
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cell_draw_setup'):
    D_cell_draw_setup = _libs['grass_display.6.4.2RC2'].D_cell_draw_setup
    D_cell_draw_setup.restype = c_int
    D_cell_draw_setup.argtypes = [c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 102
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_draw_raster_RGB'):
    D_draw_raster_RGB = _libs['grass_display.6.4.2RC2'].D_draw_raster_RGB
    D_draw_raster_RGB.restype = c_int
    D_draw_raster_RGB.argtypes = [c_int, POINTER(None), POINTER(None), POINTER(None), POINTER(struct_Colors), POINTER(struct_Colors), POINTER(struct_Colors), RASTER_MAP_TYPE, RASTER_MAP_TYPE, RASTER_MAP_TYPE]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 105
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_cell_draw_end'):
    D_cell_draw_end = _libs['grass_display.6.4.2RC2'].D_cell_draw_end
    D_cell_draw_end.restype = None
    D_cell_draw_end.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 108
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_overlay_mode'):
    D_set_overlay_mode = _libs['grass_display.6.4.2RC2'].D_set_overlay_mode
    D_set_overlay_mode.restype = c_int
    D_set_overlay_mode.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 109
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_color'):
    D_color = _libs['grass_display.6.4.2RC2'].D_color
    D_color.restype = c_int
    D_color.argtypes = [CELL, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 110
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_c_color'):
    D_c_color = _libs['grass_display.6.4.2RC2'].D_c_color
    D_c_color.restype = c_int
    D_c_color.argtypes = [CELL, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 111
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_d_color'):
    D_d_color = _libs['grass_display.6.4.2RC2'].D_d_color
    D_d_color.restype = c_int
    D_d_color.argtypes = [DCELL, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 112
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_f_color'):
    D_f_color = _libs['grass_display.6.4.2RC2'].D_f_color
    D_f_color.restype = c_int
    D_f_color.argtypes = [FCELL, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 113
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_color_of_type'):
    D_color_of_type = _libs['grass_display.6.4.2RC2'].D_color_of_type
    D_color_of_type.restype = c_int
    D_color_of_type.argtypes = [POINTER(None), POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 116
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_setup'):
    D_setup = _libs['grass_display.6.4.2RC2'].D_setup
    D_setup.restype = c_int
    D_setup.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 119
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_symbol'):
    D_symbol = _libs['grass_display.6.4.2RC2'].D_symbol
    D_symbol.restype = None
    D_symbol.argtypes = [POINTER(SYMBOL), c_int, c_int, POINTER(RGBA_Color), POINTER(RGBA_Color)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 121
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_symbol2'):
    D_symbol2 = _libs['grass_display.6.4.2RC2'].D_symbol2
    D_symbol2.restype = None
    D_symbol2.argtypes = [POINTER(SYMBOL), c_int, c_int, POINTER(RGBA_Color), POINTER(RGBA_Color)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 125
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_translate_color'):
    D_translate_color = _libs['grass_display.6.4.2RC2'].D_translate_color
    D_translate_color.restype = c_int
    D_translate_color.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 126
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_parse_color'):
    D_parse_color = _libs['grass_display.6.4.2RC2'].D_parse_color
    D_parse_color.restype = c_int
    D_parse_color.argtypes = [String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 127
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_raster_use_color'):
    D_raster_use_color = _libs['grass_display.6.4.2RC2'].D_raster_use_color
    D_raster_use_color.restype = c_int
    D_raster_use_color.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 128
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_color_number_to_RGB'):
    D_color_number_to_RGB = _libs['grass_display.6.4.2RC2'].D_color_number_to_RGB
    D_color_number_to_RGB.restype = c_int
    D_color_number_to_RGB.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 131
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_new_window'):
    D_new_window = _libs['grass_display.6.4.2RC2'].D_new_window
    D_new_window.restype = c_int
    D_new_window.argtypes = [String, c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 132
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_new_window_percent'):
    D_new_window_percent = _libs['grass_display.6.4.2RC2'].D_new_window_percent
    D_new_window_percent.restype = c_int
    D_new_window_percent.argtypes = [String, c_float, c_float, c_float, c_float]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 133
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_set_cur_wind'):
    D_set_cur_wind = _libs['grass_display.6.4.2RC2'].D_set_cur_wind
    D_set_cur_wind.restype = c_int
    D_set_cur_wind.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 134
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_cur_wind'):
    D_get_cur_wind = _libs['grass_display.6.4.2RC2'].D_get_cur_wind
    D_get_cur_wind.restype = c_int
    D_get_cur_wind.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 135
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_show_window'):
    D_show_window = _libs['grass_display.6.4.2RC2'].D_show_window
    D_show_window.restype = c_int
    D_show_window.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 136
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_get_screen_window'):
    D_get_screen_window = _libs['grass_display.6.4.2RC2'].D_get_screen_window
    D_get_screen_window.restype = c_int
    D_get_screen_window.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 137
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_check_map_window'):
    D_check_map_window = _libs['grass_display.6.4.2RC2'].D_check_map_window
    D_check_map_window.restype = c_int
    D_check_map_window.argtypes = [POINTER(struct_Cell_head)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 138
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_reset_screen_window'):
    D_reset_screen_window = _libs['grass_display.6.4.2RC2'].D_reset_screen_window
    D_reset_screen_window.restype = c_int
    D_reset_screen_window.argtypes = [c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 139
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_timestamp'):
    D_timestamp = _libs['grass_display.6.4.2RC2'].D_timestamp
    D_timestamp.restype = c_int
    D_timestamp.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 140
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_remove_window'):
    D_remove_window = _libs['grass_display.6.4.2RC2'].D_remove_window
    D_remove_window.restype = None
    D_remove_window.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 141
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_erase_window'):
    D_erase_window = _libs['grass_display.6.4.2RC2'].D_erase_window
    D_erase_window.restype = None
    D_erase_window.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 142
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_erase'):
    D_erase = _libs['grass_display.6.4.2RC2'].D_erase
    D_erase.restype = None
    D_erase.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 143
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_remove_windows'):
    D_remove_windows = _libs['grass_display.6.4.2RC2'].D_remove_windows
    D_remove_windows.restype = None
    D_remove_windows.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\display.h: 144
if hasattr(_libs['grass_display.6.4.2RC2'], 'D_full_screen'):
    D_full_screen = _libs['grass_display.6.4.2RC2'].D_full_screen
    D_full_screen.restype = None
    D_full_screen.argtypes = []

# No inserted files

