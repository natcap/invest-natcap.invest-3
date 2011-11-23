'''Wrapper for G3d.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_g3d.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/G3d.h -o g3d.py

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

_libs["grass_g3d.6.4.2RC2"] = load_library("grass_g3d.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

NULL = None # <built-in>

CELL = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 256

DCELL = c_double # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 257

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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 410
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 443
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 418
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 461
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 487
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 536
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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 583
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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 62
class struct_anon_8(Structure):
    pass

struct_anon_8.__slots__ = [
    'north',
    'south',
    'east',
    'west',
    'top',
    'bottom',
    'rows',
    'cols',
    'depths',
    'ns_res',
    'ew_res',
    'tb_res',
    'proj',
    'zone',
]
struct_anon_8._fields_ = [
    ('north', c_double),
    ('south', c_double),
    ('east', c_double),
    ('west', c_double),
    ('top', c_double),
    ('bottom', c_double),
    ('rows', c_int),
    ('cols', c_int),
    ('depths', c_int),
    ('ns_res', c_double),
    ('ew_res', c_double),
    ('tb_res', c_double),
    ('proj', c_int),
    ('zone', c_int),
]

G3D_Region = struct_anon_8 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 62

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 72
class struct_G3D_Map(Structure):
    pass

resample_fn = CFUNCTYPE(UNCHECKED(None), POINTER(struct_G3D_Map), c_int, c_int, c_int, POINTER(None), c_int) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 68

struct_G3D_Map.__slots__ = [
    'fileName',
    'tempName',
    'mapset',
    'operation',
    'region',
    'window',
    'resampleFun',
    'unit',
    'tileX',
    'tileY',
    'tileZ',
    'nx',
    'ny',
    'nz',
    'data_fd',
    'type',
    'precision',
    'compression',
    'useLzw',
    'useRle',
    'useXdr',
    'offset',
    'indexOffset',
    'indexLongNbytes',
    'indexNbytesUsed',
    'fileEndPtr',
    'hasIndex',
    'index',
    'tileLength',
    'typeIntern',
    'data',
    'currentIndex',
    'useCache',
    'cache',
    'cacheFD',
    'cacheFileName',
    'cachePosLast',
    'range',
    'numLengthExtern',
    'numLengthIntern',
    'clipX',
    'clipY',
    'clipZ',
    'tileXY',
    'tileSize',
    'nxy',
    'nTiles',
    'useMask',
]
struct_G3D_Map._fields_ = [
    ('fileName', String),
    ('tempName', String),
    ('mapset', String),
    ('operation', c_int),
    ('region', G3D_Region),
    ('window', G3D_Region),
    ('resampleFun', POINTER(resample_fn)),
    ('unit', String),
    ('tileX', c_int),
    ('tileY', c_int),
    ('tileZ', c_int),
    ('nx', c_int),
    ('ny', c_int),
    ('nz', c_int),
    ('data_fd', c_int),
    ('type', c_int),
    ('precision', c_int),
    ('compression', c_int),
    ('useLzw', c_int),
    ('useRle', c_int),
    ('useXdr', c_int),
    ('offset', c_int),
    ('indexOffset', c_long),
    ('indexLongNbytes', c_int),
    ('indexNbytesUsed', c_int),
    ('fileEndPtr', c_int),
    ('hasIndex', c_int),
    ('index', POINTER(c_long)),
    ('tileLength', POINTER(c_int)),
    ('typeIntern', c_int),
    ('data', String),
    ('currentIndex', c_int),
    ('useCache', c_int),
    ('cache', POINTER(None)),
    ('cacheFD', c_int),
    ('cacheFileName', String),
    ('cachePosLast', c_long),
    ('range', struct_FPRange),
    ('numLengthExtern', c_int),
    ('numLengthIntern', c_int),
    ('clipX', c_int),
    ('clipY', c_int),
    ('clipZ', c_int),
    ('tileXY', c_int),
    ('tileSize', c_int),
    ('nxy', c_int),
    ('nTiles', c_int),
    ('useMask', c_int),
]

G3D_Map = struct_G3D_Map # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 184

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 219
class struct_anon_9(Structure):
    pass

struct_anon_9.__slots__ = [
    'elts',
    'nofElts',
    'eltSize',
    'names',
    'locks',
    'autoLock',
    'nofUnlocked',
    'minUnlocked',
    'next',
    'prev',
    'first',
    'last',
    'eltRemoveFun',
    'eltRemoveFunData',
    'eltLoadFun',
    'eltLoadFunData',
    'hash',
]
struct_anon_9._fields_ = [
    ('elts', String),
    ('nofElts', c_int),
    ('eltSize', c_int),
    ('names', POINTER(c_int)),
    ('locks', String),
    ('autoLock', c_int),
    ('nofUnlocked', c_int),
    ('minUnlocked', c_int),
    ('next', POINTER(c_int)),
    ('prev', POINTER(c_int)),
    ('first', c_int),
    ('last', c_int),
    ('eltRemoveFun', CFUNCTYPE(UNCHECKED(c_int), )),
    ('eltRemoveFunData', POINTER(None)),
    ('eltLoadFun', CFUNCTYPE(UNCHECKED(c_int), )),
    ('eltLoadFunData', POINTER(None)),
    ('hash', POINTER(None)),
]

G3D_cache = struct_anon_9 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 219

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 233
class struct_anon_10(Structure):
    pass

struct_anon_10.__slots__ = [
    'nofNames',
    'index',
    'active',
    'lastName',
    'lastIndex',
    'lastIndexActive',
]
struct_anon_10._fields_ = [
    ('nofNames', c_int),
    ('index', POINTER(c_int)),
    ('active', String),
    ('lastName', c_int),
    ('lastIndex', c_int),
    ('lastIndexActive', c_int),
]

G3d_cache_hash = struct_anon_10 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 233

write_fn = CFUNCTYPE(UNCHECKED(c_int), c_int, POINTER(None), POINTER(None)) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 237

read_fn = CFUNCTYPE(UNCHECKED(c_int), c_int, POINTER(None), POINTER(None)) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 238

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 243
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_reset'):
    G3d_cache_reset = _libs['grass_g3d.6.4.2RC2'].G3d_cache_reset
    G3d_cache_reset.restype = None
    G3d_cache_reset.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 244
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_dispose'):
    G3d_cache_dispose = _libs['grass_g3d.6.4.2RC2'].G3d_cache_dispose
    G3d_cache_dispose.restype = None
    G3d_cache_dispose.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 245
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_new'):
    G3d_cache_new = _libs['grass_g3d.6.4.2RC2'].G3d_cache_new
    G3d_cache_new.restype = POINTER(None)
    G3d_cache_new.argtypes = [c_int, c_int, c_int, POINTER(write_fn), POINTER(None), POINTER(read_fn), POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 246
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_set_removeFun'):
    G3d_cache_set_removeFun = _libs['grass_g3d.6.4.2RC2'].G3d_cache_set_removeFun
    G3d_cache_set_removeFun.restype = None
    G3d_cache_set_removeFun.argtypes = [POINTER(G3D_cache), POINTER(write_fn), POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 247
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_set_loadFun'):
    G3d_cache_set_loadFun = _libs['grass_g3d.6.4.2RC2'].G3d_cache_set_loadFun
    G3d_cache_set_loadFun.restype = None
    G3d_cache_set_loadFun.argtypes = [POINTER(G3D_cache), POINTER(read_fn), POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 248
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_new_read'):
    G3d_cache_new_read = _libs['grass_g3d.6.4.2RC2'].G3d_cache_new_read
    G3d_cache_new_read.restype = POINTER(None)
    G3d_cache_new_read.argtypes = [c_int, c_int, c_int, POINTER(read_fn), POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 249
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_lock'):
    G3d_cache_lock = _libs['grass_g3d.6.4.2RC2'].G3d_cache_lock
    G3d_cache_lock.restype = c_int
    G3d_cache_lock.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 250
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_lock_intern'):
    G3d_cache_lock_intern = _libs['grass_g3d.6.4.2RC2'].G3d_cache_lock_intern
    G3d_cache_lock_intern.restype = None
    G3d_cache_lock_intern.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 251
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_unlock'):
    G3d_cache_unlock = _libs['grass_g3d.6.4.2RC2'].G3d_cache_unlock
    G3d_cache_unlock.restype = c_int
    G3d_cache_unlock.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 252
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_unlock_all'):
    G3d_cache_unlock_all = _libs['grass_g3d.6.4.2RC2'].G3d_cache_unlock_all
    G3d_cache_unlock_all.restype = c_int
    G3d_cache_unlock_all.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 253
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_lock_all'):
    G3d_cache_lock_all = _libs['grass_g3d.6.4.2RC2'].G3d_cache_lock_all
    G3d_cache_lock_all.restype = c_int
    G3d_cache_lock_all.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 254
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_autolock_on'):
    G3d_cache_autolock_on = _libs['grass_g3d.6.4.2RC2'].G3d_cache_autolock_on
    G3d_cache_autolock_on.restype = None
    G3d_cache_autolock_on.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 255
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_autolock_off'):
    G3d_cache_autolock_off = _libs['grass_g3d.6.4.2RC2'].G3d_cache_autolock_off
    G3d_cache_autolock_off.restype = None
    G3d_cache_autolock_off.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 256
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_set_minUnlock'):
    G3d_cache_set_minUnlock = _libs['grass_g3d.6.4.2RC2'].G3d_cache_set_minUnlock
    G3d_cache_set_minUnlock.restype = None
    G3d_cache_set_minUnlock.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 257
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_remove_elt'):
    G3d_cache_remove_elt = _libs['grass_g3d.6.4.2RC2'].G3d_cache_remove_elt
    G3d_cache_remove_elt.restype = c_int
    G3d_cache_remove_elt.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 258
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_flush'):
    G3d_cache_flush = _libs['grass_g3d.6.4.2RC2'].G3d_cache_flush
    G3d_cache_flush.restype = c_int
    G3d_cache_flush.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 259
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_remove_all'):
    G3d_cache_remove_all = _libs['grass_g3d.6.4.2RC2'].G3d_cache_remove_all
    G3d_cache_remove_all.restype = c_int
    G3d_cache_remove_all.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 260
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_flush_all'):
    G3d_cache_flush_all = _libs['grass_g3d.6.4.2RC2'].G3d_cache_flush_all
    G3d_cache_flush_all.restype = c_int
    G3d_cache_flush_all.argtypes = [POINTER(G3D_cache)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 261
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_elt_ptr'):
    G3d_cache_elt_ptr = _libs['grass_g3d.6.4.2RC2'].G3d_cache_elt_ptr
    G3d_cache_elt_ptr.restype = POINTER(None)
    G3d_cache_elt_ptr.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 262
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_load'):
    G3d_cache_load = _libs['grass_g3d.6.4.2RC2'].G3d_cache_load
    G3d_cache_load.restype = c_int
    G3d_cache_load.argtypes = [POINTER(G3D_cache), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 263
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_get_elt'):
    G3d_cache_get_elt = _libs['grass_g3d.6.4.2RC2'].G3d_cache_get_elt
    G3d_cache_get_elt.restype = c_int
    G3d_cache_get_elt.argtypes = [POINTER(G3D_cache), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 264
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_put_elt'):
    G3d_cache_put_elt = _libs['grass_g3d.6.4.2RC2'].G3d_cache_put_elt
    G3d_cache_put_elt.restype = c_int
    G3d_cache_put_elt.argtypes = [POINTER(G3D_cache), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 267
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_reset'):
    G3d_cache_hash_reset = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_reset
    G3d_cache_hash_reset.restype = None
    G3d_cache_hash_reset.argtypes = [POINTER(G3d_cache_hash)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 268
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_dispose'):
    G3d_cache_hash_dispose = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_dispose
    G3d_cache_hash_dispose.restype = None
    G3d_cache_hash_dispose.argtypes = [POINTER(G3d_cache_hash)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 269
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_new'):
    G3d_cache_hash_new = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_new
    G3d_cache_hash_new.restype = POINTER(None)
    G3d_cache_hash_new.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 270
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_remove_name'):
    G3d_cache_hash_remove_name = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_remove_name
    G3d_cache_hash_remove_name.restype = None
    G3d_cache_hash_remove_name.argtypes = [POINTER(G3d_cache_hash), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 271
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_load_name'):
    G3d_cache_hash_load_name = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_load_name
    G3d_cache_hash_load_name.restype = None
    G3d_cache_hash_load_name.argtypes = [POINTER(G3d_cache_hash), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 272
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cache_hash_name2index'):
    G3d_cache_hash_name2index = _libs['grass_g3d.6.4.2RC2'].G3d_cache_hash_name2index
    G3d_cache_hash_name2index.restype = c_int
    G3d_cache_hash_name2index.argtypes = [POINTER(G3d_cache_hash), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 275
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_changePrecision'):
    G3d_changePrecision = _libs['grass_g3d.6.4.2RC2'].G3d_changePrecision
    G3d_changePrecision.restype = None
    G3d_changePrecision.argtypes = [POINTER(None), c_int, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 278
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_changeType'):
    G3d_changeType = _libs['grass_g3d.6.4.2RC2'].G3d_changeType
    G3d_changeType.restype = None
    G3d_changeType.argtypes = [POINTER(None), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 281
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_compareFiles'):
    G3d_compareFiles = _libs['grass_g3d.6.4.2RC2'].G3d_compareFiles
    G3d_compareFiles.restype = None
    G3d_compareFiles.argtypes = [String, String, String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 284
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_filename'):
    G3d_filename = _libs['grass_g3d.6.4.2RC2'].G3d_filename
    G3d_filename.restype = None
    G3d_filename.argtypes = [String, String, String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 287
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_find_grid3'):
    G_find_grid3 = _libs['grass_g3d.6.4.2RC2'].G_find_grid3
    G_find_grid3.restype = ReturnString
    G_find_grid3.argtypes = [String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 290
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_printBinary'):
    G_fpcompress_printBinary = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_printBinary
    G_fpcompress_printBinary.restype = None
    G_fpcompress_printBinary.argtypes = [String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 291
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_dissectXdrDouble'):
    G_fpcompress_dissectXdrDouble = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_dissectXdrDouble
    G_fpcompress_dissectXdrDouble.restype = None
    G_fpcompress_dissectXdrDouble.argtypes = [POINTER(c_ubyte)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 292
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_writeXdrNums'):
    G_fpcompress_writeXdrNums = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_writeXdrNums
    G_fpcompress_writeXdrNums.restype = c_int
    G_fpcompress_writeXdrNums.argtypes = [c_int, String, c_int, c_int, String, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 293
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_writeXdrFloats'):
    G_fpcompress_writeXdrFloats = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_writeXdrFloats
    G_fpcompress_writeXdrFloats.restype = c_int
    G_fpcompress_writeXdrFloats.argtypes = [c_int, String, c_int, c_int, String, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 294
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_writeXdrDouble'):
    G_fpcompress_writeXdrDouble = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_writeXdrDouble
    G_fpcompress_writeXdrDouble.restype = c_int
    G_fpcompress_writeXdrDouble.argtypes = [c_int, String, c_int, c_int, String, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 295
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_readXdrNums'):
    G_fpcompress_readXdrNums = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_readXdrNums
    G_fpcompress_readXdrNums.restype = c_int
    G_fpcompress_readXdrNums.argtypes = [c_int, String, c_int, c_int, c_int, String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 296
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_readXdrFloats'):
    G_fpcompress_readXdrFloats = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_readXdrFloats
    G_fpcompress_readXdrFloats.restype = c_int
    G_fpcompress_readXdrFloats.argtypes = [c_int, String, c_int, c_int, c_int, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 297
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_fpcompress_readXdrDoubles'):
    G_fpcompress_readXdrDoubles = _libs['grass_g3d.6.4.2RC2'].G_fpcompress_readXdrDoubles
    G_fpcompress_readXdrDoubles.restype = c_int
    G_fpcompress_readXdrDoubles.argtypes = [c_int, String, c_int, c_int, c_int, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 300
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_malloc'):
    G3d_malloc = _libs['grass_g3d.6.4.2RC2'].G3d_malloc
    G3d_malloc.restype = POINTER(None)
    G3d_malloc.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 301
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_realloc'):
    G3d_realloc = _libs['grass_g3d.6.4.2RC2'].G3d_realloc
    G3d_realloc.restype = POINTER(None)
    G3d_realloc.argtypes = [POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 302
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_free'):
    G3d_free = _libs['grass_g3d.6.4.2RC2'].G3d_free
    G3d_free.restype = None
    G3d_free.argtypes = [POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 305
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initCache'):
    G3d_initCache = _libs['grass_g3d.6.4.2RC2'].G3d_initCache
    G3d_initCache.restype = c_int
    G3d_initCache.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 306
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_disposeCache'):
    G3d_disposeCache = _libs['grass_g3d.6.4.2RC2'].G3d_disposeCache
    G3d_disposeCache.restype = c_int
    G3d_disposeCache.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 307
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_flushAllTiles'):
    G3d_flushAllTiles = _libs['grass_g3d.6.4.2RC2'].G3d_flushAllTiles
    G3d_flushAllTiles.restype = c_int
    G3d_flushAllTiles.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 310
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeCats'):
    G3d_writeCats = _libs['grass_g3d.6.4.2RC2'].G3d_writeCats
    G3d_writeCats.restype = c_int
    G3d_writeCats.argtypes = [String, POINTER(struct_Categories)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 311
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readCats'):
    G3d_readCats = _libs['grass_g3d.6.4.2RC2'].G3d_readCats
    G3d_readCats.restype = c_int
    G3d_readCats.argtypes = [String, String, POINTER(struct_Categories)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 314
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_closeCell'):
    G3d_closeCell = _libs['grass_g3d.6.4.2RC2'].G3d_closeCell
    G3d_closeCell.restype = c_int
    G3d_closeCell.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 317
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_removeColor'):
    G3d_removeColor = _libs['grass_g3d.6.4.2RC2'].G3d_removeColor
    G3d_removeColor.restype = c_int
    G3d_removeColor.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 318
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readColors'):
    G3d_readColors = _libs['grass_g3d.6.4.2RC2'].G3d_readColors
    G3d_readColors.restype = c_int
    G3d_readColors.argtypes = [String, String, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 319
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeColors'):
    G3d_writeColors = _libs['grass_g3d.6.4.2RC2'].G3d_writeColors
    G3d_writeColors.restype = c_int
    G3d_writeColors.argtypes = [String, String, POINTER(struct_Colors)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 322
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setCompressionMode'):
    G3d_setCompressionMode = _libs['grass_g3d.6.4.2RC2'].G3d_setCompressionMode
    G3d_setCompressionMode.restype = None
    G3d_setCompressionMode.argtypes = [c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 323
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getCompressionMode'):
    G3d_getCompressionMode = _libs['grass_g3d.6.4.2RC2'].G3d_getCompressionMode
    G3d_getCompressionMode.restype = None
    G3d_getCompressionMode.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 324
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setCacheSize'):
    G3d_setCacheSize = _libs['grass_g3d.6.4.2RC2'].G3d_setCacheSize
    G3d_setCacheSize.restype = None
    G3d_setCacheSize.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 325
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getCacheSize'):
    G3d_getCacheSize = _libs['grass_g3d.6.4.2RC2'].G3d_getCacheSize
    G3d_getCacheSize.restype = c_int
    G3d_getCacheSize.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 326
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setCacheLimit'):
    G3d_setCacheLimit = _libs['grass_g3d.6.4.2RC2'].G3d_setCacheLimit
    G3d_setCacheLimit.restype = None
    G3d_setCacheLimit.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 327
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getCacheLimit'):
    G3d_getCacheLimit = _libs['grass_g3d.6.4.2RC2'].G3d_getCacheLimit
    G3d_getCacheLimit.restype = c_int
    G3d_getCacheLimit.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 328
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setFileType'):
    G3d_setFileType = _libs['grass_g3d.6.4.2RC2'].G3d_setFileType
    G3d_setFileType.restype = None
    G3d_setFileType.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 329
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getFileType'):
    G3d_getFileType = _libs['grass_g3d.6.4.2RC2'].G3d_getFileType
    G3d_getFileType.restype = c_int
    G3d_getFileType.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 330
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setTileDimension'):
    G3d_setTileDimension = _libs['grass_g3d.6.4.2RC2'].G3d_setTileDimension
    G3d_setTileDimension.restype = None
    G3d_setTileDimension.argtypes = [c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 331
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getTileDimension'):
    G3d_getTileDimension = _libs['grass_g3d.6.4.2RC2'].G3d_getTileDimension
    G3d_getTileDimension.restype = None
    G3d_getTileDimension.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 332
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setErrorFun'):
    G3d_setErrorFun = _libs['grass_g3d.6.4.2RC2'].G3d_setErrorFun
    G3d_setErrorFun.restype = None
    G3d_setErrorFun.argtypes = [CFUNCTYPE(UNCHECKED(None), String)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 333
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setUnit'):
    G3d_setUnit = _libs['grass_g3d.6.4.2RC2'].G3d_setUnit
    G3d_setUnit.restype = None
    G3d_setUnit.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 334
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initDefaults'):
    G3d_initDefaults = _libs['grass_g3d.6.4.2RC2'].G3d_initDefaults
    G3d_initDefaults.restype = None
    G3d_initDefaults.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 337
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeDoubles'):
    G3d_writeDoubles = _libs['grass_g3d.6.4.2RC2'].G3d_writeDoubles
    G3d_writeDoubles.restype = c_int
    G3d_writeDoubles.argtypes = [c_int, c_int, POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 338
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readDoubles'):
    G3d_readDoubles = _libs['grass_g3d.6.4.2RC2'].G3d_readDoubles
    G3d_readDoubles.restype = c_int
    G3d_readDoubles.argtypes = [c_int, c_int, POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 341
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_skipError'):
    G3d_skipError = _libs['grass_g3d.6.4.2RC2'].G3d_skipError
    G3d_skipError.restype = None
    G3d_skipError.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 342
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_printError'):
    G3d_printError = _libs['grass_g3d.6.4.2RC2'].G3d_printError
    G3d_printError.restype = None
    G3d_printError.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 343
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_fatalError'):
    _func = _libs['grass_g3d.6.4.2RC2'].G3d_fatalError
    _restype = None
    _argtypes = [String]
    G3d_fatalError = _variadic_function(_func,_restype,_argtypes)

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 345
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_fatalError_noargs'):
    G3d_fatalError_noargs = _libs['grass_g3d.6.4.2RC2'].G3d_fatalError_noargs
    G3d_fatalError_noargs.restype = None
    G3d_fatalError_noargs.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 346
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_error'):
    _func = _libs['grass_g3d.6.4.2RC2'].G3d_error
    _restype = None
    _argtypes = [String]
    G3d_error = _variadic_function(_func,_restype,_argtypes)

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 349
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isXdrNullNum'):
    G3d_isXdrNullNum = _libs['grass_g3d.6.4.2RC2'].G3d_isXdrNullNum
    G3d_isXdrNullNum.restype = c_int
    G3d_isXdrNullNum.argtypes = [POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 350
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isXdrNullFloat'):
    G3d_isXdrNullFloat = _libs['grass_g3d.6.4.2RC2'].G3d_isXdrNullFloat
    G3d_isXdrNullFloat.restype = c_int
    G3d_isXdrNullFloat.argtypes = [POINTER(c_float)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 351
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isXdrNullDouble'):
    G3d_isXdrNullDouble = _libs['grass_g3d.6.4.2RC2'].G3d_isXdrNullDouble
    G3d_isXdrNullDouble.restype = c_int
    G3d_isXdrNullDouble.argtypes = [POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 352
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setXdrNullNum'):
    G3d_setXdrNullNum = _libs['grass_g3d.6.4.2RC2'].G3d_setXdrNullNum
    G3d_setXdrNullNum.restype = None
    G3d_setXdrNullNum.argtypes = [POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 353
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setXdrNullDouble'):
    G3d_setXdrNullDouble = _libs['grass_g3d.6.4.2RC2'].G3d_setXdrNullDouble
    G3d_setXdrNullDouble.restype = None
    G3d_setXdrNullDouble.argtypes = [POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 354
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setXdrNullFloat'):
    G3d_setXdrNullFloat = _libs['grass_g3d.6.4.2RC2'].G3d_setXdrNullFloat
    G3d_setXdrNullFloat.restype = None
    G3d_setXdrNullFloat.argtypes = [POINTER(c_float)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 355
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initFpXdr'):
    G3d_initFpXdr = _libs['grass_g3d.6.4.2RC2'].G3d_initFpXdr
    G3d_initFpXdr.restype = c_int
    G3d_initFpXdr.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 356
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initCopyToXdr'):
    G3d_initCopyToXdr = _libs['grass_g3d.6.4.2RC2'].G3d_initCopyToXdr
    G3d_initCopyToXdr.restype = c_int
    G3d_initCopyToXdr.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 357
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_copyToXdr'):
    G3d_copyToXdr = _libs['grass_g3d.6.4.2RC2'].G3d_copyToXdr
    G3d_copyToXdr.restype = c_int
    G3d_copyToXdr.argtypes = [POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 358
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initCopyFromXdr'):
    G3d_initCopyFromXdr = _libs['grass_g3d.6.4.2RC2'].G3d_initCopyFromXdr
    G3d_initCopyFromXdr.restype = c_int
    G3d_initCopyFromXdr.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 359
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_copyFromXdr'):
    G3d_copyFromXdr = _libs['grass_g3d.6.4.2RC2'].G3d_copyFromXdr
    G3d_copyFromXdr.restype = c_int
    G3d_copyFromXdr.argtypes = [c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 362
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeHistory'):
    G3d_writeHistory = _libs['grass_g3d.6.4.2RC2'].G3d_writeHistory
    G3d_writeHistory.restype = c_int
    G3d_writeHistory.argtypes = [String, POINTER(struct_History)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 363
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readHistory'):
    G3d_readHistory = _libs['grass_g3d.6.4.2RC2'].G3d_readHistory
    G3d_readHistory.restype = c_int
    G3d_readHistory.argtypes = [String, String, POINTER(struct_History)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 366
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeInts'):
    G3d_writeInts = _libs['grass_g3d.6.4.2RC2'].G3d_writeInts
    G3d_writeInts.restype = c_int
    G3d_writeInts.argtypes = [c_int, c_int, POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 367
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readInts'):
    G3d_readInts = _libs['grass_g3d.6.4.2RC2'].G3d_readInts
    G3d_readInts.restype = c_int
    G3d_readInts.argtypes = [c_int, c_int, POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 370
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keyGetInt'):
    G3d_keyGetInt = _libs['grass_g3d.6.4.2RC2'].G3d_keyGetInt
    G3d_keyGetInt.restype = c_int
    G3d_keyGetInt.argtypes = [POINTER(struct_Key_Value), String, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 371
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keyGetDouble'):
    G3d_keyGetDouble = _libs['grass_g3d.6.4.2RC2'].G3d_keyGetDouble
    G3d_keyGetDouble.restype = c_int
    G3d_keyGetDouble.argtypes = [POINTER(struct_Key_Value), String, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 372
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keyGetString'):
    G3d_keyGetString = _libs['grass_g3d.6.4.2RC2'].G3d_keyGetString
    G3d_keyGetString.restype = c_int
    G3d_keyGetString.argtypes = [POINTER(struct_Key_Value), String, POINTER(POINTER(c_char))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 373
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keyGetValue'):
    G3d_keyGetValue = _libs['grass_g3d.6.4.2RC2'].G3d_keyGetValue
    G3d_keyGetValue.restype = c_int
    G3d_keyGetValue.argtypes = [POINTER(struct_Key_Value), String, String, String, c_int, c_int, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 375
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keySetInt'):
    G3d_keySetInt = _libs['grass_g3d.6.4.2RC2'].G3d_keySetInt
    G3d_keySetInt.restype = c_int
    G3d_keySetInt.argtypes = [POINTER(struct_Key_Value), String, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 376
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keySetDouble'):
    G3d_keySetDouble = _libs['grass_g3d.6.4.2RC2'].G3d_keySetDouble
    G3d_keySetDouble.restype = c_int
    G3d_keySetDouble.argtypes = [POINTER(struct_Key_Value), String, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 377
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keySetString'):
    G3d_keySetString = _libs['grass_g3d.6.4.2RC2'].G3d_keySetString
    G3d_keySetString.restype = c_int
    G3d_keySetString.argtypes = [POINTER(struct_Key_Value), String, POINTER(POINTER(c_char))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 378
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_keySetValue'):
    G3d_keySetValue = _libs['grass_g3d.6.4.2RC2'].G3d_keySetValue
    G3d_keySetValue.restype = c_int
    G3d_keySetValue.argtypes = [POINTER(struct_Key_Value), String, String, String, c_int, c_int, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 381
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_longEncode'):
    G3d_longEncode = _libs['grass_g3d.6.4.2RC2'].G3d_longEncode
    G3d_longEncode.restype = c_int
    G3d_longEncode.argtypes = [POINTER(c_long), POINTER(c_ubyte), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 382
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_longDecode'):
    G3d_longDecode = _libs['grass_g3d.6.4.2RC2'].G3d_longDecode
    G3d_longDecode.restype = None
    G3d_longDecode.argtypes = [POINTER(c_ubyte), POINTER(c_long), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 385
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_makeMapsetMapDirectory'):
    G3d_makeMapsetMapDirectory = _libs['grass_g3d.6.4.2RC2'].G3d_makeMapsetMapDirectory
    G3d_makeMapsetMapDirectory.restype = None
    G3d_makeMapsetMapDirectory.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 388
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskClose'):
    G3d_maskClose = _libs['grass_g3d.6.4.2RC2'].G3d_maskClose
    G3d_maskClose.restype = c_int
    G3d_maskClose.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 389
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskFileExists'):
    G3d_maskFileExists = _libs['grass_g3d.6.4.2RC2'].G3d_maskFileExists
    G3d_maskFileExists.restype = c_int
    G3d_maskFileExists.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 390
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskOpenOld'):
    G3d_maskOpenOld = _libs['grass_g3d.6.4.2RC2'].G3d_maskOpenOld
    G3d_maskOpenOld.restype = c_int
    G3d_maskOpenOld.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 391
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskReopen'):
    G3d_maskReopen = _libs['grass_g3d.6.4.2RC2'].G3d_maskReopen
    G3d_maskReopen.restype = c_int
    G3d_maskReopen.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 392
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isMasked'):
    G3d_isMasked = _libs['grass_g3d.6.4.2RC2'].G3d_isMasked
    G3d_isMasked.restype = c_int
    G3d_isMasked.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 393
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskNum'):
    G3d_maskNum = _libs['grass_g3d.6.4.2RC2'].G3d_maskNum
    G3d_maskNum.restype = None
    G3d_maskNum.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 394
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskFloat'):
    G3d_maskFloat = _libs['grass_g3d.6.4.2RC2'].G3d_maskFloat
    G3d_maskFloat.restype = None
    G3d_maskFloat.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(c_float)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 395
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskDouble'):
    G3d_maskDouble = _libs['grass_g3d.6.4.2RC2'].G3d_maskDouble
    G3d_maskDouble.restype = None
    G3d_maskDouble.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 396
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskTile'):
    G3d_maskTile = _libs['grass_g3d.6.4.2RC2'].G3d_maskTile
    G3d_maskTile.restype = None
    G3d_maskTile.argtypes = [POINTER(G3D_Map), c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 397
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskOn'):
    G3d_maskOn = _libs['grass_g3d.6.4.2RC2'].G3d_maskOn
    G3d_maskOn.restype = None
    G3d_maskOn.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 398
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskOff'):
    G3d_maskOff = _libs['grass_g3d.6.4.2RC2'].G3d_maskOff
    G3d_maskOff.restype = None
    G3d_maskOff.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 399
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskIsOn'):
    G3d_maskIsOn = _libs['grass_g3d.6.4.2RC2'].G3d_maskIsOn
    G3d_maskIsOn.restype = c_int
    G3d_maskIsOn.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 400
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskIsOff'):
    G3d_maskIsOff = _libs['grass_g3d.6.4.2RC2'].G3d_maskIsOff
    G3d_maskIsOff.restype = c_int
    G3d_maskIsOff.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 401
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskFile'):
    G3d_maskFile = _libs['grass_g3d.6.4.2RC2'].G3d_maskFile
    G3d_maskFile.restype = ReturnString
    G3d_maskFile.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 402
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_maskMapExists'):
    G3d_maskMapExists = _libs['grass_g3d.6.4.2RC2'].G3d_maskMapExists
    G3d_maskMapExists.restype = c_int
    G3d_maskMapExists.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 405
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_g3dType2cellType'):
    G3d_g3dType2cellType = _libs['grass_g3d.6.4.2RC2'].G3d_g3dType2cellType
    G3d_g3dType2cellType.restype = c_int
    G3d_g3dType2cellType.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 406
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_copyFloat2Double'):
    G3d_copyFloat2Double = _libs['grass_g3d.6.4.2RC2'].G3d_copyFloat2Double
    G3d_copyFloat2Double.restype = None
    G3d_copyFloat2Double.argtypes = [POINTER(c_float), c_int, POINTER(c_double), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 407
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_copyDouble2Float'):
    G3d_copyDouble2Float = _libs['grass_g3d.6.4.2RC2'].G3d_copyDouble2Float
    G3d_copyDouble2Float.restype = None
    G3d_copyDouble2Float.argtypes = [POINTER(c_double), c_int, POINTER(c_float), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 408
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_copyValues'):
    G3d_copyValues = _libs['grass_g3d.6.4.2RC2'].G3d_copyValues
    G3d_copyValues.restype = None
    G3d_copyValues.argtypes = [POINTER(None), c_int, c_int, POINTER(None), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 409
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_length'):
    G3d_length = _libs['grass_g3d.6.4.2RC2'].G3d_length
    G3d_length.restype = c_int
    G3d_length.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 410
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_externLength'):
    G3d_externLength = _libs['grass_g3d.6.4.2RC2'].G3d_externLength
    G3d_externLength.restype = c_int
    G3d_externLength.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 413
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isNullValueNum'):
    G3d_isNullValueNum = _libs['grass_g3d.6.4.2RC2'].G3d_isNullValueNum
    G3d_isNullValueNum.restype = c_int
    G3d_isNullValueNum.argtypes = [POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 414
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setNullValue'):
    G3d_setNullValue = _libs['grass_g3d.6.4.2RC2'].G3d_setNullValue
    G3d_setNullValue.restype = None
    G3d_setNullValue.argtypes = [POINTER(None), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 418
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_openCellOldNoHeader'):
    G3d_openCellOldNoHeader = _libs['grass_g3d.6.4.2RC2'].G3d_openCellOldNoHeader
    G3d_openCellOldNoHeader.restype = POINTER(None)
    G3d_openCellOldNoHeader.argtypes = [String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 419
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_openCellOld'):
    G3d_openCellOld = _libs['grass_g3d.6.4.2RC2'].G3d_openCellOld
    G3d_openCellOld.restype = POINTER(None)
    G3d_openCellOld.argtypes = [String, String, POINTER(G3D_Region), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 420
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_openCellNew'):
    G3d_openCellNew = _libs['grass_g3d.6.4.2RC2'].G3d_openCellNew
    G3d_openCellNew.restype = POINTER(None)
    G3d_openCellNew.argtypes = [String, c_int, c_int, POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 423
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setStandard3dInputParams'):
    G3d_setStandard3dInputParams = _libs['grass_g3d.6.4.2RC2'].G3d_setStandard3dInputParams
    G3d_setStandard3dInputParams.restype = None
    G3d_setStandard3dInputParams.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 424
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getStandard3dParams'):
    G3d_getStandard3dParams = _libs['grass_g3d.6.4.2RC2'].G3d_getStandard3dParams
    G3d_getStandard3dParams.restype = c_int
    G3d_getStandard3dParams.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 426
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setWindowParams'):
    G3d_setWindowParams = _libs['grass_g3d.6.4.2RC2'].G3d_setWindowParams
    G3d_setWindowParams.restype = None
    G3d_setWindowParams.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 427
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getWindowParams'):
    G3d_getWindowParams = _libs['grass_g3d.6.4.2RC2'].G3d_getWindowParams
    G3d_getWindowParams.restype = ReturnString
    G3d_getWindowParams.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 430
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_range_updateFromTile'):
    G3d_range_updateFromTile = _libs['grass_g3d.6.4.2RC2'].G3d_range_updateFromTile
    G3d_range_updateFromTile.restype = None
    G3d_range_updateFromTile.argtypes = [POINTER(G3D_Map), POINTER(None), c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 432
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readRange'):
    G3d_readRange = _libs['grass_g3d.6.4.2RC2'].G3d_readRange
    G3d_readRange.restype = c_int
    G3d_readRange.argtypes = [String, String, POINTER(struct_FPRange)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 433
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_range_load'):
    G3d_range_load = _libs['grass_g3d.6.4.2RC2'].G3d_range_load
    G3d_range_load.restype = c_int
    G3d_range_load.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 434
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_range_min_max'):
    G3d_range_min_max = _libs['grass_g3d.6.4.2RC2'].G3d_range_min_max
    G3d_range_min_max.restype = None
    G3d_range_min_max.argtypes = [POINTER(G3D_Map), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 435
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_range_write'):
    G3d_range_write = _libs['grass_g3d.6.4.2RC2'].G3d_range_write
    G3d_range_write.restype = c_int
    G3d_range_write.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 436
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_range_init'):
    G3d_range_init = _libs['grass_g3d.6.4.2RC2'].G3d_range_init
    G3d_range_init.restype = c_int
    G3d_range_init.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 439
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getRegionValue'):
    G3d_getRegionValue = _libs['grass_g3d.6.4.2RC2'].G3d_getRegionValue
    G3d_getRegionValue.restype = None
    G3d_getRegionValue.argtypes = [POINTER(G3D_Map), c_double, c_double, c_double, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 440
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_adjustRegion'):
    G3d_adjustRegion = _libs['grass_g3d.6.4.2RC2'].G3d_adjustRegion
    G3d_adjustRegion.restype = None
    G3d_adjustRegion.argtypes = [POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 441
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_regionCopy'):
    G3d_regionCopy = _libs['grass_g3d.6.4.2RC2'].G3d_regionCopy
    G3d_regionCopy.restype = None
    G3d_regionCopy.argtypes = [POINTER(G3D_Region), POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 442
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_incorporate2dRegion'):
    G3d_incorporate2dRegion = _libs['grass_g3d.6.4.2RC2'].G3d_incorporate2dRegion
    G3d_incorporate2dRegion.restype = None
    G3d_incorporate2dRegion.argtypes = [POINTER(struct_Cell_head), POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 443
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_regionFromToCellHead'):
    G3d_regionFromToCellHead = _libs['grass_g3d.6.4.2RC2'].G3d_regionFromToCellHead
    G3d_regionFromToCellHead.restype = None
    G3d_regionFromToCellHead.argtypes = [POINTER(struct_Cell_head), POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 444
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_adjustRegionRes'):
    G3d_adjustRegionRes = _libs['grass_g3d.6.4.2RC2'].G3d_adjustRegionRes
    G3d_adjustRegionRes.restype = None
    G3d_adjustRegionRes.argtypes = [POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 445
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_extract2dRegion'):
    G3d_extract2dRegion = _libs['grass_g3d.6.4.2RC2'].G3d_extract2dRegion
    G3d_extract2dRegion.restype = None
    G3d_extract2dRegion.argtypes = [POINTER(G3D_Region), POINTER(struct_Cell_head)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 446
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_regionToCellHead'):
    G3d_regionToCellHead = _libs['grass_g3d.6.4.2RC2'].G3d_regionToCellHead
    G3d_regionToCellHead.restype = None
    G3d_regionToCellHead.argtypes = [POINTER(G3D_Region), POINTER(struct_Cell_head)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 447
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readRegionMap'):
    G3d_readRegionMap = _libs['grass_g3d.6.4.2RC2'].G3d_readRegionMap
    G3d_readRegionMap.restype = c_int
    G3d_readRegionMap.argtypes = [String, String, POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 450
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_nearestNeighbor'):
    G3d_nearestNeighbor = _libs['grass_g3d.6.4.2RC2'].G3d_nearestNeighbor
    G3d_nearestNeighbor.restype = None
    G3d_nearestNeighbor.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 451
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setResamplingFun'):
    G3d_setResamplingFun = _libs['grass_g3d.6.4.2RC2'].G3d_setResamplingFun
    G3d_setResamplingFun.restype = None
    G3d_setResamplingFun.argtypes = [POINTER(G3D_Map), CFUNCTYPE(UNCHECKED(None), )]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 452
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getResamplingFun'):
    G3d_getResamplingFun = _libs['grass_g3d.6.4.2RC2'].G3d_getResamplingFun
    G3d_getResamplingFun.restype = None
    G3d_getResamplingFun.argtypes = [POINTER(G3D_Map), POINTER(CFUNCTYPE(UNCHECKED(None), ))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 453
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getNearestNeighborFunPtr'):
    G3d_getNearestNeighborFunPtr = _libs['grass_g3d.6.4.2RC2'].G3d_getNearestNeighborFunPtr
    G3d_getNearestNeighborFunPtr.restype = None
    G3d_getNearestNeighborFunPtr.argtypes = [POINTER(CFUNCTYPE(UNCHECKED(None), ))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 456
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getVolumeA'):
    G3d_getVolumeA = _libs['grass_g3d.6.4.2RC2'].G3d_getVolumeA
    G3d_getVolumeA.restype = None
    G3d_getVolumeA.argtypes = [POINTER(None), (((c_double * 3) * 2) * 2) * 2, c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 457
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getVolume'):
    G3d_getVolume = _libs['grass_g3d.6.4.2RC2'].G3d_getVolume
    G3d_getVolume.restype = None
    G3d_getVolume.argtypes = [POINTER(None), c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 460
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getAlignedVolume'):
    G3d_getAlignedVolume = _libs['grass_g3d.6.4.2RC2'].G3d_getAlignedVolume
    G3d_getAlignedVolume.restype = None
    G3d_getAlignedVolume.argtypes = [POINTER(None), c_double, c_double, c_double, c_double, c_double, c_double, c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 462
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_makeAlignedVolumeFile'):
    G3d_makeAlignedVolumeFile = _libs['grass_g3d.6.4.2RC2'].G3d_makeAlignedVolumeFile
    G3d_makeAlignedVolumeFile.restype = None
    G3d_makeAlignedVolumeFile.argtypes = [POINTER(None), String, c_double, c_double, c_double, c_double, c_double, c_double, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 465
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getValue'):
    G3d_getValue = _libs['grass_g3d.6.4.2RC2'].G3d_getValue
    G3d_getValue.restype = None
    G3d_getValue.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 466
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getFloat'):
    G3d_getFloat = _libs['grass_g3d.6.4.2RC2'].G3d_getFloat
    G3d_getFloat.restype = c_float
    G3d_getFloat.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 467
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getDouble'):
    G3d_getDouble = _libs['grass_g3d.6.4.2RC2'].G3d_getDouble
    G3d_getDouble.restype = c_double
    G3d_getDouble.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 468
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_windowPtr'):
    G3d_windowPtr = _libs['grass_g3d.6.4.2RC2'].G3d_windowPtr
    G3d_windowPtr.restype = POINTER(G3D_Region)
    G3d_windowPtr.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 469
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setWindow'):
    G3d_setWindow = _libs['grass_g3d.6.4.2RC2'].G3d_setWindow
    G3d_setWindow.restype = None
    G3d_setWindow.argtypes = [POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 470
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setWindowMap'):
    G3d_setWindowMap = _libs['grass_g3d.6.4.2RC2'].G3d_setWindowMap
    G3d_setWindowMap.restype = None
    G3d_setWindowMap.argtypes = [POINTER(G3D_Map), POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 471
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getWindow'):
    G3d_getWindow = _libs['grass_g3d.6.4.2RC2'].G3d_getWindow
    G3d_getWindow.restype = None
    G3d_getWindow.argtypes = [POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 474
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_useWindowParams'):
    G3d_useWindowParams = _libs['grass_g3d.6.4.2RC2'].G3d_useWindowParams
    G3d_useWindowParams.restype = None
    G3d_useWindowParams.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 475
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readWindow'):
    G3d_readWindow = _libs['grass_g3d.6.4.2RC2'].G3d_readWindow
    G3d_readWindow.restype = c_int
    G3d_readWindow.argtypes = [POINTER(G3D_Region), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 479
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getBlockNocache'):
    G3d_getBlockNocache = _libs['grass_g3d.6.4.2RC2'].G3d_getBlockNocache
    G3d_getBlockNocache.restype = None
    G3d_getBlockNocache.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 481
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getBlock'):
    G3d_getBlock = _libs['grass_g3d.6.4.2RC2'].G3d_getBlock
    G3d_getBlock.restype = None
    G3d_getBlock.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 484
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readHeader'):
    G3d_readHeader = _libs['grass_g3d.6.4.2RC2'].G3d_readHeader
    G3d_readHeader.restype = c_int
    G3d_readHeader.argtypes = [POINTER(G3D_Map), POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(POINTER(c_char))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 488
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeHeader'):
    G3d_writeHeader = _libs['grass_g3d.6.4.2RC2'].G3d_writeHeader
    G3d_writeHeader.restype = c_int
    G3d_writeHeader.argtypes = [POINTER(G3D_Map), c_int, c_int, c_double, c_double, c_double, c_double, c_double, c_double, c_int, c_int, c_int, c_double, c_double, c_double, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 492
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_cacheSizeEncode'):
    G3d_cacheSizeEncode = _libs['grass_g3d.6.4.2RC2'].G3d_cacheSizeEncode
    G3d_cacheSizeEncode.restype = c_int
    G3d_cacheSizeEncode.argtypes = [c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 493
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d__computeCacheSize'):
    G3d__computeCacheSize = _libs['grass_g3d.6.4.2RC2'].G3d__computeCacheSize
    G3d__computeCacheSize.restype = c_int
    G3d__computeCacheSize.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 494
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_fillHeader'):
    G3d_fillHeader = _libs['grass_g3d.6.4.2RC2'].G3d_fillHeader
    G3d_fillHeader.restype = c_int
    G3d_fillHeader.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_double, c_double, c_double, c_double, c_double, c_double, c_int, c_int, c_int, c_double, c_double, c_double, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 499
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getCoordsMap'):
    G3d_getCoordsMap = _libs['grass_g3d.6.4.2RC2'].G3d_getCoordsMap
    G3d_getCoordsMap.restype = None
    G3d_getCoordsMap.argtypes = [POINTER(G3D_Map), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 500
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getCoordsMapWindow'):
    G3d_getCoordsMapWindow = _libs['grass_g3d.6.4.2RC2'].G3d_getCoordsMapWindow
    G3d_getCoordsMapWindow.restype = None
    G3d_getCoordsMapWindow.argtypes = [POINTER(G3D_Map), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 501
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getNofTilesMap'):
    G3d_getNofTilesMap = _libs['grass_g3d.6.4.2RC2'].G3d_getNofTilesMap
    G3d_getNofTilesMap.restype = None
    G3d_getNofTilesMap.argtypes = [POINTER(G3D_Map), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 502
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getRegionMap'):
    G3d_getRegionMap = _libs['grass_g3d.6.4.2RC2'].G3d_getRegionMap
    G3d_getRegionMap.restype = None
    G3d_getRegionMap.argtypes = [POINTER(G3D_Map), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 504
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getWindowMap'):
    G3d_getWindowMap = _libs['grass_g3d.6.4.2RC2'].G3d_getWindowMap
    G3d_getWindowMap.restype = None
    G3d_getWindowMap.argtypes = [POINTER(G3D_Map), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 506
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getTileDimensionsMap'):
    G3d_getTileDimensionsMap = _libs['grass_g3d.6.4.2RC2'].G3d_getTileDimensionsMap
    G3d_getTileDimensionsMap.restype = None
    G3d_getTileDimensionsMap.argtypes = [POINTER(G3D_Map), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 507
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileTypeMap'):
    G3d_tileTypeMap = _libs['grass_g3d.6.4.2RC2'].G3d_tileTypeMap
    G3d_tileTypeMap.restype = c_int
    G3d_tileTypeMap.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 508
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_fileTypeMap'):
    G3d_fileTypeMap = _libs['grass_g3d.6.4.2RC2'].G3d_fileTypeMap
    G3d_fileTypeMap.restype = c_int
    G3d_fileTypeMap.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 509
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tilePrecisionMap'):
    G3d_tilePrecisionMap = _libs['grass_g3d.6.4.2RC2'].G3d_tilePrecisionMap
    G3d_tilePrecisionMap.restype = c_int
    G3d_tilePrecisionMap.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 510
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileUseCacheMap'):
    G3d_tileUseCacheMap = _libs['grass_g3d.6.4.2RC2'].G3d_tileUseCacheMap
    G3d_tileUseCacheMap.restype = c_int
    G3d_tileUseCacheMap.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 511
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_printHeader'):
    G3d_printHeader = _libs['grass_g3d.6.4.2RC2'].G3d_printHeader
    G3d_printHeader.restype = None
    G3d_printHeader.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 512
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getRegionStructMap'):
    G3d_getRegionStructMap = _libs['grass_g3d.6.4.2RC2'].G3d_getRegionStructMap
    G3d_getRegionStructMap.restype = None
    G3d_getRegionStructMap.argtypes = [POINTER(G3D_Map), POINTER(G3D_Region)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 515
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_flushIndex'):
    G3d_flushIndex = _libs['grass_g3d.6.4.2RC2'].G3d_flushIndex
    G3d_flushIndex.restype = c_int
    G3d_flushIndex.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 516
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_initIndex'):
    G3d_initIndex = _libs['grass_g3d.6.4.2RC2'].G3d_initIndex
    G3d_initIndex.restype = c_int
    G3d_initIndex.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 519
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_retile'):
    G3d_retile = _libs['grass_g3d.6.4.2RC2'].G3d_retile
    G3d_retile.restype = None
    G3d_retile.argtypes = [POINTER(None), String, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 522
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_rle_count_only'):
    G_rle_count_only = _libs['grass_g3d.6.4.2RC2'].G_rle_count_only
    G_rle_count_only.restype = c_int
    G_rle_count_only.argtypes = [String, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 523
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_rle_encode'):
    G_rle_encode = _libs['grass_g3d.6.4.2RC2'].G_rle_encode
    G_rle_encode.restype = None
    G_rle_encode.argtypes = [String, String, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 524
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G_rle_decode'):
    G_rle_decode = _libs['grass_g3d.6.4.2RC2'].G_rle_decode
    G_rle_decode.restype = None
    G_rle_decode.argtypes = [String, String, c_int, c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 527
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_allocTilesType'):
    G3d_allocTilesType = _libs['grass_g3d.6.4.2RC2'].G3d_allocTilesType
    G3d_allocTilesType.restype = POINTER(None)
    G3d_allocTilesType.argtypes = [POINTER(G3D_Map), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 528
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_allocTiles'):
    G3d_allocTiles = _libs['grass_g3d.6.4.2RC2'].G3d_allocTiles
    G3d_allocTiles.restype = POINTER(None)
    G3d_allocTiles.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 529
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_freeTiles'):
    G3d_freeTiles = _libs['grass_g3d.6.4.2RC2'].G3d_freeTiles
    G3d_freeTiles.restype = None
    G3d_freeTiles.argtypes = [POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 532
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getTilePtr'):
    G3d_getTilePtr = _libs['grass_g3d.6.4.2RC2'].G3d_getTilePtr
    G3d_getTilePtr.restype = POINTER(None)
    G3d_getTilePtr.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 533
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileLoad'):
    G3d_tileLoad = _libs['grass_g3d.6.4.2RC2'].G3d_tileLoad
    G3d_tileLoad.restype = c_int
    G3d_tileLoad.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 534
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d__removeTile'):
    G3d__removeTile = _libs['grass_g3d.6.4.2RC2'].G3d__removeTile
    G3d__removeTile.restype = c_int
    G3d__removeTile.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 535
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getFloatRegion'):
    G3d_getFloatRegion = _libs['grass_g3d.6.4.2RC2'].G3d_getFloatRegion
    G3d_getFloatRegion.restype = c_float
    G3d_getFloatRegion.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 536
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getDoubleRegion'):
    G3d_getDoubleRegion = _libs['grass_g3d.6.4.2RC2'].G3d_getDoubleRegion
    G3d_getDoubleRegion.restype = c_double
    G3d_getDoubleRegion.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 537
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_getValueRegion'):
    G3d_getValueRegion = _libs['grass_g3d.6.4.2RC2'].G3d_getValueRegion
    G3d_getValueRegion.restype = None
    G3d_getValueRegion.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 540
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileIndex2tile'):
    G3d_tileIndex2tile = _libs['grass_g3d.6.4.2RC2'].G3d_tileIndex2tile
    G3d_tileIndex2tile.restype = None
    G3d_tileIndex2tile.argtypes = [POINTER(G3D_Map), c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 541
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tile2tileIndex'):
    G3d_tile2tileIndex = _libs['grass_g3d.6.4.2RC2'].G3d_tile2tileIndex
    G3d_tile2tileIndex.restype = c_int
    G3d_tile2tileIndex.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 542
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileCoordOrigin'):
    G3d_tileCoordOrigin = _libs['grass_g3d.6.4.2RC2'].G3d_tileCoordOrigin
    G3d_tileCoordOrigin.restype = None
    G3d_tileCoordOrigin.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 543
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileIndexOrigin'):
    G3d_tileIndexOrigin = _libs['grass_g3d.6.4.2RC2'].G3d_tileIndexOrigin
    G3d_tileIndexOrigin.restype = None
    G3d_tileIndexOrigin.argtypes = [POINTER(G3D_Map), c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 544
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_coord2tileCoord'):
    G3d_coord2tileCoord = _libs['grass_g3d.6.4.2RC2'].G3d_coord2tileCoord
    G3d_coord2tileCoord.restype = None
    G3d_coord2tileCoord.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 546
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_coord2tileIndex'):
    G3d_coord2tileIndex = _libs['grass_g3d.6.4.2RC2'].G3d_coord2tileIndex
    G3d_coord2tileIndex.restype = None
    G3d_coord2tileIndex.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 547
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_coordInRange'):
    G3d_coordInRange = _libs['grass_g3d.6.4.2RC2'].G3d_coordInRange
    G3d_coordInRange.restype = c_int
    G3d_coordInRange.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 548
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileIndexInRange'):
    G3d_tileIndexInRange = _libs['grass_g3d.6.4.2RC2'].G3d_tileIndexInRange
    G3d_tileIndexInRange.restype = c_int
    G3d_tileIndexInRange.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 549
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_tileInRange'):
    G3d_tileInRange = _libs['grass_g3d.6.4.2RC2'].G3d_tileInRange
    G3d_tileInRange.restype = c_int
    G3d_tileInRange.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 550
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_computeClippedTileDimensions'):
    G3d_computeClippedTileDimensions = _libs['grass_g3d.6.4.2RC2'].G3d_computeClippedTileDimensions
    G3d_computeClippedTileDimensions.restype = c_int
    G3d_computeClippedTileDimensions.argtypes = [POINTER(G3D_Map), c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 552
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_isValidLocation'):
    G3d_isValidLocation = _libs['grass_g3d.6.4.2RC2'].G3d_isValidLocation
    G3d_isValidLocation.restype = c_int
    G3d_isValidLocation.argtypes = [POINTER(G3D_Map), c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 553
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_location2coord'):
    G3d_location2coord = _libs['grass_g3d.6.4.2RC2'].G3d_location2coord
    G3d_location2coord.restype = None
    G3d_location2coord.argtypes = [POINTER(G3D_Map), c_double, c_double, c_double, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 556
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setNullTileType'):
    G3d_setNullTileType = _libs['grass_g3d.6.4.2RC2'].G3d_setNullTileType
    G3d_setNullTileType.restype = None
    G3d_setNullTileType.argtypes = [POINTER(G3D_Map), POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 557
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_setNullTile'):
    G3d_setNullTile = _libs['grass_g3d.6.4.2RC2'].G3d_setNullTile
    G3d_setNullTile.restype = None
    G3d_setNullTile.argtypes = [POINTER(G3D_Map), POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 560
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readTile'):
    G3d_readTile = _libs['grass_g3d.6.4.2RC2'].G3d_readTile
    G3d_readTile.restype = c_int
    G3d_readTile.argtypes = [POINTER(G3D_Map), c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 561
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readTileFloat'):
    G3d_readTileFloat = _libs['grass_g3d.6.4.2RC2'].G3d_readTileFloat
    G3d_readTileFloat.restype = c_int
    G3d_readTileFloat.argtypes = [POINTER(G3D_Map), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 562
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_readTileDouble'):
    G3d_readTileDouble = _libs['grass_g3d.6.4.2RC2'].G3d_readTileDouble
    G3d_readTileDouble.restype = c_int
    G3d_readTileDouble.argtypes = [POINTER(G3D_Map), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 563
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_lockTile'):
    G3d_lockTile = _libs['grass_g3d.6.4.2RC2'].G3d_lockTile
    G3d_lockTile.restype = c_int
    G3d_lockTile.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 564
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_unlockTile'):
    G3d_unlockTile = _libs['grass_g3d.6.4.2RC2'].G3d_unlockTile
    G3d_unlockTile.restype = c_int
    G3d_unlockTile.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 565
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_unlockAll'):
    G3d_unlockAll = _libs['grass_g3d.6.4.2RC2'].G3d_unlockAll
    G3d_unlockAll.restype = c_int
    G3d_unlockAll.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 566
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_autolockOn'):
    G3d_autolockOn = _libs['grass_g3d.6.4.2RC2'].G3d_autolockOn
    G3d_autolockOn.restype = None
    G3d_autolockOn.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 567
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_autolockOff'):
    G3d_autolockOff = _libs['grass_g3d.6.4.2RC2'].G3d_autolockOff
    G3d_autolockOff.restype = None
    G3d_autolockOff.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 568
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_minUnlocked'):
    G3d_minUnlocked = _libs['grass_g3d.6.4.2RC2'].G3d_minUnlocked
    G3d_minUnlocked.restype = None
    G3d_minUnlocked.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 569
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_beginCycle'):
    G3d_beginCycle = _libs['grass_g3d.6.4.2RC2'].G3d_beginCycle
    G3d_beginCycle.restype = c_int
    G3d_beginCycle.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 570
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_endCycle'):
    G3d_endCycle = _libs['grass_g3d.6.4.2RC2'].G3d_endCycle
    G3d_endCycle.restype = c_int
    G3d_endCycle.argtypes = [POINTER(G3D_Map)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 573
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeTile'):
    G3d_writeTile = _libs['grass_g3d.6.4.2RC2'].G3d_writeTile
    G3d_writeTile.restype = c_int
    G3d_writeTile.argtypes = [POINTER(G3D_Map), c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 574
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeTileFloat'):
    G3d_writeTileFloat = _libs['grass_g3d.6.4.2RC2'].G3d_writeTileFloat
    G3d_writeTileFloat.restype = c_int
    G3d_writeTileFloat.argtypes = [POINTER(G3D_Map), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 575
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeTileDouble'):
    G3d_writeTileDouble = _libs['grass_g3d.6.4.2RC2'].G3d_writeTileDouble
    G3d_writeTileDouble.restype = c_int
    G3d_writeTileDouble.argtypes = [POINTER(G3D_Map), c_int, POINTER(None)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 576
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_flushTile'):
    G3d_flushTile = _libs['grass_g3d.6.4.2RC2'].G3d_flushTile
    G3d_flushTile.restype = c_int
    G3d_flushTile.argtypes = [POINTER(G3D_Map), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 577
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_flushTileCube'):
    G3d_flushTileCube = _libs['grass_g3d.6.4.2RC2'].G3d_flushTileCube
    G3d_flushTileCube.restype = c_int
    G3d_flushTileCube.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 578
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_flushTilesInCube'):
    G3d_flushTilesInCube = _libs['grass_g3d.6.4.2RC2'].G3d_flushTilesInCube
    G3d_flushTilesInCube.restype = c_int
    G3d_flushTilesInCube.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_int, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 579
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_putFloat'):
    G3d_putFloat = _libs['grass_g3d.6.4.2RC2'].G3d_putFloat
    G3d_putFloat.restype = c_int
    G3d_putFloat.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_float]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 580
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_putDouble'):
    G3d_putDouble = _libs['grass_g3d.6.4.2RC2'].G3d_putDouble
    G3d_putDouble.restype = c_int
    G3d_putDouble.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 581
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_putValue'):
    G3d_putValue = _libs['grass_g3d.6.4.2RC2'].G3d_putValue
    G3d_putValue.restype = c_int
    G3d_putValue.argtypes = [POINTER(G3D_Map), c_int, c_int, c_int, POINTER(None), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 584
if hasattr(_libs['grass_g3d.6.4.2RC2'], 'G3d_writeAscii'):
    G3d_writeAscii = _libs['grass_g3d.6.4.2RC2'].G3d_writeAscii
    G3d_writeAscii.restype = None
    G3d_writeAscii.argtypes = [POINTER(None), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 5
try:
    G3D_TILE_SAME_AS_FILE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 6
try:
    G3D_NO_COMPRESSION = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 6
try:
    G3D_COMPRESSION = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 7
try:
    G3D_USE_LZW = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 7
try:
    G3D_NO_LZW = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 8
try:
    G3D_USE_RLE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 8
try:
    G3D_NO_RLE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 9
try:
    G3D_MAX_PRECISION = (-1)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_NO_CACHE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_DEFAULT = (-1)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_X = (-2)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_Y = (-3)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_Z = (-4)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_XY = (-5)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_XZ = (-6)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_YZ = (-7)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 10
try:
    G3D_USE_CACHE_XYZ = (-8)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 11
try:
    G3D_DEFAULT_WINDOW = NULL
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_DIRECTORY = 'grid3'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_CELL_ELEMENT = 'cell'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_CATS_ELEMENT = 'cats'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_RANGE_ELEMENT = 'range'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_HEADER_ELEMENT = 'cellhd'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_HISTORY_ELEMENT = 'hist'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_COLOR_ELEMENT = 'color'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_COLOR2_DIRECTORY = 'colr2'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_MASK_MAP = 'G3D_MASK'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_WINDOW_ELEMENT = 'WIND3'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_DEFAULT_WINDOW_ELEMENT = 'DEFAULT_WIND3'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_WINDOW_DATABASE = 'windows3d'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 12
try:
    G3D_PERMANENT_MAPSET = 'PERMANENT'
except:
    pass

G3D_Map = struct_G3D_Map # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\G3d.h: 72

# No inserted files

