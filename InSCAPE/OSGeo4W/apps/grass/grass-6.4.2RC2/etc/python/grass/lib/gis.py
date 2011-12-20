'''Wrapper for gis.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_gis.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h -o gis.py

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

_libs["grass_gis.6.4.2RC2"] = load_library("grass_gis.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:/OSGeo4W/include/stdio.h: 139
class struct__iobuf(Structure):
    pass

struct__iobuf.__slots__ = [
    '_ptr',
    '_cnt',
    '_base',
    '_flag',
    '_file',
    '_charbuf',
    '_bufsiz',
    '_tmpfname',
]
struct__iobuf._fields_ = [
    ('_ptr', String),
    ('_cnt', c_int),
    ('_base', String),
    ('_flag', c_int),
    ('_file', c_int),
    ('_charbuf', c_int),
    ('_bufsiz', c_int),
    ('_tmpfname', String),
]

FILE = struct__iobuf # c:/OSGeo4W/include/stdio.h: 139

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/datetime.h: 25
class struct_anon_1(Structure):
    pass

struct_anon_1.__slots__ = [
    'mode',
    '_from',
    'to',
    'fracsec',
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
    'positive',
    'tz',
]
struct_anon_1._fields_ = [
    ('mode', c_int),
    ('_from', c_int),
    ('to', c_int),
    ('fracsec', c_int),
    ('year', c_int),
    ('month', c_int),
    ('day', c_int),
    ('hour', c_int),
    ('minute', c_int),
    ('second', c_double),
    ('positive', c_int),
    ('tz', c_int),
]

DateTime = struct_anon_1 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/datetime.h: 25

enum_anon_2 = c_int # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_WHERE = 0 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_TABLE = (G_OPT_WHERE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_DRIVER = (G_OPT_TABLE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_DATABASE = (G_OPT_DRIVER + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_COLUMN = (G_OPT_DATABASE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_COLUMNS = (G_OPT_COLUMN + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_I_GROUP = (G_OPT_COLUMNS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_I_SUBGROUP = (G_OPT_I_GROUP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_INPUT = (G_OPT_I_SUBGROUP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_INPUTS = (G_OPT_R_INPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_OUTPUT = (G_OPT_R_INPUTS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_MAP = (G_OPT_R_OUTPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_MAPS = (G_OPT_R_MAP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_BASE = (G_OPT_R_MAPS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_COVER = (G_OPT_R_BASE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_ELEV = (G_OPT_R_COVER + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R_ELEVS = (G_OPT_R_ELEV + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R3_INPUT = (G_OPT_R_ELEVS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R3_INPUTS = (G_OPT_R3_INPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R3_OUTPUT = (G_OPT_R3_INPUTS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R3_MAP = (G_OPT_R3_OUTPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_R3_MAPS = (G_OPT_R3_MAP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_INPUT = (G_OPT_R3_MAPS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_INPUTS = (G_OPT_V_INPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_OUTPUT = (G_OPT_V_INPUTS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_MAP = (G_OPT_V_OUTPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_MAPS = (G_OPT_V_MAP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_TYPE = (G_OPT_V_MAPS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V3_TYPE = (G_OPT_V_TYPE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_FIELD = (G_OPT_V3_TYPE + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_CAT = (G_OPT_V_FIELD + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_CATS = (G_OPT_V_CAT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_ID = (G_OPT_V_CATS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_V_IDS = (G_OPT_V_ID + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_F_INPUT = (G_OPT_V_IDS + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_F_OUTPUT = (G_OPT_F_INPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_F_SEP = (G_OPT_F_OUTPUT + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_C_FG = (G_OPT_F_SEP + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

G_OPT_C_BG = (G_OPT_C_FG + 1) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

STD_OPT = enum_anon_2 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 209

enum_anon_3 = c_int # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_RASTER = 1 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_RASTER3D = 2 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_VECTOR = 3 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_OLDVECTOR = 4 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_ASCIIVECTOR = 5 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_ICON = 6 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_LABEL = 7 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_SITE = 8 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_REGION = 9 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_REGION3D = 10 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_GROUP = 11 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

G_ELEMENT_3DVIEW = 12 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 238

CELL = c_int # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 256

DCELL = c_double # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 257

FCELL = c_float # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 258

RASTER_MAP_TYPE = c_int # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 260

INTERP_TYPE = c_int # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 263

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 265
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 289
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 297
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 309
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 319
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 304
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 331
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 355
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

RGBA_Color = struct_anon_6 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 355

RGB_Color = RGBA_Color # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 357

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 365
class struct_Reclass(Structure):
    pass

struct_Reclass.__slots__ = [
    'name',
    'mapset',
    'type',
    'num',
    'min',
    'max',
    'table',
]
struct_Reclass._fields_ = [
    ('name', String),
    ('mapset', String),
    ('type', c_int),
    ('num', c_int),
    ('min', CELL),
    ('max', CELL),
    ('table', POINTER(CELL)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 376
class struct_FPReclass_table(Structure):
    pass

struct_FPReclass_table.__slots__ = [
    'dLow',
    'dHigh',
    'rLow',
    'rHigh',
]
struct_FPReclass_table._fields_ = [
    ('dLow', DCELL),
    ('dHigh', DCELL),
    ('rLow', DCELL),
    ('rHigh', DCELL),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 386
class struct_FPReclass(Structure):
    pass

struct_FPReclass.__slots__ = [
    'defaultDRuleSet',
    'defaultRRuleSet',
    'infiniteLeftSet',
    'infiniteRightSet',
    'rRangeSet',
    'maxNofRules',
    'nofRules',
    'defaultDMin',
    'defaultDMax',
    'defaultRMin',
    'defaultRMax',
    'infiniteDLeft',
    'infiniteDRight',
    'infiniteRLeft',
    'infiniteRRight',
    'dMin',
    'dMax',
    'rMin',
    'rMax',
    'table',
]
struct_FPReclass._fields_ = [
    ('defaultDRuleSet', c_int),
    ('defaultRRuleSet', c_int),
    ('infiniteLeftSet', c_int),
    ('infiniteRightSet', c_int),
    ('rRangeSet', c_int),
    ('maxNofRules', c_int),
    ('nofRules', c_int),
    ('defaultDMin', DCELL),
    ('defaultDMax', DCELL),
    ('defaultRMin', DCELL),
    ('defaultRMax', DCELL),
    ('infiniteDLeft', DCELL),
    ('infiniteDRight', DCELL),
    ('infiniteRLeft', DCELL),
    ('infiniteRRight', DCELL),
    ('dMin', DCELL),
    ('dMax', DCELL),
    ('rMin', DCELL),
    ('rMax', DCELL),
    ('table', POINTER(struct_FPReclass_table)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 410
class struct_Quant_table(Structure):
    pass

struct_Quant_table.__slots__ = [
    'dLow',
    'dHigh',
    'cLow',
    'cHigh',
]
struct_Quant_table._fields_ = [
    ('dLow', DCELL),
    ('dHigh', DCELL),
    ('cLow', CELL),
    ('cHigh', CELL),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 443
class struct_anon_7(Structure):
    pass

struct_anon_7.__slots__ = [
    'vals',
    'rules',
    'nalloc',
    'active',
    'inf_dmin',
    'inf_dmax',
    'inf_min',
    'inf_max',
]
struct_anon_7._fields_ = [
    ('vals', POINTER(DCELL)),
    ('rules', POINTER(POINTER(struct_Quant_table))),
    ('nalloc', c_int),
    ('active', c_int),
    ('inf_dmin', DCELL),
    ('inf_dmax', DCELL),
    ('inf_min', CELL),
    ('inf_max', CELL),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 418
class struct_Quant(Structure):
    pass

struct_Quant.__slots__ = [
    'truncate_only',
    'round_only',
    'defaultDRuleSet',
    'defaultCRuleSet',
    'infiniteLeftSet',
    'infiniteRightSet',
    'cRangeSet',
    'maxNofRules',
    'nofRules',
    'defaultDMin',
    'defaultDMax',
    'defaultCMin',
    'defaultCMax',
    'infiniteDLeft',
    'infiniteDRight',
    'infiniteCLeft',
    'infiniteCRight',
    'dMin',
    'dMax',
    'cMin',
    'cMax',
    'table',
    'fp_lookup',
]
struct_Quant._fields_ = [
    ('truncate_only', c_int),
    ('round_only', c_int),
    ('defaultDRuleSet', c_int),
    ('defaultCRuleSet', c_int),
    ('infiniteLeftSet', c_int),
    ('infiniteRightSet', c_int),
    ('cRangeSet', c_int),
    ('maxNofRules', c_int),
    ('nofRules', c_int),
    ('defaultDMin', DCELL),
    ('defaultDMax', DCELL),
    ('defaultCMin', CELL),
    ('defaultCMax', CELL),
    ('infiniteDLeft', DCELL),
    ('infiniteDRight', DCELL),
    ('infiniteCLeft', CELL),
    ('infiniteCRight', CELL),
    ('dMin', DCELL),
    ('dMax', DCELL),
    ('cMin', CELL),
    ('cMax', CELL),
    ('table', POINTER(struct_Quant_table)),
    ('fp_lookup', struct_anon_7),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 461
class struct_Categories(Structure):
    pass

struct_Categories.__slots__ = [
    'ncats',
    'num',
    'title',
    'fmt',
    'm1',
    'a1',
    'm2',
    'a2',
    'q',
    'labels',
    'marks',
    'nalloc',
    'last_marked_rule',
]
struct_Categories._fields_ = [
    ('ncats', CELL),
    ('num', CELL),
    ('title', String),
    ('fmt', String),
    ('m1', c_float),
    ('a1', c_float),
    ('m2', c_float),
    ('a2', c_float),
    ('q', struct_Quant),
    ('labels', POINTER(POINTER(c_char))),
    ('marks', POINTER(c_int)),
    ('nalloc', c_int),
    ('last_marked_rule', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 487
class struct_History(Structure):
    pass

struct_History.__slots__ = [
    'mapid',
    'title',
    'mapset',
    'creator',
    'maptype',
    'datsrc_1',
    'datsrc_2',
    'keywrd',
    'edlinecnt',
    'edhist',
]
struct_History._fields_ = [
    ('mapid', c_char * 80),
    ('title', c_char * 80),
    ('mapset', c_char * 80),
    ('creator', c_char * 80),
    ('maptype', c_char * 80),
    ('datsrc_1', c_char * 80),
    ('datsrc_2', c_char * 80),
    ('keywrd', c_char * 80),
    ('edlinecnt', c_int),
    ('edhist', (c_char * 80) * 50),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 503
class struct_Cell_stats_node(Structure):
    pass

struct_Cell_stats_node.__slots__ = [
    'idx',
    'count',
    'left',
    'right',
]
struct_Cell_stats_node._fields_ = [
    ('idx', c_int),
    ('count', POINTER(c_long)),
    ('left', c_int),
    ('right', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 501
class struct_Cell_stats(Structure):
    pass

struct_Cell_stats.__slots__ = [
    'node',
    'tlen',
    'N',
    'curp',
    'null_data_count',
    'curoffset',
]
struct_Cell_stats._fields_ = [
    ('node', POINTER(struct_Cell_stats_node)),
    ('tlen', c_int),
    ('N', c_int),
    ('curp', c_int),
    ('null_data_count', c_long),
    ('curoffset', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 522
class struct_Histogram_list(Structure):
    pass

struct_Histogram_list.__slots__ = [
    'cat',
    'count',
]
struct_Histogram_list._fields_ = [
    ('cat', CELL),
    ('count', c_long),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 518
class struct_Histogram(Structure):
    pass

struct_Histogram.__slots__ = [
    'num',
    'list',
]
struct_Histogram._fields_ = [
    ('num', c_int),
    ('list', POINTER(struct_Histogram_list)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 529
class struct_Range(Structure):
    pass

struct_Range.__slots__ = [
    'min',
    'max',
    'first_time',
]
struct_Range._fields_ = [
    ('min', CELL),
    ('max', CELL),
    ('first_time', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 536
class struct_FPRange(Structure):
    pass

struct_FPRange.__slots__ = [
    'min',
    'max',
    'first_time',
]
struct_FPRange._fields_ = [
    ('min', DCELL),
    ('max', DCELL),
    ('first_time', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 543
class struct_FP_stats(Structure):
    pass

struct_FP_stats.__slots__ = [
    'geometric',
    'geom_abs',
    'flip',
    'count',
    'min',
    'max',
    'stats',
    'total',
]
struct_FP_stats._fields_ = [
    ('geometric', c_int),
    ('geom_abs', c_int),
    ('flip', c_int),
    ('count', c_int),
    ('min', DCELL),
    ('max', DCELL),
    ('stats', POINTER(c_ulong)),
    ('total', c_ulong),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 556
class struct_G_3dview(Structure):
    pass

struct_G_3dview.__slots__ = [
    'pgm_id',
    'from_to',
    'fov',
    'twist',
    'exag',
    'mesh_freq',
    'poly_freq',
    'display_type',
    'lightson',
    'dozero',
    'colorgrid',
    'shading',
    'fringe',
    'surfonly',
    'doavg',
    'grid_col',
    'bg_col',
    'other_col',
    'lightpos',
    'lightcol',
    'ambient',
    'shine',
    'vwin',
]
struct_G_3dview._fields_ = [
    ('pgm_id', c_char * 40),
    ('from_to', (c_float * 3) * 2),
    ('fov', c_float),
    ('twist', c_float),
    ('exag', c_float),
    ('mesh_freq', c_int),
    ('poly_freq', c_int),
    ('display_type', c_int),
    ('lightson', c_int),
    ('dozero', c_int),
    ('colorgrid', c_int),
    ('shading', c_int),
    ('fringe', c_int),
    ('surfonly', c_int),
    ('doavg', c_int),
    ('grid_col', c_char * 40),
    ('bg_col', c_char * 40),
    ('other_col', c_char * 40),
    ('lightpos', c_float * 4),
    ('lightcol', c_float * 3),
    ('ambient', c_float),
    ('shine', c_float),
    ('vwin', struct_Cell_head),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 583
class struct_Key_Value(Structure):
    pass

struct_Key_Value.__slots__ = [
    'nitems',
    'nalloc',
    'key',
    'value',
]
struct_Key_Value._fields_ = [
    ('nitems', c_int),
    ('nalloc', c_int),
    ('key', POINTER(POINTER(c_char))),
    ('value', POINTER(POINTER(c_char))),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 591
class struct_Option(Structure):
    pass

struct_Option.__slots__ = [
    'key',
    'type',
    'required',
    'multiple',
    'options',
    'opts',
    'key_desc',
    'label',
    'description',
    'descriptions',
    'descs',
    'answer',
    '_def',
    'answers',
    'next_opt',
    'gisprompt',
    'guisection',
    'checker',
    'count',
]
struct_Option._fields_ = [
    ('key', String),
    ('type', c_int),
    ('required', c_int),
    ('multiple', c_int),
    ('options', String),
    ('opts', POINTER(POINTER(c_char))),
    ('key_desc', String),
    ('label', String),
    ('description', String),
    ('descriptions', String),
    ('descs', POINTER(POINTER(c_char))),
    ('answer', String),
    ('_def', String),
    ('answers', POINTER(POINTER(c_char))),
    ('next_opt', POINTER(struct_Option)),
    ('gisprompt', String),
    ('guisection', String),
    ('checker', CFUNCTYPE(UNCHECKED(c_int), )),
    ('count', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 619
class struct_Flag(Structure):
    pass

struct_Flag.__slots__ = [
    'key',
    'answer',
    'label',
    'description',
    'guisection',
    'next_flag',
]
struct_Flag._fields_ = [
    ('key', c_char),
    ('answer', c_char),
    ('label', String),
    ('description', String),
    ('guisection', String),
    ('next_flag', POINTER(struct_Flag)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 629
class struct_GModule(Structure):
    pass

struct_GModule.__slots__ = [
    'label',
    'description',
    'keywords',
    'overwrite',
    'verbose',
]
struct_GModule._fields_ = [
    ('label', String),
    ('description', String),
    ('keywords', String),
    ('overwrite', c_int),
    ('verbose', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 639
class struct_TimeStamp(Structure):
    pass

struct_TimeStamp.__slots__ = [
    'dt',
    'count',
]
struct_TimeStamp._fields_ = [
    ('dt', DateTime * 2),
    ('count', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 645
class struct_GDAL_link(Structure):
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 35
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_adjust_Cell_head'):
    G_adjust_Cell_head = _libs['grass_gis.6.4.2RC2'].G_adjust_Cell_head
    G_adjust_Cell_head.restype = ReturnString
    G_adjust_Cell_head.argtypes = [POINTER(struct_Cell_head), c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 36
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_adjust_Cell_head3'):
    G_adjust_Cell_head3 = _libs['grass_gis.6.4.2RC2'].G_adjust_Cell_head3
    G_adjust_Cell_head3.restype = ReturnString
    G_adjust_Cell_head3.argtypes = [POINTER(struct_Cell_head), c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 39
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_align_window'):
    G_align_window = _libs['grass_gis.6.4.2RC2'].G_align_window
    G_align_window.restype = ReturnString
    G_align_window.argtypes = [POINTER(struct_Cell_head), POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 42
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__malloc'):
    G__malloc = _libs['grass_gis.6.4.2RC2'].G__malloc
    G__malloc.restype = POINTER(None)
    G__malloc.argtypes = [String, c_int, c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 43
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__calloc'):
    G__calloc = _libs['grass_gis.6.4.2RC2'].G__calloc
    G__calloc.restype = POINTER(None)
    G__calloc.argtypes = [String, c_int, c_size_t, c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 44
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__realloc'):
    G__realloc = _libs['grass_gis.6.4.2RC2'].G__realloc
    G__realloc.restype = POINTER(None)
    G__realloc.argtypes = [String, c_int, POINTER(None), c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 45
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free'):
    G_free = _libs['grass_gis.6.4.2RC2'].G_free
    G_free.restype = None
    G_free.argtypes = [POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 52
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_raster_size'):
    G_raster_size = _libs['grass_gis.6.4.2RC2'].G_raster_size
    G_raster_size.restype = c_size_t
    G_raster_size.argtypes = [RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 53
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_cell_buf'):
    G_allocate_cell_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_cell_buf
    G_allocate_cell_buf.restype = POINTER(CELL)
    G_allocate_cell_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 54
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_raster_buf'):
    G_allocate_raster_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_raster_buf
    G_allocate_raster_buf.restype = POINTER(None)
    G_allocate_raster_buf.argtypes = [RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 55
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_c_raster_buf'):
    G_allocate_c_raster_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_c_raster_buf
    G_allocate_c_raster_buf.restype = POINTER(CELL)
    G_allocate_c_raster_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 56
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_f_raster_buf'):
    G_allocate_f_raster_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_f_raster_buf
    G_allocate_f_raster_buf.restype = POINTER(FCELL)
    G_allocate_f_raster_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 57
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_d_raster_buf'):
    G_allocate_d_raster_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_d_raster_buf
    G_allocate_d_raster_buf.restype = POINTER(DCELL)
    G_allocate_d_raster_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 58
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_allocate_null_buf'):
    G_allocate_null_buf = _libs['grass_gis.6.4.2RC2'].G_allocate_null_buf
    G_allocate_null_buf.restype = ReturnString
    G_allocate_null_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 59
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__allocate_null_bits'):
    G__allocate_null_bits = _libs['grass_gis.6.4.2RC2'].G__allocate_null_bits
    G__allocate_null_bits.restype = POINTER(c_ubyte)
    G__allocate_null_bits.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 60
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__null_bitstream_size'):
    G__null_bitstream_size = _libs['grass_gis.6.4.2RC2'].G__null_bitstream_size
    G__null_bitstream_size.restype = c_int
    G__null_bitstream_size.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 63
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_cell_area_calculations'):
    G_begin_cell_area_calculations = _libs['grass_gis.6.4.2RC2'].G_begin_cell_area_calculations
    G_begin_cell_area_calculations.restype = c_int
    G_begin_cell_area_calculations.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 64
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_area_of_cell_at_row'):
    G_area_of_cell_at_row = _libs['grass_gis.6.4.2RC2'].G_area_of_cell_at_row
    G_area_of_cell_at_row.restype = c_double
    G_area_of_cell_at_row.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 65
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_polygon_area_calculations'):
    G_begin_polygon_area_calculations = _libs['grass_gis.6.4.2RC2'].G_begin_polygon_area_calculations
    G_begin_polygon_area_calculations.restype = c_int
    G_begin_polygon_area_calculations.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 66
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_area_of_polygon'):
    G_area_of_polygon = _libs['grass_gis.6.4.2RC2'].G_area_of_polygon
    G_area_of_polygon.restype = c_double
    G_area_of_polygon.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 69
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_zone_area_on_ellipsoid'):
    G_begin_zone_area_on_ellipsoid = _libs['grass_gis.6.4.2RC2'].G_begin_zone_area_on_ellipsoid
    G_begin_zone_area_on_ellipsoid.restype = c_int
    G_begin_zone_area_on_ellipsoid.argtypes = [c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 70
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_darea0_on_ellipsoid'):
    G_darea0_on_ellipsoid = _libs['grass_gis.6.4.2RC2'].G_darea0_on_ellipsoid
    G_darea0_on_ellipsoid.restype = c_double
    G_darea0_on_ellipsoid.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 71
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_area_for_zone_on_ellipsoid'):
    G_area_for_zone_on_ellipsoid = _libs['grass_gis.6.4.2RC2'].G_area_for_zone_on_ellipsoid
    G_area_for_zone_on_ellipsoid.restype = c_double
    G_area_for_zone_on_ellipsoid.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 74
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_ellipsoid_polygon_area'):
    G_begin_ellipsoid_polygon_area = _libs['grass_gis.6.4.2RC2'].G_begin_ellipsoid_polygon_area
    G_begin_ellipsoid_polygon_area.restype = c_int
    G_begin_ellipsoid_polygon_area.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 75
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ellipsoid_polygon_area'):
    G_ellipsoid_polygon_area = _libs['grass_gis.6.4.2RC2'].G_ellipsoid_polygon_area
    G_ellipsoid_polygon_area.restype = c_double
    G_ellipsoid_polygon_area.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 78
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_planimetric_polygon_area'):
    G_planimetric_polygon_area = _libs['grass_gis.6.4.2RC2'].G_planimetric_polygon_area
    G_planimetric_polygon_area.restype = c_double
    G_planimetric_polygon_area.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 81
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_zone_area_on_sphere'):
    G_begin_zone_area_on_sphere = _libs['grass_gis.6.4.2RC2'].G_begin_zone_area_on_sphere
    G_begin_zone_area_on_sphere.restype = c_int
    G_begin_zone_area_on_sphere.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 82
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_darea0_on_sphere'):
    G_darea0_on_sphere = _libs['grass_gis.6.4.2RC2'].G_darea0_on_sphere
    G_darea0_on_sphere.restype = c_double
    G_darea0_on_sphere.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 83
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_area_for_zone_on_sphere'):
    G_area_for_zone_on_sphere = _libs['grass_gis.6.4.2RC2'].G_area_for_zone_on_sphere
    G_area_for_zone_on_sphere.restype = c_double
    G_area_for_zone_on_sphere.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 86
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ascii_check'):
    G_ascii_check = _libs['grass_gis.6.4.2RC2'].G_ascii_check
    G_ascii_check.restype = c_int
    G_ascii_check.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 89
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_new'):
    G_ask_new = _libs['grass_gis.6.4.2RC2'].G_ask_new
    G_ask_new.restype = ReturnString
    G_ask_new.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 90
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_new_ext'):
    G_ask_new_ext = _libs['grass_gis.6.4.2RC2'].G_ask_new_ext
    G_ask_new_ext.restype = ReturnString
    G_ask_new_ext.argtypes = [String, String, String, String, String, CFUNCTYPE(UNCHECKED(c_int), )]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 91
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_old'):
    G_ask_old = _libs['grass_gis.6.4.2RC2'].G_ask_old
    G_ask_old.restype = ReturnString
    G_ask_old.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 92
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_old_ext'):
    G_ask_old_ext = _libs['grass_gis.6.4.2RC2'].G_ask_old_ext
    G_ask_old_ext.restype = ReturnString
    G_ask_old_ext.argtypes = [String, String, String, String, String, CFUNCTYPE(UNCHECKED(c_int), )]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 93
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_any'):
    G_ask_any = _libs['grass_gis.6.4.2RC2'].G_ask_any
    G_ask_any.restype = ReturnString
    G_ask_any.argtypes = [String, String, String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 94
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_any_ext'):
    G_ask_any_ext = _libs['grass_gis.6.4.2RC2'].G_ask_any_ext
    G_ask_any_ext.restype = ReturnString
    G_ask_any_ext.argtypes = [String, String, String, String, c_int, String, CFUNCTYPE(UNCHECKED(c_int), )]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 96
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_in_mapset'):
    G_ask_in_mapset = _libs['grass_gis.6.4.2RC2'].G_ask_in_mapset
    G_ask_in_mapset.restype = ReturnString
    G_ask_in_mapset.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 97
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_in_mapset_ext'):
    G_ask_in_mapset_ext = _libs['grass_gis.6.4.2RC2'].G_ask_in_mapset_ext
    G_ask_in_mapset_ext.restype = ReturnString
    G_ask_in_mapset_ext.argtypes = [String, String, String, String, String, CFUNCTYPE(UNCHECKED(c_int), )]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 99
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_new_file'):
    G_ask_new_file = _libs['grass_gis.6.4.2RC2'].G_ask_new_file
    G_ask_new_file.restype = ReturnString
    G_ask_new_file.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 100
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_old_file'):
    G_ask_old_file = _libs['grass_gis.6.4.2RC2'].G_ask_old_file
    G_ask_old_file.restype = ReturnString
    G_ask_old_file.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 101
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_ask_return_msg'):
    G_set_ask_return_msg = _libs['grass_gis.6.4.2RC2'].G_set_ask_return_msg
    G_set_ask_return_msg.restype = c_int
    G_set_ask_return_msg.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 102
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ask_return_msg'):
    G_get_ask_return_msg = _libs['grass_gis.6.4.2RC2'].G_get_ask_return_msg
    G_get_ask_return_msg.restype = ReturnString
    G_get_ask_return_msg.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 105
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_cell_new'):
    G_ask_cell_new = _libs['grass_gis.6.4.2RC2'].G_ask_cell_new
    G_ask_cell_new.restype = ReturnString
    G_ask_cell_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 106
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_cell_old'):
    G_ask_cell_old = _libs['grass_gis.6.4.2RC2'].G_ask_cell_old
    G_ask_cell_old.restype = ReturnString
    G_ask_cell_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 107
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_cell_in_mapset'):
    G_ask_cell_in_mapset = _libs['grass_gis.6.4.2RC2'].G_ask_cell_in_mapset
    G_ask_cell_in_mapset.restype = ReturnString
    G_ask_cell_in_mapset.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 108
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_cell_any'):
    G_ask_cell_any = _libs['grass_gis.6.4.2RC2'].G_ask_cell_any
    G_ask_cell_any.restype = ReturnString
    G_ask_cell_any.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 111
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_vector_new'):
    G_ask_vector_new = _libs['grass_gis.6.4.2RC2'].G_ask_vector_new
    G_ask_vector_new.restype = ReturnString
    G_ask_vector_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 112
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_vector_old'):
    G_ask_vector_old = _libs['grass_gis.6.4.2RC2'].G_ask_vector_old
    G_ask_vector_old.restype = ReturnString
    G_ask_vector_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 113
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_vector_any'):
    G_ask_vector_any = _libs['grass_gis.6.4.2RC2'].G_ask_vector_any
    G_ask_vector_any.restype = ReturnString
    G_ask_vector_any.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 114
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_vector_in_mapset'):
    G_ask_vector_in_mapset = _libs['grass_gis.6.4.2RC2'].G_ask_vector_in_mapset
    G_ask_vector_in_mapset.restype = ReturnString
    G_ask_vector_in_mapset.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 126
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_vasprintf'):
    G_vasprintf = _libs['grass_gis.6.4.2RC2'].G_vasprintf
    G_vasprintf.restype = c_int
    G_vasprintf.argtypes = [POINTER(POINTER(c_char)), String, c_void_p]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 128
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_asprintf'):
    _func = _libs['grass_gis.6.4.2RC2'].G_asprintf
    _restype = c_int
    _argtypes = [POINTER(POINTER(c_char)), String]
    G_asprintf = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 132
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__check_for_auto_masking'):
    G__check_for_auto_masking = _libs['grass_gis.6.4.2RC2'].G__check_for_auto_masking
    G__check_for_auto_masking.restype = c_int
    G__check_for_auto_masking.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 133
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_suppress_masking'):
    G_suppress_masking = _libs['grass_gis.6.4.2RC2'].G_suppress_masking
    G_suppress_masking.restype = c_int
    G_suppress_masking.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 134
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unsuppress_masking'):
    G_unsuppress_masking = _libs['grass_gis.6.4.2RC2'].G_unsuppress_masking
    G_unsuppress_masking.restype = c_int
    G_unsuppress_masking.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 137
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_basename'):
    G_basename = _libs['grass_gis.6.4.2RC2'].G_basename
    G_basename.restype = ReturnString
    G_basename.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 140
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_bresenham_line'):
    G_bresenham_line = _libs['grass_gis.6.4.2RC2'].G_bresenham_line
    G_bresenham_line.restype = c_int
    G_bresenham_line.argtypes = [c_int, c_int, c_int, c_int, CFUNCTYPE(UNCHECKED(c_int), c_int, c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 143
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_cats'):
    G_read_cats = _libs['grass_gis.6.4.2RC2'].G_read_cats
    G_read_cats.restype = c_int
    G_read_cats.argtypes = [String, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 144
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_raster_cats'):
    G_read_raster_cats = _libs['grass_gis.6.4.2RC2'].G_read_raster_cats
    G_read_raster_cats.restype = c_int
    G_read_raster_cats.argtypes = [String, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 145
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_vector_cats'):
    G_read_vector_cats = _libs['grass_gis.6.4.2RC2'].G_read_vector_cats
    G_read_vector_cats.restype = c_int
    G_read_vector_cats.argtypes = [String, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 146
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_number_of_cats'):
    G_number_of_cats = _libs['grass_gis.6.4.2RC2'].G_number_of_cats
    G_number_of_cats.restype = CELL
    G_number_of_cats.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 147
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_cats'):
    G__read_cats = _libs['grass_gis.6.4.2RC2'].G__read_cats
    G__read_cats.restype = CELL
    G__read_cats.argtypes = [String, String, String, POINTER(struct_Categories), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 149
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_cats_title'):
    G_get_cats_title = _libs['grass_gis.6.4.2RC2'].G_get_cats_title
    G_get_cats_title.restype = ReturnString
    G_get_cats_title.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 150
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_cats_title'):
    G_get_raster_cats_title = _libs['grass_gis.6.4.2RC2'].G_get_raster_cats_title
    G_get_raster_cats_title.restype = ReturnString
    G_get_raster_cats_title.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 151
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_cat'):
    G_get_cat = _libs['grass_gis.6.4.2RC2'].G_get_cat
    G_get_cat.restype = ReturnString
    G_get_cat.argtypes = [CELL, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 152
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_c_raster_cat'):
    G_get_c_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_c_raster_cat
    G_get_c_raster_cat.restype = ReturnString
    G_get_c_raster_cat.argtypes = [POINTER(CELL), POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 153
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_f_raster_cat'):
    G_get_f_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_f_raster_cat
    G_get_f_raster_cat.restype = ReturnString
    G_get_f_raster_cat.argtypes = [POINTER(FCELL), POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 154
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_d_raster_cat'):
    G_get_d_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_d_raster_cat
    G_get_d_raster_cat.restype = ReturnString
    G_get_d_raster_cat.argtypes = [POINTER(DCELL), POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 155
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_cat'):
    G_get_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_raster_cat
    G_get_raster_cat.restype = ReturnString
    G_get_raster_cat.argtypes = [POINTER(None), POINTER(struct_Categories), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 156
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unmark_raster_cats'):
    G_unmark_raster_cats = _libs['grass_gis.6.4.2RC2'].G_unmark_raster_cats
    G_unmark_raster_cats.restype = c_int
    G_unmark_raster_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 157
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mark_c_raster_cats'):
    G_mark_c_raster_cats = _libs['grass_gis.6.4.2RC2'].G_mark_c_raster_cats
    G_mark_c_raster_cats.restype = c_int
    G_mark_c_raster_cats.argtypes = [POINTER(CELL), c_int, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 158
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mark_f_raster_cats'):
    G_mark_f_raster_cats = _libs['grass_gis.6.4.2RC2'].G_mark_f_raster_cats
    G_mark_f_raster_cats.restype = c_int
    G_mark_f_raster_cats.argtypes = [POINTER(FCELL), c_int, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 159
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mark_d_raster_cats'):
    G_mark_d_raster_cats = _libs['grass_gis.6.4.2RC2'].G_mark_d_raster_cats
    G_mark_d_raster_cats.restype = c_int
    G_mark_d_raster_cats.argtypes = [POINTER(DCELL), c_int, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 160
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mark_raster_cats'):
    G_mark_raster_cats = _libs['grass_gis.6.4.2RC2'].G_mark_raster_cats
    G_mark_raster_cats.restype = c_int
    G_mark_raster_cats.argtypes = [POINTER(None), c_int, POINTER(struct_Categories), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 161
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rewind_raster_cats'):
    G_rewind_raster_cats = _libs['grass_gis.6.4.2RC2'].G_rewind_raster_cats
    G_rewind_raster_cats.restype = c_int
    G_rewind_raster_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 162
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_next_marked_d_raster_cat'):
    G_get_next_marked_d_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_next_marked_d_raster_cat
    G_get_next_marked_d_raster_cat.restype = ReturnString
    G_get_next_marked_d_raster_cat.argtypes = [POINTER(struct_Categories), POINTER(DCELL), POINTER(DCELL), POINTER(c_long)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 164
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_next_marked_c_raster_cat'):
    G_get_next_marked_c_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_next_marked_c_raster_cat
    G_get_next_marked_c_raster_cat.restype = ReturnString
    G_get_next_marked_c_raster_cat.argtypes = [POINTER(struct_Categories), POINTER(CELL), POINTER(CELL), POINTER(c_long)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 166
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_next_marked_f_raster_cat'):
    G_get_next_marked_f_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_next_marked_f_raster_cat
    G_get_next_marked_f_raster_cat.restype = ReturnString
    G_get_next_marked_f_raster_cat.argtypes = [POINTER(struct_Categories), POINTER(FCELL), POINTER(FCELL), POINTER(c_long)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 168
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_next_marked_raster_cat'):
    G_get_next_marked_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_next_marked_raster_cat
    G_get_next_marked_raster_cat.restype = ReturnString
    G_get_next_marked_raster_cat.argtypes = [POINTER(struct_Categories), POINTER(None), POINTER(None), POINTER(c_long), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 170
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_cat'):
    G_set_cat = _libs['grass_gis.6.4.2RC2'].G_set_cat
    G_set_cat.restype = c_int
    G_set_cat.argtypes = [CELL, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 171
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_c_raster_cat'):
    G_set_c_raster_cat = _libs['grass_gis.6.4.2RC2'].G_set_c_raster_cat
    G_set_c_raster_cat.restype = c_int
    G_set_c_raster_cat.argtypes = [POINTER(CELL), POINTER(CELL), String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 172
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_f_raster_cat'):
    G_set_f_raster_cat = _libs['grass_gis.6.4.2RC2'].G_set_f_raster_cat
    G_set_f_raster_cat.restype = c_int
    G_set_f_raster_cat.argtypes = [POINTER(FCELL), POINTER(FCELL), String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 173
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_d_raster_cat'):
    G_set_d_raster_cat = _libs['grass_gis.6.4.2RC2'].G_set_d_raster_cat
    G_set_d_raster_cat.restype = c_int
    G_set_d_raster_cat.argtypes = [POINTER(DCELL), POINTER(DCELL), String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 174
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_cat'):
    G_set_raster_cat = _libs['grass_gis.6.4.2RC2'].G_set_raster_cat
    G_set_raster_cat.restype = c_int
    G_set_raster_cat.argtypes = [POINTER(None), POINTER(None), String, POINTER(struct_Categories), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 176
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_cats'):
    G_write_cats = _libs['grass_gis.6.4.2RC2'].G_write_cats
    G_write_cats.restype = c_int
    G_write_cats.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 177
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_raster_cats'):
    G_write_raster_cats = _libs['grass_gis.6.4.2RC2'].G_write_raster_cats
    G_write_raster_cats.restype = c_int
    G_write_raster_cats.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 178
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_vector_cats'):
    G_write_vector_cats = _libs['grass_gis.6.4.2RC2'].G_write_vector_cats
    G_write_vector_cats.restype = c_int
    G_write_vector_cats.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 179
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_cats'):
    G__write_cats = _libs['grass_gis.6.4.2RC2'].G__write_cats
    G__write_cats.restype = c_int
    G__write_cats.argtypes = [String, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 180
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ith_d_raster_cat'):
    G_get_ith_d_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_ith_d_raster_cat
    G_get_ith_d_raster_cat.restype = ReturnString
    G_get_ith_d_raster_cat.argtypes = [POINTER(struct_Categories), c_int, POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 182
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ith_f_raster_cat'):
    G_get_ith_f_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_ith_f_raster_cat
    G_get_ith_f_raster_cat.restype = ReturnString
    G_get_ith_f_raster_cat.argtypes = [POINTER(struct_Categories), c_int, POINTER(None), POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 183
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ith_c_raster_cat'):
    G_get_ith_c_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_ith_c_raster_cat
    G_get_ith_c_raster_cat.restype = ReturnString
    G_get_ith_c_raster_cat.argtypes = [POINTER(struct_Categories), c_int, POINTER(None), POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 184
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ith_raster_cat'):
    G_get_ith_raster_cat = _libs['grass_gis.6.4.2RC2'].G_get_ith_raster_cat
    G_get_ith_raster_cat.restype = ReturnString
    G_get_ith_raster_cat.argtypes = [POINTER(struct_Categories), c_int, POINTER(None), POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 186
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_cats'):
    G_init_cats = _libs['grass_gis.6.4.2RC2'].G_init_cats
    G_init_cats.restype = c_int
    G_init_cats.argtypes = [CELL, String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 187
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_raster_cats'):
    G_init_raster_cats = _libs['grass_gis.6.4.2RC2'].G_init_raster_cats
    G_init_raster_cats.restype = c_int
    G_init_raster_cats.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 188
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_cats_title'):
    G_set_cats_title = _libs['grass_gis.6.4.2RC2'].G_set_cats_title
    G_set_cats_title.restype = c_int
    G_set_cats_title.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 189
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_cats_title'):
    G_set_raster_cats_title = _libs['grass_gis.6.4.2RC2'].G_set_raster_cats_title
    G_set_raster_cats_title.restype = c_int
    G_set_raster_cats_title.argtypes = [String, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 190
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_cats_fmt'):
    G_set_cats_fmt = _libs['grass_gis.6.4.2RC2'].G_set_cats_fmt
    G_set_cats_fmt.restype = c_int
    G_set_cats_fmt.argtypes = [String, c_double, c_double, c_double, c_double, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 192
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_cats_fmt'):
    G_set_raster_cats_fmt = _libs['grass_gis.6.4.2RC2'].G_set_raster_cats_fmt
    G_set_raster_cats_fmt.restype = c_int
    G_set_raster_cats_fmt.argtypes = [String, c_double, c_double, c_double, c_double, POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 194
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_cats'):
    G_free_cats = _libs['grass_gis.6.4.2RC2'].G_free_cats
    G_free_cats.restype = c_int
    G_free_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 195
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_raster_cats'):
    G_free_raster_cats = _libs['grass_gis.6.4.2RC2'].G_free_raster_cats
    G_free_raster_cats.restype = c_int
    G_free_raster_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 196
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_copy_raster_cats'):
    G_copy_raster_cats = _libs['grass_gis.6.4.2RC2'].G_copy_raster_cats
    G_copy_raster_cats.restype = c_int
    G_copy_raster_cats.argtypes = [POINTER(struct_Categories), POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 197
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_number_of_raster_cats'):
    G_number_of_raster_cats = _libs['grass_gis.6.4.2RC2'].G_number_of_raster_cats
    G_number_of_raster_cats.restype = c_int
    G_number_of_raster_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 198
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_sort_cats'):
    G_sort_cats = _libs['grass_gis.6.4.2RC2'].G_sort_cats
    G_sort_cats.restype = c_int
    G_sort_cats.argtypes = [POINTER(struct_Categories)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 201
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_cell_stats'):
    G_init_cell_stats = _libs['grass_gis.6.4.2RC2'].G_init_cell_stats
    G_init_cell_stats.restype = c_int
    G_init_cell_stats.argtypes = [POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 202
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_update_cell_stats'):
    G_update_cell_stats = _libs['grass_gis.6.4.2RC2'].G_update_cell_stats
    G_update_cell_stats.restype = c_int
    G_update_cell_stats.argtypes = [POINTER(CELL), c_int, POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 203
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_cell_stat'):
    G_find_cell_stat = _libs['grass_gis.6.4.2RC2'].G_find_cell_stat
    G_find_cell_stat.restype = c_int
    G_find_cell_stat.argtypes = [CELL, POINTER(c_long), POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 204
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rewind_cell_stats'):
    G_rewind_cell_stats = _libs['grass_gis.6.4.2RC2'].G_rewind_cell_stats
    G_rewind_cell_stats.restype = c_int
    G_rewind_cell_stats.argtypes = [POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 205
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_next_cell_stat'):
    G_next_cell_stat = _libs['grass_gis.6.4.2RC2'].G_next_cell_stat
    G_next_cell_stat.restype = c_int
    G_next_cell_stat.argtypes = [POINTER(CELL), POINTER(c_long), POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 206
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_stats_for_null_value'):
    G_get_stats_for_null_value = _libs['grass_gis.6.4.2RC2'].G_get_stats_for_null_value
    G_get_stats_for_null_value.restype = c_int
    G_get_stats_for_null_value.argtypes = [POINTER(c_long), POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 207
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_cell_stats'):
    G_free_cell_stats = _libs['grass_gis.6.4.2RC2'].G_free_cell_stats
    G_free_cell_stats.restype = c_int
    G_free_cell_stats.argtypes = [POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 210
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_cell_title'):
    G_get_cell_title = _libs['grass_gis.6.4.2RC2'].G_get_cell_title
    G_get_cell_title.restype = ReturnString
    G_get_cell_title.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 213
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_cell_stats_histo_eq'):
    G_cell_stats_histo_eq = _libs['grass_gis.6.4.2RC2'].G_cell_stats_histo_eq
    G_cell_stats_histo_eq.restype = c_int
    G_cell_stats_histo_eq.argtypes = [POINTER(struct_Cell_stats), CELL, CELL, CELL, CELL, c_int, CFUNCTYPE(UNCHECKED(None), CELL, CELL, CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 217
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_chop'):
    G_chop = _libs['grass_gis.6.4.2RC2'].G_chop
    G_chop.restype = ReturnString
    G_chop.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 220
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_clear_screen'):
    G_clear_screen = _libs['grass_gis.6.4.2RC2'].G_clear_screen
    G_clear_screen.restype = c_int
    G_clear_screen.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 223
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_clicker'):
    G_clicker = _libs['grass_gis.6.4.2RC2'].G_clicker
    G_clicker.restype = c_int
    G_clicker.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 226
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_close_cell'):
    G_close_cell = _libs['grass_gis.6.4.2RC2'].G_close_cell
    G_close_cell.restype = c_int
    G_close_cell.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 227
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unopen_cell'):
    G_unopen_cell = _libs['grass_gis.6.4.2RC2'].G_unopen_cell
    G_unopen_cell.restype = c_int
    G_unopen_cell.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 228
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_fp_format'):
    G__write_fp_format = _libs['grass_gis.6.4.2RC2'].G__write_fp_format
    G__write_fp_format.restype = c_int
    G__write_fp_format.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 231
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_ryg_colors'):
    G_make_ryg_colors = _libs['grass_gis.6.4.2RC2'].G_make_ryg_colors
    G_make_ryg_colors.restype = c_int
    G_make_ryg_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 232
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_ryg_fp_colors'):
    G_make_ryg_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_ryg_fp_colors
    G_make_ryg_fp_colors.restype = c_int
    G_make_ryg_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 233
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_aspect_colors'):
    G_make_aspect_colors = _libs['grass_gis.6.4.2RC2'].G_make_aspect_colors
    G_make_aspect_colors.restype = c_int
    G_make_aspect_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 234
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_aspect_fp_colors'):
    G_make_aspect_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_aspect_fp_colors
    G_make_aspect_fp_colors.restype = c_int
    G_make_aspect_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 235
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_byr_colors'):
    G_make_byr_colors = _libs['grass_gis.6.4.2RC2'].G_make_byr_colors
    G_make_byr_colors.restype = c_int
    G_make_byr_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 236
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_byr_fp_colors'):
    G_make_byr_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_byr_fp_colors
    G_make_byr_fp_colors.restype = c_int
    G_make_byr_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 237
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_bgyr_colors'):
    G_make_bgyr_colors = _libs['grass_gis.6.4.2RC2'].G_make_bgyr_colors
    G_make_bgyr_colors.restype = c_int
    G_make_bgyr_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 238
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_bgyr_fp_colors'):
    G_make_bgyr_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_bgyr_fp_colors
    G_make_bgyr_fp_colors.restype = c_int
    G_make_bgyr_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 239
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_byg_colors'):
    G_make_byg_colors = _libs['grass_gis.6.4.2RC2'].G_make_byg_colors
    G_make_byg_colors.restype = c_int
    G_make_byg_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 240
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_byg_fp_colors'):
    G_make_byg_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_byg_fp_colors
    G_make_byg_fp_colors.restype = c_int
    G_make_byg_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 241
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_grey_scale_colors'):
    G_make_grey_scale_colors = _libs['grass_gis.6.4.2RC2'].G_make_grey_scale_colors
    G_make_grey_scale_colors.restype = c_int
    G_make_grey_scale_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 242
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_grey_scale_fp_colors'):
    G_make_grey_scale_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_grey_scale_fp_colors
    G_make_grey_scale_fp_colors.restype = c_int
    G_make_grey_scale_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 243
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_gyr_colors'):
    G_make_gyr_colors = _libs['grass_gis.6.4.2RC2'].G_make_gyr_colors
    G_make_gyr_colors.restype = c_int
    G_make_gyr_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 244
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_gyr_fp_colors'):
    G_make_gyr_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_gyr_fp_colors
    G_make_gyr_fp_colors.restype = c_int
    G_make_gyr_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 245
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_rainbow_colors'):
    G_make_rainbow_colors = _libs['grass_gis.6.4.2RC2'].G_make_rainbow_colors
    G_make_rainbow_colors.restype = c_int
    G_make_rainbow_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 246
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_rainbow_fp_colors'):
    G_make_rainbow_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_rainbow_fp_colors
    G_make_rainbow_fp_colors.restype = c_int
    G_make_rainbow_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 247
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_ramp_colors'):
    G_make_ramp_colors = _libs['grass_gis.6.4.2RC2'].G_make_ramp_colors
    G_make_ramp_colors.restype = c_int
    G_make_ramp_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 248
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_ramp_fp_colors'):
    G_make_ramp_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_ramp_fp_colors
    G_make_ramp_fp_colors.restype = c_int
    G_make_ramp_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 249
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_wave_colors'):
    G_make_wave_colors = _libs['grass_gis.6.4.2RC2'].G_make_wave_colors
    G_make_wave_colors.restype = c_int
    G_make_wave_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 250
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_wave_fp_colors'):
    G_make_wave_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_wave_fp_colors
    G_make_wave_fp_colors.restype = c_int
    G_make_wave_fp_colors.argtypes = [POINTER(struct_Colors), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 253
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_colors'):
    G_free_colors = _libs['grass_gis.6.4.2RC2'].G_free_colors
    G_free_colors.restype = c_int
    G_free_colors.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 254
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__color_free_rules'):
    G__color_free_rules = _libs['grass_gis.6.4.2RC2'].G__color_free_rules
    G__color_free_rules.restype = c_int
    G__color_free_rules.argtypes = [POINTER(struct__Color_Info_)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 255
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__color_free_lookup'):
    G__color_free_lookup = _libs['grass_gis.6.4.2RC2'].G__color_free_lookup
    G__color_free_lookup.restype = c_int
    G__color_free_lookup.argtypes = [POINTER(struct__Color_Info_)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 256
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__color_free_fp_lookup'):
    G__color_free_fp_lookup = _libs['grass_gis.6.4.2RC2'].G__color_free_fp_lookup
    G__color_free_fp_lookup.restype = c_int
    G__color_free_fp_lookup.argtypes = [POINTER(struct__Color_Info_)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 257
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__color_reset'):
    G__color_reset = _libs['grass_gis.6.4.2RC2'].G__color_reset
    G__color_reset.restype = c_int
    G__color_reset.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 260
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_color'):
    G_get_color = _libs['grass_gis.6.4.2RC2'].G_get_color
    G_get_color.restype = c_int
    G_get_color.argtypes = [CELL, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 261
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_color'):
    G_get_raster_color = _libs['grass_gis.6.4.2RC2'].G_get_raster_color
    G_get_raster_color.restype = c_int
    G_get_raster_color.argtypes = [POINTER(None), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 263
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_c_raster_color'):
    G_get_c_raster_color = _libs['grass_gis.6.4.2RC2'].G_get_c_raster_color
    G_get_c_raster_color.restype = c_int
    G_get_c_raster_color.argtypes = [POINTER(CELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 264
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_f_raster_color'):
    G_get_f_raster_color = _libs['grass_gis.6.4.2RC2'].G_get_f_raster_color
    G_get_f_raster_color.restype = c_int
    G_get_f_raster_color.argtypes = [POINTER(FCELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 265
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_d_raster_color'):
    G_get_d_raster_color = _libs['grass_gis.6.4.2RC2'].G_get_d_raster_color
    G_get_d_raster_color.restype = c_int
    G_get_d_raster_color.argtypes = [POINTER(DCELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 266
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_null_value_color'):
    G_get_null_value_color = _libs['grass_gis.6.4.2RC2'].G_get_null_value_color
    G_get_null_value_color.restype = c_int
    G_get_null_value_color.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 267
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_default_color'):
    G_get_default_color = _libs['grass_gis.6.4.2RC2'].G_get_default_color
    G_get_default_color.restype = c_int
    G_get_default_color.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 270
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_histogram_eq_colors'):
    G_make_histogram_eq_colors = _libs['grass_gis.6.4.2RC2'].G_make_histogram_eq_colors
    G_make_histogram_eq_colors.restype = c_int
    G_make_histogram_eq_colors.argtypes = [POINTER(struct_Colors), POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 271
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_histogram_log_colors'):
    G_make_histogram_log_colors = _libs['grass_gis.6.4.2RC2'].G_make_histogram_log_colors
    G_make_histogram_log_colors.restype = c_int
    G_make_histogram_log_colors.argtypes = [POINTER(struct_Colors), POINTER(struct_Cell_stats), c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 275
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_colors'):
    G_init_colors = _libs['grass_gis.6.4.2RC2'].G_init_colors
    G_init_colors.restype = c_int
    G_init_colors.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 278
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__insert_color_into_lookup'):
    G__insert_color_into_lookup = _libs['grass_gis.6.4.2RC2'].G__insert_color_into_lookup
    G__insert_color_into_lookup.restype = c_int
    G__insert_color_into_lookup.argtypes = [CELL, c_int, c_int, c_int, POINTER(struct__Color_Info_)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 281
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_invert_colors'):
    G_invert_colors = _libs['grass_gis.6.4.2RC2'].G_invert_colors
    G_invert_colors.restype = c_int
    G_invert_colors.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 284
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_colors'):
    G_lookup_colors = _libs['grass_gis.6.4.2RC2'].G_lookup_colors
    G_lookup_colors.restype = c_int
    G_lookup_colors.argtypes = [POINTER(CELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 286
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_c_raster_colors'):
    G_lookup_c_raster_colors = _libs['grass_gis.6.4.2RC2'].G_lookup_c_raster_colors
    G_lookup_c_raster_colors.restype = c_int
    G_lookup_c_raster_colors.argtypes = [POINTER(CELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 289
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_raster_colors'):
    G_lookup_raster_colors = _libs['grass_gis.6.4.2RC2'].G_lookup_raster_colors
    G_lookup_raster_colors.restype = c_int
    G_lookup_raster_colors.argtypes = [POINTER(None), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 292
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_f_raster_colors'):
    G_lookup_f_raster_colors = _libs['grass_gis.6.4.2RC2'].G_lookup_f_raster_colors
    G_lookup_f_raster_colors.restype = c_int
    G_lookup_f_raster_colors.argtypes = [POINTER(FCELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 295
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_d_raster_colors'):
    G_lookup_d_raster_colors = _libs['grass_gis.6.4.2RC2'].G_lookup_d_raster_colors
    G_lookup_d_raster_colors.restype = c_int
    G_lookup_d_raster_colors.argtypes = [POINTER(DCELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 298
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__lookup_colors'):
    G__lookup_colors = _libs['grass_gis.6.4.2RC2'].G__lookup_colors
    G__lookup_colors.restype = c_int
    G__lookup_colors.argtypes = [POINTER(None), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), c_int, POINTER(struct_Colors), c_int, c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 301
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__interpolate_color_rule'):
    G__interpolate_color_rule = _libs['grass_gis.6.4.2RC2'].G__interpolate_color_rule
    G__interpolate_color_rule.restype = c_int
    G__interpolate_color_rule.argtypes = [DCELL, POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(struct__Color_Rule_)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 305
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__organize_colors'):
    G__organize_colors = _libs['grass_gis.6.4.2RC2'].G__organize_colors
    G__organize_colors.restype = c_int
    G__organize_colors.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 308
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_random_colors'):
    G_make_random_colors = _libs['grass_gis.6.4.2RC2'].G_make_random_colors
    G_make_random_colors.restype = c_int
    G_make_random_colors.argtypes = [POINTER(struct_Colors), CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 311
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_color_range'):
    G_set_color_range = _libs['grass_gis.6.4.2RC2'].G_set_color_range
    G_set_color_range.restype = c_int
    G_set_color_range.argtypes = [CELL, CELL, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 312
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_d_color_range'):
    G_set_d_color_range = _libs['grass_gis.6.4.2RC2'].G_set_d_color_range
    G_set_d_color_range.restype = c_int
    G_set_d_color_range.argtypes = [DCELL, DCELL, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 313
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_color_range'):
    G_get_color_range = _libs['grass_gis.6.4.2RC2'].G_get_color_range
    G_get_color_range.restype = c_int
    G_get_color_range.argtypes = [POINTER(CELL), POINTER(CELL), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 314
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_d_color_range'):
    G_get_d_color_range = _libs['grass_gis.6.4.2RC2'].G_get_d_color_range
    G_get_d_color_range.restype = c_int
    G_get_d_color_range.argtypes = [POINTER(DCELL), POINTER(DCELL), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 317
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_colors'):
    G_read_colors = _libs['grass_gis.6.4.2RC2'].G_read_colors
    G_read_colors.restype = c_int
    G_read_colors.argtypes = [String, String, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 318
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mark_colors_as_fp'):
    G_mark_colors_as_fp = _libs['grass_gis.6.4.2RC2'].G_mark_colors_as_fp
    G_mark_colors_as_fp.restype = c_int
    G_mark_colors_as_fp.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 321
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_colors'):
    G_remove_colors = _libs['grass_gis.6.4.2RC2'].G_remove_colors
    G_remove_colors.restype = c_int
    G_remove_colors.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 324
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_d_raster_color_rule'):
    G_add_d_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_d_raster_color_rule
    G_add_d_raster_color_rule.restype = c_int
    G_add_d_raster_color_rule.argtypes = [POINTER(DCELL), c_int, c_int, c_int, POINTER(DCELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 326
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_f_raster_color_rule'):
    G_add_f_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_f_raster_color_rule
    G_add_f_raster_color_rule.restype = c_int
    G_add_f_raster_color_rule.argtypes = [POINTER(FCELL), c_int, c_int, c_int, POINTER(FCELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 328
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_c_raster_color_rule'):
    G_add_c_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_c_raster_color_rule
    G_add_c_raster_color_rule.restype = c_int
    G_add_c_raster_color_rule.argtypes = [POINTER(CELL), c_int, c_int, c_int, POINTER(CELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 330
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_raster_color_rule'):
    G_add_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_raster_color_rule
    G_add_raster_color_rule.restype = c_int
    G_add_raster_color_rule.argtypes = [POINTER(None), c_int, c_int, c_int, POINTER(None), c_int, c_int, c_int, POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 332
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_color_rule'):
    G_add_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_color_rule
    G_add_color_rule.restype = c_int
    G_add_color_rule.argtypes = [CELL, c_int, c_int, c_int, CELL, c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 334
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_modular_d_raster_color_rule'):
    G_add_modular_d_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_modular_d_raster_color_rule
    G_add_modular_d_raster_color_rule.restype = c_int
    G_add_modular_d_raster_color_rule.argtypes = [POINTER(DCELL), c_int, c_int, c_int, POINTER(DCELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 337
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_modular_f_raster_color_rule'):
    G_add_modular_f_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_modular_f_raster_color_rule
    G_add_modular_f_raster_color_rule.restype = c_int
    G_add_modular_f_raster_color_rule.argtypes = [POINTER(FCELL), c_int, c_int, c_int, POINTER(FCELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 340
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_modular_c_raster_color_rule'):
    G_add_modular_c_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_modular_c_raster_color_rule
    G_add_modular_c_raster_color_rule.restype = c_int
    G_add_modular_c_raster_color_rule.argtypes = [POINTER(CELL), c_int, c_int, c_int, POINTER(CELL), c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 343
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_modular_raster_color_rule'):
    G_add_modular_raster_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_modular_raster_color_rule
    G_add_modular_raster_color_rule.restype = c_int
    G_add_modular_raster_color_rule.argtypes = [POINTER(None), c_int, c_int, c_int, POINTER(None), c_int, c_int, c_int, POINTER(struct_Colors), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 346
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_modular_color_rule'):
    G_add_modular_color_rule = _libs['grass_gis.6.4.2RC2'].G_add_modular_color_rule
    G_add_modular_color_rule.restype = c_int
    G_add_modular_color_rule.argtypes = [CELL, c_int, c_int, c_int, CELL, c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 350
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_colors_count'):
    G_colors_count = _libs['grass_gis.6.4.2RC2'].G_colors_count
    G_colors_count.restype = c_int
    G_colors_count.argtypes = [POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 351
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_f_color_rule'):
    G_get_f_color_rule = _libs['grass_gis.6.4.2RC2'].G_get_f_color_rule
    G_get_f_color_rule.restype = c_int
    G_get_f_color_rule.argtypes = [POINTER(DCELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(DCELL), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(struct_Colors), c_int]

read_rule_fn = CFUNCTYPE(UNCHECKED(c_int), POINTER(None), DCELL, DCELL, POINTER(DCELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)) # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 357

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 359
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_parse_color_rule'):
    G_parse_color_rule = _libs['grass_gis.6.4.2RC2'].G_parse_color_rule
    G_parse_color_rule.restype = c_int
    G_parse_color_rule.argtypes = [DCELL, DCELL, String, POINTER(DCELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 361
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_parse_color_rule_error'):
    G_parse_color_rule_error = _libs['grass_gis.6.4.2RC2'].G_parse_color_rule_error
    G_parse_color_rule_error.restype = ReturnString
    G_parse_color_rule_error.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 362
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_color_rule'):
    G_read_color_rule = _libs['grass_gis.6.4.2RC2'].G_read_color_rule
    G_read_color_rule.restype = c_int
    G_read_color_rule.argtypes = [POINTER(None), DCELL, DCELL, POINTER(DCELL), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 364
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_color_rules'):
    G_read_color_rules = _libs['grass_gis.6.4.2RC2'].G_read_color_rules
    G_read_color_rules.restype = c_int
    G_read_color_rules.argtypes = [POINTER(struct_Colors), DCELL, DCELL, POINTER(read_rule_fn), POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 365
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_load_colors'):
    G_load_colors = _libs['grass_gis.6.4.2RC2'].G_load_colors
    G_load_colors.restype = c_int
    G_load_colors.argtypes = [POINTER(struct_Colors), String, CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 366
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_load_fp_colors'):
    G_load_fp_colors = _libs['grass_gis.6.4.2RC2'].G_load_fp_colors
    G_load_fp_colors.restype = c_int
    G_load_fp_colors.argtypes = [POINTER(struct_Colors), String, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 367
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_colors'):
    G_make_colors = _libs['grass_gis.6.4.2RC2'].G_make_colors
    G_make_colors.restype = c_int
    G_make_colors.argtypes = [POINTER(struct_Colors), String, CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 368
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_fp_colors'):
    G_make_fp_colors = _libs['grass_gis.6.4.2RC2'].G_make_fp_colors
    G_make_fp_colors.restype = c_int
    G_make_fp_colors.argtypes = [POINTER(struct_Colors), String, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 371
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_color'):
    G_set_color = _libs['grass_gis.6.4.2RC2'].G_set_color
    G_set_color.restype = c_int
    G_set_color.argtypes = [CELL, c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 372
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_d_color'):
    G_set_d_color = _libs['grass_gis.6.4.2RC2'].G_set_d_color
    G_set_d_color.restype = c_int
    G_set_d_color.argtypes = [DCELL, c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 373
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_null_value_color'):
    G_set_null_value_color = _libs['grass_gis.6.4.2RC2'].G_set_null_value_color
    G_set_null_value_color.restype = c_int
    G_set_null_value_color.argtypes = [c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 374
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_default_color'):
    G_set_default_color = _libs['grass_gis.6.4.2RC2'].G_set_default_color
    G_set_default_color.restype = c_int
    G_set_default_color.argtypes = [c_int, c_int, c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 377
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_shift_colors'):
    G_shift_colors = _libs['grass_gis.6.4.2RC2'].G_shift_colors
    G_shift_colors.restype = c_int
    G_shift_colors.argtypes = [c_int, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 378
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_shift_d_colors'):
    G_shift_d_colors = _libs['grass_gis.6.4.2RC2'].G_shift_d_colors
    G_shift_d_colors.restype = c_int
    G_shift_d_colors.argtypes = [DCELL, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 381
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_str_to_color'):
    G_str_to_color = _libs['grass_gis.6.4.2RC2'].G_str_to_color
    G_str_to_color.restype = c_int
    G_str_to_color.argtypes = [String, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 384
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_colors'):
    G_write_colors = _libs['grass_gis.6.4.2RC2'].G_write_colors
    G_write_colors.restype = c_int
    G_write_colors.argtypes = [String, String, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 385
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_colors'):
    G__write_colors = _libs['grass_gis.6.4.2RC2'].G__write_colors
    G__write_colors.restype = c_int
    G__write_colors.argtypes = [POINTER(FILE), POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 388
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_histogram_eq_colors'):
    G_histogram_eq_colors = _libs['grass_gis.6.4.2RC2'].G_histogram_eq_colors
    G_histogram_eq_colors.restype = c_int
    G_histogram_eq_colors.argtypes = [POINTER(struct_Colors), POINTER(struct_Colors), POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 390
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_histogram_eq_colors_fp'):
    G_histogram_eq_colors_fp = _libs['grass_gis.6.4.2RC2'].G_histogram_eq_colors_fp
    G_histogram_eq_colors_fp.restype = None
    G_histogram_eq_colors_fp.argtypes = [POINTER(struct_Colors), POINTER(struct_Colors), POINTER(struct_FP_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 392
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_log_colors'):
    G_log_colors = _libs['grass_gis.6.4.2RC2'].G_log_colors
    G_log_colors.restype = c_int
    G_log_colors.argtypes = [POINTER(struct_Colors), POINTER(struct_Colors), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 393
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_abs_log_colors'):
    G_abs_log_colors = _libs['grass_gis.6.4.2RC2'].G_abs_log_colors
    G_abs_log_colors.restype = c_int
    G_abs_log_colors.argtypes = [POINTER(struct_Colors), POINTER(struct_Colors), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 396
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_insert_commas'):
    G_insert_commas = _libs['grass_gis.6.4.2RC2'].G_insert_commas
    G_insert_commas.restype = c_int
    G_insert_commas.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 397
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_commas'):
    G_remove_commas = _libs['grass_gis.6.4.2RC2'].G_remove_commas
    G_remove_commas.restype = c_int
    G_remove_commas.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 400
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_copy'):
    G_copy = _libs['grass_gis.6.4.2RC2'].G_copy
    G_copy.restype = c_int
    G_copy.argtypes = [POINTER(None), POINTER(None), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 403
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_copy_file'):
    G_copy_file = _libs['grass_gis.6.4.2RC2'].G_copy_file
    G_copy_file.restype = c_int
    G_copy_file.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 404
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_recursive_copy'):
    G_recursive_copy = _libs['grass_gis.6.4.2RC2'].G_recursive_copy
    G_recursive_copy.restype = c_int
    G_recursive_copy.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 407
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_date'):
    G_date = _libs['grass_gis.6.4.2RC2'].G_date
    G_date.restype = ReturnString
    G_date.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 410
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_datum_by_name'):
    G_get_datum_by_name = _libs['grass_gis.6.4.2RC2'].G_get_datum_by_name
    G_get_datum_by_name.restype = c_int
    G_get_datum_by_name.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 411
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_datum_name'):
    G_datum_name = _libs['grass_gis.6.4.2RC2'].G_datum_name
    G_datum_name.restype = ReturnString
    G_datum_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 412
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_datum_description'):
    G_datum_description = _libs['grass_gis.6.4.2RC2'].G_datum_description
    G_datum_description.restype = ReturnString
    G_datum_description.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 413
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_datum_ellipsoid'):
    G_datum_ellipsoid = _libs['grass_gis.6.4.2RC2'].G_datum_ellipsoid
    G_datum_ellipsoid.restype = ReturnString
    G_datum_ellipsoid.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 414
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_datumparams_from_projinfo'):
    G_get_datumparams_from_projinfo = _libs['grass_gis.6.4.2RC2'].G_get_datumparams_from_projinfo
    G_get_datumparams_from_projinfo.restype = c_int
    G_get_datumparams_from_projinfo.argtypes = [POINTER(struct_Key_Value), String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 418
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_debug'):
    _func = _libs['grass_gis.6.4.2RC2'].G_debug
    _restype = c_int
    _argtypes = [c_int, String]
    G_debug = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 421
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_distance_calculations'):
    G_begin_distance_calculations = _libs['grass_gis.6.4.2RC2'].G_begin_distance_calculations
    G_begin_distance_calculations.restype = c_int
    G_begin_distance_calculations.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 422
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_distance'):
    G_distance = _libs['grass_gis.6.4.2RC2'].G_distance
    G_distance.restype = c_double
    G_distance.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 423
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_distance_between_line_segments'):
    G_distance_between_line_segments = _libs['grass_gis.6.4.2RC2'].G_distance_between_line_segments
    G_distance_between_line_segments.restype = c_double
    G_distance_between_line_segments.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 425
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_distance_point_to_line_segment'):
    G_distance_point_to_line_segment = _libs['grass_gis.6.4.2RC2'].G_distance_point_to_line_segment
    G_distance_point_to_line_segment.restype = c_double
    G_distance_point_to_line_segment.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 429
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_done_msg'):
    _func = _libs['grass_gis.6.4.2RC2'].G_done_msg
    _restype = c_int
    _argtypes = [String]
    G_done_msg = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 432
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_little_endian'):
    G_is_little_endian = _libs['grass_gis.6.4.2RC2'].G_is_little_endian
    G_is_little_endian.restype = c_int
    G_is_little_endian.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 435
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_getenv'):
    G_getenv = _libs['grass_gis.6.4.2RC2'].G_getenv
    G_getenv.restype = ReturnString
    G_getenv.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 436
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_getenv2'):
    G_getenv2 = _libs['grass_gis.6.4.2RC2'].G_getenv2
    G_getenv2.restype = ReturnString
    G_getenv2.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 437
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__getenv'):
    G__getenv = _libs['grass_gis.6.4.2RC2'].G__getenv
    G__getenv.restype = ReturnString
    G__getenv.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 438
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__getenv2'):
    G__getenv2 = _libs['grass_gis.6.4.2RC2'].G__getenv2
    G__getenv2.restype = ReturnString
    G__getenv2.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 439
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_setenv'):
    G_setenv = _libs['grass_gis.6.4.2RC2'].G_setenv
    G_setenv.restype = c_int
    G_setenv.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 440
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_setenv2'):
    G_setenv2 = _libs['grass_gis.6.4.2RC2'].G_setenv2
    G_setenv2.restype = c_int
    G_setenv2.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 441
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__setenv'):
    G__setenv = _libs['grass_gis.6.4.2RC2'].G__setenv
    G__setenv.restype = c_int
    G__setenv.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 442
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__setenv2'):
    G__setenv2 = _libs['grass_gis.6.4.2RC2'].G__setenv2
    G__setenv2.restype = c_int
    G__setenv2.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 443
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unsetenv'):
    G_unsetenv = _libs['grass_gis.6.4.2RC2'].G_unsetenv
    G_unsetenv.restype = c_int
    G_unsetenv.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 444
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unsetenv2'):
    G_unsetenv2 = _libs['grass_gis.6.4.2RC2'].G_unsetenv2
    G_unsetenv2.restype = c_int
    G_unsetenv2.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 445
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_env'):
    G__write_env = _libs['grass_gis.6.4.2RC2'].G__write_env
    G__write_env.restype = c_int
    G__write_env.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 446
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__env_name'):
    G__env_name = _libs['grass_gis.6.4.2RC2'].G__env_name
    G__env_name.restype = ReturnString
    G__env_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 447
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_env'):
    G__read_env = _libs['grass_gis.6.4.2RC2'].G__read_env
    G__read_env.restype = c_int
    G__read_env.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 448
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_gisrc_mode'):
    G_set_gisrc_mode = _libs['grass_gis.6.4.2RC2'].G_set_gisrc_mode
    G_set_gisrc_mode.restype = None
    G_set_gisrc_mode.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 449
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_gisrc_mode'):
    G_get_gisrc_mode = _libs['grass_gis.6.4.2RC2'].G_get_gisrc_mode
    G_get_gisrc_mode.restype = c_int
    G_get_gisrc_mode.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 450
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__set_gisrc_file'):
    G__set_gisrc_file = _libs['grass_gis.6.4.2RC2'].G__set_gisrc_file
    G__set_gisrc_file.restype = c_int
    G__set_gisrc_file.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 451
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__get_gisrc_file'):
    G__get_gisrc_file = _libs['grass_gis.6.4.2RC2'].G__get_gisrc_file
    G__get_gisrc_file.restype = ReturnString
    G__get_gisrc_file.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 452
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__create_alt_env'):
    G__create_alt_env = _libs['grass_gis.6.4.2RC2'].G__create_alt_env
    G__create_alt_env.restype = c_int
    G__create_alt_env.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 453
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__switch_env'):
    G__switch_env = _libs['grass_gis.6.4.2RC2'].G__switch_env
    G__switch_env.restype = c_int
    G__switch_env.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 456
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_info_format'):
    G_info_format = _libs['grass_gis.6.4.2RC2'].G_info_format
    G_info_format.restype = c_int
    G_info_format.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 457
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_message'):
    _func = _libs['grass_gis.6.4.2RC2'].G_message
    _restype = None
    _argtypes = [String]
    G_message = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 458
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_verbose_message'):
    _func = _libs['grass_gis.6.4.2RC2'].G_verbose_message
    _restype = None
    _argtypes = [String]
    G_verbose_message = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 460
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_important_message'):
    _func = _libs['grass_gis.6.4.2RC2'].G_important_message
    _restype = None
    _argtypes = [String]
    G_important_message = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 462
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fatal_error'):
    _func = _libs['grass_gis.6.4.2RC2'].G_fatal_error
    _restype = c_int
    _argtypes = [String]
    G_fatal_error = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 464
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_warning'):
    _func = _libs['grass_gis.6.4.2RC2'].G_warning
    _restype = c_int
    _argtypes = [String]
    G_warning = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 465
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_suppress_warnings'):
    G_suppress_warnings = _libs['grass_gis.6.4.2RC2'].G_suppress_warnings
    G_suppress_warnings.restype = c_int
    G_suppress_warnings.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 466
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_sleep_on_error'):
    G_sleep_on_error = _libs['grass_gis.6.4.2RC2'].G_sleep_on_error
    G_sleep_on_error.restype = c_int
    G_sleep_on_error.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 467
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_error_routine'):
    G_set_error_routine = _libs['grass_gis.6.4.2RC2'].G_set_error_routine
    G_set_error_routine.restype = c_int
    G_set_error_routine.argtypes = [CFUNCTYPE(UNCHECKED(c_int), String, c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 468
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unset_error_routine'):
    G_unset_error_routine = _libs['grass_gis.6.4.2RC2'].G_unset_error_routine
    G_unset_error_routine.restype = c_int
    G_unset_error_routine.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 471
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__file_name'):
    G__file_name = _libs['grass_gis.6.4.2RC2'].G__file_name
    G__file_name.restype = ReturnString
    G__file_name.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 472
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__file_name_misc'):
    G__file_name_misc = _libs['grass_gis.6.4.2RC2'].G__file_name_misc
    G__file_name_misc.restype = ReturnString
    G__file_name_misc.argtypes = [String, String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 476
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_cell'):
    G_find_cell = _libs['grass_gis.6.4.2RC2'].G_find_cell
    G_find_cell.restype = ReturnString
    G_find_cell.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 477
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_cell2'):
    G_find_cell2 = _libs['grass_gis.6.4.2RC2'].G_find_cell2
    G_find_cell2.restype = ReturnString
    G_find_cell2.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 480
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_file'):
    G_find_file = _libs['grass_gis.6.4.2RC2'].G_find_file
    G_find_file.restype = ReturnString
    G_find_file.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 481
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_file2'):
    G_find_file2 = _libs['grass_gis.6.4.2RC2'].G_find_file2
    G_find_file2.restype = ReturnString
    G_find_file2.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 482
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_file_misc'):
    G_find_file_misc = _libs['grass_gis.6.4.2RC2'].G_find_file_misc
    G_find_file_misc.restype = ReturnString
    G_find_file_misc.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 483
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_file2_misc'):
    G_find_file2_misc = _libs['grass_gis.6.4.2RC2'].G_find_file2_misc
    G_find_file2_misc.restype = ReturnString
    G_find_file2_misc.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 487
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_etc'):
    G_find_etc = _libs['grass_gis.6.4.2RC2'].G_find_etc
    G_find_etc.restype = ReturnString
    G_find_etc.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 490
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_vector'):
    G_find_vector = _libs['grass_gis.6.4.2RC2'].G_find_vector
    G_find_vector.restype = ReturnString
    G_find_vector.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 491
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_vector2'):
    G_find_vector2 = _libs['grass_gis.6.4.2RC2'].G_find_vector2
    G_find_vector2.restype = ReturnString
    G_find_vector2.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 494
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zlib_compress'):
    G_zlib_compress = _libs['grass_gis.6.4.2RC2'].G_zlib_compress
    G_zlib_compress.restype = c_int
    G_zlib_compress.argtypes = [POINTER(c_ubyte), c_int, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 495
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zlib_expand'):
    G_zlib_expand = _libs['grass_gis.6.4.2RC2'].G_zlib_expand
    G_zlib_expand.restype = c_int
    G_zlib_expand.argtypes = [POINTER(c_ubyte), c_int, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 496
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zlib_write'):
    G_zlib_write = _libs['grass_gis.6.4.2RC2'].G_zlib_write
    G_zlib_write.restype = c_int
    G_zlib_write.argtypes = [c_int, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 497
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zlib_read'):
    G_zlib_read = _libs['grass_gis.6.4.2RC2'].G_zlib_read
    G_zlib_read.restype = c_int
    G_zlib_read.argtypes = [c_int, c_int, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 498
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zlib_write_noCompress'):
    G_zlib_write_noCompress = _libs['grass_gis.6.4.2RC2'].G_zlib_write_noCompress
    G_zlib_write_noCompress.restype = c_int
    G_zlib_write_noCompress.argtypes = [c_int, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 501
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fork'):
    G_fork = _libs['grass_gis.6.4.2RC2'].G_fork
    G_fork.restype = c_int
    G_fork.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 504
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__check_format'):
    G__check_format = _libs['grass_gis.6.4.2RC2'].G__check_format
    G__check_format.restype = c_int
    G__check_format.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 505
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_row_ptrs'):
    G__read_row_ptrs = _libs['grass_gis.6.4.2RC2'].G__read_row_ptrs
    G__read_row_ptrs.restype = c_int
    G__read_row_ptrs.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 506
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_row_ptrs'):
    G__write_row_ptrs = _libs['grass_gis.6.4.2RC2'].G__write_row_ptrs
    G__write_row_ptrs.restype = c_int
    G__write_row_ptrs.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 509
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_clear'):
    G_fpreclass_clear = _libs['grass_gis.6.4.2RC2'].G_fpreclass_clear
    G_fpreclass_clear.restype = None
    G_fpreclass_clear.argtypes = [POINTER(struct_FPReclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 510
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_reset'):
    G_fpreclass_reset = _libs['grass_gis.6.4.2RC2'].G_fpreclass_reset
    G_fpreclass_reset.restype = None
    G_fpreclass_reset.argtypes = [POINTER(struct_FPReclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 511
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_init'):
    G_fpreclass_init = _libs['grass_gis.6.4.2RC2'].G_fpreclass_init
    G_fpreclass_init.restype = c_int
    G_fpreclass_init.argtypes = [POINTER(struct_FPReclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 512
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_set_domain'):
    G_fpreclass_set_domain = _libs['grass_gis.6.4.2RC2'].G_fpreclass_set_domain
    G_fpreclass_set_domain.restype = None
    G_fpreclass_set_domain.argtypes = [POINTER(struct_FPReclass), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 513
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_set_range'):
    G_fpreclass_set_range = _libs['grass_gis.6.4.2RC2'].G_fpreclass_set_range
    G_fpreclass_set_range.restype = None
    G_fpreclass_set_range.argtypes = [POINTER(struct_FPReclass), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 514
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_get_limits'):
    G_fpreclass_get_limits = _libs['grass_gis.6.4.2RC2'].G_fpreclass_get_limits
    G_fpreclass_get_limits.restype = c_int
    G_fpreclass_get_limits.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(DCELL), POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 516
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_nof_rules'):
    G_fpreclass_nof_rules = _libs['grass_gis.6.4.2RC2'].G_fpreclass_nof_rules
    G_fpreclass_nof_rules.restype = c_int
    G_fpreclass_nof_rules.argtypes = [POINTER(struct_FPReclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 517
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_get_ith_rule'):
    G_fpreclass_get_ith_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_get_ith_rule
    G_fpreclass_get_ith_rule.restype = None
    G_fpreclass_get_ith_rule.argtypes = [POINTER(struct_FPReclass), c_int, POINTER(DCELL), POINTER(DCELL), POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 519
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_set_neg_infinite_rule'):
    G_fpreclass_set_neg_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_set_neg_infinite_rule
    G_fpreclass_set_neg_infinite_rule.restype = None
    G_fpreclass_set_neg_infinite_rule.argtypes = [POINTER(struct_FPReclass), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 520
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_get_neg_infinite_rule'):
    G_fpreclass_get_neg_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_get_neg_infinite_rule
    G_fpreclass_get_neg_infinite_rule.restype = c_int
    G_fpreclass_get_neg_infinite_rule.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 522
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_set_pos_infinite_rule'):
    G_fpreclass_set_pos_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_set_pos_infinite_rule
    G_fpreclass_set_pos_infinite_rule.restype = None
    G_fpreclass_set_pos_infinite_rule.argtypes = [POINTER(struct_FPReclass), DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 523
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_get_pos_infinite_rule'):
    G_fpreclass_get_pos_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_get_pos_infinite_rule
    G_fpreclass_get_pos_infinite_rule.restype = c_int
    G_fpreclass_get_pos_infinite_rule.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 525
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_add_rule'):
    G_fpreclass_add_rule = _libs['grass_gis.6.4.2RC2'].G_fpreclass_add_rule
    G_fpreclass_add_rule.restype = None
    G_fpreclass_add_rule.argtypes = [POINTER(struct_FPReclass), DCELL, DCELL, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 526
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_reverse_rule_order'):
    G_fpreclass_reverse_rule_order = _libs['grass_gis.6.4.2RC2'].G_fpreclass_reverse_rule_order
    G_fpreclass_reverse_rule_order.restype = None
    G_fpreclass_reverse_rule_order.argtypes = [POINTER(struct_FPReclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 527
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_get_cell_value'):
    G_fpreclass_get_cell_value = _libs['grass_gis.6.4.2RC2'].G_fpreclass_get_cell_value
    G_fpreclass_get_cell_value.restype = DCELL
    G_fpreclass_get_cell_value.argtypes = [POINTER(struct_FPReclass), DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 528
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_di'):
    G_fpreclass_perform_di = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_di
    G_fpreclass_perform_di.restype = None
    G_fpreclass_perform_di.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 530
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_df'):
    G_fpreclass_perform_df = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_df
    G_fpreclass_perform_df.restype = None
    G_fpreclass_perform_df.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 532
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_dd'):
    G_fpreclass_perform_dd = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_dd
    G_fpreclass_perform_dd.restype = None
    G_fpreclass_perform_dd.argtypes = [POINTER(struct_FPReclass), POINTER(DCELL), POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 534
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_fi'):
    G_fpreclass_perform_fi = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_fi
    G_fpreclass_perform_fi.restype = None
    G_fpreclass_perform_fi.argtypes = [POINTER(struct_FPReclass), POINTER(FCELL), POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 536
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_ff'):
    G_fpreclass_perform_ff = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_ff
    G_fpreclass_perform_ff.restype = None
    G_fpreclass_perform_ff.argtypes = [POINTER(struct_FPReclass), POINTER(FCELL), POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 538
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_fd'):
    G_fpreclass_perform_fd = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_fd
    G_fpreclass_perform_fd.restype = None
    G_fpreclass_perform_fd.argtypes = [POINTER(struct_FPReclass), POINTER(FCELL), POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 540
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_ii'):
    G_fpreclass_perform_ii = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_ii
    G_fpreclass_perform_ii.restype = None
    G_fpreclass_perform_ii.argtypes = [POINTER(struct_FPReclass), POINTER(CELL), POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 542
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_if'):
    G_fpreclass_perform_if = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_if
    G_fpreclass_perform_if.restype = None
    G_fpreclass_perform_if.argtypes = [POINTER(struct_FPReclass), POINTER(CELL), POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 544
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fpreclass_perform_id'):
    G_fpreclass_perform_id = _libs['grass_gis.6.4.2RC2'].G_fpreclass_perform_id
    G_fpreclass_perform_id.restype = None
    G_fpreclass_perform_id.argtypes = [POINTER(struct_FPReclass), POINTER(CELL), POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 547
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_gdal_link'):
    G_get_gdal_link = _libs['grass_gis.6.4.2RC2'].G_get_gdal_link
    G_get_gdal_link.restype = POINTER(struct_GDAL_link)
    G_get_gdal_link.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 548
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_close_gdal_link'):
    G_close_gdal_link = _libs['grass_gis.6.4.2RC2'].G_close_gdal_link
    G_close_gdal_link.restype = None
    G_close_gdal_link.argtypes = [POINTER(struct_GDAL_link)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 551
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_geodesic_equation'):
    G_begin_geodesic_equation = _libs['grass_gis.6.4.2RC2'].G_begin_geodesic_equation
    G_begin_geodesic_equation.restype = c_int
    G_begin_geodesic_equation.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 552
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_geodesic_lat_from_lon'):
    G_geodesic_lat_from_lon = _libs['grass_gis.6.4.2RC2'].G_geodesic_lat_from_lon
    G_geodesic_lat_from_lon.restype = c_double
    G_geodesic_lat_from_lon.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 555
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_geodesic_distance'):
    G_begin_geodesic_distance = _libs['grass_gis.6.4.2RC2'].G_begin_geodesic_distance
    G_begin_geodesic_distance.restype = c_int
    G_begin_geodesic_distance.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 556
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_geodesic_distance_lat1'):
    G_set_geodesic_distance_lat1 = _libs['grass_gis.6.4.2RC2'].G_set_geodesic_distance_lat1
    G_set_geodesic_distance_lat1.restype = c_int
    G_set_geodesic_distance_lat1.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 557
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_geodesic_distance_lat2'):
    G_set_geodesic_distance_lat2 = _libs['grass_gis.6.4.2RC2'].G_set_geodesic_distance_lat2
    G_set_geodesic_distance_lat2.restype = c_int
    G_set_geodesic_distance_lat2.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 558
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_geodesic_distance_lon_to_lon'):
    G_geodesic_distance_lon_to_lon = _libs['grass_gis.6.4.2RC2'].G_geodesic_distance_lon_to_lon
    G_geodesic_distance_lon_to_lon.restype = c_double
    G_geodesic_distance_lon_to_lon.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 559
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_geodesic_distance'):
    G_geodesic_distance = _libs['grass_gis.6.4.2RC2'].G_geodesic_distance
    G_geodesic_distance.restype = c_double
    G_geodesic_distance.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 562
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_cellhd'):
    G_get_cellhd = _libs['grass_gis.6.4.2RC2'].G_get_cellhd
    G_get_cellhd.restype = c_int
    G_get_cellhd.argtypes = [String, String, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 565
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_datum_name'):
    G_ask_datum_name = _libs['grass_gis.6.4.2RC2'].G_ask_datum_name
    G_ask_datum_name.restype = c_int
    G_ask_datum_name.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 568
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_ellipse_name'):
    G_ask_ellipse_name = _libs['grass_gis.6.4.2RC2'].G_ask_ellipse_name
    G_ask_ellipse_name.restype = c_int
    G_ask_ellipse_name.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 571
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ellipsoid_parameters'):
    G_get_ellipsoid_parameters = _libs['grass_gis.6.4.2RC2'].G_get_ellipsoid_parameters
    G_get_ellipsoid_parameters.restype = c_int
    G_get_ellipsoid_parameters.argtypes = [POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 572
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_spheroid_by_name'):
    G_get_spheroid_by_name = _libs['grass_gis.6.4.2RC2'].G_get_spheroid_by_name
    G_get_spheroid_by_name.restype = c_int
    G_get_spheroid_by_name.argtypes = [String, POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 573
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_ellipsoid_by_name'):
    G_get_ellipsoid_by_name = _libs['grass_gis.6.4.2RC2'].G_get_ellipsoid_by_name
    G_get_ellipsoid_by_name.restype = c_int
    G_get_ellipsoid_by_name.argtypes = [String, POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 574
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ellipsoid_name'):
    G_ellipsoid_name = _libs['grass_gis.6.4.2RC2'].G_ellipsoid_name
    G_ellipsoid_name.restype = ReturnString
    G_ellipsoid_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 575
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ellipsoid_description'):
    G_ellipsoid_description = _libs['grass_gis.6.4.2RC2'].G_ellipsoid_description
    G_ellipsoid_description.restype = ReturnString
    G_ellipsoid_description.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 578
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_projunits'):
    G_get_projunits = _libs['grass_gis.6.4.2RC2'].G_get_projunits
    G_get_projunits.restype = POINTER(struct_Key_Value)
    G_get_projunits.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 579
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_projinfo'):
    G_get_projinfo = _libs['grass_gis.6.4.2RC2'].G_get_projinfo
    G_get_projinfo.restype = POINTER(struct_Key_Value)
    G_get_projinfo.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 582
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_proj_name'):
    G_ask_proj_name = _libs['grass_gis.6.4.2RC2'].G_ask_proj_name
    G_ask_proj_name.restype = c_int
    G_ask_proj_name.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 585
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_map_row_nomask'):
    G_get_map_row_nomask = _libs['grass_gis.6.4.2RC2'].G_get_map_row_nomask
    G_get_map_row_nomask.restype = c_int
    G_get_map_row_nomask.argtypes = [c_int, POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 586
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_row_nomask'):
    G_get_raster_row_nomask = _libs['grass_gis.6.4.2RC2'].G_get_raster_row_nomask
    G_get_raster_row_nomask.restype = c_int
    G_get_raster_row_nomask.argtypes = [c_int, POINTER(None), c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 587
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_c_raster_row_nomask'):
    G_get_c_raster_row_nomask = _libs['grass_gis.6.4.2RC2'].G_get_c_raster_row_nomask
    G_get_c_raster_row_nomask.restype = c_int
    G_get_c_raster_row_nomask.argtypes = [c_int, POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 588
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_f_raster_row_nomask'):
    G_get_f_raster_row_nomask = _libs['grass_gis.6.4.2RC2'].G_get_f_raster_row_nomask
    G_get_f_raster_row_nomask.restype = c_int
    G_get_f_raster_row_nomask.argtypes = [c_int, POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 589
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_d_raster_row_nomask'):
    G_get_d_raster_row_nomask = _libs['grass_gis.6.4.2RC2'].G_get_d_raster_row_nomask
    G_get_d_raster_row_nomask.restype = c_int
    G_get_d_raster_row_nomask.argtypes = [c_int, POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 590
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_map_row'):
    G_get_map_row = _libs['grass_gis.6.4.2RC2'].G_get_map_row
    G_get_map_row.restype = c_int
    G_get_map_row.argtypes = [c_int, POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 591
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_row'):
    G_get_raster_row = _libs['grass_gis.6.4.2RC2'].G_get_raster_row
    G_get_raster_row.restype = c_int
    G_get_raster_row.argtypes = [c_int, POINTER(None), c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 592
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_c_raster_row'):
    G_get_c_raster_row = _libs['grass_gis.6.4.2RC2'].G_get_c_raster_row
    G_get_c_raster_row.restype = c_int
    G_get_c_raster_row.argtypes = [c_int, POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 593
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_f_raster_row'):
    G_get_f_raster_row = _libs['grass_gis.6.4.2RC2'].G_get_f_raster_row
    G_get_f_raster_row.restype = c_int
    G_get_f_raster_row.argtypes = [c_int, POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 594
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_d_raster_row'):
    G_get_d_raster_row = _libs['grass_gis.6.4.2RC2'].G_get_d_raster_row
    G_get_d_raster_row.restype = c_int
    G_get_d_raster_row.argtypes = [c_int, POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 595
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_null_value_row'):
    G_get_null_value_row = _libs['grass_gis.6.4.2RC2'].G_get_null_value_row
    G_get_null_value_row.restype = c_int
    G_get_null_value_row.argtypes = [c_int, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 598
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_row_colors'):
    G_get_raster_row_colors = _libs['grass_gis.6.4.2RC2'].G_get_raster_row_colors
    G_get_raster_row_colors.restype = c_int
    G_get_raster_row_colors.argtypes = [c_int, c_int, POINTER(struct_Colors), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte), POINTER(c_ubyte)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 603
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_window'):
    G_get_window = _libs['grass_gis.6.4.2RC2'].G_get_window
    G_get_window.restype = c_int
    G_get_window.argtypes = [POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 604
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_default_window'):
    G_get_default_window = _libs['grass_gis.6.4.2RC2'].G_get_default_window
    G_get_default_window.restype = c_int
    G_get_default_window.argtypes = [POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 605
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__get_window'):
    G__get_window = _libs['grass_gis.6.4.2RC2'].G__get_window
    G__get_window.restype = ReturnString
    G__get_window.argtypes = [POINTER(struct_Cell_head), String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 609
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_getl'):
    G_getl = _libs['grass_gis.6.4.2RC2'].G_getl
    G_getl.restype = c_int
    G_getl.argtypes = [String, c_int, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 610
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_getl2'):
    G_getl2 = _libs['grass_gis.6.4.2RC2'].G_getl2
    G_getl2.restype = c_int
    G_getl2.argtypes = [String, c_int, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 613
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_gets'):
    G_gets = _libs['grass_gis.6.4.2RC2'].G_gets
    G_gets.restype = c_int
    G_gets.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 616
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_gisbase'):
    G_gisbase = _libs['grass_gis.6.4.2RC2'].G_gisbase
    G_gisbase.restype = ReturnString
    G_gisbase.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 619
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_gisdbase'):
    G_gisdbase = _libs['grass_gis.6.4.2RC2'].G_gisdbase
    G_gisdbase.restype = ReturnString
    G_gisdbase.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 622
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_gishelp'):
    G_gishelp = _libs['grass_gis.6.4.2RC2'].G_gishelp
    G_gishelp.restype = c_int
    G_gishelp.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 625
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__gisinit'):
    G__gisinit = _libs['grass_gis.6.4.2RC2'].G__gisinit
    G__gisinit.restype = c_int
    G__gisinit.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 626
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__no_gisinit'):
    G__no_gisinit = _libs['grass_gis.6.4.2RC2'].G__no_gisinit
    G__no_gisinit.restype = c_int
    G__no_gisinit.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 627
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__check_gisinit'):
    G__check_gisinit = _libs['grass_gis.6.4.2RC2'].G__check_gisinit
    G__check_gisinit.restype = c_int
    G__check_gisinit.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 630
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_histogram_eq'):
    G_histogram_eq = _libs['grass_gis.6.4.2RC2'].G_histogram_eq
    G_histogram_eq.restype = c_int
    G_histogram_eq.argtypes = [POINTER(struct_Histogram), POINTER(POINTER(c_ubyte)), POINTER(CELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 634
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_histogram'):
    G_init_histogram = _libs['grass_gis.6.4.2RC2'].G_init_histogram
    G_init_histogram.restype = c_int
    G_init_histogram.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 635
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_histogram'):
    G_read_histogram = _libs['grass_gis.6.4.2RC2'].G_read_histogram
    G_read_histogram.restype = c_int
    G_read_histogram.argtypes = [String, String, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 636
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_histogram'):
    G_write_histogram = _libs['grass_gis.6.4.2RC2'].G_write_histogram
    G_write_histogram.restype = c_int
    G_write_histogram.argtypes = [String, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 637
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_histogram_cs'):
    G_write_histogram_cs = _libs['grass_gis.6.4.2RC2'].G_write_histogram_cs
    G_write_histogram_cs.restype = c_int
    G_write_histogram_cs.argtypes = [String, POINTER(struct_Cell_stats)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 638
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_histogram_cs'):
    G_make_histogram_cs = _libs['grass_gis.6.4.2RC2'].G_make_histogram_cs
    G_make_histogram_cs.restype = c_int
    G_make_histogram_cs.argtypes = [POINTER(struct_Cell_stats), POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 639
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_histogram_num'):
    G_get_histogram_num = _libs['grass_gis.6.4.2RC2'].G_get_histogram_num
    G_get_histogram_num.restype = c_int
    G_get_histogram_num.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 640
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_histogram_cat'):
    G_get_histogram_cat = _libs['grass_gis.6.4.2RC2'].G_get_histogram_cat
    G_get_histogram_cat.restype = CELL
    G_get_histogram_cat.argtypes = [c_int, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 641
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_histogram_count'):
    G_get_histogram_count = _libs['grass_gis.6.4.2RC2'].G_get_histogram_count
    G_get_histogram_count.restype = c_long
    G_get_histogram_count.argtypes = [c_int, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 642
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_histogram'):
    G_free_histogram = _libs['grass_gis.6.4.2RC2'].G_free_histogram
    G_free_histogram.restype = c_int
    G_free_histogram.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 643
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_sort_histogram'):
    G_sort_histogram = _libs['grass_gis.6.4.2RC2'].G_sort_histogram
    G_sort_histogram.restype = c_int
    G_sort_histogram.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 644
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_sort_histogram_by_count'):
    G_sort_histogram_by_count = _libs['grass_gis.6.4.2RC2'].G_sort_histogram_by_count
    G_sort_histogram_by_count.restype = c_int
    G_sort_histogram_by_count.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 645
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_histogram'):
    G_remove_histogram = _libs['grass_gis.6.4.2RC2'].G_remove_histogram
    G_remove_histogram.restype = c_int
    G_remove_histogram.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 646
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_histogram'):
    G_add_histogram = _libs['grass_gis.6.4.2RC2'].G_add_histogram
    G_add_histogram.restype = c_int
    G_add_histogram.argtypes = [CELL, c_long, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 647
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_histogram'):
    G_set_histogram = _libs['grass_gis.6.4.2RC2'].G_set_histogram
    G_set_histogram.restype = c_int
    G_set_histogram.argtypes = [CELL, c_long, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 648
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_extend_histogram'):
    G_extend_histogram = _libs['grass_gis.6.4.2RC2'].G_extend_histogram
    G_extend_histogram.restype = c_int
    G_extend_histogram.argtypes = [CELL, c_long, POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 649
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zero_histogram'):
    G_zero_histogram = _libs['grass_gis.6.4.2RC2'].G_zero_histogram
    G_zero_histogram.restype = c_int
    G_zero_histogram.argtypes = [POINTER(struct_Histogram)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 652
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_history'):
    G_read_history = _libs['grass_gis.6.4.2RC2'].G_read_history
    G_read_history.restype = c_int
    G_read_history.argtypes = [String, String, POINTER(struct_History)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 653
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_history'):
    G_write_history = _libs['grass_gis.6.4.2RC2'].G_write_history
    G_write_history.restype = c_int
    G_write_history.argtypes = [String, POINTER(struct_History)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 654
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_short_history'):
    G_short_history = _libs['grass_gis.6.4.2RC2'].G_short_history
    G_short_history.restype = c_int
    G_short_history.argtypes = [String, String, POINTER(struct_History)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 655
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_command_history'):
    G_command_history = _libs['grass_gis.6.4.2RC2'].G_command_history
    G_command_history.restype = c_int
    G_command_history.argtypes = [POINTER(struct_History)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 658
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_home'):
    G_home = _libs['grass_gis.6.4.2RC2'].G_home
    G_home.restype = ReturnString
    G_home.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 659
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__home'):
    G__home = _libs['grass_gis.6.4.2RC2'].G__home
    G__home.restype = ReturnString
    G__home.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 662
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_index'):
    G_index = _libs['grass_gis.6.4.2RC2'].G_index
    G_index.restype = ReturnString
    G_index.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 663
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rindex'):
    G_rindex = _libs['grass_gis.6.4.2RC2'].G_rindex
    G_rindex.restype = ReturnString
    G_rindex.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 666
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__random_d_initialize_0'):
    G__random_d_initialize_0 = _libs['grass_gis.6.4.2RC2'].G__random_d_initialize_0
    G__random_d_initialize_0.restype = c_int
    G__random_d_initialize_0.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 667
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__random_f_initialize_0'):
    G__random_f_initialize_0 = _libs['grass_gis.6.4.2RC2'].G__random_f_initialize_0
    G__random_f_initialize_0.restype = c_int
    G__random_f_initialize_0.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 670
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_interp_linear'):
    G_interp_linear = _libs['grass_gis.6.4.2RC2'].G_interp_linear
    G_interp_linear.restype = DCELL
    G_interp_linear.argtypes = [c_double, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 671
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_interp_bilinear'):
    G_interp_bilinear = _libs['grass_gis.6.4.2RC2'].G_interp_bilinear
    G_interp_bilinear.restype = DCELL
    G_interp_bilinear.argtypes = [c_double, c_double, DCELL, DCELL, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 672
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_interp_cubic'):
    G_interp_cubic = _libs['grass_gis.6.4.2RC2'].G_interp_cubic
    G_interp_cubic.restype = DCELL
    G_interp_cubic.argtypes = [c_double, DCELL, DCELL, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 673
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_interp_bicubic'):
    G_interp_bicubic = _libs['grass_gis.6.4.2RC2'].G_interp_bicubic
    G_interp_bicubic.restype = DCELL
    G_interp_bicubic.argtypes = [c_double, c_double, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL, DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 679
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_intersect_line_segments'):
    G_intersect_line_segments = _libs['grass_gis.6.4.2RC2'].G_intersect_line_segments
    G_intersect_line_segments.restype = c_int
    G_intersect_line_segments.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 684
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_intr_char'):
    G_intr_char = _libs['grass_gis.6.4.2RC2'].G_intr_char
    G_intr_char.restype = c_char
    G_intr_char.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 687
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_gisbase'):
    G_is_gisbase = _libs['grass_gis.6.4.2RC2'].G_is_gisbase
    G_is_gisbase.restype = c_int
    G_is_gisbase.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 688
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_location'):
    G_is_location = _libs['grass_gis.6.4.2RC2'].G_is_location
    G_is_location.restype = c_int
    G_is_location.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 689
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_mapset'):
    G_is_mapset = _libs['grass_gis.6.4.2RC2'].G_is_mapset
    G_is_mapset.restype = c_int
    G_is_mapset.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 692
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_create_key_value'):
    G_create_key_value = _libs['grass_gis.6.4.2RC2'].G_create_key_value
    G_create_key_value.restype = POINTER(struct_Key_Value)
    G_create_key_value.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 693
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_key_value'):
    G_set_key_value = _libs['grass_gis.6.4.2RC2'].G_set_key_value
    G_set_key_value.restype = c_int
    G_set_key_value.argtypes = [String, String, POINTER(struct_Key_Value)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 694
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_find_key_value'):
    G_find_key_value = _libs['grass_gis.6.4.2RC2'].G_find_key_value
    G_find_key_value.restype = ReturnString
    G_find_key_value.argtypes = [String, POINTER(struct_Key_Value)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 695
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_key_value'):
    G_free_key_value = _libs['grass_gis.6.4.2RC2'].G_free_key_value
    G_free_key_value.restype = c_int
    G_free_key_value.argtypes = [POINTER(struct_Key_Value)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 698
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fwrite_key_value'):
    G_fwrite_key_value = _libs['grass_gis.6.4.2RC2'].G_fwrite_key_value
    G_fwrite_key_value.restype = c_int
    G_fwrite_key_value.argtypes = [POINTER(FILE), POINTER(struct_Key_Value)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 699
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fread_key_value'):
    G_fread_key_value = _libs['grass_gis.6.4.2RC2'].G_fread_key_value
    G_fread_key_value.restype = POINTER(struct_Key_Value)
    G_fread_key_value.argtypes = [POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 702
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_key_value_file'):
    G_write_key_value_file = _libs['grass_gis.6.4.2RC2'].G_write_key_value_file
    G_write_key_value_file.restype = c_int
    G_write_key_value_file.argtypes = [String, POINTER(struct_Key_Value), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 703
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_key_value_file'):
    G_read_key_value_file = _libs['grass_gis.6.4.2RC2'].G_read_key_value_file
    G_read_key_value_file.restype = POINTER(struct_Key_Value)
    G_read_key_value_file.argtypes = [String, POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 706
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_update_key_value_file'):
    G_update_key_value_file = _libs['grass_gis.6.4.2RC2'].G_update_key_value_file
    G_update_key_value_file.restype = c_int
    G_update_key_value_file.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 707
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lookup_key_value_from_file'):
    G_lookup_key_value_from_file = _libs['grass_gis.6.4.2RC2'].G_lookup_key_value_from_file
    G_lookup_key_value_from_file.restype = c_int
    G_lookup_key_value_from_file.argtypes = [String, String, POINTER(c_char), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 710
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_legal_filename'):
    G_legal_filename = _libs['grass_gis.6.4.2RC2'].G_legal_filename
    G_legal_filename.restype = c_int
    G_legal_filename.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 711
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_check_input_output_name'):
    G_check_input_output_name = _libs['grass_gis.6.4.2RC2'].G_check_input_output_name
    G_check_input_output_name.restype = c_int
    G_check_input_output_name.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 714
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_distance_to_line_tolerance'):
    G_set_distance_to_line_tolerance = _libs['grass_gis.6.4.2RC2'].G_set_distance_to_line_tolerance
    G_set_distance_to_line_tolerance.restype = c_int
    G_set_distance_to_line_tolerance.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 715
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_distance2_point_to_line'):
    G_distance2_point_to_line = _libs['grass_gis.6.4.2RC2'].G_distance2_point_to_line
    G_distance2_point_to_line.restype = c_double
    G_distance2_point_to_line.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 719
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_list_hit_return'):
    G_set_list_hit_return = _libs['grass_gis.6.4.2RC2'].G_set_list_hit_return
    G_set_list_hit_return.restype = c_int
    G_set_list_hit_return.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 720
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_list_element'):
    G_list_element = _libs['grass_gis.6.4.2RC2'].G_list_element
    G_list_element.restype = c_int
    G_list_element.argtypes = [String, String, String, CFUNCTYPE(UNCHECKED(c_int), String, String, String)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 722
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_list'):
    G_list = _libs['grass_gis.6.4.2RC2'].G_list
    G_list.restype = POINTER(POINTER(c_char))
    G_list.argtypes = [c_int, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 723
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_list'):
    G_free_list = _libs['grass_gis.6.4.2RC2'].G_free_list
    G_free_list.restype = None
    G_free_list.argtypes = [POINTER(POINTER(c_char))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 726
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lat_format'):
    G_lat_format = _libs['grass_gis.6.4.2RC2'].G_lat_format
    G_lat_format.restype = c_int
    G_lat_format.argtypes = [c_double, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 727
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lat_format_string'):
    G_lat_format_string = _libs['grass_gis.6.4.2RC2'].G_lat_format_string
    G_lat_format_string.restype = ReturnString
    G_lat_format_string.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 728
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lon_format'):
    G_lon_format = _libs['grass_gis.6.4.2RC2'].G_lon_format
    G_lon_format.restype = c_int
    G_lon_format.argtypes = [c_double, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 729
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lon_format_string'):
    G_lon_format_string = _libs['grass_gis.6.4.2RC2'].G_lon_format_string
    G_lon_format_string.restype = ReturnString
    G_lon_format_string.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 730
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_llres_format'):
    G_llres_format = _libs['grass_gis.6.4.2RC2'].G_llres_format
    G_llres_format.restype = c_int
    G_llres_format.argtypes = [c_double, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 731
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_llres_format_string'):
    G_llres_format_string = _libs['grass_gis.6.4.2RC2'].G_llres_format_string
    G_llres_format_string.restype = ReturnString
    G_llres_format_string.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 732
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lat_parts'):
    G_lat_parts = _libs['grass_gis.6.4.2RC2'].G_lat_parts
    G_lat_parts.restype = c_int
    G_lat_parts.argtypes = [c_double, POINTER(c_int), POINTER(c_int), POINTER(c_double), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 733
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lon_parts'):
    G_lon_parts = _libs['grass_gis.6.4.2RC2'].G_lon_parts
    G_lon_parts.restype = c_int
    G_lon_parts.argtypes = [c_double, POINTER(c_int), POINTER(c_int), POINTER(c_double), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 736
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lat_scan'):
    G_lat_scan = _libs['grass_gis.6.4.2RC2'].G_lat_scan
    G_lat_scan.restype = c_int
    G_lat_scan.argtypes = [String, POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 737
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lon_scan'):
    G_lon_scan = _libs['grass_gis.6.4.2RC2'].G_lon_scan
    G_lon_scan.restype = c_int
    G_lon_scan.argtypes = [String, POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 738
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_llres_scan'):
    G_llres_scan = _libs['grass_gis.6.4.2RC2'].G_llres_scan
    G_llres_scan.restype = c_int
    G_llres_scan.argtypes = [String, POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 741
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_location_path'):
    G_location_path = _libs['grass_gis.6.4.2RC2'].G_location_path
    G_location_path.restype = ReturnString
    G_location_path.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 742
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_location'):
    G_location = _libs['grass_gis.6.4.2RC2'].G_location
    G_location.restype = ReturnString
    G_location.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 743
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__location_path'):
    G__location_path = _libs['grass_gis.6.4.2RC2'].G__location_path
    G__location_path.restype = ReturnString
    G__location_path.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 746
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_ls_filter'):
    G_set_ls_filter = _libs['grass_gis.6.4.2RC2'].G_set_ls_filter
    G_set_ls_filter.restype = None
    G_set_ls_filter.argtypes = [CFUNCTYPE(UNCHECKED(c_int), String, POINTER(None)), POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 747
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_ls_exclude_filter'):
    G_set_ls_exclude_filter = _libs['grass_gis.6.4.2RC2'].G_set_ls_exclude_filter
    G_set_ls_exclude_filter.restype = None
    G_set_ls_exclude_filter.argtypes = [CFUNCTYPE(UNCHECKED(c_int), String, POINTER(None)), POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 748
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__ls'):
    G__ls = _libs['grass_gis.6.4.2RC2'].G__ls
    G__ls.restype = POINTER(POINTER(c_char))
    G__ls.argtypes = [String, POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 749
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ls'):
    G_ls = _libs['grass_gis.6.4.2RC2'].G_ls
    G_ls.restype = None
    G_ls.argtypes = [String, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 750
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ls_format'):
    G_ls_format = _libs['grass_gis.6.4.2RC2'].G_ls_format
    G_ls_format.restype = None
    G_ls_format.argtypes = [POINTER(POINTER(c_char)), c_int, c_int, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 753
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__machine_name'):
    G__machine_name = _libs['grass_gis.6.4.2RC2'].G__machine_name
    G__machine_name.restype = ReturnString
    G__machine_name.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 756
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ask_colors'):
    G_ask_colors = _libs['grass_gis.6.4.2RC2'].G_ask_colors
    G_ask_colors.restype = c_int
    G_ask_colors.argtypes = [String, String, POINTER(struct_Colors)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 759
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__make_location'):
    G__make_location = _libs['grass_gis.6.4.2RC2'].G__make_location
    G__make_location.restype = c_int
    G__make_location.argtypes = [String, POINTER(struct_Cell_head), POINTER(struct_Key_Value), POINTER(struct_Key_Value), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 761
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_location'):
    G_make_location = _libs['grass_gis.6.4.2RC2'].G_make_location
    G_make_location.restype = c_int
    G_make_location.argtypes = [String, POINTER(struct_Cell_head), POINTER(struct_Key_Value), POINTER(struct_Key_Value), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 763
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_compare_projections'):
    G_compare_projections = _libs['grass_gis.6.4.2RC2'].G_compare_projections
    G_compare_projections.restype = c_int
    G_compare_projections.argtypes = [POINTER(struct_Key_Value), POINTER(struct_Key_Value), POINTER(struct_Key_Value), POINTER(struct_Key_Value)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 767
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__make_mapset'):
    G__make_mapset = _libs['grass_gis.6.4.2RC2'].G__make_mapset
    G__make_mapset.restype = c_int
    G__make_mapset.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 769
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_make_mapset'):
    G_make_mapset = _libs['grass_gis.6.4.2RC2'].G_make_mapset
    G_make_mapset.restype = c_int
    G_make_mapset.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 773
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_tolcase'):
    G_tolcase = _libs['grass_gis.6.4.2RC2'].G_tolcase
    G_tolcase.restype = ReturnString
    G_tolcase.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 774
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_toucase'):
    G_toucase = _libs['grass_gis.6.4.2RC2'].G_toucase
    G_toucase.restype = ReturnString
    G_toucase.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 777
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mapset'):
    G_mapset = _libs['grass_gis.6.4.2RC2'].G_mapset
    G_mapset.restype = ReturnString
    G_mapset.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 778
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__mapset'):
    G__mapset = _libs['grass_gis.6.4.2RC2'].G__mapset
    G__mapset.restype = ReturnString
    G__mapset.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 781
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__make_mapset_element'):
    G__make_mapset_element = _libs['grass_gis.6.4.2RC2'].G__make_mapset_element
    G__make_mapset_element.restype = c_int
    G__make_mapset_element.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 782
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__make_mapset_element_misc'):
    G__make_mapset_element_misc = _libs['grass_gis.6.4.2RC2'].G__make_mapset_element_misc
    G__make_mapset_element_misc.restype = c_int
    G__make_mapset_element_misc.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 783
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__mapset_permissions'):
    G__mapset_permissions = _libs['grass_gis.6.4.2RC2'].G__mapset_permissions
    G__mapset_permissions.restype = c_int
    G__mapset_permissions.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 784
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__mapset_permissions2'):
    G__mapset_permissions2 = _libs['grass_gis.6.4.2RC2'].G__mapset_permissions2
    G__mapset_permissions2.restype = c_int
    G__mapset_permissions2.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 787
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__mapset_name'):
    G__mapset_name = _libs['grass_gis.6.4.2RC2'].G__mapset_name
    G__mapset_name.restype = ReturnString
    G__mapset_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 788
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__create_alt_search_path'):
    G__create_alt_search_path = _libs['grass_gis.6.4.2RC2'].G__create_alt_search_path
    G__create_alt_search_path.restype = c_int
    G__create_alt_search_path.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 789
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__switch_search_path'):
    G__switch_search_path = _libs['grass_gis.6.4.2RC2'].G__switch_search_path
    G__switch_search_path.restype = c_int
    G__switch_search_path.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 790
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_reset_mapsets'):
    G_reset_mapsets = _libs['grass_gis.6.4.2RC2'].G_reset_mapsets
    G_reset_mapsets.restype = c_int
    G_reset_mapsets.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 791
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_available_mapsets'):
    G_available_mapsets = _libs['grass_gis.6.4.2RC2'].G_available_mapsets
    G_available_mapsets.restype = POINTER(POINTER(c_char))
    G_available_mapsets.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 792
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_add_mapset_to_search_path'):
    G_add_mapset_to_search_path = _libs['grass_gis.6.4.2RC2'].G_add_mapset_to_search_path
    G_add_mapset_to_search_path.restype = None
    G_add_mapset_to_search_path.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 793
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_mapset_in_search_path'):
    G_is_mapset_in_search_path = _libs['grass_gis.6.4.2RC2'].G_is_mapset_in_search_path
    G_is_mapset_in_search_path.restype = c_int
    G_is_mapset_in_search_path.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 796
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mask_info'):
    G_mask_info = _libs['grass_gis.6.4.2RC2'].G_mask_info
    G_mask_info.restype = ReturnString
    G_mask_info.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 797
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__mask_info'):
    G__mask_info = _libs['grass_gis.6.4.2RC2'].G__mask_info
    G__mask_info.restype = c_int
    G__mask_info.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 800
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_maskfd'):
    G_maskfd = _libs['grass_gis.6.4.2RC2'].G_maskfd
    G_maskfd.restype = c_int
    G_maskfd.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 803
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_myname'):
    G_myname = _libs['grass_gis.6.4.2RC2'].G_myname
    G_myname.restype = ReturnString
    G_myname.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 806
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_color_values'):
    G_color_values = _libs['grass_gis.6.4.2RC2'].G_color_values
    G_color_values.restype = c_int
    G_color_values.argtypes = [String, POINTER(c_float), POINTER(c_float), POINTER(c_float)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 807
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_color_name'):
    G_color_name = _libs['grass_gis.6.4.2RC2'].G_color_name
    G_color_name.restype = ReturnString
    G_color_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 810
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_newlines_to_spaces'):
    G_newlines_to_spaces = _libs['grass_gis.6.4.2RC2'].G_newlines_to_spaces
    G_newlines_to_spaces.restype = None
    G_newlines_to_spaces.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 813
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__name_in_mapset'):
    G__name_in_mapset = _libs['grass_gis.6.4.2RC2'].G__name_in_mapset
    G__name_in_mapset.restype = c_int
    G__name_in_mapset.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 814
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__name_is_fully_qualified'):
    G__name_is_fully_qualified = _libs['grass_gis.6.4.2RC2'].G__name_is_fully_qualified
    G__name_is_fully_qualified.restype = c_int
    G__name_is_fully_qualified.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 815
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fully_qualified_name'):
    G_fully_qualified_name = _libs['grass_gis.6.4.2RC2'].G_fully_qualified_name
    G_fully_qualified_name.restype = ReturnString
    G_fully_qualified_name.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 818
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__init_null_patterns'):
    G__init_null_patterns = _libs['grass_gis.6.4.2RC2'].G__init_null_patterns
    G__init_null_patterns.restype = None
    G__init_null_patterns.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 819
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__set_null_value'):
    G__set_null_value = _libs['grass_gis.6.4.2RC2'].G__set_null_value
    G__set_null_value.restype = None
    G__set_null_value.argtypes = [POINTER(None), c_int, c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 820
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_null_value'):
    G_set_null_value = _libs['grass_gis.6.4.2RC2'].G_set_null_value
    G_set_null_value.restype = None
    G_set_null_value.argtypes = [POINTER(None), c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 821
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_c_null_value'):
    G_set_c_null_value = _libs['grass_gis.6.4.2RC2'].G_set_c_null_value
    G_set_c_null_value.restype = None
    G_set_c_null_value.argtypes = [POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 822
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_f_null_value'):
    G_set_f_null_value = _libs['grass_gis.6.4.2RC2'].G_set_f_null_value
    G_set_f_null_value.restype = None
    G_set_f_null_value.argtypes = [POINTER(FCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 823
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_d_null_value'):
    G_set_d_null_value = _libs['grass_gis.6.4.2RC2'].G_set_d_null_value
    G_set_d_null_value.restype = None
    G_set_d_null_value.argtypes = [POINTER(DCELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 824
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_null_value'):
    G_is_null_value = _libs['grass_gis.6.4.2RC2'].G_is_null_value
    G_is_null_value.restype = c_int
    G_is_null_value.argtypes = [POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 825
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_c_null_value'):
    G_is_c_null_value = _libs['grass_gis.6.4.2RC2'].G_is_c_null_value
    G_is_c_null_value.restype = c_int
    G_is_c_null_value.argtypes = [POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 826
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_f_null_value'):
    G_is_f_null_value = _libs['grass_gis.6.4.2RC2'].G_is_f_null_value
    G_is_f_null_value.restype = c_int
    G_is_f_null_value.argtypes = [POINTER(FCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 827
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_d_null_value'):
    G_is_d_null_value = _libs['grass_gis.6.4.2RC2'].G_is_d_null_value
    G_is_d_null_value.restype = c_int
    G_is_d_null_value.argtypes = [POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 828
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_insert_null_values'):
    G_insert_null_values = _libs['grass_gis.6.4.2RC2'].G_insert_null_values
    G_insert_null_values.restype = c_int
    G_insert_null_values.argtypes = [POINTER(None), String, c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 829
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_insert_c_null_values'):
    G_insert_c_null_values = _libs['grass_gis.6.4.2RC2'].G_insert_c_null_values
    G_insert_c_null_values.restype = c_int
    G_insert_c_null_values.argtypes = [POINTER(CELL), String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 830
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_insert_f_null_values'):
    G_insert_f_null_values = _libs['grass_gis.6.4.2RC2'].G_insert_f_null_values
    G_insert_f_null_values.restype = c_int
    G_insert_f_null_values.argtypes = [POINTER(FCELL), String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 831
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_insert_d_null_values'):
    G_insert_d_null_values = _libs['grass_gis.6.4.2RC2'].G_insert_d_null_values
    G_insert_d_null_values.restype = c_int
    G_insert_d_null_values.argtypes = [POINTER(DCELL), String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 832
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__check_null_bit'):
    G__check_null_bit = _libs['grass_gis.6.4.2RC2'].G__check_null_bit
    G__check_null_bit.restype = c_int
    G__check_null_bit.argtypes = [POINTER(c_ubyte), c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 833
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__set_flags_from_01_random'):
    G__set_flags_from_01_random = _libs['grass_gis.6.4.2RC2'].G__set_flags_from_01_random
    G__set_flags_from_01_random.restype = c_int
    G__set_flags_from_01_random.argtypes = [String, POINTER(c_ubyte), c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 834
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__convert_01_flags'):
    G__convert_01_flags = _libs['grass_gis.6.4.2RC2'].G__convert_01_flags
    G__convert_01_flags.restype = c_int
    G__convert_01_flags.argtypes = [String, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 835
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__convert_flags_01'):
    G__convert_flags_01 = _libs['grass_gis.6.4.2RC2'].G__convert_flags_01
    G__convert_flags_01.restype = c_int
    G__convert_flags_01.argtypes = [String, POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 836
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__init_null_bits'):
    G__init_null_bits = _libs['grass_gis.6.4.2RC2'].G__init_null_bits
    G__init_null_bits.restype = c_int
    G__init_null_bits.argtypes = [POINTER(c_ubyte), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 839
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_new'):
    G_open_new = _libs['grass_gis.6.4.2RC2'].G_open_new
    G_open_new.restype = c_int
    G_open_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 840
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_old'):
    G_open_old = _libs['grass_gis.6.4.2RC2'].G_open_old
    G_open_old.restype = c_int
    G_open_old.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 841
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_update'):
    G_open_update = _libs['grass_gis.6.4.2RC2'].G_open_update
    G_open_update.restype = c_int
    G_open_update.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 842
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_new'):
    G_fopen_new = _libs['grass_gis.6.4.2RC2'].G_fopen_new
    G_fopen_new.restype = POINTER(FILE)
    G_fopen_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 843
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_old'):
    G_fopen_old = _libs['grass_gis.6.4.2RC2'].G_fopen_old
    G_fopen_old.restype = POINTER(FILE)
    G_fopen_old.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 844
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_append'):
    G_fopen_append = _libs['grass_gis.6.4.2RC2'].G_fopen_append
    G_fopen_append.restype = POINTER(FILE)
    G_fopen_append.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 845
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_modify'):
    G_fopen_modify = _libs['grass_gis.6.4.2RC2'].G_fopen_modify
    G_fopen_modify.restype = POINTER(FILE)
    G_fopen_modify.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 848
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_new_misc'):
    G_open_new_misc = _libs['grass_gis.6.4.2RC2'].G_open_new_misc
    G_open_new_misc.restype = c_int
    G_open_new_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 849
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_old_misc'):
    G_open_old_misc = _libs['grass_gis.6.4.2RC2'].G_open_old_misc
    G_open_old_misc.restype = c_int
    G_open_old_misc.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 850
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_update_misc'):
    G_open_update_misc = _libs['grass_gis.6.4.2RC2'].G_open_update_misc
    G_open_update_misc.restype = c_int
    G_open_update_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 851
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_new_misc'):
    G_fopen_new_misc = _libs['grass_gis.6.4.2RC2'].G_fopen_new_misc
    G_fopen_new_misc.restype = POINTER(FILE)
    G_fopen_new_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 852
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_old_misc'):
    G_fopen_old_misc = _libs['grass_gis.6.4.2RC2'].G_fopen_old_misc
    G_fopen_old_misc.restype = POINTER(FILE)
    G_fopen_old_misc.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 854
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_append_misc'):
    G_fopen_append_misc = _libs['grass_gis.6.4.2RC2'].G_fopen_append_misc
    G_fopen_append_misc.restype = POINTER(FILE)
    G_fopen_append_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 855
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fopen_modify_misc'):
    G_fopen_modify_misc = _libs['grass_gis.6.4.2RC2'].G_fopen_modify_misc
    G_fopen_modify_misc.restype = POINTER(FILE)
    G_fopen_modify_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 858
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_cell_old'):
    G_open_cell_old = _libs['grass_gis.6.4.2RC2'].G_open_cell_old
    G_open_cell_old.restype = c_int
    G_open_cell_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 859
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__open_cell_old'):
    G__open_cell_old = _libs['grass_gis.6.4.2RC2'].G__open_cell_old
    G__open_cell_old.restype = c_int
    G__open_cell_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 860
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_cell_new'):
    G_open_cell_new = _libs['grass_gis.6.4.2RC2'].G_open_cell_new
    G_open_cell_new.restype = c_int
    G_open_cell_new.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 861
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_cell_new_random'):
    G_open_cell_new_random = _libs['grass_gis.6.4.2RC2'].G_open_cell_new_random
    G_open_cell_new_random.restype = c_int
    G_open_cell_new_random.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 862
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_cell_new_uncompressed'):
    G_open_cell_new_uncompressed = _libs['grass_gis.6.4.2RC2'].G_open_cell_new_uncompressed
    G_open_cell_new_uncompressed.restype = c_int
    G_open_cell_new_uncompressed.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 863
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_want_histogram'):
    G_want_histogram = _libs['grass_gis.6.4.2RC2'].G_want_histogram
    G_want_histogram.restype = c_int
    G_want_histogram.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 864
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_cell_format'):
    G_set_cell_format = _libs['grass_gis.6.4.2RC2'].G_set_cell_format
    G_set_cell_format.restype = c_int
    G_set_cell_format.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 865
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_cellvalue_format'):
    G_cellvalue_format = _libs['grass_gis.6.4.2RC2'].G_cellvalue_format
    G_cellvalue_format.restype = c_int
    G_cellvalue_format.argtypes = [CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 866
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_fp_cell_new'):
    G_open_fp_cell_new = _libs['grass_gis.6.4.2RC2'].G_open_fp_cell_new
    G_open_fp_cell_new.restype = c_int
    G_open_fp_cell_new.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 867
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_fp_cell_new_uncompressed'):
    G_open_fp_cell_new_uncompressed = _libs['grass_gis.6.4.2RC2'].G_open_fp_cell_new_uncompressed
    G_open_fp_cell_new_uncompressed.restype = c_int
    G_open_fp_cell_new_uncompressed.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 868
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__reallocate_work_buf'):
    G__reallocate_work_buf = _libs['grass_gis.6.4.2RC2'].G__reallocate_work_buf
    G__reallocate_work_buf.restype = c_int
    G__reallocate_work_buf.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 869
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__reallocate_null_buf'):
    G__reallocate_null_buf = _libs['grass_gis.6.4.2RC2'].G__reallocate_null_buf
    G__reallocate_null_buf.restype = c_int
    G__reallocate_null_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 870
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__reallocate_mask_buf'):
    G__reallocate_mask_buf = _libs['grass_gis.6.4.2RC2'].G__reallocate_mask_buf
    G__reallocate_mask_buf.restype = c_int
    G__reallocate_mask_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 871
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__reallocate_temp_buf'):
    G__reallocate_temp_buf = _libs['grass_gis.6.4.2RC2'].G__reallocate_temp_buf
    G__reallocate_temp_buf.restype = c_int
    G__reallocate_temp_buf.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 872
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_fp_type'):
    G_set_fp_type = _libs['grass_gis.6.4.2RC2'].G_set_fp_type
    G_set_fp_type.restype = c_int
    G_set_fp_type.argtypes = [RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 873
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_raster_map_is_fp'):
    G_raster_map_is_fp = _libs['grass_gis.6.4.2RC2'].G_raster_map_is_fp
    G_raster_map_is_fp.restype = c_int
    G_raster_map_is_fp.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 874
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_raster_map_type'):
    G_raster_map_type = _libs['grass_gis.6.4.2RC2'].G_raster_map_type
    G_raster_map_type.restype = RASTER_MAP_TYPE
    G_raster_map_type.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 875
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__check_fp_type'):
    G__check_fp_type = _libs['grass_gis.6.4.2RC2'].G__check_fp_type
    G__check_fp_type.restype = RASTER_MAP_TYPE
    G__check_fp_type.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 876
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_map_type'):
    G_get_raster_map_type = _libs['grass_gis.6.4.2RC2'].G_get_raster_map_type
    G_get_raster_map_type.restype = RASTER_MAP_TYPE
    G_get_raster_map_type.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 877
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_raster_new'):
    G_open_raster_new = _libs['grass_gis.6.4.2RC2'].G_open_raster_new
    G_open_raster_new.restype = c_int
    G_open_raster_new.argtypes = [String, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 878
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_open_raster_new_uncompressed'):
    G_open_raster_new_uncompressed = _libs['grass_gis.6.4.2RC2'].G_open_raster_new_uncompressed
    G_open_raster_new_uncompressed.restype = c_int
    G_open_raster_new_uncompressed.argtypes = [String, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 879
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_quant_rules'):
    G_set_quant_rules = _libs['grass_gis.6.4.2RC2'].G_set_quant_rules
    G_set_quant_rules.restype = c_int
    G_set_quant_rules.argtypes = [c_int, POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 882
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_check_overwrite'):
    G_check_overwrite = _libs['grass_gis.6.4.2RC2'].G_check_overwrite
    G_check_overwrite.restype = c_int
    G_check_overwrite.argtypes = [c_int, POINTER(POINTER(c_char))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 885
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_disable_interactive'):
    G_disable_interactive = _libs['grass_gis.6.4.2RC2'].G_disable_interactive
    G_disable_interactive.restype = c_int
    G_disable_interactive.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 886
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_define_module'):
    G_define_module = _libs['grass_gis.6.4.2RC2'].G_define_module
    G_define_module.restype = POINTER(struct_GModule)
    G_define_module.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 887
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_define_flag'):
    G_define_flag = _libs['grass_gis.6.4.2RC2'].G_define_flag
    G_define_flag.restype = POINTER(struct_Flag)
    G_define_flag.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 888
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_define_option'):
    G_define_option = _libs['grass_gis.6.4.2RC2'].G_define_option
    G_define_option.restype = POINTER(struct_Option)
    G_define_option.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 889
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_define_standard_option'):
    G_define_standard_option = _libs['grass_gis.6.4.2RC2'].G_define_standard_option
    G_define_standard_option.restype = POINTER(struct_Option)
    G_define_standard_option.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 890
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_parser'):
    G_parser = _libs['grass_gis.6.4.2RC2'].G_parser
    G_parser.restype = c_int
    G_parser.argtypes = [c_int, POINTER(POINTER(c_char))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 891
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_usage'):
    G_usage = _libs['grass_gis.6.4.2RC2'].G_usage
    G_usage.restype = c_int
    G_usage.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 892
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_recreate_command'):
    G_recreate_command = _libs['grass_gis.6.4.2RC2'].G_recreate_command
    G_recreate_command.restype = ReturnString
    G_recreate_command.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 895
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_mkdir'):
    G_mkdir = _libs['grass_gis.6.4.2RC2'].G_mkdir
    G_mkdir.restype = c_int
    G_mkdir.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 896
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_dirsep'):
    G_is_dirsep = _libs['grass_gis.6.4.2RC2'].G_is_dirsep
    G_is_dirsep.restype = c_int
    G_is_dirsep.argtypes = [c_char]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 897
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_absolute_path'):
    G_is_absolute_path = _libs['grass_gis.6.4.2RC2'].G_is_absolute_path
    G_is_absolute_path.restype = c_int
    G_is_absolute_path.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 898
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_convert_dirseps_to_host'):
    G_convert_dirseps_to_host = _libs['grass_gis.6.4.2RC2'].G_convert_dirseps_to_host
    G_convert_dirseps_to_host.restype = ReturnString
    G_convert_dirseps_to_host.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 899
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_convert_dirseps_from_host'):
    G_convert_dirseps_from_host = _libs['grass_gis.6.4.2RC2'].G_convert_dirseps_from_host
    G_convert_dirseps_from_host.restype = ReturnString
    G_convert_dirseps_from_host.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 900
class struct_stat(Structure):
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 901
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_lstat'):
    G_lstat = _libs['grass_gis.6.4.2RC2'].G_lstat
    G_lstat.restype = c_int
    G_lstat.argtypes = [String, POINTER(struct_stat)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 902
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_stat'):
    G_stat = _libs['grass_gis.6.4.2RC2'].G_stat
    G_stat.restype = c_int
    G_stat.argtypes = [String, POINTER(struct_stat)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 905
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_percent'):
    G_percent = _libs['grass_gis.6.4.2RC2'].G_percent
    G_percent.restype = c_int
    G_percent.argtypes = [c_long, c_long, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 906
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_percent2'):
    G_percent2 = _libs['grass_gis.6.4.2RC2'].G_percent2
    G_percent2.restype = c_int
    G_percent2.argtypes = [c_long, c_long, c_int, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 907
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_percent_reset'):
    G_percent_reset = _libs['grass_gis.6.4.2RC2'].G_percent_reset
    G_percent_reset.restype = c_int
    G_percent_reset.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 908
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_percent_routine'):
    G_set_percent_routine = _libs['grass_gis.6.4.2RC2'].G_set_percent_routine
    G_set_percent_routine.restype = None
    G_set_percent_routine.argtypes = [CFUNCTYPE(UNCHECKED(c_int), c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 909
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unset_percent_routine'):
    G_unset_percent_routine = _libs['grass_gis.6.4.2RC2'].G_unset_percent_routine
    G_unset_percent_routine.restype = None
    G_unset_percent_routine.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 912
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_setup_plot'):
    G_setup_plot = _libs['grass_gis.6.4.2RC2'].G_setup_plot
    G_setup_plot.restype = c_int
    G_setup_plot.argtypes = [c_double, c_double, c_double, c_double, CFUNCTYPE(UNCHECKED(c_int), c_int, c_int), CFUNCTYPE(UNCHECKED(c_int), c_int, c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 914
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_setup_fill'):
    G_setup_fill = _libs['grass_gis.6.4.2RC2'].G_setup_fill
    G_setup_fill.restype = c_int
    G_setup_fill.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 915
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_where_xy'):
    G_plot_where_xy = _libs['grass_gis.6.4.2RC2'].G_plot_where_xy
    G_plot_where_xy.restype = c_int
    G_plot_where_xy.argtypes = [c_double, c_double, POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 916
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_where_en'):
    G_plot_where_en = _libs['grass_gis.6.4.2RC2'].G_plot_where_en
    G_plot_where_en.restype = c_int
    G_plot_where_en.argtypes = [c_int, c_int, POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 917
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_point'):
    G_plot_point = _libs['grass_gis.6.4.2RC2'].G_plot_point
    G_plot_point.restype = c_int
    G_plot_point.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 918
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_line'):
    G_plot_line = _libs['grass_gis.6.4.2RC2'].G_plot_line
    G_plot_line.restype = c_int
    G_plot_line.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 919
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_line2'):
    G_plot_line2 = _libs['grass_gis.6.4.2RC2'].G_plot_line2
    G_plot_line2.restype = c_int
    G_plot_line2.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 920
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_polygon'):
    G_plot_polygon = _libs['grass_gis.6.4.2RC2'].G_plot_polygon
    G_plot_polygon.restype = c_int
    G_plot_polygon.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 921
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_area'):
    G_plot_area = _libs['grass_gis.6.4.2RC2'].G_plot_area
    G_plot_area.restype = c_int
    G_plot_area.argtypes = [POINTER(POINTER(c_double)), POINTER(POINTER(c_double)), POINTER(c_int), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 922
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_fx'):
    G_plot_fx = _libs['grass_gis.6.4.2RC2'].G_plot_fx
    G_plot_fx.restype = c_int
    G_plot_fx.argtypes = [CFUNCTYPE(UNCHECKED(c_double), c_double), c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 923
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_plot_icon'):
    G_plot_icon = _libs['grass_gis.6.4.2RC2'].G_plot_icon
    G_plot_icon.restype = c_int
    G_plot_icon.argtypes = [c_double, c_double, c_int, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 926
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_pole_in_polygon'):
    G_pole_in_polygon = _libs['grass_gis.6.4.2RC2'].G_pole_in_polygon
    G_pole_in_polygon.restype = c_int
    G_pole_in_polygon.argtypes = [POINTER(c_double), POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 929
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_popen'):
    G_popen = _libs['grass_gis.6.4.2RC2'].G_popen
    G_popen.restype = POINTER(FILE)
    G_popen.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 930
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_pclose'):
    G_pclose = _libs['grass_gis.6.4.2RC2'].G_pclose
    G_pclose.restype = c_int
    G_pclose.argtypes = [POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 933
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_program_name'):
    G_program_name = _libs['grass_gis.6.4.2RC2'].G_program_name
    G_program_name.restype = ReturnString
    G_program_name.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 934
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_program_name'):
    G_set_program_name = _libs['grass_gis.6.4.2RC2'].G_set_program_name
    G_set_program_name.restype = c_int
    G_set_program_name.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 937
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_projection'):
    G_projection = _libs['grass_gis.6.4.2RC2'].G_projection
    G_projection.restype = c_int
    G_projection.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 940
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__projection_units'):
    G__projection_units = _libs['grass_gis.6.4.2RC2'].G__projection_units
    G__projection_units.restype = c_int
    G__projection_units.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 941
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__unit_name'):
    G__unit_name = _libs['grass_gis.6.4.2RC2'].G__unit_name
    G__unit_name.restype = ReturnString
    G__unit_name.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 942
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__projection_name'):
    G__projection_name = _libs['grass_gis.6.4.2RC2'].G__projection_name
    G__projection_name.restype = ReturnString
    G__projection_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 945
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_database_unit_name'):
    G_database_unit_name = _libs['grass_gis.6.4.2RC2'].G_database_unit_name
    G_database_unit_name.restype = ReturnString
    G_database_unit_name.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 946
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_database_projection_name'):
    G_database_projection_name = _libs['grass_gis.6.4.2RC2'].G_database_projection_name
    G_database_projection_name.restype = ReturnString
    G_database_projection_name.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 947
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_database_units_to_meters_factor'):
    G_database_units_to_meters_factor = _libs['grass_gis.6.4.2RC2'].G_database_units_to_meters_factor
    G_database_units_to_meters_factor.restype = c_double
    G_database_units_to_meters_factor.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 948
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_database_datum_name'):
    G_database_datum_name = _libs['grass_gis.6.4.2RC2'].G_database_datum_name
    G_database_datum_name.restype = ReturnString
    G_database_datum_name.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 949
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_database_ellipse_name'):
    G_database_ellipse_name = _libs['grass_gis.6.4.2RC2'].G_database_ellipse_name
    G_database_ellipse_name.restype = ReturnString
    G_database_ellipse_name.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 952
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_cellhd'):
    G_put_cellhd = _libs['grass_gis.6.4.2RC2'].G_put_cellhd
    G_put_cellhd.restype = c_int
    G_put_cellhd.argtypes = [String, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 955
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zeros_r_nulls'):
    G_zeros_r_nulls = _libs['grass_gis.6.4.2RC2'].G_zeros_r_nulls
    G_zeros_r_nulls.restype = c_int
    G_zeros_r_nulls.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 956
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_map_row'):
    G_put_map_row = _libs['grass_gis.6.4.2RC2'].G_put_map_row
    G_put_map_row.restype = c_int
    G_put_map_row.argtypes = [c_int, POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 957
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_map_row_random'):
    G_put_map_row_random = _libs['grass_gis.6.4.2RC2'].G_put_map_row_random
    G_put_map_row_random.restype = c_int
    G_put_map_row_random.argtypes = [c_int, POINTER(CELL), c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 958
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__put_null_value_row'):
    G__put_null_value_row = _libs['grass_gis.6.4.2RC2'].G__put_null_value_row
    G__put_null_value_row.restype = c_int
    G__put_null_value_row.argtypes = [c_int, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 959
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_raster_row'):
    G_put_raster_row = _libs['grass_gis.6.4.2RC2'].G_put_raster_row
    G_put_raster_row.restype = c_int
    G_put_raster_row.argtypes = [c_int, POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 960
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_c_raster_row'):
    G_put_c_raster_row = _libs['grass_gis.6.4.2RC2'].G_put_c_raster_row
    G_put_c_raster_row.restype = c_int
    G_put_c_raster_row.argtypes = [c_int, POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 961
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_f_raster_row'):
    G_put_f_raster_row = _libs['grass_gis.6.4.2RC2'].G_put_f_raster_row
    G_put_f_raster_row.restype = c_int
    G_put_f_raster_row.argtypes = [c_int, POINTER(FCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 962
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_d_raster_row'):
    G_put_d_raster_row = _libs['grass_gis.6.4.2RC2'].G_put_d_raster_row
    G_put_d_raster_row.restype = c_int
    G_put_d_raster_row.argtypes = [c_int, POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 963
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_data'):
    G__write_data = _libs['grass_gis.6.4.2RC2'].G__write_data
    G__write_data.restype = c_int
    G__write_data.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 964
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_data_compressed'):
    G__write_data_compressed = _libs['grass_gis.6.4.2RC2'].G__write_data_compressed
    G__write_data_compressed.restype = c_int
    G__write_data_compressed.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 965
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__open_null_write'):
    G__open_null_write = _libs['grass_gis.6.4.2RC2'].G__open_null_write
    G__open_null_write.restype = c_int
    G__open_null_write.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 966
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_null_bits'):
    G__write_null_bits = _libs['grass_gis.6.4.2RC2'].G__write_null_bits
    G__write_null_bits.restype = c_int
    G__write_null_bits.argtypes = [c_int, POINTER(c_ubyte), c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 969
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_cell_title'):
    G_put_cell_title = _libs['grass_gis.6.4.2RC2'].G_put_cell_title
    G_put_cell_title.restype = c_int
    G_put_cell_title.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 972
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_window'):
    G_put_window = _libs['grass_gis.6.4.2RC2'].G_put_window
    G_put_window.restype = c_int
    G_put_window.argtypes = [POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 973
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__put_window'):
    G__put_window = _libs['grass_gis.6.4.2RC2'].G__put_window
    G__put_window.restype = c_int
    G__put_window.argtypes = [POINTER(struct_Cell_head), String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 976
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_putenv'):
    G_putenv = _libs['grass_gis.6.4.2RC2'].G_putenv
    G_putenv.restype = None
    G_putenv.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 979
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_clear'):
    G_quant_clear = _libs['grass_gis.6.4.2RC2'].G_quant_clear
    G_quant_clear.restype = None
    G_quant_clear.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 980
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_free'):
    G_quant_free = _libs['grass_gis.6.4.2RC2'].G_quant_free
    G_quant_free.restype = None
    G_quant_free.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 981
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__quant_organize_fp_lookup'):
    G__quant_organize_fp_lookup = _libs['grass_gis.6.4.2RC2'].G__quant_organize_fp_lookup
    G__quant_organize_fp_lookup.restype = c_int
    G__quant_organize_fp_lookup.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 982
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_init'):
    G_quant_init = _libs['grass_gis.6.4.2RC2'].G_quant_init
    G_quant_init.restype = c_int
    G_quant_init.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 983
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_is_truncate'):
    G_quant_is_truncate = _libs['grass_gis.6.4.2RC2'].G_quant_is_truncate
    G_quant_is_truncate.restype = c_int
    G_quant_is_truncate.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 984
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_is_round'):
    G_quant_is_round = _libs['grass_gis.6.4.2RC2'].G_quant_is_round
    G_quant_is_round.restype = c_int
    G_quant_is_round.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 985
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_truncate'):
    G_quant_truncate = _libs['grass_gis.6.4.2RC2'].G_quant_truncate
    G_quant_truncate.restype = c_int
    G_quant_truncate.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 986
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_round'):
    G_quant_round = _libs['grass_gis.6.4.2RC2'].G_quant_round
    G_quant_round.restype = c_int
    G_quant_round.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 987
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_get_limits'):
    G_quant_get_limits = _libs['grass_gis.6.4.2RC2'].G_quant_get_limits
    G_quant_get_limits.restype = c_int
    G_quant_get_limits.argtypes = [POINTER(struct_Quant), POINTER(DCELL), POINTER(DCELL), POINTER(CELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 989
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_nof_rules'):
    G_quant_nof_rules = _libs['grass_gis.6.4.2RC2'].G_quant_nof_rules
    G_quant_nof_rules.restype = c_int
    G_quant_nof_rules.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 990
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_get_ith_rule'):
    G_quant_get_ith_rule = _libs['grass_gis.6.4.2RC2'].G_quant_get_ith_rule
    G_quant_get_ith_rule.restype = None
    G_quant_get_ith_rule.argtypes = [POINTER(struct_Quant), c_int, POINTER(DCELL), POINTER(DCELL), POINTER(CELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 992
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_set_neg_infinite_rule'):
    G_quant_set_neg_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_quant_set_neg_infinite_rule
    G_quant_set_neg_infinite_rule.restype = None
    G_quant_set_neg_infinite_rule.argtypes = [POINTER(struct_Quant), DCELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 993
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_get_neg_infinite_rule'):
    G_quant_get_neg_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_quant_get_neg_infinite_rule
    G_quant_get_neg_infinite_rule.restype = c_int
    G_quant_get_neg_infinite_rule.argtypes = [POINTER(struct_Quant), POINTER(DCELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 994
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_set_pos_infinite_rule'):
    G_quant_set_pos_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_quant_set_pos_infinite_rule
    G_quant_set_pos_infinite_rule.restype = None
    G_quant_set_pos_infinite_rule.argtypes = [POINTER(struct_Quant), DCELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 995
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_get_pos_infinite_rule'):
    G_quant_get_pos_infinite_rule = _libs['grass_gis.6.4.2RC2'].G_quant_get_pos_infinite_rule
    G_quant_get_pos_infinite_rule.restype = c_int
    G_quant_get_pos_infinite_rule.argtypes = [POINTER(struct_Quant), POINTER(DCELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 996
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_add_rule'):
    G_quant_add_rule = _libs['grass_gis.6.4.2RC2'].G_quant_add_rule
    G_quant_add_rule.restype = None
    G_quant_add_rule.argtypes = [POINTER(struct_Quant), DCELL, DCELL, CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 997
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_reverse_rule_order'):
    G_quant_reverse_rule_order = _libs['grass_gis.6.4.2RC2'].G_quant_reverse_rule_order
    G_quant_reverse_rule_order.restype = None
    G_quant_reverse_rule_order.argtypes = [POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 998
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_get_cell_value'):
    G_quant_get_cell_value = _libs['grass_gis.6.4.2RC2'].G_quant_get_cell_value
    G_quant_get_cell_value.restype = CELL
    G_quant_get_cell_value.argtypes = [POINTER(struct_Quant), DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 999
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_perform_d'):
    G_quant_perform_d = _libs['grass_gis.6.4.2RC2'].G_quant_perform_d
    G_quant_perform_d.restype = None
    G_quant_perform_d.argtypes = [POINTER(struct_Quant), POINTER(DCELL), POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1000
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quant_perform_f'):
    G_quant_perform_f = _libs['grass_gis.6.4.2RC2'].G_quant_perform_f
    G_quant_perform_f.restype = None
    G_quant_perform_f.argtypes = [POINTER(struct_Quant), POINTER(FCELL), POINTER(CELL), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1001
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__quant_get_rule_for_d_raster_val'):
    G__quant_get_rule_for_d_raster_val = _libs['grass_gis.6.4.2RC2'].G__quant_get_rule_for_d_raster_val
    G__quant_get_rule_for_d_raster_val.restype = POINTER(struct_Quant_table)
    G__quant_get_rule_for_d_raster_val.argtypes = [POINTER(struct_Quant), DCELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1005
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__quant_import'):
    G__quant_import = _libs['grass_gis.6.4.2RC2'].G__quant_import
    G__quant_import.restype = c_int
    G__quant_import.argtypes = [String, String, POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1006
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__quant_export'):
    G__quant_export = _libs['grass_gis.6.4.2RC2'].G__quant_export
    G__quant_export.restype = c_int
    G__quant_export.argtypes = [String, String, POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1009
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_truncate_fp_map'):
    G_truncate_fp_map = _libs['grass_gis.6.4.2RC2'].G_truncate_fp_map
    G_truncate_fp_map.restype = c_int
    G_truncate_fp_map.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1010
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_round_fp_map'):
    G_round_fp_map = _libs['grass_gis.6.4.2RC2'].G_round_fp_map
    G_round_fp_map.restype = c_int
    G_round_fp_map.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1011
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quantize_fp_map'):
    G_quantize_fp_map = _libs['grass_gis.6.4.2RC2'].G_quantize_fp_map
    G_quantize_fp_map.restype = c_int
    G_quantize_fp_map.argtypes = [String, String, CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1012
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_quantize_fp_map_range'):
    G_quantize_fp_map_range = _libs['grass_gis.6.4.2RC2'].G_quantize_fp_map_range
    G_quantize_fp_map_range.restype = c_int
    G_quantize_fp_map_range.argtypes = [String, String, DCELL, DCELL, CELL, CELL]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1014
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_quant'):
    G_write_quant = _libs['grass_gis.6.4.2RC2'].G_write_quant
    G_write_quant.restype = c_int
    G_write_quant.argtypes = [String, String, POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1015
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_quant'):
    G_read_quant = _libs['grass_gis.6.4.2RC2'].G_read_quant
    G_read_quant.restype = c_int
    G_read_quant.argtypes = [String, String, POINTER(struct_Quant)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1018
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_meridional_radius_of_curvature'):
    G_meridional_radius_of_curvature = _libs['grass_gis.6.4.2RC2'].G_meridional_radius_of_curvature
    G_meridional_radius_of_curvature.restype = c_double
    G_meridional_radius_of_curvature.argtypes = [c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1019
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_transverse_radius_of_curvature'):
    G_transverse_radius_of_curvature = _libs['grass_gis.6.4.2RC2'].G_transverse_radius_of_curvature
    G_transverse_radius_of_curvature.restype = c_double
    G_transverse_radius_of_curvature.argtypes = [c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1020
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_radius_of_conformal_tangent_sphere'):
    G_radius_of_conformal_tangent_sphere = _libs['grass_gis.6.4.2RC2'].G_radius_of_conformal_tangent_sphere
    G_radius_of_conformal_tangent_sphere.restype = c_double
    G_radius_of_conformal_tangent_sphere.argtypes = [c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1023
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__remove_fp_range'):
    G__remove_fp_range = _libs['grass_gis.6.4.2RC2'].G__remove_fp_range
    G__remove_fp_range.restype = c_int
    G__remove_fp_range.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1024
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_construct_default_range'):
    G_construct_default_range = _libs['grass_gis.6.4.2RC2'].G_construct_default_range
    G_construct_default_range.restype = c_int
    G_construct_default_range.argtypes = [POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1025
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_fp_range'):
    G_read_fp_range = _libs['grass_gis.6.4.2RC2'].G_read_fp_range
    G_read_fp_range.restype = c_int
    G_read_fp_range.argtypes = [String, String, POINTER(struct_FPRange)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1026
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_range'):
    G_read_range = _libs['grass_gis.6.4.2RC2'].G_read_range
    G_read_range.restype = c_int
    G_read_range.argtypes = [String, String, POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1027
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_range'):
    G_write_range = _libs['grass_gis.6.4.2RC2'].G_write_range
    G_write_range.restype = c_int
    G_write_range.argtypes = [String, POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1028
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_fp_range'):
    G_write_fp_range = _libs['grass_gis.6.4.2RC2'].G_write_fp_range
    G_write_fp_range.restype = c_int
    G_write_fp_range.argtypes = [String, POINTER(struct_FPRange)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1029
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_update_range'):
    G_update_range = _libs['grass_gis.6.4.2RC2'].G_update_range
    G_update_range.restype = c_int
    G_update_range.argtypes = [CELL, POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1030
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_update_fp_range'):
    G_update_fp_range = _libs['grass_gis.6.4.2RC2'].G_update_fp_range
    G_update_fp_range.restype = c_int
    G_update_fp_range.argtypes = [DCELL, POINTER(struct_FPRange)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1031
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_row_update_range'):
    G_row_update_range = _libs['grass_gis.6.4.2RC2'].G_row_update_range
    G_row_update_range.restype = c_int
    G_row_update_range.argtypes = [POINTER(CELL), c_int, POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1032
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__row_update_range'):
    G__row_update_range = _libs['grass_gis.6.4.2RC2'].G__row_update_range
    G__row_update_range.restype = c_int
    G__row_update_range.argtypes = [POINTER(CELL), c_int, POINTER(struct_Range), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1033
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_row_update_fp_range'):
    G_row_update_fp_range = _libs['grass_gis.6.4.2RC2'].G_row_update_fp_range
    G_row_update_fp_range.restype = c_int
    G_row_update_fp_range.argtypes = [POINTER(None), c_int, POINTER(struct_FPRange), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1035
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_range'):
    G_init_range = _libs['grass_gis.6.4.2RC2'].G_init_range
    G_init_range.restype = c_int
    G_init_range.argtypes = [POINTER(struct_Range)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1036
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_range_min_max'):
    G_get_range_min_max = _libs['grass_gis.6.4.2RC2'].G_get_range_min_max
    G_get_range_min_max.restype = c_int
    G_get_range_min_max.argtypes = [POINTER(struct_Range), POINTER(CELL), POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1037
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_fp_range'):
    G_init_fp_range = _libs['grass_gis.6.4.2RC2'].G_init_fp_range
    G_init_fp_range.restype = c_int
    G_init_fp_range.argtypes = [POINTER(struct_FPRange)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1038
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_fp_range_min_max'):
    G_get_fp_range_min_max = _libs['grass_gis.6.4.2RC2'].G_get_fp_range_min_max
    G_get_fp_range_min_max.restype = c_int
    G_get_fp_range_min_max.argtypes = [POINTER(struct_FPRange), POINTER(DCELL), POINTER(DCELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1041
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_incr_void_ptr'):
    G_incr_void_ptr = _libs['grass_gis.6.4.2RC2'].G_incr_void_ptr
    G_incr_void_ptr.restype = POINTER(None)
    G_incr_void_ptr.argtypes = [POINTER(None), c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1042
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_raster_cmp'):
    G_raster_cmp = _libs['grass_gis.6.4.2RC2'].G_raster_cmp
    G_raster_cmp.restype = c_int
    G_raster_cmp.argtypes = [POINTER(None), POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1043
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_raster_cpy'):
    G_raster_cpy = _libs['grass_gis.6.4.2RC2'].G_raster_cpy
    G_raster_cpy.restype = c_int
    G_raster_cpy.argtypes = [POINTER(None), POINTER(None), c_int, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1044
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_value_c'):
    G_set_raster_value_c = _libs['grass_gis.6.4.2RC2'].G_set_raster_value_c
    G_set_raster_value_c.restype = c_int
    G_set_raster_value_c.argtypes = [POINTER(None), CELL, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1045
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_value_f'):
    G_set_raster_value_f = _libs['grass_gis.6.4.2RC2'].G_set_raster_value_f
    G_set_raster_value_f.restype = c_int
    G_set_raster_value_f.argtypes = [POINTER(None), FCELL, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1046
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_raster_value_d'):
    G_set_raster_value_d = _libs['grass_gis.6.4.2RC2'].G_set_raster_value_d
    G_set_raster_value_d.restype = c_int
    G_set_raster_value_d.argtypes = [POINTER(None), DCELL, RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1047
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_value_c'):
    G_get_raster_value_c = _libs['grass_gis.6.4.2RC2'].G_get_raster_value_c
    G_get_raster_value_c.restype = CELL
    G_get_raster_value_c.argtypes = [POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1048
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_value_f'):
    G_get_raster_value_f = _libs['grass_gis.6.4.2RC2'].G_get_raster_value_f
    G_get_raster_value_f.restype = FCELL
    G_get_raster_value_f.argtypes = [POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1049
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_value_d'):
    G_get_raster_value_d = _libs['grass_gis.6.4.2RC2'].G_get_raster_value_d
    G_get_raster_value_d.restype = DCELL
    G_get_raster_value_d.argtypes = [POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1052
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_raster_units'):
    G_read_raster_units = _libs['grass_gis.6.4.2RC2'].G_read_raster_units
    G_read_raster_units.restype = c_int
    G_read_raster_units.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1053
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_raster_vdatum'):
    G_read_raster_vdatum = _libs['grass_gis.6.4.2RC2'].G_read_raster_vdatum
    G_read_raster_vdatum.restype = c_int
    G_read_raster_vdatum.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1054
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_raster_units'):
    G_write_raster_units = _libs['grass_gis.6.4.2RC2'].G_write_raster_units
    G_write_raster_units.restype = c_int
    G_write_raster_units.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1055
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_raster_vdatum'):
    G_write_raster_vdatum = _libs['grass_gis.6.4.2RC2'].G_write_raster_vdatum
    G_write_raster_vdatum.restype = c_int
    G_write_raster_vdatum.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1056
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__raster_misc_read_line'):
    G__raster_misc_read_line = _libs['grass_gis.6.4.2RC2'].G__raster_misc_read_line
    G__raster_misc_read_line.restype = c_int
    G__raster_misc_read_line.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1058
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__raster_misc_write_line'):
    G__raster_misc_write_line = _libs['grass_gis.6.4.2RC2'].G__raster_misc_write_line
    G__raster_misc_write_line.restype = c_int
    G__raster_misc_write_line.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1061
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_Cell_head'):
    G__read_Cell_head = _libs['grass_gis.6.4.2RC2'].G__read_Cell_head
    G__read_Cell_head.restype = ReturnString
    G__read_Cell_head.argtypes = [POINTER(FILE), POINTER(struct_Cell_head), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1062
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_Cell_head_array'):
    G__read_Cell_head_array = _libs['grass_gis.6.4.2RC2'].G__read_Cell_head_array
    G__read_Cell_head_array.restype = ReturnString
    G__read_Cell_head_array.argtypes = [POINTER(POINTER(c_char)), POINTER(struct_Cell_head), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1065
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_reclass'):
    G_is_reclass = _libs['grass_gis.6.4.2RC2'].G_is_reclass
    G_is_reclass.restype = c_int
    G_is_reclass.argtypes = [String, String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1066
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_is_reclassed_to'):
    G_is_reclassed_to = _libs['grass_gis.6.4.2RC2'].G_is_reclassed_to
    G_is_reclassed_to.restype = c_int
    G_is_reclassed_to.argtypes = [String, String, POINTER(c_int), POINTER(POINTER(POINTER(c_char)))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1067
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_reclass'):
    G_get_reclass = _libs['grass_gis.6.4.2RC2'].G_get_reclass
    G_get_reclass.restype = c_int
    G_get_reclass.argtypes = [String, String, POINTER(struct_Reclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1068
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_reclass'):
    G_free_reclass = _libs['grass_gis.6.4.2RC2'].G_free_reclass
    G_free_reclass.restype = c_int
    G_free_reclass.argtypes = [POINTER(struct_Reclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1069
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_reclass'):
    G_put_reclass = _libs['grass_gis.6.4.2RC2'].G_put_reclass
    G_put_reclass.restype = c_int
    G_put_reclass.argtypes = [String, POINTER(struct_Reclass)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1072
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove'):
    G_remove = _libs['grass_gis.6.4.2RC2'].G_remove
    G_remove.restype = c_int
    G_remove.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1073
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_misc'):
    G_remove_misc = _libs['grass_gis.6.4.2RC2'].G_remove_misc
    G_remove_misc.restype = c_int
    G_remove_misc.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1076
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rename_file'):
    G_rename_file = _libs['grass_gis.6.4.2RC2'].G_rename_file
    G_rename_file.restype = c_int
    G_rename_file.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1077
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rename'):
    G_rename = _libs['grass_gis.6.4.2RC2'].G_rename
    G_rename.restype = c_int
    G_rename.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1080
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_begin_rhumbline_equation'):
    G_begin_rhumbline_equation = _libs['grass_gis.6.4.2RC2'].G_begin_rhumbline_equation
    G_begin_rhumbline_equation.restype = c_int
    G_begin_rhumbline_equation.argtypes = [c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1081
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rhumbline_lat_from_lon'):
    G_rhumbline_lat_from_lon = _libs['grass_gis.6.4.2RC2'].G_rhumbline_lat_from_lon
    G_rhumbline_lat_from_lon.restype = c_double
    G_rhumbline_lat_from_lon.argtypes = [c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1084
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rotate_around_point'):
    G_rotate_around_point = _libs['grass_gis.6.4.2RC2'].G_rotate_around_point
    G_rotate_around_point.restype = None
    G_rotate_around_point.argtypes = [c_double, c_double, POINTER(c_double), POINTER(c_double), c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1085
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_rotate_around_point_int'):
    G_rotate_around_point_int = _libs['grass_gis.6.4.2RC2'].G_rotate_around_point_int
    G_rotate_around_point_int.restype = None
    G_rotate_around_point_int.argtypes = [c_int, c_int, POINTER(c_int), POINTER(c_int), c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1088
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_ftell'):
    G_ftell = _libs['grass_gis.6.4.2RC2'].G_ftell
    G_ftell.restype = c_int
    G_ftell.argtypes = [POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1089
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_fseek'):
    G_fseek = _libs['grass_gis.6.4.2RC2'].G_fseek
    G_fseek.restype = None
    G_fseek.argtypes = [POINTER(FILE), c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1092
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_sample_nearest'):
    G_get_raster_sample_nearest = _libs['grass_gis.6.4.2RC2'].G_get_raster_sample_nearest
    G_get_raster_sample_nearest.restype = DCELL
    G_get_raster_sample_nearest.argtypes = [c_int, POINTER(struct_Cell_head), POINTER(struct_Categories), c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1094
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_sample_bilinear'):
    G_get_raster_sample_bilinear = _libs['grass_gis.6.4.2RC2'].G_get_raster_sample_bilinear
    G_get_raster_sample_bilinear.restype = DCELL
    G_get_raster_sample_bilinear.argtypes = [c_int, POINTER(struct_Cell_head), POINTER(struct_Categories), c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1096
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_sample_cubic'):
    G_get_raster_sample_cubic = _libs['grass_gis.6.4.2RC2'].G_get_raster_sample_cubic
    G_get_raster_sample_cubic.restype = DCELL
    G_get_raster_sample_cubic.argtypes = [c_int, POINTER(struct_Cell_head), POINTER(struct_Categories), c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1098
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_raster_sample'):
    G_get_raster_sample = _libs['grass_gis.6.4.2RC2'].G_get_raster_sample
    G_get_raster_sample.restype = DCELL
    G_get_raster_sample.argtypes = [c_int, POINTER(struct_Cell_head), POINTER(struct_Categories), c_double, c_double, c_int, INTERP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1103
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_set_window'):
    G_get_set_window = _libs['grass_gis.6.4.2RC2'].G_get_set_window
    G_get_set_window.restype = c_int
    G_get_set_window.argtypes = [POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1104
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_window'):
    G_set_window = _libs['grass_gis.6.4.2RC2'].G_set_window
    G_set_window.restype = c_int
    G_set_window.argtypes = [POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1107
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_shortest_way'):
    G_shortest_way = _libs['grass_gis.6.4.2RC2'].G_shortest_way
    G_shortest_way.restype = c_int
    G_shortest_way.argtypes = [POINTER(c_double), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1110
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_sleep'):
    G_sleep = _libs['grass_gis.6.4.2RC2'].G_sleep
    G_sleep.restype = None
    G_sleep.argtypes = [c_uint]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1113
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_snprintf'):
    _func = _libs['grass_gis.6.4.2RC2'].G_snprintf
    _restype = c_int
    _argtypes = [String, c_size_t, String]
    G_snprintf = _variadic_function(_func,_restype,_argtypes)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1117
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_squeeze'):
    G_squeeze = _libs['grass_gis.6.4.2RC2'].G_squeeze
    G_squeeze.restype = ReturnString
    G_squeeze.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1120
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_store'):
    G_store = _libs['grass_gis.6.4.2RC2'].G_store
    G_store.restype = ReturnString
    G_store.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1123
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strcpy'):
    G_strcpy = _libs['grass_gis.6.4.2RC2'].G_strcpy
    G_strcpy.restype = ReturnString
    G_strcpy.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1124
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_chrcpy'):
    G_chrcpy = _libs['grass_gis.6.4.2RC2'].G_chrcpy
    G_chrcpy.restype = ReturnString
    G_chrcpy.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1125
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strncpy'):
    G_strncpy = _libs['grass_gis.6.4.2RC2'].G_strncpy
    G_strncpy.restype = ReturnString
    G_strncpy.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1126
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strcat'):
    G_strcat = _libs['grass_gis.6.4.2RC2'].G_strcat
    G_strcat.restype = ReturnString
    G_strcat.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1127
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_chrcat'):
    G_chrcat = _libs['grass_gis.6.4.2RC2'].G_chrcat
    G_chrcat.restype = ReturnString
    G_chrcat.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1128
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strmov'):
    G_strmov = _libs['grass_gis.6.4.2RC2'].G_strmov
    G_strmov.restype = ReturnString
    G_strmov.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1129
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_chrmov'):
    G_chrmov = _libs['grass_gis.6.4.2RC2'].G_chrmov
    G_chrmov.restype = ReturnString
    G_chrmov.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1130
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strcasecmp'):
    G_strcasecmp = _libs['grass_gis.6.4.2RC2'].G_strcasecmp
    G_strcasecmp.restype = c_int
    G_strcasecmp.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1131
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strstr'):
    G_strstr = _libs['grass_gis.6.4.2RC2'].G_strstr
    G_strstr.restype = ReturnString
    G_strstr.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1132
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strdup'):
    G_strdup = _libs['grass_gis.6.4.2RC2'].G_strdup
    G_strdup.restype = ReturnString
    G_strdup.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1133
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strchg'):
    G_strchg = _libs['grass_gis.6.4.2RC2'].G_strchg
    G_strchg.restype = ReturnString
    G_strchg.argtypes = [String, c_char, c_char]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1134
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_str_replace'):
    G_str_replace = _libs['grass_gis.6.4.2RC2'].G_str_replace
    G_str_replace.restype = ReturnString
    G_str_replace.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1135
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_str_to_upper'):
    G_str_to_upper = _libs['grass_gis.6.4.2RC2'].G_str_to_upper
    G_str_to_upper.restype = None
    G_str_to_upper.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1136
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_str_to_lower'):
    G_str_to_lower = _libs['grass_gis.6.4.2RC2'].G_str_to_lower
    G_str_to_lower.restype = None
    G_str_to_lower.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1137
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_str_to_sql'):
    G_str_to_sql = _libs['grass_gis.6.4.2RC2'].G_str_to_sql
    G_str_to_sql.restype = c_int
    G_str_to_sql.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1138
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_strip'):
    G_strip = _libs['grass_gis.6.4.2RC2'].G_strip
    G_strip.restype = c_int
    G_strip.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1141
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_system'):
    G_system = _libs['grass_gis.6.4.2RC2'].G_system
    G_system.restype = c_int
    G_system.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1144
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_tempfile'):
    G_tempfile = _libs['grass_gis.6.4.2RC2'].G_tempfile
    G_tempfile.restype = ReturnString
    G_tempfile.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1145
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__tempfile'):
    G__tempfile = _libs['grass_gis.6.4.2RC2'].G__tempfile
    G__tempfile.restype = ReturnString
    G__tempfile.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1146
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__temp_element'):
    G__temp_element = _libs['grass_gis.6.4.2RC2'].G__temp_element
    G__temp_element.restype = c_int
    G__temp_element.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1149
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_init_timestamp'):
    G_init_timestamp = _libs['grass_gis.6.4.2RC2'].G_init_timestamp
    G_init_timestamp.restype = None
    G_init_timestamp.argtypes = [POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1150
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_timestamp'):
    G_set_timestamp = _libs['grass_gis.6.4.2RC2'].G_set_timestamp
    G_set_timestamp.restype = None
    G_set_timestamp.argtypes = [POINTER(struct_TimeStamp), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1151
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_timestamp_range'):
    G_set_timestamp_range = _libs['grass_gis.6.4.2RC2'].G_set_timestamp_range
    G_set_timestamp_range.restype = None
    G_set_timestamp_range.argtypes = [POINTER(struct_TimeStamp), POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1153
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__read_timestamp'):
    G__read_timestamp = _libs['grass_gis.6.4.2RC2'].G__read_timestamp
    G__read_timestamp.restype = c_int
    G__read_timestamp.argtypes = [POINTER(FILE), POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1154
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_timestamp'):
    G__write_timestamp = _libs['grass_gis.6.4.2RC2'].G__write_timestamp
    G__write_timestamp.restype = c_int
    G__write_timestamp.argtypes = [POINTER(FILE), POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1155
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_timestamps'):
    G_get_timestamps = _libs['grass_gis.6.4.2RC2'].G_get_timestamps
    G_get_timestamps.restype = c_int
    G_get_timestamps.argtypes = [POINTER(struct_TimeStamp), POINTER(DateTime), POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1156
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_raster_timestamp'):
    G_read_raster_timestamp = _libs['grass_gis.6.4.2RC2'].G_read_raster_timestamp
    G_read_raster_timestamp.restype = c_int
    G_read_raster_timestamp.argtypes = [String, String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1157
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_vector_timestamp'):
    G_read_vector_timestamp = _libs['grass_gis.6.4.2RC2'].G_read_vector_timestamp
    G_read_vector_timestamp.restype = c_int
    G_read_vector_timestamp.argtypes = [String, String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1158
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_raster_timestamp'):
    G_write_raster_timestamp = _libs['grass_gis.6.4.2RC2'].G_write_raster_timestamp
    G_write_raster_timestamp.restype = c_int
    G_write_raster_timestamp.argtypes = [String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1159
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_vector_timestamp'):
    G_write_vector_timestamp = _libs['grass_gis.6.4.2RC2'].G_write_vector_timestamp
    G_write_vector_timestamp.restype = c_int
    G_write_vector_timestamp.argtypes = [String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1160
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_format_timestamp'):
    G_format_timestamp = _libs['grass_gis.6.4.2RC2'].G_format_timestamp
    G_format_timestamp.restype = c_int
    G_format_timestamp.argtypes = [POINTER(struct_TimeStamp), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1161
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_scan_timestamp'):
    G_scan_timestamp = _libs['grass_gis.6.4.2RC2'].G_scan_timestamp
    G_scan_timestamp.restype = c_int
    G_scan_timestamp.argtypes = [POINTER(struct_TimeStamp), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1162
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_raster_timestamp'):
    G_remove_raster_timestamp = _libs['grass_gis.6.4.2RC2'].G_remove_raster_timestamp
    G_remove_raster_timestamp.restype = c_int
    G_remove_raster_timestamp.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1163
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_vector_timestamp'):
    G_remove_vector_timestamp = _libs['grass_gis.6.4.2RC2'].G_remove_vector_timestamp
    G_remove_vector_timestamp.restype = c_int
    G_remove_vector_timestamp.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1164
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_read_grid3_timestamp'):
    G_read_grid3_timestamp = _libs['grass_gis.6.4.2RC2'].G_read_grid3_timestamp
    G_read_grid3_timestamp.restype = c_int
    G_read_grid3_timestamp.argtypes = [String, String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1165
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_remove_grid3_timestamp'):
    G_remove_grid3_timestamp = _libs['grass_gis.6.4.2RC2'].G_remove_grid3_timestamp
    G_remove_grid3_timestamp.restype = c_int
    G_remove_grid3_timestamp.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1166
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_grid3_timestamp'):
    G_write_grid3_timestamp = _libs['grass_gis.6.4.2RC2'].G_write_grid3_timestamp
    G_write_grid3_timestamp.restype = c_int
    G_write_grid3_timestamp.argtypes = [String, POINTER(struct_TimeStamp)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1169
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_tokenize'):
    G_tokenize = _libs['grass_gis.6.4.2RC2'].G_tokenize
    G_tokenize.restype = POINTER(POINTER(c_char))
    G_tokenize.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1170
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_number_of_tokens'):
    G_number_of_tokens = _libs['grass_gis.6.4.2RC2'].G_number_of_tokens
    G_number_of_tokens.restype = c_int
    G_number_of_tokens.argtypes = [POINTER(POINTER(c_char))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1171
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_free_tokens'):
    G_free_tokens = _libs['grass_gis.6.4.2RC2'].G_free_tokens
    G_free_tokens.restype = c_int
    G_free_tokens.argtypes = [POINTER(POINTER(c_char))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1174
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_trim_decimal'):
    G_trim_decimal = _libs['grass_gis.6.4.2RC2'].G_trim_decimal
    G_trim_decimal.restype = c_int
    G_trim_decimal.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1177
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_unctrl'):
    G_unctrl = _libs['grass_gis.6.4.2RC2'].G_unctrl
    G_unctrl.restype = ReturnString
    G_unctrl.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1180
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_get_fname'):
        G_sock_get_fname = _lib.G_sock_get_fname
        G_sock_get_fname.restype = ReturnString
        G_sock_get_fname.argtypes = [String]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1181
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_exists'):
        G_sock_exists = _lib.G_sock_exists
        G_sock_exists.restype = c_int
        G_sock_exists.argtypes = [String]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1182
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_bind'):
        G_sock_bind = _lib.G_sock_bind
        G_sock_bind.restype = c_int
        G_sock_bind.argtypes = [String]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1183
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_listen'):
        G_sock_listen = _lib.G_sock_listen
        G_sock_listen.restype = c_int
        G_sock_listen.argtypes = [c_int, c_uint]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1184
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_accept'):
        G_sock_accept = _lib.G_sock_accept
        G_sock_accept.restype = c_int
        G_sock_accept.argtypes = [c_int]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1185
for _lib in _libs.values():
    if hasattr(_lib, 'G_sock_connect'):
        G_sock_connect = _lib.G_sock_connect
        G_sock_connect.restype = c_int
        G_sock_connect.argtypes = [String]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1188
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_verbose'):
    G_verbose = _libs['grass_gis.6.4.2RC2'].G_verbose
    G_verbose.restype = c_int
    G_verbose.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1189
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_verbose_min'):
    G_verbose_min = _libs['grass_gis.6.4.2RC2'].G_verbose_min
    G_verbose_min.restype = c_int
    G_verbose_min.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1190
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_verbose_std'):
    G_verbose_std = _libs['grass_gis.6.4.2RC2'].G_verbose_std
    G_verbose_std.restype = c_int
    G_verbose_std.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1191
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_verbose_max'):
    G_verbose_max = _libs['grass_gis.6.4.2RC2'].G_verbose_max
    G_verbose_max.restype = c_int
    G_verbose_max.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1192
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_set_verbose'):
    G_set_verbose = _libs['grass_gis.6.4.2RC2'].G_set_verbose
    G_set_verbose.restype = c_int
    G_set_verbose.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1195
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_3dview_warning'):
    G_3dview_warning = _libs['grass_gis.6.4.2RC2'].G_3dview_warning
    G_3dview_warning.restype = c_int
    G_3dview_warning.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1196
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_3dview_defaults'):
    G_get_3dview_defaults = _libs['grass_gis.6.4.2RC2'].G_get_3dview_defaults
    G_get_3dview_defaults.restype = c_int
    G_get_3dview_defaults.argtypes = [POINTER(struct_G_3dview), POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1197
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_put_3dview'):
    G_put_3dview = _libs['grass_gis.6.4.2RC2'].G_put_3dview
    G_put_3dview.restype = c_int
    G_put_3dview.argtypes = [String, String, POINTER(struct_G_3dview), POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1199
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_get_3dview'):
    G_get_3dview = _libs['grass_gis.6.4.2RC2'].G_get_3dview
    G_get_3dview.restype = c_int
    G_get_3dview.argtypes = [String, String, POINTER(struct_G_3dview)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1202
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_whoami'):
    G_whoami = _libs['grass_gis.6.4.2RC2'].G_whoami
    G_whoami.restype = ReturnString
    G_whoami.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1205
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_adjust_window_to_box'):
    G_adjust_window_to_box = _libs['grass_gis.6.4.2RC2'].G_adjust_window_to_box
    G_adjust_window_to_box.restype = c_int
    G_adjust_window_to_box.argtypes = [POINTER(struct_Cell_head), POINTER(struct_Cell_head), c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1209
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_format_northing'):
    G_format_northing = _libs['grass_gis.6.4.2RC2'].G_format_northing
    G_format_northing.restype = c_int
    G_format_northing.argtypes = [c_double, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1210
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_format_easting'):
    G_format_easting = _libs['grass_gis.6.4.2RC2'].G_format_easting
    G_format_easting.restype = c_int
    G_format_easting.argtypes = [c_double, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1211
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_format_resolution'):
    G_format_resolution = _libs['grass_gis.6.4.2RC2'].G_format_resolution
    G_format_resolution.restype = c_int
    G_format_resolution.argtypes = [c_double, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1214
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_point_in_region'):
    G_point_in_region = _libs['grass_gis.6.4.2RC2'].G_point_in_region
    G_point_in_region.restype = c_int
    G_point_in_region.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1215
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_point_in_window'):
    G_point_in_window = _libs['grass_gis.6.4.2RC2'].G_point_in_window
    G_point_in_window.restype = c_int
    G_point_in_window.argtypes = [c_double, c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1218
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_limit_east'):
    G_limit_east = _libs['grass_gis.6.4.2RC2'].G_limit_east
    G_limit_east.restype = c_int
    G_limit_east.argtypes = [POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1219
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_limit_west'):
    G_limit_west = _libs['grass_gis.6.4.2RC2'].G_limit_west
    G_limit_west.restype = c_int
    G_limit_west.argtypes = [POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1220
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_limit_north'):
    G_limit_north = _libs['grass_gis.6.4.2RC2'].G_limit_north
    G_limit_north.restype = c_int
    G_limit_north.argtypes = [POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1221
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_limit_south'):
    G_limit_south = _libs['grass_gis.6.4.2RC2'].G_limit_south
    G_limit_south.restype = c_int
    G_limit_south.argtypes = [POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1224
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_window_overlap'):
    G_window_overlap = _libs['grass_gis.6.4.2RC2'].G_window_overlap
    G_window_overlap.restype = c_int
    G_window_overlap.argtypes = [POINTER(struct_Cell_head), c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1226
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_window_percentage_overlap'):
    G_window_percentage_overlap = _libs['grass_gis.6.4.2RC2'].G_window_percentage_overlap
    G_window_percentage_overlap.restype = c_double
    G_window_percentage_overlap.argtypes = [POINTER(struct_Cell_head), c_double, c_double, c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1230
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_scan_northing'):
    G_scan_northing = _libs['grass_gis.6.4.2RC2'].G_scan_northing
    G_scan_northing.restype = c_int
    G_scan_northing.argtypes = [String, POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1231
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_scan_easting'):
    G_scan_easting = _libs['grass_gis.6.4.2RC2'].G_scan_easting
    G_scan_easting.restype = c_int
    G_scan_easting.argtypes = [String, POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1232
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_scan_resolution'):
    G_scan_resolution = _libs['grass_gis.6.4.2RC2'].G_scan_resolution
    G_scan_resolution.restype = c_int
    G_scan_resolution.argtypes = [String, POINTER(c_double), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1235
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__create_window_mapping'):
    G__create_window_mapping = _libs['grass_gis.6.4.2RC2'].G__create_window_mapping
    G__create_window_mapping.restype = c_int
    G__create_window_mapping.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1236
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_northing_to_row'):
    G_northing_to_row = _libs['grass_gis.6.4.2RC2'].G_northing_to_row
    G_northing_to_row.restype = c_double
    G_northing_to_row.argtypes = [c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1237
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_adjust_east_longitude'):
    G_adjust_east_longitude = _libs['grass_gis.6.4.2RC2'].G_adjust_east_longitude
    G_adjust_east_longitude.restype = c_double
    G_adjust_east_longitude.argtypes = [c_double, c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1238
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_adjust_easting'):
    G_adjust_easting = _libs['grass_gis.6.4.2RC2'].G_adjust_easting
    G_adjust_easting.restype = c_double
    G_adjust_easting.argtypes = [c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1239
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_easting_to_col'):
    G_easting_to_col = _libs['grass_gis.6.4.2RC2'].G_easting_to_col
    G_easting_to_col.restype = c_double
    G_easting_to_col.argtypes = [c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1240
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_row_to_northing'):
    G_row_to_northing = _libs['grass_gis.6.4.2RC2'].G_row_to_northing
    G_row_to_northing.restype = c_double
    G_row_to_northing.argtypes = [c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1241
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_col_to_easting'):
    G_col_to_easting = _libs['grass_gis.6.4.2RC2'].G_col_to_easting
    G_col_to_easting.restype = c_double
    G_col_to_easting.argtypes = [c_double, POINTER(struct_Cell_head)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1242
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_window_rows'):
    G_window_rows = _libs['grass_gis.6.4.2RC2'].G_window_rows
    G_window_rows.restype = c_int
    G_window_rows.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1243
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_window_cols'):
    G_window_cols = _libs['grass_gis.6.4.2RC2'].G_window_cols
    G_window_cols.restype = c_int
    G_window_cols.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1244
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__init_window'):
    G__init_window = _libs['grass_gis.6.4.2RC2'].G__init_window
    G__init_window.restype = c_int
    G__init_window.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1245
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_row_repeat_nomask'):
    G_row_repeat_nomask = _libs['grass_gis.6.4.2RC2'].G_row_repeat_nomask
    G_row_repeat_nomask.restype = c_int
    G_row_repeat_nomask.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1248
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_Cell_head'):
    G__write_Cell_head = _libs['grass_gis.6.4.2RC2'].G__write_Cell_head
    G__write_Cell_head.restype = c_int
    G__write_Cell_head.argtypes = [POINTER(FILE), POINTER(struct_Cell_head), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1249
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G__write_Cell_head3'):
    G__write_Cell_head3 = _libs['grass_gis.6.4.2RC2'].G__write_Cell_head3
    G__write_Cell_head3.restype = c_int
    G__write_Cell_head3.argtypes = [POINTER(FILE), POINTER(struct_Cell_head), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1252
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_write_zeros'):
    G_write_zeros = _libs['grass_gis.6.4.2RC2'].G_write_zeros
    G_write_zeros.restype = c_int
    G_write_zeros.argtypes = [c_int, c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1255
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_yes'):
    G_yes = _libs['grass_gis.6.4.2RC2'].G_yes
    G_yes.restype = c_int
    G_yes.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1258
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zero'):
    G_zero = _libs['grass_gis.6.4.2RC2'].G_zero
    G_zero.restype = c_int
    G_zero.argtypes = [POINTER(None), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1261
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zero_cell_buf'):
    G_zero_cell_buf = _libs['grass_gis.6.4.2RC2'].G_zero_cell_buf
    G_zero_cell_buf.restype = c_int
    G_zero_cell_buf.argtypes = [POINTER(CELL)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1262
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zero_raster_buf'):
    G_zero_raster_buf = _libs['grass_gis.6.4.2RC2'].G_zero_raster_buf
    G_zero_raster_buf.restype = c_int
    G_zero_raster_buf.argtypes = [POINTER(None), RASTER_MAP_TYPE]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 1265
if hasattr(_libs['grass_gis.6.4.2RC2'], 'G_zone'):
    G_zone = _libs['grass_gis.6.4.2RC2'].G_zone
    G_zone.restype = c_int
    G_zone.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 40
try:
    GIS_H_VERSION = '$Revision: 45934 $'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 40
try:
    GIS_H_DATE = '$Date: 2011-04-13 13:19:03 +0200 (st, 13 IV 2011) $'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 41
def G_gisinit(pgm):
    return (G__gisinit (GIS_H_VERSION, pgm))

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 41
try:
    G_no_gisinit = (G__no_gisinit (GIS_H_VERSION))
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 44
try:
    TRUE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 47
try:
    FALSE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 52
try:
    PRI_OFF_T = 'ld'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    MAXEDLINES = 50
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    RECORD_LEN = 80
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    NEWLINE = '\\n'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    RECLASS_TABLE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    RECLASS_RULES = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 54
try:
    RECLASS_SCALE = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 55
try:
    METERS = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 55
try:
    FEET = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 55
try:
    DEGREES = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 56
try:
    CELL_TYPE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 56
try:
    FCELL_TYPE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 56
try:
    DCELL_TYPE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 57
try:
    PROJECTION_XY = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 57
try:
    PROJECTION_UTM = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 57
try:
    PROJECTION_SP = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 57
try:
    PROJECTION_LL = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 57
try:
    PROJECTION_OTHER = 99
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 58
try:
    PROJECTION_FILE = 'PROJ_INFO'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 58
try:
    UNIT_FILE = 'PROJ_UNITS'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 61
try:
    M_PI = 3.1415926535897931
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 63
try:
    M_PI_2 = 1.5707963267948966
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 65
try:
    M_PI_4 = 0.78539816339744828
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 67
try:
    GRASS_EPSILON = 1.0000000000000001e-015
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 69
try:
    G_VAR_GISRC = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 69
try:
    G_VAR_MAPSET = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 71
try:
    G_GISRC_MODE_FILE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 71
try:
    G_GISRC_MODE_MEMORY = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    TYPE_INTEGER = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    TYPE_DOUBLE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    TYPE_STRING = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    YES = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    NO = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 73
try:
    GISPROMPT_COLOR = 'old_color,color,color'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 75
try:
    GNAME_MAX = 256
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 75
try:
    GMAPSET_MAX = 256
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 76
try:
    GPATH_MAX = 4096
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 89
def deserialize_int32_le(buf):
    return (((((buf [0]) << 0) | ((buf [1]) << 8)) | ((buf [2]) << 16)) | ((buf [3]) << 24))

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 101
def deserialize_int32_be(buf):
    return (((((buf [0]) << 24) | ((buf [1]) << 16)) | ((buf [2]) << 8)) | ((buf [3]) << 0))

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 106
try:
    GRASS_DIRSEP = '/'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 107
try:
    HOST_DIRSEP = '\\\\'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 107
try:
    G_DEV_NULL = 'NUL:'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 161
try:
    G_INFO_FORMAT_STANDARD = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 161
try:
    G_INFO_FORMAT_GUI = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 161
try:
    G_INFO_FORMAT_SILENT = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 161
try:
    G_INFO_FORMAT_PLAIN = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 163
try:
    G_ICON_CROSS = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 163
try:
    G_ICON_BOX = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 163
try:
    G_ICON_ARROW = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 165
try:
    DEFAULT_FG_COLOR = 'black'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 165
try:
    DEFAULT_BG_COLOR = 'white'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 167
try:
    UNKNOWN = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 167
try:
    NEAREST = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 167
try:
    BILINEAR = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 167
try:
    CUBIC = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 169
try:
    GR_FATAL_EXIT = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 169
try:
    GR_FATAL_PRINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 169
try:
    GR_FATAL_RETURN = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 293
try:
    RGBA_COLOR_OPAQUE = 255
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 293
try:
    RGBA_COLOR_TRANSPARENT = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 293
try:
    RGBA_COLOR_NONE = 0
except:
    pass

Cell_head = struct_Cell_head # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 265

_Color_Value_ = struct__Color_Value_ # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 289

_Color_Rule_ = struct__Color_Rule_ # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 297

_Color_Info_ = struct__Color_Info_ # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 304

Colors = struct_Colors # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 331

Reclass = struct_Reclass # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 365

FPReclass_table = struct_FPReclass_table # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 376

FPReclass = struct_FPReclass # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 386

Quant_table = struct_Quant_table # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 410

Quant = struct_Quant # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 418

Categories = struct_Categories # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 461

History = struct_History # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 487

Cell_stats_node = struct_Cell_stats_node # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 503

Cell_stats = struct_Cell_stats # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 501

Histogram_list = struct_Histogram_list # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 522

Histogram = struct_Histogram # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 518

Range = struct_Range # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 529

FPRange = struct_FPRange # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 536

FP_stats = struct_FP_stats # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 543

G_3dview = struct_G_3dview # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 556

Key_Value = struct_Key_Value # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 583

Option = struct_Option # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 591

Flag = struct_Flag # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 619

GModule = struct_GModule # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 629

TimeStamp = struct_TimeStamp # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 639

GDAL_link = struct_GDAL_link # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\gis.h: 645

stat = struct_stat # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gisdefs.h: 900

# No inserted files

