'''Wrapper for imagery.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_I.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagery.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h -o imagery.py

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

_libs["grass_I.6.4.2RC2"] = load_library("grass_I.6.4.2RC2")

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

CELL = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 256

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 9
class struct_Ref_Color(Structure):
    pass

struct_Ref_Color.__slots__ = [
    'table',
    'index',
    'buf',
    'fd',
    'min',
    'max',
    'n',
]
struct_Ref_Color._fields_ = [
    ('table', POINTER(c_ubyte)),
    ('index', POINTER(c_ubyte)),
    ('buf', POINTER(c_ubyte)),
    ('fd', c_int),
    ('min', CELL),
    ('max', CELL),
    ('n', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 19
class struct_Ref_Files(Structure):
    pass

struct_Ref_Files.__slots__ = [
    'name',
    'mapset',
]
struct_Ref_Files._fields_ = [
    ('name', c_char * 256),
    ('mapset', c_char * 256),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 25
class struct_Ref(Structure):
    pass

struct_Ref.__slots__ = [
    'nfiles',
    'file',
    'red',
    'grn',
    'blu',
]
struct_Ref._fields_ = [
    ('nfiles', c_int),
    ('file', POINTER(struct_Ref_Files)),
    ('red', struct_Ref_Color),
    ('grn', struct_Ref_Color),
    ('blu', struct_Ref_Color),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 32
class struct_Tape_Info(Structure):
    pass

struct_Tape_Info.__slots__ = [
    'title',
    'id',
    'desc',
]
struct_Tape_Info._fields_ = [
    ('title', c_char * 75),
    ('id', (c_char * 75) * 2),
    ('desc', (c_char * 75) * 5),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 39
class struct_Control_Points(Structure):
    pass

struct_Control_Points.__slots__ = [
    'count',
    'e1',
    'n1',
    'e2',
    'n2',
    'status',
]
struct_Control_Points._fields_ = [
    ('count', c_int),
    ('e1', POINTER(c_double)),
    ('n1', POINTER(c_double)),
    ('e2', POINTER(c_double)),
    ('n2', POINTER(c_double)),
    ('status', POINTER(c_int)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 49
class struct_One_Sig(Structure):
    pass

struct_One_Sig.__slots__ = [
    'desc',
    'npoints',
    'mean',
    'var',
    'status',
    'r',
    'g',
    'b',
    'have_color',
]
struct_One_Sig._fields_ = [
    ('desc', c_char * 100),
    ('npoints', c_int),
    ('mean', POINTER(c_double)),
    ('var', POINTER(POINTER(c_double))),
    ('status', c_int),
    ('r', c_float),
    ('g', c_float),
    ('b', c_float),
    ('have_color', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 60
class struct_Signature(Structure):
    pass

struct_Signature.__slots__ = [
    'nbands',
    'nsigs',
    'title',
    'sig',
]
struct_Signature._fields_ = [
    ('nbands', c_int),
    ('nsigs', c_int),
    ('title', c_char * 100),
    ('sig', POINTER(struct_One_Sig)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 68
class struct_SubSig(Structure):
    pass

struct_SubSig.__slots__ = [
    'N',
    'pi',
    'means',
    'R',
    'Rinv',
    'cnst',
    'used',
]
struct_SubSig._fields_ = [
    ('N', c_double),
    ('pi', c_double),
    ('means', POINTER(c_double)),
    ('R', POINTER(POINTER(c_double))),
    ('Rinv', POINTER(POINTER(c_double))),
    ('cnst', c_double),
    ('used', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 79
class struct_ClassData(Structure):
    pass

struct_ClassData.__slots__ = [
    'npixels',
    'count',
    'x',
    'p',
]
struct_ClassData._fields_ = [
    ('npixels', c_int),
    ('count', c_int),
    ('x', POINTER(POINTER(c_double))),
    ('p', POINTER(POINTER(c_double))),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 87
class struct_ClassSig(Structure):
    pass

struct_ClassSig.__slots__ = [
    'classnum',
    'title',
    'used',
    'type',
    'nsubclasses',
    'SubSig',
    'ClassData',
]
struct_ClassSig._fields_ = [
    ('classnum', c_long),
    ('title', String),
    ('used', c_int),
    ('type', c_int),
    ('nsubclasses', c_int),
    ('SubSig', POINTER(struct_SubSig)),
    ('ClassData', struct_ClassData),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 98
class struct_SigSet(Structure):
    pass

struct_SigSet.__slots__ = [
    'nbands',
    'nclasses',
    'title',
    'ClassSig',
]
struct_SigSet._fields_ = [
    ('nbands', c_int),
    ('nclasses', c_int),
    ('title', String),
    ('ClassSig', POINTER(struct_ClassSig)),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 5
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_malloc'):
    I_malloc = _libs['grass_I.6.4.2RC2'].I_malloc
    I_malloc.restype = POINTER(None)
    I_malloc.argtypes = [c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 6
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_realloc'):
    I_realloc = _libs['grass_I.6.4.2RC2'].I_realloc
    I_realloc.restype = POINTER(None)
    I_realloc.argtypes = [POINTER(None), c_size_t]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 7
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free'):
    I_free = _libs['grass_I.6.4.2RC2'].I_free
    I_free.restype = c_int
    I_free.argtypes = [POINTER(None)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 8
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_alloc_double2'):
    I_alloc_double2 = _libs['grass_I.6.4.2RC2'].I_alloc_double2
    I_alloc_double2.restype = POINTER(POINTER(c_double))
    I_alloc_double2.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 9
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_alloc_int'):
    I_alloc_int = _libs['grass_I.6.4.2RC2'].I_alloc_int
    I_alloc_int.restype = POINTER(c_int)
    I_alloc_int.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 10
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_alloc_int2'):
    I_alloc_int2 = _libs['grass_I.6.4.2RC2'].I_alloc_int2
    I_alloc_int2.restype = POINTER(POINTER(c_int))
    I_alloc_int2.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 11
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free_int2'):
    I_free_int2 = _libs['grass_I.6.4.2RC2'].I_free_int2
    I_free_int2.restype = c_int
    I_free_int2.argtypes = [POINTER(POINTER(c_int))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 12
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free_double2'):
    I_free_double2 = _libs['grass_I.6.4.2RC2'].I_free_double2
    I_free_double2.restype = c_int
    I_free_double2.argtypes = [POINTER(POINTER(c_double))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 13
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_alloc_double3'):
    I_alloc_double3 = _libs['grass_I.6.4.2RC2'].I_alloc_double3
    I_alloc_double3.restype = POINTER(POINTER(POINTER(c_double)))
    I_alloc_double3.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 14
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free_double3'):
    I_free_double3 = _libs['grass_I.6.4.2RC2'].I_free_double3
    I_free_double3.restype = c_int
    I_free_double3.argtypes = [POINTER(POINTER(POINTER(c_double)))]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 17
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_ask_group_old'):
    I_ask_group_old = _libs['grass_I.6.4.2RC2'].I_ask_group_old
    I_ask_group_old.restype = c_int
    I_ask_group_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 20
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_to_eol'):
    I_get_to_eol = _libs['grass_I.6.4.2RC2'].I_get_to_eol
    I_get_to_eol.restype = c_int
    I_get_to_eol.argtypes = [String, c_int, POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 23
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_find_group'):
    I_find_group = _libs['grass_I.6.4.2RC2'].I_find_group
    I_find_group.restype = c_int
    I_find_group.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 24
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_find_group_file'):
    I_find_group_file = _libs['grass_I.6.4.2RC2'].I_find_group_file
    I_find_group_file.restype = c_int
    I_find_group_file.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 25
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_find_subgroup'):
    I_find_subgroup = _libs['grass_I.6.4.2RC2'].I_find_subgroup
    I_find_subgroup.restype = c_int
    I_find_subgroup.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 26
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_find_subgroup_file'):
    I_find_subgroup_file = _libs['grass_I.6.4.2RC2'].I_find_subgroup_file
    I_find_subgroup_file.restype = c_int
    I_find_subgroup_file.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 29
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_group_file_new'):
    I_fopen_group_file_new = _libs['grass_I.6.4.2RC2'].I_fopen_group_file_new
    I_fopen_group_file_new.restype = POINTER(FILE)
    I_fopen_group_file_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 30
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_group_file_append'):
    I_fopen_group_file_append = _libs['grass_I.6.4.2RC2'].I_fopen_group_file_append
    I_fopen_group_file_append.restype = POINTER(FILE)
    I_fopen_group_file_append.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 31
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_group_file_old'):
    I_fopen_group_file_old = _libs['grass_I.6.4.2RC2'].I_fopen_group_file_old
    I_fopen_group_file_old.restype = POINTER(FILE)
    I_fopen_group_file_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 32
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_subgroup_file_new'):
    I_fopen_subgroup_file_new = _libs['grass_I.6.4.2RC2'].I_fopen_subgroup_file_new
    I_fopen_subgroup_file_new.restype = POINTER(FILE)
    I_fopen_subgroup_file_new.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 33
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_subgroup_file_append'):
    I_fopen_subgroup_file_append = _libs['grass_I.6.4.2RC2'].I_fopen_subgroup_file_append
    I_fopen_subgroup_file_append.restype = POINTER(FILE)
    I_fopen_subgroup_file_append.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 34
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_subgroup_file_old'):
    I_fopen_subgroup_file_old = _libs['grass_I.6.4.2RC2'].I_fopen_subgroup_file_old
    I_fopen_subgroup_file_old.restype = POINTER(FILE)
    I_fopen_subgroup_file_old.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 37
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_compute_georef_equations'):
    I_compute_georef_equations = _libs['grass_I.6.4.2RC2'].I_compute_georef_equations
    I_compute_georef_equations.restype = c_int
    I_compute_georef_equations.argtypes = [POINTER(struct_Control_Points), c_double * 3, c_double * 3, c_double * 3, c_double * 3]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 39
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_georef'):
    I_georef = _libs['grass_I.6.4.2RC2'].I_georef
    I_georef.restype = c_int
    I_georef.argtypes = [c_double, c_double, POINTER(c_double), POINTER(c_double), c_double * 3, c_double * 3]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 42
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_group'):
    I_get_group = _libs['grass_I.6.4.2RC2'].I_get_group
    I_get_group.restype = c_int
    I_get_group.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 43
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_group'):
    I_put_group = _libs['grass_I.6.4.2RC2'].I_put_group
    I_put_group.restype = c_int
    I_put_group.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 44
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_subgroup'):
    I_get_subgroup = _libs['grass_I.6.4.2RC2'].I_get_subgroup
    I_get_subgroup.restype = c_int
    I_get_subgroup.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 45
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_subgroup'):
    I_put_subgroup = _libs['grass_I.6.4.2RC2'].I_put_subgroup
    I_put_subgroup.restype = c_int
    I_put_subgroup.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 46
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_group_ref'):
    I_get_group_ref = _libs['grass_I.6.4.2RC2'].I_get_group_ref
    I_get_group_ref.restype = c_int
    I_get_group_ref.argtypes = [String, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 47
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_subgroup_ref'):
    I_get_subgroup_ref = _libs['grass_I.6.4.2RC2'].I_get_subgroup_ref
    I_get_subgroup_ref.restype = c_int
    I_get_subgroup_ref.argtypes = [String, String, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 48
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_init_ref_color_nums'):
    I_init_ref_color_nums = _libs['grass_I.6.4.2RC2'].I_init_ref_color_nums
    I_init_ref_color_nums.restype = c_int
    I_init_ref_color_nums.argtypes = [POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 49
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_group_ref'):
    I_put_group_ref = _libs['grass_I.6.4.2RC2'].I_put_group_ref
    I_put_group_ref.restype = c_int
    I_put_group_ref.argtypes = [String, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 50
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_subgroup_ref'):
    I_put_subgroup_ref = _libs['grass_I.6.4.2RC2'].I_put_subgroup_ref
    I_put_subgroup_ref.restype = c_int
    I_put_subgroup_ref.argtypes = [String, String, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 51
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_add_file_to_group_ref'):
    I_add_file_to_group_ref = _libs['grass_I.6.4.2RC2'].I_add_file_to_group_ref
    I_add_file_to_group_ref.restype = c_int
    I_add_file_to_group_ref.argtypes = [String, String, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 52
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_transfer_group_ref_file'):
    I_transfer_group_ref_file = _libs['grass_I.6.4.2RC2'].I_transfer_group_ref_file
    I_transfer_group_ref_file.restype = c_int
    I_transfer_group_ref_file.argtypes = [POINTER(struct_Ref), c_int, POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 53
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_init_group_ref'):
    I_init_group_ref = _libs['grass_I.6.4.2RC2'].I_init_group_ref
    I_init_group_ref.restype = c_int
    I_init_group_ref.argtypes = [POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 54
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free_group_ref'):
    I_free_group_ref = _libs['grass_I.6.4.2RC2'].I_free_group_ref
    I_free_group_ref.restype = c_int
    I_free_group_ref.argtypes = [POINTER(struct_Ref)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 57
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_group'):
    I_list_group = _libs['grass_I.6.4.2RC2'].I_list_group
    I_list_group.restype = c_int
    I_list_group.argtypes = [String, POINTER(struct_Ref), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 58
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_group_simple'):
    I_list_group_simple = _libs['grass_I.6.4.2RC2'].I_list_group_simple
    I_list_group_simple.restype = c_int
    I_list_group_simple.argtypes = [POINTER(struct_Ref), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 61
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_subgroup'):
    I_list_subgroup = _libs['grass_I.6.4.2RC2'].I_list_subgroup
    I_list_subgroup.restype = c_int
    I_list_subgroup.argtypes = [String, String, POINTER(struct_Ref), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 62
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_subgroup_simple'):
    I_list_subgroup_simple = _libs['grass_I.6.4.2RC2'].I_list_subgroup_simple
    I_list_subgroup_simple.restype = c_int
    I_list_subgroup_simple.argtypes = [POINTER(struct_Ref), POINTER(FILE)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 65
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_location_info'):
    I_location_info = _libs['grass_I.6.4.2RC2'].I_location_info
    I_location_info.restype = c_int
    I_location_info.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 68
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_groups'):
    I_list_groups = _libs['grass_I.6.4.2RC2'].I_list_groups
    I_list_groups.restype = c_int
    I_list_groups.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 69
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_list_subgroups'):
    I_list_subgroups = _libs['grass_I.6.4.2RC2'].I_list_subgroups
    I_list_subgroups.restype = c_int
    I_list_subgroups.argtypes = [String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 72
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_new_control_point'):
    I_new_control_point = _libs['grass_I.6.4.2RC2'].I_new_control_point
    I_new_control_point.restype = c_int
    I_new_control_point.argtypes = [POINTER(struct_Control_Points), c_double, c_double, c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 74
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_control_points'):
    I_get_control_points = _libs['grass_I.6.4.2RC2'].I_get_control_points
    I_get_control_points.restype = c_int
    I_get_control_points.argtypes = [String, POINTER(struct_Control_Points)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 75
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_control_points'):
    I_put_control_points = _libs['grass_I.6.4.2RC2'].I_put_control_points
    I_put_control_points.restype = c_int
    I_put_control_points.argtypes = [String, POINTER(struct_Control_Points)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 78
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_group_ref_new'):
    I_fopen_group_ref_new = _libs['grass_I.6.4.2RC2'].I_fopen_group_ref_new
    I_fopen_group_ref_new.restype = POINTER(FILE)
    I_fopen_group_ref_new.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 79
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_group_ref_old'):
    I_fopen_group_ref_old = _libs['grass_I.6.4.2RC2'].I_fopen_group_ref_old
    I_fopen_group_ref_old.restype = POINTER(FILE)
    I_fopen_group_ref_old.argtypes = [String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 80
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_subgroup_ref_new'):
    I_fopen_subgroup_ref_new = _libs['grass_I.6.4.2RC2'].I_fopen_subgroup_ref_new
    I_fopen_subgroup_ref_new.restype = POINTER(FILE)
    I_fopen_subgroup_ref_new.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 81
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_subgroup_ref_old'):
    I_fopen_subgroup_ref_old = _libs['grass_I.6.4.2RC2'].I_fopen_subgroup_ref_old
    I_fopen_subgroup_ref_old.restype = POINTER(FILE)
    I_fopen_subgroup_ref_old.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 84
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_init_signatures'):
    I_init_signatures = _libs['grass_I.6.4.2RC2'].I_init_signatures
    I_init_signatures.restype = c_int
    I_init_signatures.argtypes = [POINTER(struct_Signature), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 85
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_new_signature'):
    I_new_signature = _libs['grass_I.6.4.2RC2'].I_new_signature
    I_new_signature.restype = c_int
    I_new_signature.argtypes = [POINTER(struct_Signature)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 86
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_free_signatures'):
    I_free_signatures = _libs['grass_I.6.4.2RC2'].I_free_signatures
    I_free_signatures.restype = c_int
    I_free_signatures.argtypes = [POINTER(struct_Signature)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 87
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_read_one_signature'):
    I_read_one_signature = _libs['grass_I.6.4.2RC2'].I_read_one_signature
    I_read_one_signature.restype = c_int
    I_read_one_signature.argtypes = [POINTER(FILE), POINTER(struct_Signature)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 88
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_read_signatures'):
    I_read_signatures = _libs['grass_I.6.4.2RC2'].I_read_signatures
    I_read_signatures.restype = c_int
    I_read_signatures.argtypes = [POINTER(FILE), POINTER(struct_Signature)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 89
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_write_signatures'):
    I_write_signatures = _libs['grass_I.6.4.2RC2'].I_write_signatures
    I_write_signatures.restype = c_int
    I_write_signatures.argtypes = [POINTER(FILE), POINTER(struct_Signature)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 92
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_signature_file_new'):
    I_fopen_signature_file_new = _libs['grass_I.6.4.2RC2'].I_fopen_signature_file_new
    I_fopen_signature_file_new.restype = POINTER(FILE)
    I_fopen_signature_file_new.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 93
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_signature_file_old'):
    I_fopen_signature_file_old = _libs['grass_I.6.4.2RC2'].I_fopen_signature_file_old
    I_fopen_signature_file_old.restype = POINTER(FILE)
    I_fopen_signature_file_old.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 96
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_SigSetNClasses'):
    I_SigSetNClasses = _libs['grass_I.6.4.2RC2'].I_SigSetNClasses
    I_SigSetNClasses.restype = c_int
    I_SigSetNClasses.argtypes = [POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 97
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_AllocClassData'):
    I_AllocClassData = _libs['grass_I.6.4.2RC2'].I_AllocClassData
    I_AllocClassData.restype = POINTER(struct_ClassData)
    I_AllocClassData.argtypes = [POINTER(struct_SigSet), POINTER(struct_ClassSig), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 98
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_InitSigSet'):
    I_InitSigSet = _libs['grass_I.6.4.2RC2'].I_InitSigSet
    I_InitSigSet.restype = c_int
    I_InitSigSet.argtypes = [POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 99
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_SigSetNBands'):
    I_SigSetNBands = _libs['grass_I.6.4.2RC2'].I_SigSetNBands
    I_SigSetNBands.restype = c_int
    I_SigSetNBands.argtypes = [POINTER(struct_SigSet), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 100
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_NewClassSig'):
    I_NewClassSig = _libs['grass_I.6.4.2RC2'].I_NewClassSig
    I_NewClassSig.restype = POINTER(struct_ClassSig)
    I_NewClassSig.argtypes = [POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 101
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_NewSubSig'):
    I_NewSubSig = _libs['grass_I.6.4.2RC2'].I_NewSubSig
    I_NewSubSig.restype = POINTER(struct_SubSig)
    I_NewSubSig.argtypes = [POINTER(struct_SigSet), POINTER(struct_ClassSig)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 102
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_ReadSigSet'):
    I_ReadSigSet = _libs['grass_I.6.4.2RC2'].I_ReadSigSet
    I_ReadSigSet.restype = c_int
    I_ReadSigSet.argtypes = [POINTER(FILE), POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 103
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_SetSigTitle'):
    I_SetSigTitle = _libs['grass_I.6.4.2RC2'].I_SetSigTitle
    I_SetSigTitle.restype = c_int
    I_SetSigTitle.argtypes = [POINTER(struct_SigSet), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 104
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_GetSigTitle'):
    I_GetSigTitle = _libs['grass_I.6.4.2RC2'].I_GetSigTitle
    I_GetSigTitle.restype = ReturnString
    I_GetSigTitle.argtypes = [POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 105
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_SetClassTitle'):
    I_SetClassTitle = _libs['grass_I.6.4.2RC2'].I_SetClassTitle
    I_SetClassTitle.restype = c_int
    I_SetClassTitle.argtypes = [POINTER(struct_ClassSig), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 106
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_GetClassTitle'):
    I_GetClassTitle = _libs['grass_I.6.4.2RC2'].I_GetClassTitle
    I_GetClassTitle.restype = ReturnString
    I_GetClassTitle.argtypes = [POINTER(struct_ClassSig)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 107
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_WriteSigSet'):
    I_WriteSigSet = _libs['grass_I.6.4.2RC2'].I_WriteSigSet
    I_WriteSigSet.restype = c_int
    I_WriteSigSet.argtypes = [POINTER(FILE), POINTER(struct_SigSet)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 110
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_sigset_file_new'):
    I_fopen_sigset_file_new = _libs['grass_I.6.4.2RC2'].I_fopen_sigset_file_new
    I_fopen_sigset_file_new.restype = POINTER(FILE)
    I_fopen_sigset_file_new.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 111
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_fopen_sigset_file_old'):
    I_fopen_sigset_file_old = _libs['grass_I.6.4.2RC2'].I_fopen_sigset_file_old
    I_fopen_sigset_file_old.restype = POINTER(FILE)
    I_fopen_sigset_file_old.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 114
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_target'):
    I_get_target = _libs['grass_I.6.4.2RC2'].I_get_target
    I_get_target.restype = c_int
    I_get_target.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 115
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_target'):
    I_put_target = _libs['grass_I.6.4.2RC2'].I_put_target
    I_put_target.restype = c_int
    I_put_target.argtypes = [String, String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 118
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_get_group_title'):
    I_get_group_title = _libs['grass_I.6.4.2RC2'].I_get_group_title
    I_get_group_title.restype = c_int
    I_get_group_title.argtypes = [String, String, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 119
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_put_group_title'):
    I_put_group_title = _libs['grass_I.6.4.2RC2'].I_put_group_title
    I_put_group_title.restype = c_int
    I_put_group_title.argtypes = [String, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 122
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_variance'):
    I_variance = _libs['grass_I.6.4.2RC2'].I_variance
    I_variance.restype = c_double
    I_variance.argtypes = [c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/imagedefs.h: 123
if hasattr(_libs['grass_I.6.4.2RC2'], 'I_stddev'):
    I_stddev = _libs['grass_I.6.4.2RC2'].I_stddev
    I_stddev.restype = c_double
    I_stddev.argtypes = [c_double, c_double, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 75
try:
    GNAME_MAX = 256
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 7
try:
    INAME_LEN = GNAME_MAX
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 105
try:
    SIGNATURE_TYPE_MIXED = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 106
try:
    GROUPFILE = 'CURGROUP'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 106
try:
    SUBGROUPFILE = 'CURSUBGROUP'
except:
    pass

Ref_Color = struct_Ref_Color # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 9

Ref_Files = struct_Ref_Files # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 19

Ref = struct_Ref # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 25

Tape_Info = struct_Tape_Info # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 32

Control_Points = struct_Control_Points # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 39

One_Sig = struct_One_Sig # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 49

Signature = struct_Signature # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 60

SubSig = struct_SubSig # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 68

ClassData = struct_ClassData # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 79

ClassSig = struct_ClassSig # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 87

SigSet = struct_SigSet # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\imagery.h: 98

# No inserted files

