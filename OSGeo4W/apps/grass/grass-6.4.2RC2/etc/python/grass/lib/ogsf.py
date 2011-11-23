'''Wrapper for ogsf_proto.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_ogsf.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/ogsf_proto.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h -o ogsf.py

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

_libs["grass_ogsf.6.4.2RC2"] = load_library("grass_ogsf.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/linkm.h: 12
class struct_link_head(Structure):
    pass

struct_link_head.__slots__ = [
    'ptr_array',
    'max_ptr',
    'alloced',
    'chunk_size',
    'unit_size',
    'Unused',
    'exit_flag',
]
struct_link_head._fields_ = [
    ('ptr_array', POINTER(POINTER(c_char))),
    ('max_ptr', c_int),
    ('alloced', c_int),
    ('chunk_size', c_int),
    ('unit_size', c_int),
    ('Unused', String),
    ('exit_flag', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/bitmap.h: 17
class struct_BM(Structure):
    pass

struct_BM.__slots__ = [
    'rows',
    'cols',
    'bytes',
    'data',
    'sparse',
    'token',
]
struct_BM._fields_ = [
    ('rows', c_int),
    ('cols', c_int),
    ('bytes', c_int),
    ('data', POINTER(c_ubyte)),
    ('sparse', c_int),
    ('token', POINTER(struct_link_head)),
]

GLint = c_int # c:/OSGeo4W/include/GL/gl.h: 118

GLuint = c_uint # c:/OSGeo4W/include/GL/gl.h: 121

Point4 = c_float * 4 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 81

Point3 = c_float * 3 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 82

Point2 = c_float * 2 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 83

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 95
class struct_anon_8(Structure):
    pass

struct_anon_8.__slots__ = [
    'fb',
    'ib',
    'sb',
    'cb',
    'bm',
    'nm',
    'tfunc',
    'k',
]
struct_anon_8._fields_ = [
    ('fb', POINTER(c_float)),
    ('ib', POINTER(c_int)),
    ('sb', POINTER(c_short)),
    ('cb', POINTER(c_ubyte)),
    ('bm', POINTER(struct_BM)),
    ('nm', POINTER(struct_BM)),
    ('tfunc', CFUNCTYPE(UNCHECKED(c_float), c_float, c_int)),
    ('k', c_float),
]

typbuff = struct_anon_8 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 95

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 102
class struct_anon_9(Structure):
    pass

struct_anon_9.__slots__ = [
    'n_elem',
    'index',
    'value',
]
struct_anon_9._fields_ = [
    ('n_elem', c_int),
    ('index', String),
    ('value', POINTER(c_int)),
]

table256 = struct_anon_9 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 102

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 110
class struct_anon_10(Structure):
    pass

struct_anon_10.__slots__ = [
    'offset',
    'mult',
    'use_lookup',
    'lookup',
]
struct_anon_10._fields_ = [
    ('offset', c_float),
    ('mult', c_float),
    ('use_lookup', c_int),
    ('lookup', table256),
]

transform = struct_anon_10 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 110

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 123
class struct_anon_11(Structure):
    pass

struct_anon_11.__slots__ = [
    'data_id',
    'dims',
    'ndims',
    'numbytes',
    'unique_name',
    'databuff',
    'changed',
    'need_reload',
]
struct_anon_11._fields_ = [
    ('data_id', c_int),
    ('dims', c_int * 4),
    ('ndims', c_int),
    ('numbytes', c_int),
    ('unique_name', String),
    ('databuff', typbuff),
    ('changed', c_uint),
    ('need_reload', c_int),
]

dataset = struct_anon_11 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 123

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 136
class struct_anon_12(Structure):
    pass

struct_anon_12.__slots__ = [
    'att_src',
    'att_type',
    'hdata',
    'user_func',
    'constant',
    'lookup',
    'min_nz',
    'max_nz',
    'range_nz',
    'default_null',
]
struct_anon_12._fields_ = [
    ('att_src', c_uint),
    ('att_type', c_uint),
    ('hdata', c_int),
    ('user_func', CFUNCTYPE(UNCHECKED(c_int), )),
    ('constant', c_float),
    ('lookup', POINTER(c_int)),
    ('min_nz', c_float),
    ('max_nz', c_float),
    ('range_nz', c_float),
    ('default_null', c_float),
]

gsurf_att = struct_anon_12 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 136

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 138
class struct_g_surf(Structure):
    pass

struct_g_surf.__slots__ = [
    'gsurf_id',
    'cols',
    'rows',
    'att',
    'draw_mode',
    'wire_color',
    'ox',
    'oy',
    'xres',
    'yres',
    'z_exag',
    'x_trans',
    'y_trans',
    'z_trans',
    'xmin',
    'xmax',
    'ymin',
    'ymax',
    'zmin',
    'zmax',
    'zminmasked',
    'xrange',
    'yrange',
    'zrange',
    'zmin_nz',
    'zmax_nz',
    'zrange_nz',
    'x_mod',
    'y_mod',
    'x_modw',
    'y_modw',
    'nz_topo',
    'nz_color',
    'mask_needupdate',
    'norm_needupdate',
    'norms',
    'curmask',
    'next',
    'clientdata',
]
struct_g_surf._fields_ = [
    ('gsurf_id', c_int),
    ('cols', c_int),
    ('rows', c_int),
    ('att', gsurf_att * 7),
    ('draw_mode', c_uint),
    ('wire_color', c_long),
    ('ox', c_double),
    ('oy', c_double),
    ('xres', c_double),
    ('yres', c_double),
    ('z_exag', c_float),
    ('x_trans', c_float),
    ('y_trans', c_float),
    ('z_trans', c_float),
    ('xmin', c_float),
    ('xmax', c_float),
    ('ymin', c_float),
    ('ymax', c_float),
    ('zmin', c_float),
    ('zmax', c_float),
    ('zminmasked', c_float),
    ('xrange', c_float),
    ('yrange', c_float),
    ('zrange', c_float),
    ('zmin_nz', c_float),
    ('zmax_nz', c_float),
    ('zrange_nz', c_float),
    ('x_mod', c_int),
    ('y_mod', c_int),
    ('x_modw', c_int),
    ('y_modw', c_int),
    ('nz_topo', c_int),
    ('nz_color', c_int),
    ('mask_needupdate', c_int),
    ('norm_needupdate', c_int),
    ('norms', POINTER(c_ulong)),
    ('curmask', POINTER(struct_BM)),
    ('next', POINTER(struct_g_surf)),
    ('clientdata', POINTER(None)),
]

geosurf = struct_g_surf # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 159

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 165
class struct_g_line(Structure):
    pass

struct_g_line.__slots__ = [
    'type',
    'norm',
    'dims',
    'npts',
    'p3',
    'p2',
    'next',
]
struct_g_line._fields_ = [
    ('type', c_int),
    ('norm', c_float * 3),
    ('dims', c_int),
    ('npts', c_int),
    ('p3', POINTER(Point3)),
    ('p2', POINTER(Point2)),
    ('next', POINTER(struct_g_line)),
]

geoline = struct_g_line # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 173

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 175
class struct_g_vect(Structure):
    pass

struct_g_vect.__slots__ = [
    'gvect_id',
    'use_mem',
    'n_lines',
    'drape_surf_id',
    'flat_val',
    'n_surfs',
    'color',
    'width',
    'filename',
    'x_trans',
    'y_trans',
    'z_trans',
    'lines',
    'fastlines',
    'bgn_read',
    'end_read',
    'nxt_line',
    'next',
    'clientdata',
]
struct_g_vect._fields_ = [
    ('gvect_id', c_int),
    ('use_mem', c_int),
    ('n_lines', c_int),
    ('drape_surf_id', c_int * 12),
    ('flat_val', c_int),
    ('n_surfs', c_int),
    ('color', c_int),
    ('width', c_int),
    ('filename', String),
    ('x_trans', c_float),
    ('y_trans', c_float),
    ('z_trans', c_float),
    ('lines', POINTER(geoline)),
    ('fastlines', POINTER(geoline)),
    ('bgn_read', CFUNCTYPE(UNCHECKED(c_int), )),
    ('end_read', CFUNCTYPE(UNCHECKED(c_int), )),
    ('nxt_line', CFUNCTYPE(UNCHECKED(c_int), )),
    ('next', POINTER(struct_g_vect)),
    ('clientdata', POINTER(None)),
]

geovect = struct_g_vect # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 191

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 196
class struct_g_point(Structure):
    pass

struct_g_point.__slots__ = [
    'dims',
    'p3',
    'fattr',
    'iattr',
    'cattr',
    'cat',
    'color',
    'size',
    'marker',
    'highlight_color',
    'highlight_size',
    'highlight_marker',
    'highlight_color_value',
    'highlight_size_value',
    'highlight_marker_value',
    'next',
]
struct_g_point._fields_ = [
    ('dims', c_int),
    ('p3', Point3),
    ('fattr', c_float),
    ('iattr', c_int),
    ('cattr', String),
    ('cat', c_int),
    ('color', c_int * 8),
    ('size', c_float * 8),
    ('marker', c_int * 8),
    ('highlight_color', c_int),
    ('highlight_size', c_int),
    ('highlight_marker', c_int),
    ('highlight_color_value', c_int),
    ('highlight_size_value', c_float),
    ('highlight_marker_value', c_int),
    ('next', POINTER(struct_g_point)),
]

geopoint = struct_g_point # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 222

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 224
class struct_g_site(Structure):
    pass

struct_g_site.__slots__ = [
    'gsite_id',
    'drape_surf_id',
    'n_surfs',
    'n_sites',
    'color',
    'width',
    'marker',
    'use_z',
    'use_mem',
    'has_z',
    'has_att',
    'attr_mode',
    'use_attr',
    'filename',
    'attr_trans',
    'size',
    'x_trans',
    'y_trans',
    'z_trans',
    'points',
    'bgn_read',
    'end_read',
    'nxt_site',
    'next',
    'clientdata',
]
struct_g_site._fields_ = [
    ('gsite_id', c_int),
    ('drape_surf_id', c_int * 12),
    ('n_surfs', c_int),
    ('n_sites', c_int),
    ('color', c_int),
    ('width', c_int),
    ('marker', c_int),
    ('use_z', c_int),
    ('use_mem', c_int),
    ('has_z', c_int),
    ('has_att', c_int),
    ('attr_mode', c_int),
    ('use_attr', c_int * 8),
    ('filename', String),
    ('attr_trans', transform),
    ('size', c_float),
    ('x_trans', c_float),
    ('y_trans', c_float),
    ('z_trans', c_float),
    ('points', POINTER(geopoint)),
    ('bgn_read', CFUNCTYPE(UNCHECKED(c_int), )),
    ('end_read', CFUNCTYPE(UNCHECKED(c_int), )),
    ('nxt_site', CFUNCTYPE(UNCHECKED(c_int), )),
    ('next', POINTER(struct_g_site)),
    ('clientdata', POINTER(None)),
]

geosite = struct_g_site # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 244

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 261
class struct_anon_13(Structure):
    pass

struct_anon_13.__slots__ = [
    'data_id',
    'file_type',
    'count',
    'file_name',
    'data_type',
    'map',
    'min',
    'max',
    'status',
    'mode',
    'buff',
]
struct_anon_13._fields_ = [
    ('data_id', c_int),
    ('file_type', c_uint),
    ('count', c_uint),
    ('file_name', String),
    ('data_type', c_uint),
    ('map', POINTER(None)),
    ('min', c_double),
    ('max', c_double),
    ('status', c_uint),
    ('mode', c_uint),
    ('buff', POINTER(None)),
]

geovol_file = struct_anon_13 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 261

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 273
class struct_anon_14(Structure):
    pass

struct_anon_14.__slots__ = [
    'att_src',
    'hfile',
    'user_func',
    'constant',
    'att_data',
    'changed',
]
struct_anon_14._fields_ = [
    ('att_src', c_uint),
    ('hfile', c_int),
    ('user_func', CFUNCTYPE(UNCHECKED(c_int), )),
    ('constant', c_float),
    ('att_data', POINTER(None)),
    ('changed', c_int),
]

geovol_isosurf_att = struct_anon_14 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 273

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 282
class struct_anon_15(Structure):
    pass

struct_anon_15.__slots__ = [
    'inout_mode',
    'att',
    'data_desc',
    'data',
]
struct_anon_15._fields_ = [
    ('inout_mode', c_int),
    ('att', geovol_isosurf_att * 7),
    ('data_desc', c_int),
    ('data', POINTER(c_ubyte)),
]

geovol_isosurf = struct_anon_15 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 282

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 292
class struct_anon_16(Structure):
    pass

struct_anon_16.__slots__ = [
    'dir',
    'x1',
    'x2',
    'y1',
    'y2',
    'z1',
    'z2',
    'data',
    'changed',
    'mode',
    'transp',
]
struct_anon_16._fields_ = [
    ('dir', c_int),
    ('x1', c_float),
    ('x2', c_float),
    ('y1', c_float),
    ('y2', c_float),
    ('z1', c_float),
    ('z2', c_float),
    ('data', POINTER(c_ubyte)),
    ('changed', c_int),
    ('mode', c_int),
    ('transp', c_int),
]

geovol_slice = struct_anon_16 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 292

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 294
class struct_g_vol(Structure):
    pass

struct_g_vol.__slots__ = [
    'gvol_id',
    'next',
    'hfile',
    'cols',
    'rows',
    'depths',
    'ox',
    'oy',
    'oz',
    'xres',
    'yres',
    'zres',
    'xmin',
    'xmax',
    'ymin',
    'ymax',
    'zmin',
    'zmax',
    'xrange',
    'yrange',
    'zrange',
    'x_trans',
    'y_trans',
    'z_trans',
    'n_isosurfs',
    'isosurf',
    'isosurf_x_mod',
    'isosurf_y_mod',
    'isosurf_z_mod',
    'isosurf_draw_mode',
    'n_slices',
    'slice',
    'slice_x_mod',
    'slice_y_mod',
    'slice_z_mod',
    'slice_draw_mode',
    'clientdata',
]
struct_g_vol._fields_ = [
    ('gvol_id', c_int),
    ('next', POINTER(struct_g_vol)),
    ('hfile', c_int),
    ('cols', c_int),
    ('rows', c_int),
    ('depths', c_int),
    ('ox', c_double),
    ('oy', c_double),
    ('oz', c_double),
    ('xres', c_double),
    ('yres', c_double),
    ('zres', c_double),
    ('xmin', c_double),
    ('xmax', c_double),
    ('ymin', c_double),
    ('ymax', c_double),
    ('zmin', c_double),
    ('zmax', c_double),
    ('xrange', c_double),
    ('yrange', c_double),
    ('zrange', c_double),
    ('x_trans', c_float),
    ('y_trans', c_float),
    ('z_trans', c_float),
    ('n_isosurfs', c_int),
    ('isosurf', POINTER(geovol_isosurf) * 12),
    ('isosurf_x_mod', c_int),
    ('isosurf_y_mod', c_int),
    ('isosurf_z_mod', c_int),
    ('isosurf_draw_mode', c_uint),
    ('n_slices', c_int),
    ('slice', POINTER(geovol_slice) * 12),
    ('slice_x_mod', c_int),
    ('slice_y_mod', c_int),
    ('slice_z_mod', c_int),
    ('slice_draw_mode', c_uint),
    ('clientdata', POINTER(None)),
]

geovol = struct_g_vol # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 318

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 320
class struct_lightdefs(Structure):
    pass

struct_lightdefs.__slots__ = [
    'position',
    'color',
    'ambient',
    'emission',
    'shine',
]
struct_lightdefs._fields_ = [
    ('position', c_float * 4),
    ('color', c_float * 3),
    ('ambient', c_float * 3),
    ('emission', c_float * 3),
    ('shine', c_float),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 339
class struct_anon_17(Structure):
    pass

struct_anon_17.__slots__ = [
    'coord_sys',
    'view_proj',
    'infocus',
    'from_to',
    'twist',
    'fov',
    'incl',
    'look',
    'real_to',
    'vert_exag',
    'scale',
    'lights',
]
struct_anon_17._fields_ = [
    ('coord_sys', c_int),
    ('view_proj', c_int),
    ('infocus', c_int),
    ('from_to', (c_float * 4) * 2),
    ('twist', c_int),
    ('fov', c_int),
    ('incl', c_int),
    ('look', c_int),
    ('real_to', c_float * 4),
    ('vert_exag', c_float),
    ('scale', c_float),
    ('lights', struct_lightdefs * 3),
]

geoview = struct_anon_17 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 339

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 346
class struct_anon_18(Structure):
    pass

struct_anon_18.__slots__ = [
    'nearclip',
    'farclip',
    'aspect',
    'left',
    'right',
    'bottom',
    'top',
    'bgcol',
]
struct_anon_18._fields_ = [
    ('nearclip', c_float),
    ('farclip', c_float),
    ('aspect', c_float),
    ('left', c_short),
    ('right', c_short),
    ('bottom', c_short),
    ('top', c_short),
    ('bgcol', c_int),
]

geodisplay = struct_anon_18 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 346

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 348
for _lib in _libs.values():
    try:
        Cxl_func = (POINTER(CFUNCTYPE(UNCHECKED(None), ))).in_dll(_lib, 'Cxl_func')
        break
    except:
        pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 349
for _lib in _libs.values():
    try:
        Swap_func = (POINTER(CFUNCTYPE(UNCHECKED(None), ))).in_dll(_lib, 'Swap_func')
        break
    except:
        pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 26
class struct_view_node(Structure):
    pass

struct_view_node.__slots__ = [
    'fields',
]
struct_view_node._fields_ = [
    ('fields', c_float * 8),
]

Viewnode = struct_view_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 26

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 28
class struct_key_node(Structure):
    pass

struct_key_node.__slots__ = [
    'pos',
    'fields',
    'look_ahead',
    'fieldmask',
    'next',
    'prior',
]
struct_key_node._fields_ = [
    ('pos', c_float),
    ('fields', c_float * 8),
    ('look_ahead', c_int),
    ('fieldmask', c_ulong),
    ('next', POINTER(struct_key_node)),
    ('prior', POINTER(struct_key_node)),
]

Keylist = struct_key_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 34

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 37
for _lib in _libs.values():
    if hasattr(_lib, 'GK_set_interpmode'):
        GK_set_interpmode = _lib.GK_set_interpmode
        GK_set_interpmode.restype = c_int
        GK_set_interpmode.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 38
for _lib in _libs.values():
    if hasattr(_lib, 'GK_set_tension'):
        GK_set_tension = _lib.GK_set_tension
        GK_set_tension.restype = None
        GK_set_tension.argtypes = [c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 39
for _lib in _libs.values():
    if hasattr(_lib, 'GK_showtension_start'):
        GK_showtension_start = _lib.GK_showtension_start
        GK_showtension_start.restype = None
        GK_showtension_start.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 40
for _lib in _libs.values():
    if hasattr(_lib, 'GK_showtension_stop'):
        GK_showtension_stop = _lib.GK_showtension_stop
        GK_showtension_stop.restype = None
        GK_showtension_stop.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 41
for _lib in _libs.values():
    if hasattr(_lib, 'GK_update_tension'):
        GK_update_tension = _lib.GK_update_tension
        GK_update_tension.restype = None
        GK_update_tension.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 42
for _lib in _libs.values():
    if hasattr(_lib, 'GK_update_frames'):
        GK_update_frames = _lib.GK_update_frames
        GK_update_frames.restype = None
        GK_update_frames.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 43
for _lib in _libs.values():
    if hasattr(_lib, 'GK_set_numsteps'):
        GK_set_numsteps = _lib.GK_set_numsteps
        GK_set_numsteps.restype = None
        GK_set_numsteps.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 44
for _lib in _libs.values():
    if hasattr(_lib, 'GK_clear_keys'):
        GK_clear_keys = _lib.GK_clear_keys
        GK_clear_keys.restype = None
        GK_clear_keys.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 45
for _lib in _libs.values():
    if hasattr(_lib, 'GK_print_keys'):
        GK_print_keys = _lib.GK_print_keys
        GK_print_keys.restype = None
        GK_print_keys.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 46
for _lib in _libs.values():
    if hasattr(_lib, 'GK_move_key'):
        GK_move_key = _lib.GK_move_key
        GK_move_key.restype = c_int
        GK_move_key.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 47
for _lib in _libs.values():
    if hasattr(_lib, 'GK_delete_key'):
        GK_delete_key = _lib.GK_delete_key
        GK_delete_key.restype = c_int
        GK_delete_key.argtypes = [c_float, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 48
for _lib in _libs.values():
    if hasattr(_lib, 'GK_add_key'):
        GK_add_key = _lib.GK_add_key
        GK_add_key.restype = c_int
        GK_add_key.argtypes = [c_float, c_ulong, c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 49
for _lib in _libs.values():
    if hasattr(_lib, 'GK_do_framestep'):
        GK_do_framestep = _lib.GK_do_framestep
        GK_do_framestep.restype = None
        GK_do_framestep.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 50
for _lib in _libs.values():
    if hasattr(_lib, 'GK_show_path'):
        GK_show_path = _lib.GK_show_path
        GK_show_path.restype = None
        GK_show_path.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 51
for _lib in _libs.values():
    if hasattr(_lib, 'GK_show_vect'):
        GK_show_vect = _lib.GK_show_vect
        GK_show_vect.restype = None
        GK_show_vect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 52
for _lib in _libs.values():
    if hasattr(_lib, 'GK_show_site'):
        GK_show_site = _lib.GK_show_site
        GK_show_site.restype = None
        GK_show_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 53
for _lib in _libs.values():
    if hasattr(_lib, 'GK_show_vol'):
        GK_show_vol = _lib.GK_show_vol
        GK_show_vol.restype = None
        GK_show_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 54
for _lib in _libs.values():
    if hasattr(_lib, 'GK_show_list'):
        GK_show_list = _lib.GK_show_list
        GK_show_list.restype = None
        GK_show_list.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 57
for _lib in _libs.values():
    if hasattr(_lib, 'GP_site_exists'):
        GP_site_exists = _lib.GP_site_exists
        GP_site_exists.restype = c_int
        GP_site_exists.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 58
for _lib in _libs.values():
    if hasattr(_lib, 'GP_new_site'):
        GP_new_site = _lib.GP_new_site
        GP_new_site.restype = c_int
        GP_new_site.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 59
for _lib in _libs.values():
    if hasattr(_lib, 'GP_num_sites'):
        GP_num_sites = _lib.GP_num_sites
        GP_num_sites.restype = c_int
        GP_num_sites.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 60
for _lib in _libs.values():
    if hasattr(_lib, 'GP_get_site_list'):
        GP_get_site_list = _lib.GP_get_site_list
        GP_get_site_list.restype = POINTER(c_int)
        GP_get_site_list.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 61
for _lib in _libs.values():
    if hasattr(_lib, 'GP_delete_site'):
        GP_delete_site = _lib.GP_delete_site
        GP_delete_site.restype = c_int
        GP_delete_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 62
for _lib in _libs.values():
    if hasattr(_lib, 'GP_load_site'):
        GP_load_site = _lib.GP_load_site
        GP_load_site.restype = c_int
        GP_load_site.argtypes = [c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 63
for _lib in _libs.values():
    if hasattr(_lib, 'GP_get_sitename'):
        GP_get_sitename = _lib.GP_get_sitename
        GP_get_sitename.restype = c_int
        GP_get_sitename.argtypes = [c_int, POINTER(POINTER(c_char))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 64
for _lib in _libs.values():
    if hasattr(_lib, 'GP_get_sitemode'):
        GP_get_sitemode = _lib.GP_get_sitemode
        GP_get_sitemode.restype = c_int
        GP_get_sitemode.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 65
for _lib in _libs.values():
    if hasattr(_lib, 'GP_set_sitemode'):
        GP_set_sitemode = _lib.GP_set_sitemode
        GP_set_sitemode.restype = c_int
        GP_set_sitemode.argtypes = [c_int, c_int, c_int, c_int, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 66
for _lib in _libs.values():
    if hasattr(_lib, 'GP_attmode_color'):
        GP_attmode_color = _lib.GP_attmode_color
        GP_attmode_color.restype = c_int
        GP_attmode_color.argtypes = [c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 67
for _lib in _libs.values():
    if hasattr(_lib, 'GP_attmode_none'):
        GP_attmode_none = _lib.GP_attmode_none
        GP_attmode_none.restype = c_int
        GP_attmode_none.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 68
for _lib in _libs.values():
    if hasattr(_lib, 'GP_set_zmode'):
        GP_set_zmode = _lib.GP_set_zmode
        GP_set_zmode.restype = c_int
        GP_set_zmode.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 69
for _lib in _libs.values():
    if hasattr(_lib, 'GP_get_zmode'):
        GP_get_zmode = _lib.GP_get_zmode
        GP_get_zmode.restype = c_int
        GP_get_zmode.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 70
for _lib in _libs.values():
    if hasattr(_lib, 'GP_set_trans'):
        GP_set_trans = _lib.GP_set_trans
        GP_set_trans.restype = None
        GP_set_trans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 71
for _lib in _libs.values():
    if hasattr(_lib, 'GP_get_trans'):
        GP_get_trans = _lib.GP_get_trans
        GP_get_trans.restype = None
        GP_get_trans.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 72
for _lib in _libs.values():
    if hasattr(_lib, 'GP_select_surf'):
        GP_select_surf = _lib.GP_select_surf
        GP_select_surf.restype = c_int
        GP_select_surf.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 73
for _lib in _libs.values():
    if hasattr(_lib, 'GP_unselect_surf'):
        GP_unselect_surf = _lib.GP_unselect_surf
        GP_unselect_surf.restype = c_int
        GP_unselect_surf.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 74
for _lib in _libs.values():
    if hasattr(_lib, 'GP_surf_is_selected'):
        GP_surf_is_selected = _lib.GP_surf_is_selected
        GP_surf_is_selected.restype = c_int
        GP_surf_is_selected.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 75
for _lib in _libs.values():
    if hasattr(_lib, 'GP_draw_site'):
        GP_draw_site = _lib.GP_draw_site
        GP_draw_site.restype = None
        GP_draw_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 76
for _lib in _libs.values():
    if hasattr(_lib, 'GP_alldraw_site'):
        GP_alldraw_site = _lib.GP_alldraw_site
        GP_alldraw_site.restype = None
        GP_alldraw_site.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 77
for _lib in _libs.values():
    if hasattr(_lib, 'GP_Set_ClientData'):
        GP_Set_ClientData = _lib.GP_Set_ClientData
        GP_Set_ClientData.restype = c_int
        GP_Set_ClientData.argtypes = [c_int, POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 78
for _lib in _libs.values():
    if hasattr(_lib, 'GP_Get_ClientData'):
        GP_Get_ClientData = _lib.GP_Get_ClientData
        GP_Get_ClientData.restype = POINTER(None)
        GP_Get_ClientData.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 81
for _lib in _libs.values():
    if hasattr(_lib, 'void_func'):
        void_func = _lib.void_func
        void_func.restype = None
        void_func.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 82
for _lib in _libs.values():
    if hasattr(_lib, 'GS_libinit'):
        GS_libinit = _lib.GS_libinit
        GS_libinit.restype = None
        GS_libinit.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 83
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_longdim'):
        GS_get_longdim = _lib.GS_get_longdim
        GS_get_longdim.restype = c_int
        GS_get_longdim.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 84
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_region'):
        GS_get_region = _lib.GS_get_region
        GS_get_region.restype = c_int
        GS_get_region.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 85
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_att_defaults'):
        GS_set_att_defaults = _lib.GS_set_att_defaults
        GS_set_att_defaults.restype = None
        GS_set_att_defaults.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 86
for _lib in _libs.values():
    if hasattr(_lib, 'GS_surf_exists'):
        GS_surf_exists = _lib.GS_surf_exists
        GS_surf_exists.restype = c_int
        GS_surf_exists.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 87
for _lib in _libs.values():
    if hasattr(_lib, 'GS_new_surface'):
        GS_new_surface = _lib.GS_new_surface
        GS_new_surface.restype = c_int
        GS_new_surface.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 88
for _lib in _libs.values():
    if hasattr(_lib, 'GS_new_light'):
        GS_new_light = _lib.GS_new_light
        GS_new_light.restype = c_int
        GS_new_light.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 89
for _lib in _libs.values():
    if hasattr(_lib, 'GS_setlight_position'):
        GS_setlight_position = _lib.GS_setlight_position
        GS_setlight_position.restype = None
        GS_setlight_position.argtypes = [c_int, c_float, c_float, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 90
for _lib in _libs.values():
    if hasattr(_lib, 'GS_setlight_color'):
        GS_setlight_color = _lib.GS_setlight_color
        GS_setlight_color.restype = None
        GS_setlight_color.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 91
for _lib in _libs.values():
    if hasattr(_lib, 'GS_setlight_ambient'):
        GS_setlight_ambient = _lib.GS_setlight_ambient
        GS_setlight_ambient.restype = None
        GS_setlight_ambient.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 92
for _lib in _libs.values():
    if hasattr(_lib, 'GS_lights_off'):
        GS_lights_off = _lib.GS_lights_off
        GS_lights_off.restype = None
        GS_lights_off.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 93
for _lib in _libs.values():
    if hasattr(_lib, 'GS_lights_on'):
        GS_lights_on = _lib.GS_lights_on
        GS_lights_on.restype = None
        GS_lights_on.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 94
for _lib in _libs.values():
    if hasattr(_lib, 'GS_switchlight'):
        GS_switchlight = _lib.GS_switchlight
        GS_switchlight.restype = None
        GS_switchlight.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 95
for _lib in _libs.values():
    if hasattr(_lib, 'GS_transp_is_set'):
        GS_transp_is_set = _lib.GS_transp_is_set
        GS_transp_is_set.restype = c_int
        GS_transp_is_set.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 96
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_modelposition1'):
        GS_get_modelposition1 = _lib.GS_get_modelposition1
        GS_get_modelposition1.restype = None
        GS_get_modelposition1.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 97
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_modelposition'):
        GS_get_modelposition = _lib.GS_get_modelposition
        GS_get_modelposition.restype = None
        GS_get_modelposition.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 98
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_X'):
        GS_draw_X = _lib.GS_draw_X
        GS_draw_X.restype = None
        GS_draw_X.argtypes = [c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 99
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_Narrow'):
        GS_set_Narrow = _lib.GS_set_Narrow
        GS_set_Narrow.restype = None
        GS_set_Narrow.argtypes = [POINTER(c_int), c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 100
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_line_onsurf'):
        GS_draw_line_onsurf = _lib.GS_draw_line_onsurf
        GS_draw_line_onsurf.restype = None
        GS_draw_line_onsurf.argtypes = [c_int, c_float, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 101
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_nline_onsurf'):
        GS_draw_nline_onsurf = _lib.GS_draw_nline_onsurf
        GS_draw_nline_onsurf.restype = c_int
        GS_draw_nline_onsurf.argtypes = [c_int, c_float, c_float, c_float, c_float, POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 102
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_flowline_at_xy'):
        GS_draw_flowline_at_xy = _lib.GS_draw_flowline_at_xy
        GS_draw_flowline_at_xy.restype = None
        GS_draw_flowline_at_xy.argtypes = [c_int, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 103
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_lighting_model1'):
        GS_draw_lighting_model1 = _lib.GS_draw_lighting_model1
        GS_draw_lighting_model1.restype = None
        GS_draw_lighting_model1.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 104
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_lighting_model'):
        GS_draw_lighting_model = _lib.GS_draw_lighting_model
        GS_draw_lighting_model.restype = None
        GS_draw_lighting_model.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 105
for _lib in _libs.values():
    if hasattr(_lib, 'GS_update_curmask'):
        GS_update_curmask = _lib.GS_update_curmask
        GS_update_curmask.restype = c_int
        GS_update_curmask.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 106
for _lib in _libs.values():
    if hasattr(_lib, 'GS_is_masked'):
        GS_is_masked = _lib.GS_is_masked
        GS_is_masked.restype = c_int
        GS_is_masked.argtypes = [c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 107
for _lib in _libs.values():
    if hasattr(_lib, 'GS_unset_SDsurf'):
        GS_unset_SDsurf = _lib.GS_unset_SDsurf
        GS_unset_SDsurf.restype = None
        GS_unset_SDsurf.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 108
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_SDsurf'):
        GS_set_SDsurf = _lib.GS_set_SDsurf
        GS_set_SDsurf.restype = c_int
        GS_set_SDsurf.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 109
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_SDscale'):
        GS_set_SDscale = _lib.GS_set_SDscale
        GS_set_SDscale.restype = c_int
        GS_set_SDscale.argtypes = [c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 110
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_SDsurf'):
        GS_get_SDsurf = _lib.GS_get_SDsurf
        GS_get_SDsurf.restype = c_int
        GS_get_SDsurf.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 111
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_SDscale'):
        GS_get_SDscale = _lib.GS_get_SDscale
        GS_get_SDscale.restype = c_int
        GS_get_SDscale.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 112
for _lib in _libs.values():
    if hasattr(_lib, 'GS_update_normals'):
        GS_update_normals = _lib.GS_update_normals
        GS_update_normals.restype = c_int
        GS_update_normals.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 113
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_att'):
        GS_get_att = _lib.GS_get_att
        GS_get_att.restype = c_int
        GS_get_att.argtypes = [c_int, c_int, POINTER(c_int), POINTER(c_float), String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 114
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_cat_at_xy'):
        GS_get_cat_at_xy = _lib.GS_get_cat_at_xy
        GS_get_cat_at_xy.restype = c_int
        GS_get_cat_at_xy.argtypes = [c_int, c_int, String, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 115
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_norm_at_xy'):
        GS_get_norm_at_xy = _lib.GS_get_norm_at_xy
        GS_get_norm_at_xy.restype = c_int
        GS_get_norm_at_xy.argtypes = [c_int, c_float, c_float, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 116
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_val_at_xy'):
        GS_get_val_at_xy = _lib.GS_get_val_at_xy
        GS_get_val_at_xy.restype = c_int
        GS_get_val_at_xy.argtypes = [c_int, c_int, String, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 117
for _lib in _libs.values():
    if hasattr(_lib, 'GS_unset_att'):
        GS_unset_att = _lib.GS_unset_att
        GS_unset_att.restype = c_int
        GS_unset_att.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 118
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_att_const'):
        GS_set_att_const = _lib.GS_set_att_const
        GS_set_att_const.restype = c_int
        GS_set_att_const.argtypes = [c_int, c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 119
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_maskmode'):
        GS_set_maskmode = _lib.GS_set_maskmode
        GS_set_maskmode.restype = c_int
        GS_set_maskmode.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 120
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_maskmode'):
        GS_get_maskmode = _lib.GS_get_maskmode
        GS_get_maskmode.restype = c_int
        GS_get_maskmode.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 121
for _lib in _libs.values():
    if hasattr(_lib, 'GS_Set_ClientData'):
        GS_Set_ClientData = _lib.GS_Set_ClientData
        GS_Set_ClientData.restype = c_int
        GS_Set_ClientData.argtypes = [c_int, POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 122
for _lib in _libs.values():
    if hasattr(_lib, 'GS_Get_ClientData'):
        GS_Get_ClientData = _lib.GS_Get_ClientData
        GS_Get_ClientData.restype = POINTER(None)
        GS_Get_ClientData.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 123
for _lib in _libs.values():
    if hasattr(_lib, 'GS_num_surfs'):
        GS_num_surfs = _lib.GS_num_surfs
        GS_num_surfs.restype = c_int
        GS_num_surfs.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 124
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_surf_list'):
        GS_get_surf_list = _lib.GS_get_surf_list
        GS_get_surf_list.restype = POINTER(c_int)
        GS_get_surf_list.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 125
for _lib in _libs.values():
    if hasattr(_lib, 'GS_delete_surface'):
        GS_delete_surface = _lib.GS_delete_surface
        GS_delete_surface.restype = c_int
        GS_delete_surface.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 126
for _lib in _libs.values():
    if hasattr(_lib, 'GS_load_att_map'):
        GS_load_att_map = _lib.GS_load_att_map
        GS_load_att_map.restype = c_int
        GS_load_att_map.argtypes = [c_int, String, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 127
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_surf'):
        GS_draw_surf = _lib.GS_draw_surf
        GS_draw_surf.restype = None
        GS_draw_surf.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 128
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_wire'):
        GS_draw_wire = _lib.GS_draw_wire
        GS_draw_wire.restype = None
        GS_draw_wire.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 129
for _lib in _libs.values():
    if hasattr(_lib, 'GS_alldraw_wire'):
        GS_alldraw_wire = _lib.GS_alldraw_wire
        GS_alldraw_wire.restype = None
        GS_alldraw_wire.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 130
for _lib in _libs.values():
    if hasattr(_lib, 'GS_alldraw_surf'):
        GS_alldraw_surf = _lib.GS_alldraw_surf
        GS_alldraw_surf.restype = None
        GS_alldraw_surf.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 131
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_exag'):
        GS_set_exag = _lib.GS_set_exag
        GS_set_exag.restype = None
        GS_set_exag.argtypes = [c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 132
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_global_exag'):
        GS_set_global_exag = _lib.GS_set_global_exag
        GS_set_global_exag.restype = None
        GS_set_global_exag.argtypes = [c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 133
for _lib in _libs.values():
    if hasattr(_lib, 'GS_global_exag'):
        GS_global_exag = _lib.GS_global_exag
        GS_global_exag.restype = c_float
        GS_global_exag.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 134
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_wire_color'):
        GS_set_wire_color = _lib.GS_set_wire_color
        GS_set_wire_color.restype = None
        GS_set_wire_color.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 135
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_wire_color'):
        GS_get_wire_color = _lib.GS_get_wire_color
        GS_get_wire_color.restype = c_int
        GS_get_wire_color.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 136
for _lib in _libs.values():
    if hasattr(_lib, 'GS_setall_drawmode'):
        GS_setall_drawmode = _lib.GS_setall_drawmode
        GS_setall_drawmode.restype = c_int
        GS_setall_drawmode.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 137
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_drawmode'):
        GS_set_drawmode = _lib.GS_set_drawmode
        GS_set_drawmode.restype = c_int
        GS_set_drawmode.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 138
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_drawmode'):
        GS_get_drawmode = _lib.GS_get_drawmode
        GS_get_drawmode.restype = c_int
        GS_get_drawmode.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 139
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_nozero'):
        GS_set_nozero = _lib.GS_set_nozero
        GS_set_nozero.restype = None
        GS_set_nozero.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 140
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_nozero'):
        GS_get_nozero = _lib.GS_get_nozero
        GS_get_nozero.restype = c_int
        GS_get_nozero.argtypes = [c_int, c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 141
for _lib in _libs.values():
    if hasattr(_lib, 'GS_setall_drawres'):
        GS_setall_drawres = _lib.GS_setall_drawres
        GS_setall_drawres.restype = c_int
        GS_setall_drawres.argtypes = [c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 142
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_drawres'):
        GS_set_drawres = _lib.GS_set_drawres
        GS_set_drawres.restype = c_int
        GS_set_drawres.argtypes = [c_int, c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 143
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_drawres'):
        GS_get_drawres = _lib.GS_get_drawres
        GS_get_drawres.restype = None
        GS_get_drawres.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 144
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_dims'):
        GS_get_dims = _lib.GS_get_dims
        GS_get_dims.restype = None
        GS_get_dims.argtypes = [c_int, POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 145
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_exag_guess'):
        GS_get_exag_guess = _lib.GS_get_exag_guess
        GS_get_exag_guess.restype = c_int
        GS_get_exag_guess.argtypes = [c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 146
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_zrange_nz'):
        GS_get_zrange_nz = _lib.GS_get_zrange_nz
        GS_get_zrange_nz.restype = None
        GS_get_zrange_nz.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 147
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_trans'):
        GS_set_trans = _lib.GS_set_trans
        GS_set_trans.restype = None
        GS_set_trans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 148
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_trans'):
        GS_get_trans = _lib.GS_get_trans
        GS_get_trans.restype = None
        GS_get_trans.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 149
for _lib in _libs.values():
    if hasattr(_lib, 'GS_default_draw_color'):
        GS_default_draw_color = _lib.GS_default_draw_color
        GS_default_draw_color.restype = c_uint
        GS_default_draw_color.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 150
for _lib in _libs.values():
    if hasattr(_lib, 'GS_background_color'):
        GS_background_color = _lib.GS_background_color
        GS_background_color.restype = c_uint
        GS_background_color.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 151
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_draw'):
        GS_set_draw = _lib.GS_set_draw
        GS_set_draw.restype = None
        GS_set_draw.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 152
for _lib in _libs.values():
    if hasattr(_lib, 'GS_ready_draw'):
        GS_ready_draw = _lib.GS_ready_draw
        GS_ready_draw.restype = None
        GS_ready_draw.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 153
for _lib in _libs.values():
    if hasattr(_lib, 'GS_done_draw'):
        GS_done_draw = _lib.GS_done_draw
        GS_done_draw.restype = None
        GS_done_draw.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 154
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_focus'):
        GS_set_focus = _lib.GS_set_focus
        GS_set_focus.restype = None
        GS_set_focus.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 155
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_focus'):
        GS_get_focus = _lib.GS_get_focus
        GS_get_focus.restype = c_int
        GS_get_focus.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 156
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_focus_center_map'):
        GS_set_focus_center_map = _lib.GS_set_focus_center_map
        GS_set_focus_center_map.restype = None
        GS_set_focus_center_map.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 157
for _lib in _libs.values():
    if hasattr(_lib, 'GS_moveto'):
        GS_moveto = _lib.GS_moveto
        GS_moveto.restype = None
        GS_moveto.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 158
for _lib in _libs.values():
    if hasattr(_lib, 'GS_moveto_real'):
        GS_moveto_real = _lib.GS_moveto_real
        GS_moveto_real.restype = None
        GS_moveto_real.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 159
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_focus_real'):
        GS_set_focus_real = _lib.GS_set_focus_real
        GS_set_focus_real.restype = None
        GS_set_focus_real.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 160
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_to_real'):
        GS_get_to_real = _lib.GS_get_to_real
        GS_get_to_real.restype = None
        GS_get_to_real.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 161
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_zextents'):
        GS_get_zextents = _lib.GS_get_zextents
        GS_get_zextents.restype = c_int
        GS_get_zextents.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 162
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_zrange'):
        GS_get_zrange = _lib.GS_get_zrange
        GS_get_zrange.restype = c_int
        GS_get_zrange.argtypes = [POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 163
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_from'):
        GS_get_from = _lib.GS_get_from
        GS_get_from.restype = None
        GS_get_from.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 164
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_from_real'):
        GS_get_from_real = _lib.GS_get_from_real
        GS_get_from_real.restype = None
        GS_get_from_real.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 165
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_to'):
        GS_get_to = _lib.GS_get_to
        GS_get_to.restype = None
        GS_get_to.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 166
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_viewdir'):
        GS_get_viewdir = _lib.GS_get_viewdir
        GS_get_viewdir.restype = None
        GS_get_viewdir.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 167
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_viewdir'):
        GS_set_viewdir = _lib.GS_set_viewdir
        GS_set_viewdir.restype = None
        GS_set_viewdir.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 168
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_fov'):
        GS_set_fov = _lib.GS_set_fov
        GS_set_fov.restype = None
        GS_set_fov.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 169
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_fov'):
        GS_get_fov = _lib.GS_get_fov
        GS_get_fov.restype = c_int
        GS_get_fov.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 170
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_twist'):
        GS_get_twist = _lib.GS_get_twist
        GS_get_twist.restype = c_int
        GS_get_twist.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 171
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_twist'):
        GS_set_twist = _lib.GS_set_twist
        GS_set_twist.restype = None
        GS_set_twist.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 172
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_nofocus'):
        GS_set_nofocus = _lib.GS_set_nofocus
        GS_set_nofocus.restype = None
        GS_set_nofocus.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 173
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_infocus'):
        GS_set_infocus = _lib.GS_set_infocus
        GS_set_infocus.restype = None
        GS_set_infocus.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 174
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_viewport'):
        GS_set_viewport = _lib.GS_set_viewport
        GS_set_viewport.restype = None
        GS_set_viewport.argtypes = [c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 175
for _lib in _libs.values():
    if hasattr(_lib, 'GS_look_here'):
        GS_look_here = _lib.GS_look_here
        GS_look_here.restype = c_int
        GS_look_here.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 176
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_selected_point_on_surface'):
        GS_get_selected_point_on_surface = _lib.GS_get_selected_point_on_surface
        GS_get_selected_point_on_surface.restype = c_int
        GS_get_selected_point_on_surface.argtypes = [c_int, c_int, POINTER(c_int), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 178
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_cplane_rot'):
        GS_set_cplane_rot = _lib.GS_set_cplane_rot
        GS_set_cplane_rot.restype = None
        GS_set_cplane_rot.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 179
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_cplane_trans'):
        GS_set_cplane_trans = _lib.GS_set_cplane_trans
        GS_set_cplane_trans.restype = None
        GS_set_cplane_trans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 180
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_cplane'):
        GS_draw_cplane = _lib.GS_draw_cplane
        GS_draw_cplane.restype = None
        GS_draw_cplane.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 181
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_cplane_fence'):
        GS_draw_cplane_fence = _lib.GS_draw_cplane_fence
        GS_draw_cplane_fence.restype = c_int
        GS_draw_cplane_fence.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 182
for _lib in _libs.values():
    if hasattr(_lib, 'GS_alldraw_cplane_fences'):
        GS_alldraw_cplane_fences = _lib.GS_alldraw_cplane_fences
        GS_alldraw_cplane_fences.restype = None
        GS_alldraw_cplane_fences.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 183
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_cplane'):
        GS_set_cplane = _lib.GS_set_cplane
        GS_set_cplane.restype = None
        GS_set_cplane.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 184
for _lib in _libs.values():
    if hasattr(_lib, 'GS_unset_cplane'):
        GS_unset_cplane = _lib.GS_unset_cplane
        GS_unset_cplane.restype = None
        GS_unset_cplane.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 185
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_scale'):
        GS_get_scale = _lib.GS_get_scale
        GS_get_scale.restype = None
        GS_get_scale.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 186
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_fencecolor'):
        GS_set_fencecolor = _lib.GS_set_fencecolor
        GS_set_fencecolor.restype = None
        GS_set_fencecolor.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 187
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_fencecolor'):
        GS_get_fencecolor = _lib.GS_get_fencecolor
        GS_get_fencecolor.restype = c_int
        GS_get_fencecolor.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 188
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_distance_alongsurf'):
        GS_get_distance_alongsurf = _lib.GS_get_distance_alongsurf
        GS_get_distance_alongsurf.restype = c_int
        GS_get_distance_alongsurf.argtypes = [c_int, c_float, c_float, c_float, c_float, POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 189
for _lib in _libs.values():
    if hasattr(_lib, 'GS_save_3dview'):
        GS_save_3dview = _lib.GS_save_3dview
        GS_save_3dview.restype = c_int
        GS_save_3dview.argtypes = [String, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 190
for _lib in _libs.values():
    if hasattr(_lib, 'GS_load_3dview'):
        GS_load_3dview = _lib.GS_load_3dview
        GS_load_3dview.restype = c_int
        GS_load_3dview.argtypes = [String, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 191
for _lib in _libs.values():
    if hasattr(_lib, 'GS_init_view'):
        GS_init_view = _lib.GS_init_view
        GS_init_view.restype = None
        GS_init_view.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 192
for _lib in _libs.values():
    if hasattr(_lib, 'GS_clear'):
        GS_clear = _lib.GS_clear
        GS_clear.restype = None
        GS_clear.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 193
for _lib in _libs.values():
    if hasattr(_lib, 'GS_get_aspect'):
        GS_get_aspect = _lib.GS_get_aspect
        GS_get_aspect.restype = c_double
        GS_get_aspect.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 194
for _lib in _libs.values():
    if hasattr(_lib, 'GS_has_transparency'):
        GS_has_transparency = _lib.GS_has_transparency
        GS_has_transparency.restype = c_int
        GS_has_transparency.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 195
for _lib in _libs.values():
    if hasattr(_lib, 'GS_zoom_setup'):
        GS_zoom_setup = _lib.GS_zoom_setup
        GS_zoom_setup.restype = None
        GS_zoom_setup.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 196
for _lib in _libs.values():
    if hasattr(_lib, 'GS_write_zoom'):
        GS_write_zoom = _lib.GS_write_zoom
        GS_write_zoom.restype = c_int
        GS_write_zoom.argtypes = [String, c_uint, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 197
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_all_list'):
        GS_draw_all_list = _lib.GS_draw_all_list
        GS_draw_all_list.restype = None
        GS_draw_all_list.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 198
for _lib in _libs.values():
    if hasattr(_lib, 'GS_delete_list'):
        GS_delete_list = _lib.GS_delete_list
        GS_delete_list.restype = None
        GS_delete_list.argtypes = [GLuint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 199
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_legend'):
        GS_draw_legend = _lib.GS_draw_legend
        GS_draw_legend.restype = c_int
        GS_draw_legend.argtypes = [String, GLuint, c_int, POINTER(c_int), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 200
for _lib in _libs.values():
    if hasattr(_lib, 'GS_draw_fringe'):
        GS_draw_fringe = _lib.GS_draw_fringe
        GS_draw_fringe.restype = None
        GS_draw_fringe.argtypes = [c_int, c_ulong, c_float, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 201
for _lib in _libs.values():
    if hasattr(_lib, 'GS_getlight_position'):
        GS_getlight_position = _lib.GS_getlight_position
        GS_getlight_position.restype = None
        GS_getlight_position.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 202
for _lib in _libs.values():
    if hasattr(_lib, 'GS_getlight_color'):
        GS_getlight_color = _lib.GS_getlight_color
        GS_getlight_color.restype = None
        GS_getlight_color.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 203
for _lib in _libs.values():
    if hasattr(_lib, 'GS_getlight_ambient'):
        GS_getlight_ambient = _lib.GS_getlight_ambient
        GS_getlight_ambient.restype = None
        GS_getlight_ambient.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 206
for _lib in _libs.values():
    if hasattr(_lib, 'GS_check_cancel'):
        GS_check_cancel = _lib.GS_check_cancel
        GS_check_cancel.restype = c_int
        GS_check_cancel.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 207
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_cancel'):
        GS_set_cancel = _lib.GS_set_cancel
        GS_set_cancel.restype = None
        GS_set_cancel.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 208
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_cxl_func'):
        GS_set_cxl_func = _lib.GS_set_cxl_func
        GS_set_cxl_func.restype = None
        GS_set_cxl_func.argtypes = [CFUNCTYPE(UNCHECKED(None), )]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 209
for _lib in _libs.values():
    if hasattr(_lib, 'GS_set_swap_func'):
        GS_set_swap_func = _lib.GS_set_swap_func
        GS_set_swap_func.restype = None
        GS_set_swap_func.argtypes = [CFUNCTYPE(UNCHECKED(None), )]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 212
for _lib in _libs.values():
    if hasattr(_lib, 'GS_geodistance'):
        GS_geodistance = _lib.GS_geodistance
        GS_geodistance.restype = c_double
        GS_geodistance.argtypes = [POINTER(c_double), POINTER(c_double), String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 213
for _lib in _libs.values():
    if hasattr(_lib, 'GS_distance'):
        GS_distance = _lib.GS_distance
        GS_distance.restype = c_float
        GS_distance.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 214
for _lib in _libs.values():
    if hasattr(_lib, 'GS_P2distance'):
        GS_P2distance = _lib.GS_P2distance
        GS_P2distance.restype = c_float
        GS_P2distance.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 215
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3eq'):
        GS_v3eq = _lib.GS_v3eq
        GS_v3eq.restype = None
        GS_v3eq.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 216
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3add'):
        GS_v3add = _lib.GS_v3add
        GS_v3add.restype = None
        GS_v3add.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 217
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3sub'):
        GS_v3sub = _lib.GS_v3sub
        GS_v3sub.restype = None
        GS_v3sub.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 218
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3mult'):
        GS_v3mult = _lib.GS_v3mult
        GS_v3mult.restype = None
        GS_v3mult.argtypes = [POINTER(c_float), c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 219
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3norm'):
        GS_v3norm = _lib.GS_v3norm
        GS_v3norm.restype = c_int
        GS_v3norm.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 220
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v2norm'):
        GS_v2norm = _lib.GS_v2norm
        GS_v2norm.restype = c_int
        GS_v2norm.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 221
for _lib in _libs.values():
    if hasattr(_lib, 'GS_dv3norm'):
        GS_dv3norm = _lib.GS_dv3norm
        GS_dv3norm.restype = c_int
        GS_dv3norm.argtypes = [POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 222
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3normalize'):
        GS_v3normalize = _lib.GS_v3normalize
        GS_v3normalize.restype = c_int
        GS_v3normalize.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 223
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3dir'):
        GS_v3dir = _lib.GS_v3dir
        GS_v3dir.restype = c_int
        GS_v3dir.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 224
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v2dir'):
        GS_v2dir = _lib.GS_v2dir
        GS_v2dir.restype = None
        GS_v2dir.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 225
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3cross'):
        GS_v3cross = _lib.GS_v3cross
        GS_v3cross.restype = None
        GS_v3cross.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 226
for _lib in _libs.values():
    if hasattr(_lib, 'GS_v3mag'):
        GS_v3mag = _lib.GS_v3mag
        GS_v3mag.restype = None
        GS_v3mag.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 227
for _lib in _libs.values():
    if hasattr(_lib, 'GS_coordpair_repeats'):
        GS_coordpair_repeats = _lib.GS_coordpair_repeats
        GS_coordpair_repeats.restype = c_int
        GS_coordpair_repeats.argtypes = [POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 230
for _lib in _libs.values():
    if hasattr(_lib, 'GV_vect_exists'):
        GV_vect_exists = _lib.GV_vect_exists
        GV_vect_exists.restype = c_int
        GV_vect_exists.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 231
for _lib in _libs.values():
    if hasattr(_lib, 'GV_new_vector'):
        GV_new_vector = _lib.GV_new_vector
        GV_new_vector.restype = c_int
        GV_new_vector.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 232
for _lib in _libs.values():
    if hasattr(_lib, 'GV_num_vects'):
        GV_num_vects = _lib.GV_num_vects
        GV_num_vects.restype = c_int
        GV_num_vects.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 233
for _lib in _libs.values():
    if hasattr(_lib, 'GV_get_vect_list'):
        GV_get_vect_list = _lib.GV_get_vect_list
        GV_get_vect_list.restype = POINTER(c_int)
        GV_get_vect_list.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 234
for _lib in _libs.values():
    if hasattr(_lib, 'GV_delete_vector'):
        GV_delete_vector = _lib.GV_delete_vector
        GV_delete_vector.restype = c_int
        GV_delete_vector.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 235
for _lib in _libs.values():
    if hasattr(_lib, 'GV_load_vector'):
        GV_load_vector = _lib.GV_load_vector
        GV_load_vector.restype = c_int
        GV_load_vector.argtypes = [c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 236
for _lib in _libs.values():
    if hasattr(_lib, 'GV_get_vectname'):
        GV_get_vectname = _lib.GV_get_vectname
        GV_get_vectname.restype = c_int
        GV_get_vectname.argtypes = [c_int, POINTER(POINTER(c_char))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 237
for _lib in _libs.values():
    if hasattr(_lib, 'GV_set_vectmode'):
        GV_set_vectmode = _lib.GV_set_vectmode
        GV_set_vectmode.restype = c_int
        GV_set_vectmode.argtypes = [c_int, c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 238
for _lib in _libs.values():
    if hasattr(_lib, 'GV_get_vectmode'):
        GV_get_vectmode = _lib.GV_get_vectmode
        GV_get_vectmode.restype = c_int
        GV_get_vectmode.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 239
for _lib in _libs.values():
    if hasattr(_lib, 'GV_set_trans'):
        GV_set_trans = _lib.GV_set_trans
        GV_set_trans.restype = None
        GV_set_trans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 240
for _lib in _libs.values():
    if hasattr(_lib, 'GV_get_trans'):
        GV_get_trans = _lib.GV_get_trans
        GV_get_trans.restype = c_int
        GV_get_trans.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 241
for _lib in _libs.values():
    if hasattr(_lib, 'GV_select_surf'):
        GV_select_surf = _lib.GV_select_surf
        GV_select_surf.restype = c_int
        GV_select_surf.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 242
for _lib in _libs.values():
    if hasattr(_lib, 'GV_unselect_surf'):
        GV_unselect_surf = _lib.GV_unselect_surf
        GV_unselect_surf.restype = c_int
        GV_unselect_surf.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 243
for _lib in _libs.values():
    if hasattr(_lib, 'GV_surf_is_selected'):
        GV_surf_is_selected = _lib.GV_surf_is_selected
        GV_surf_is_selected.restype = c_int
        GV_surf_is_selected.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 244
for _lib in _libs.values():
    if hasattr(_lib, 'GV_draw_vect'):
        GV_draw_vect = _lib.GV_draw_vect
        GV_draw_vect.restype = None
        GV_draw_vect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 245
for _lib in _libs.values():
    if hasattr(_lib, 'GV_alldraw_vect'):
        GV_alldraw_vect = _lib.GV_alldraw_vect
        GV_alldraw_vect.restype = None
        GV_alldraw_vect.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 246
for _lib in _libs.values():
    if hasattr(_lib, 'GV_draw_fastvect'):
        GV_draw_fastvect = _lib.GV_draw_fastvect
        GV_draw_fastvect.restype = None
        GV_draw_fastvect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 247
for _lib in _libs.values():
    if hasattr(_lib, 'GV_Set_ClientData'):
        GV_Set_ClientData = _lib.GV_Set_ClientData
        GV_Set_ClientData.restype = c_int
        GV_Set_ClientData.argtypes = [c_int, POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 248
for _lib in _libs.values():
    if hasattr(_lib, 'GV_Get_ClientData'):
        GV_Get_ClientData = _lib.GV_Get_ClientData
        GV_Get_ClientData.restype = POINTER(None)
        GV_Get_ClientData.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 251
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_libinit'):
        GVL_libinit = _lib.GVL_libinit
        GVL_libinit.restype = None
        GVL_libinit.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 252
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_region'):
        GVL_get_region = _lib.GVL_get_region
        GVL_get_region.restype = c_int
        GVL_get_region.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 253
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_window'):
        GVL_get_window = _lib.GVL_get_window
        GVL_get_window.restype = POINTER(None)
        GVL_get_window.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 254
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_vol_exists'):
        GVL_vol_exists = _lib.GVL_vol_exists
        GVL_vol_exists.restype = c_int
        GVL_vol_exists.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 255
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_new_vol'):
        GVL_new_vol = _lib.GVL_new_vol
        GVL_new_vol.restype = c_int
        GVL_new_vol.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 256
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_num_vols'):
        GVL_num_vols = _lib.GVL_num_vols
        GVL_num_vols.restype = c_int
        GVL_num_vols.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 257
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_vol_list'):
        GVL_get_vol_list = _lib.GVL_get_vol_list
        GVL_get_vol_list.restype = POINTER(c_int)
        GVL_get_vol_list.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 258
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_delete_vol'):
        GVL_delete_vol = _lib.GVL_delete_vol
        GVL_delete_vol.restype = c_int
        GVL_delete_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 259
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_load_vol'):
        GVL_load_vol = _lib.GVL_load_vol
        GVL_load_vol.restype = c_int
        GVL_load_vol.argtypes = [c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 260
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_volname'):
        GVL_get_volname = _lib.GVL_get_volname
        GVL_get_volname.restype = c_int
        GVL_get_volname.argtypes = [c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 261
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_set_trans'):
        GVL_set_trans = _lib.GVL_set_trans
        GVL_set_trans.restype = None
        GVL_set_trans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 262
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_trans'):
        GVL_get_trans = _lib.GVL_get_trans
        GVL_get_trans.restype = c_int
        GVL_get_trans.argtypes = [c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 263
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_draw_vol'):
        GVL_draw_vol = _lib.GVL_draw_vol
        GVL_draw_vol.restype = None
        GVL_draw_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 264
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_draw_wire'):
        GVL_draw_wire = _lib.GVL_draw_wire
        GVL_draw_wire.restype = None
        GVL_draw_wire.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 265
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_alldraw_vol'):
        GVL_alldraw_vol = _lib.GVL_alldraw_vol
        GVL_alldraw_vol.restype = None
        GVL_alldraw_vol.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 266
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_alldraw_wire'):
        GVL_alldraw_wire = _lib.GVL_alldraw_wire
        GVL_alldraw_wire.restype = None
        GVL_alldraw_wire.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 267
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_Set_ClientData'):
        GVL_Set_ClientData = _lib.GVL_Set_ClientData
        GVL_Set_ClientData.restype = c_int
        GVL_Set_ClientData.argtypes = [c_int, POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 268
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_Get_ClientData'):
        GVL_Get_ClientData = _lib.GVL_Get_ClientData
        GVL_Get_ClientData.restype = POINTER(None)
        GVL_Get_ClientData.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 269
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_get_dims'):
        GVL_get_dims = _lib.GVL_get_dims
        GVL_get_dims.restype = None
        GVL_get_dims.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 270
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_set_focus_center_map'):
        GVL_set_focus_center_map = _lib.GVL_set_focus_center_map
        GVL_set_focus_center_map.restype = None
        GVL_set_focus_center_map.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 272
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_move_up'):
        GVL_isosurf_move_up = _lib.GVL_isosurf_move_up
        GVL_isosurf_move_up.restype = c_int
        GVL_isosurf_move_up.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 273
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_move_down'):
        GVL_isosurf_move_down = _lib.GVL_isosurf_move_down
        GVL_isosurf_move_down.restype = c_int
        GVL_isosurf_move_down.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 274
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_get_drawres'):
        GVL_isosurf_get_drawres = _lib.GVL_isosurf_get_drawres
        GVL_isosurf_get_drawres.restype = None
        GVL_isosurf_get_drawres.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 275
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_drawres'):
        GVL_isosurf_set_drawres = _lib.GVL_isosurf_set_drawres
        GVL_isosurf_set_drawres.restype = c_int
        GVL_isosurf_set_drawres.argtypes = [c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 276
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_get_drawmode'):
        GVL_isosurf_get_drawmode = _lib.GVL_isosurf_get_drawmode
        GVL_isosurf_get_drawmode.restype = c_int
        GVL_isosurf_get_drawmode.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 277
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_drawmode'):
        GVL_isosurf_set_drawmode = _lib.GVL_isosurf_set_drawmode
        GVL_isosurf_set_drawmode.restype = c_int
        GVL_isosurf_set_drawmode.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 278
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_add'):
        GVL_isosurf_add = _lib.GVL_isosurf_add
        GVL_isosurf_add.restype = c_int
        GVL_isosurf_add.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 279
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_del'):
        GVL_isosurf_del = _lib.GVL_isosurf_del
        GVL_isosurf_del.restype = c_int
        GVL_isosurf_del.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 280
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_get_att'):
        GVL_isosurf_get_att = _lib.GVL_isosurf_get_att
        GVL_isosurf_get_att.restype = c_int
        GVL_isosurf_get_att.argtypes = [c_int, c_int, c_int, POINTER(c_int), POINTER(c_float), String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 281
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_unset_att'):
        GVL_isosurf_unset_att = _lib.GVL_isosurf_unset_att
        GVL_isosurf_unset_att.restype = c_int
        GVL_isosurf_unset_att.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 282
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_att_const'):
        GVL_isosurf_set_att_const = _lib.GVL_isosurf_set_att_const
        GVL_isosurf_set_att_const.restype = c_int
        GVL_isosurf_set_att_const.argtypes = [c_int, c_int, c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 283
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_att_map'):
        GVL_isosurf_set_att_map = _lib.GVL_isosurf_set_att_map
        GVL_isosurf_set_att_map.restype = c_int
        GVL_isosurf_set_att_map.argtypes = [c_int, c_int, c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 284
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_get_flags'):
        GVL_isosurf_get_flags = _lib.GVL_isosurf_get_flags
        GVL_isosurf_get_flags.restype = c_int
        GVL_isosurf_get_flags.argtypes = [c_int, c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 285
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_flags'):
        GVL_isosurf_set_flags = _lib.GVL_isosurf_set_flags
        GVL_isosurf_set_flags.restype = c_int
        GVL_isosurf_set_flags.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 286
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_num_isosurfs'):
        GVL_isosurf_num_isosurfs = _lib.GVL_isosurf_num_isosurfs
        GVL_isosurf_num_isosurfs.restype = c_int
        GVL_isosurf_num_isosurfs.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 287
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_set_maskmode'):
        GVL_isosurf_set_maskmode = _lib.GVL_isosurf_set_maskmode
        GVL_isosurf_set_maskmode.restype = c_int
        GVL_isosurf_set_maskmode.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 288
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_isosurf_get_maskmode'):
        GVL_isosurf_get_maskmode = _lib.GVL_isosurf_get_maskmode
        GVL_isosurf_get_maskmode.restype = c_int
        GVL_isosurf_get_maskmode.argtypes = [c_int, c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 290
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_move_up'):
        GVL_slice_move_up = _lib.GVL_slice_move_up
        GVL_slice_move_up.restype = c_int
        GVL_slice_move_up.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 291
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_move_down'):
        GVL_slice_move_down = _lib.GVL_slice_move_down
        GVL_slice_move_down.restype = c_int
        GVL_slice_move_down.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 292
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_get_drawres'):
        GVL_slice_get_drawres = _lib.GVL_slice_get_drawres
        GVL_slice_get_drawres.restype = None
        GVL_slice_get_drawres.argtypes = [c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 293
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_get_transp'):
        GVL_slice_get_transp = _lib.GVL_slice_get_transp
        GVL_slice_get_transp.restype = c_int
        GVL_slice_get_transp.argtypes = [c_int, c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 294
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_set_transp'):
        GVL_slice_set_transp = _lib.GVL_slice_set_transp
        GVL_slice_set_transp.restype = c_int
        GVL_slice_set_transp.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 295
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_set_drawres'):
        GVL_slice_set_drawres = _lib.GVL_slice_set_drawres
        GVL_slice_set_drawres.restype = c_int
        GVL_slice_set_drawres.argtypes = [c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 296
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_get_drawmode'):
        GVL_slice_get_drawmode = _lib.GVL_slice_get_drawmode
        GVL_slice_get_drawmode.restype = c_int
        GVL_slice_get_drawmode.argtypes = [c_int, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 297
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_set_drawmode'):
        GVL_slice_set_drawmode = _lib.GVL_slice_set_drawmode
        GVL_slice_set_drawmode.restype = c_int
        GVL_slice_set_drawmode.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 298
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_add'):
        GVL_slice_add = _lib.GVL_slice_add
        GVL_slice_add.restype = c_int
        GVL_slice_add.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 299
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_del'):
        GVL_slice_del = _lib.GVL_slice_del
        GVL_slice_del.restype = c_int
        GVL_slice_del.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 300
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_num_slices'):
        GVL_slice_num_slices = _lib.GVL_slice_num_slices
        GVL_slice_num_slices.restype = c_int
        GVL_slice_num_slices.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 301
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_get_pos'):
        GVL_slice_get_pos = _lib.GVL_slice_get_pos
        GVL_slice_get_pos.restype = c_int
        GVL_slice_get_pos.argtypes = [c_int, c_int, POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 303
for _lib in _libs.values():
    if hasattr(_lib, 'GVL_slice_set_pos'):
        GVL_slice_set_pos = _lib.GVL_slice_set_pos
        GVL_slice_set_pos.restype = c_int
        GVL_slice_set_pos.argtypes = [c_int, c_int, c_float, c_float, c_float, c_float, c_float, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 307
for _lib in _libs.values():
    if hasattr(_lib, 'Gp_set_color'):
        Gp_set_color = _lib.Gp_set_color
        Gp_set_color.restype = c_int
        Gp_set_color.argtypes = [String, POINTER(geopoint)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 308
for _lib in _libs.values():
    if hasattr(_lib, 'Gp_load_sites'):
        Gp_load_sites = _lib.Gp_load_sites
        Gp_load_sites.restype = POINTER(geopoint)
        Gp_load_sites.argtypes = [String, POINTER(c_int), POINTER(c_int), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 311
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_distance'):
        Gs_distance = _lib.Gs_distance
        Gs_distance.restype = c_double
        Gs_distance.argtypes = [POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 312
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_loadmap_as_float'):
        Gs_loadmap_as_float = _lib.Gs_loadmap_as_float
        Gs_loadmap_as_float.restype = c_int
        Gs_loadmap_as_float.argtypes = [POINTER(struct_Cell_head), String, POINTER(c_float), POINTER(struct_BM), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 314
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_loadmap_as_int'):
        Gs_loadmap_as_int = _lib.Gs_loadmap_as_int
        Gs_loadmap_as_int.restype = c_int
        Gs_loadmap_as_int.argtypes = [POINTER(struct_Cell_head), String, POINTER(c_int), POINTER(struct_BM), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 316
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_numtype'):
        Gs_numtype = _lib.Gs_numtype
        Gs_numtype.restype = c_int
        Gs_numtype.argtypes = [String, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 317
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_loadmap_as_short'):
        Gs_loadmap_as_short = _lib.Gs_loadmap_as_short
        Gs_loadmap_as_short.restype = c_int
        Gs_loadmap_as_short.argtypes = [POINTER(struct_Cell_head), String, POINTER(c_short), POINTER(struct_BM), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 319
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_loadmap_as_char'):
        Gs_loadmap_as_char = _lib.Gs_loadmap_as_char
        Gs_loadmap_as_char.restype = c_int
        Gs_loadmap_as_char.argtypes = [POINTER(struct_Cell_head), String, POINTER(c_ubyte), POINTER(struct_BM), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 321
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_loadmap_as_bitmap'):
        Gs_loadmap_as_bitmap = _lib.Gs_loadmap_as_bitmap
        Gs_loadmap_as_bitmap.restype = c_int
        Gs_loadmap_as_bitmap.argtypes = [POINTER(struct_Cell_head), String, POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 322
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_build_256lookup'):
        Gs_build_256lookup = _lib.Gs_build_256lookup
        Gs_build_256lookup.restype = c_int
        Gs_build_256lookup.argtypes = [String, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 323
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_pack_colors'):
        Gs_pack_colors = _lib.Gs_pack_colors
        Gs_pack_colors.restype = None
        Gs_pack_colors.argtypes = [String, POINTER(c_int), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 324
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_pack_colors_float'):
        Gs_pack_colors_float = _lib.Gs_pack_colors_float
        Gs_pack_colors_float.restype = None
        Gs_pack_colors_float.argtypes = [String, POINTER(c_float), POINTER(c_int), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 325
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_get_cat_label'):
        Gs_get_cat_label = _lib.Gs_get_cat_label
        Gs_get_cat_label.restype = c_int
        Gs_get_cat_label.argtypes = [String, c_int, c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 326
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_save_3dview'):
        Gs_save_3dview = _lib.Gs_save_3dview
        Gs_save_3dview.restype = c_int
        Gs_save_3dview.argtypes = [String, POINTER(geoview), POINTER(geodisplay), POINTER(struct_Cell_head), POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 328
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_load_3dview'):
        Gs_load_3dview = _lib.Gs_load_3dview
        Gs_load_3dview.restype = c_int
        Gs_load_3dview.argtypes = [String, POINTER(geoview), POINTER(geodisplay), POINTER(struct_Cell_head), POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 330
for _lib in _libs.values():
    if hasattr(_lib, 'Gs_update_attrange'):
        Gs_update_attrange = _lib.Gs_update_attrange
        Gs_update_attrange.restype = c_int
        Gs_update_attrange.argtypes = [POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 333
for _lib in _libs.values():
    if hasattr(_lib, 'Gv_load_vect'):
        Gv_load_vect = _lib.Gv_load_vect
        Gv_load_vect.restype = POINTER(geoline)
        Gv_load_vect.argtypes = [String, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 334
for _lib in _libs.values():
    if hasattr(_lib, 'sub_Vectmem'):
        sub_Vectmem = _lib.sub_Vectmem
        sub_Vectmem.restype = None
        sub_Vectmem.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 337
for _lib in _libs.values():
    if hasattr(_lib, 'gk_copy_key'):
        gk_copy_key = _lib.gk_copy_key
        gk_copy_key.restype = POINTER(Keylist)
        gk_copy_key.argtypes = [POINTER(Keylist)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 338
for _lib in _libs.values():
    if hasattr(_lib, 'gk_get_mask_sofar'):
        gk_get_mask_sofar = _lib.gk_get_mask_sofar
        gk_get_mask_sofar.restype = c_ulong
        gk_get_mask_sofar.argtypes = [c_float, POINTER(Keylist)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 339
for _lib in _libs.values():
    if hasattr(_lib, 'gk_viable_keys_for_mask'):
        gk_viable_keys_for_mask = _lib.gk_viable_keys_for_mask
        gk_viable_keys_for_mask.restype = c_int
        gk_viable_keys_for_mask.argtypes = [c_ulong, POINTER(Keylist), POINTER(POINTER(Keylist))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 340
for _lib in _libs.values():
    if hasattr(_lib, 'gk_follow_frames'):
        gk_follow_frames = _lib.gk_follow_frames
        gk_follow_frames.restype = None
        gk_follow_frames.argtypes = [POINTER(Viewnode), c_int, POINTER(Keylist), c_int, c_int, c_int, c_ulong]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 342
for _lib in _libs.values():
    if hasattr(_lib, 'gk_free_key'):
        gk_free_key = _lib.gk_free_key
        gk_free_key.restype = None
        gk_free_key.argtypes = [POINTER(Keylist)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 343
for _lib in _libs.values():
    if hasattr(_lib, 'gk_make_framesfromkeys'):
        gk_make_framesfromkeys = _lib.gk_make_framesfromkeys
        gk_make_framesfromkeys.restype = POINTER(Viewnode)
        gk_make_framesfromkeys.argtypes = [POINTER(Keylist), c_int, c_int, c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 344
for _lib in _libs.values():
    if hasattr(_lib, 'get_key_neighbors'):
        get_key_neighbors = _lib.get_key_neighbors
        get_key_neighbors.restype = c_double
        get_key_neighbors.argtypes = [c_int, c_double, c_double, c_int, POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist)), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 347
for _lib in _libs.values():
    if hasattr(_lib, 'lin_interp'):
        lin_interp = _lib.lin_interp
        lin_interp.restype = c_double
        lin_interp.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 348
for _lib in _libs.values():
    if hasattr(_lib, 'get_2key_neighbors'):
        get_2key_neighbors = _lib.get_2key_neighbors
        get_2key_neighbors.restype = c_double
        get_2key_neighbors.argtypes = [c_int, c_float, c_float, c_int, POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist)), POINTER(POINTER(Keylist))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 350
for _lib in _libs.values():
    if hasattr(_lib, 'gk_make_linear_framesfromkeys'):
        gk_make_linear_framesfromkeys = _lib.gk_make_linear_framesfromkeys
        gk_make_linear_framesfromkeys.restype = POINTER(Viewnode)
        gk_make_linear_framesfromkeys.argtypes = [POINTER(Keylist), c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 351
for _lib in _libs.values():
    if hasattr(_lib, 'correct_twist'):
        correct_twist = _lib.correct_twist
        correct_twist.restype = None
        correct_twist.argtypes = [POINTER(Keylist)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 352
for _lib in _libs.values():
    if hasattr(_lib, 'gk_draw_path'):
        gk_draw_path = _lib.gk_draw_path
        gk_draw_path.restype = c_int
        gk_draw_path.argtypes = [POINTER(Viewnode), c_int, POINTER(Keylist)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 355
for _lib in _libs.values():
    if hasattr(_lib, 'gp_get_site'):
        gp_get_site = _lib.gp_get_site
        gp_get_site.restype = POINTER(geosite)
        gp_get_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 356
for _lib in _libs.values():
    if hasattr(_lib, 'gp_get_prev_site'):
        gp_get_prev_site = _lib.gp_get_prev_site
        gp_get_prev_site.restype = POINTER(geosite)
        gp_get_prev_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 357
for _lib in _libs.values():
    if hasattr(_lib, 'gp_num_sites'):
        gp_num_sites = _lib.gp_num_sites
        gp_num_sites.restype = c_int
        gp_num_sites.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 358
for _lib in _libs.values():
    if hasattr(_lib, 'gp_get_last_site'):
        gp_get_last_site = _lib.gp_get_last_site
        gp_get_last_site.restype = POINTER(geosite)
        gp_get_last_site.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 359
for _lib in _libs.values():
    if hasattr(_lib, 'gp_get_new_site'):
        gp_get_new_site = _lib.gp_get_new_site
        gp_get_new_site.restype = POINTER(geosite)
        gp_get_new_site.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 360
for _lib in _libs.values():
    if hasattr(_lib, 'gp_update_drapesurfs'):
        gp_update_drapesurfs = _lib.gp_update_drapesurfs
        gp_update_drapesurfs.restype = None
        gp_update_drapesurfs.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 361
for _lib in _libs.values():
    if hasattr(_lib, 'gp_set_defaults'):
        gp_set_defaults = _lib.gp_set_defaults
        gp_set_defaults.restype = c_int
        gp_set_defaults.argtypes = [POINTER(geosite)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 362
for _lib in _libs.values():
    if hasattr(_lib, 'print_site_fields'):
        print_site_fields = _lib.print_site_fields
        print_site_fields.restype = None
        print_site_fields.argtypes = [POINTER(geosite)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 363
for _lib in _libs.values():
    if hasattr(_lib, 'gp_init_site'):
        gp_init_site = _lib.gp_init_site
        gp_init_site.restype = c_int
        gp_init_site.argtypes = [POINTER(geosite)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 364
for _lib in _libs.values():
    if hasattr(_lib, 'gp_delete_site'):
        gp_delete_site = _lib.gp_delete_site
        gp_delete_site.restype = None
        gp_delete_site.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 365
for _lib in _libs.values():
    if hasattr(_lib, 'gp_free_site'):
        gp_free_site = _lib.gp_free_site
        gp_free_site.restype = c_int
        gp_free_site.argtypes = [POINTER(geosite)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 366
for _lib in _libs.values():
    if hasattr(_lib, 'gp_free_sitemem'):
        gp_free_sitemem = _lib.gp_free_sitemem
        gp_free_sitemem.restype = None
        gp_free_sitemem.argtypes = [POINTER(geosite)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 367
for _lib in _libs.values():
    if hasattr(_lib, 'gp_set_drapesurfs'):
        gp_set_drapesurfs = _lib.gp_set_drapesurfs
        gp_set_drapesurfs.restype = None
        gp_set_drapesurfs.argtypes = [POINTER(geosite), POINTER(c_int), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 370
for _lib in _libs.values():
    if hasattr(_lib, 'gs_point_in_region'):
        gs_point_in_region = _lib.gs_point_in_region
        gs_point_in_region.restype = c_int
        gs_point_in_region.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 371
for _lib in _libs.values():
    if hasattr(_lib, 'gpd_obj'):
        gpd_obj = _lib.gpd_obj
        gpd_obj.restype = None
        gpd_obj.argtypes = [POINTER(geosurf), c_int, c_float, c_int, Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 372
for _lib in _libs.values():
    if hasattr(_lib, 'gpd_2dsite'):
        gpd_2dsite = _lib.gpd_2dsite
        gpd_2dsite.restype = c_int
        gpd_2dsite.argtypes = [POINTER(geosite), POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 373
for _lib in _libs.values():
    if hasattr(_lib, 'gpd_3dsite'):
        gpd_3dsite = _lib.gpd_3dsite
        gpd_3dsite.restype = c_int
        gpd_3dsite.argtypes = [POINTER(geosite), c_float, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 376
for _lib in _libs.values():
    if hasattr(_lib, 'gs_err'):
        gs_err = _lib.gs_err
        gs_err.restype = None
        gs_err.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 377
for _lib in _libs.values():
    if hasattr(_lib, 'gs_init'):
        gs_init = _lib.gs_init
        gs_init.restype = None
        gs_init.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 378
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_surf'):
        gs_get_surf = _lib.gs_get_surf
        gs_get_surf.restype = POINTER(geosurf)
        gs_get_surf.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 379
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_prev_surface'):
        gs_get_prev_surface = _lib.gs_get_prev_surface
        gs_get_prev_surface.restype = POINTER(geosurf)
        gs_get_prev_surface.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 380
for _lib in _libs.values():
    if hasattr(_lib, 'gs_getall_surfaces'):
        gs_getall_surfaces = _lib.gs_getall_surfaces
        gs_getall_surfaces.restype = c_int
        gs_getall_surfaces.argtypes = [POINTER(POINTER(geosurf))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 381
for _lib in _libs.values():
    if hasattr(_lib, 'gs_num_surfaces'):
        gs_num_surfaces = _lib.gs_num_surfaces
        gs_num_surfaces.restype = c_int
        gs_num_surfaces.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 382
for _lib in _libs.values():
    if hasattr(_lib, 'gs_att_is_set'):
        gs_att_is_set = _lib.gs_att_is_set
        gs_att_is_set.restype = c_int
        gs_att_is_set.argtypes = [POINTER(geosurf), c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 383
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_last_surface'):
        gs_get_last_surface = _lib.gs_get_last_surface
        gs_get_last_surface.restype = POINTER(geosurf)
        gs_get_last_surface.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 384
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_new_surface'):
        gs_get_new_surface = _lib.gs_get_new_surface
        gs_get_new_surface.restype = POINTER(geosurf)
        gs_get_new_surface.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 385
for _lib in _libs.values():
    if hasattr(_lib, 'gs_init_surf'):
        gs_init_surf = _lib.gs_init_surf
        gs_init_surf.restype = c_int
        gs_init_surf.argtypes = [POINTER(geosurf), c_double, c_double, c_int, c_int, c_double, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 386
for _lib in _libs.values():
    if hasattr(_lib, 'gs_init_normbuff'):
        gs_init_normbuff = _lib.gs_init_normbuff
        gs_init_normbuff.restype = c_int
        gs_init_normbuff.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 387
for _lib in _libs.values():
    if hasattr(_lib, 'print_frto'):
        print_frto = _lib.print_frto
        print_frto.restype = None
        print_frto.argtypes = [POINTER(c_float * 4)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 388
for _lib in _libs.values():
    if hasattr(_lib, 'print_realto'):
        print_realto = _lib.print_realto
        print_realto.restype = None
        print_realto.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 389
for _lib in _libs.values():
    if hasattr(_lib, 'print_256lookup'):
        print_256lookup = _lib.print_256lookup
        print_256lookup.restype = None
        print_256lookup.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 390
for _lib in _libs.values():
    if hasattr(_lib, 'print_surf_fields'):
        print_surf_fields = _lib.print_surf_fields
        print_surf_fields.restype = None
        print_surf_fields.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 391
for _lib in _libs.values():
    if hasattr(_lib, 'print_view_fields'):
        print_view_fields = _lib.print_view_fields
        print_view_fields.restype = None
        print_view_fields.argtypes = [POINTER(geoview)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 392
for _lib in _libs.values():
    if hasattr(_lib, 'gs_set_defaults'):
        gs_set_defaults = _lib.gs_set_defaults
        gs_set_defaults.restype = None
        gs_set_defaults.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 393
for _lib in _libs.values():
    if hasattr(_lib, 'gs_delete_surf'):
        gs_delete_surf = _lib.gs_delete_surf
        gs_delete_surf.restype = None
        gs_delete_surf.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 394
for _lib in _libs.values():
    if hasattr(_lib, 'gs_free_surf'):
        gs_free_surf = _lib.gs_free_surf
        gs_free_surf.restype = c_int
        gs_free_surf.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 395
for _lib in _libs.values():
    if hasattr(_lib, 'gs_free_unshared_buffs'):
        gs_free_unshared_buffs = _lib.gs_free_unshared_buffs
        gs_free_unshared_buffs.restype = None
        gs_free_unshared_buffs.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 396
for _lib in _libs.values():
    if hasattr(_lib, 'gs_num_datah_reused'):
        gs_num_datah_reused = _lib.gs_num_datah_reused
        gs_num_datah_reused.restype = c_int
        gs_num_datah_reused.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 397
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_att_type'):
        gs_get_att_type = _lib.gs_get_att_type
        gs_get_att_type.restype = c_int
        gs_get_att_type.argtypes = [POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 398
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_att_src'):
        gs_get_att_src = _lib.gs_get_att_src
        gs_get_att_src.restype = c_int
        gs_get_att_src.argtypes = [POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 399
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_att_typbuff'):
        gs_get_att_typbuff = _lib.gs_get_att_typbuff
        gs_get_att_typbuff.restype = POINTER(typbuff)
        gs_get_att_typbuff.argtypes = [POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 400
for _lib in _libs.values():
    if hasattr(_lib, 'gs_malloc_att_buff'):
        gs_malloc_att_buff = _lib.gs_malloc_att_buff
        gs_malloc_att_buff.restype = c_int
        gs_malloc_att_buff.argtypes = [POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 401
for _lib in _libs.values():
    if hasattr(_lib, 'gs_malloc_lookup'):
        gs_malloc_lookup = _lib.gs_malloc_lookup
        gs_malloc_lookup.restype = c_int
        gs_malloc_lookup.argtypes = [POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 402
for _lib in _libs.values():
    if hasattr(_lib, 'gs_set_att_type'):
        gs_set_att_type = _lib.gs_set_att_type
        gs_set_att_type.restype = c_int
        gs_set_att_type.argtypes = [POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 403
for _lib in _libs.values():
    if hasattr(_lib, 'gs_set_att_src'):
        gs_set_att_src = _lib.gs_set_att_src
        gs_set_att_src.restype = c_int
        gs_set_att_src.argtypes = [POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 404
for _lib in _libs.values():
    if hasattr(_lib, 'gs_set_att_const'):
        gs_set_att_const = _lib.gs_set_att_const
        gs_set_att_const.restype = c_int
        gs_set_att_const.argtypes = [POINTER(geosurf), c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 405
for _lib in _libs.values():
    if hasattr(_lib, 'gs_set_maskmode'):
        gs_set_maskmode = _lib.gs_set_maskmode
        gs_set_maskmode.restype = None
        gs_set_maskmode.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 406
for _lib in _libs.values():
    if hasattr(_lib, 'gs_mask_defined'):
        gs_mask_defined = _lib.gs_mask_defined
        gs_mask_defined.restype = c_int
        gs_mask_defined.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 407
for _lib in _libs.values():
    if hasattr(_lib, 'gs_masked'):
        gs_masked = _lib.gs_masked
        gs_masked.restype = c_int
        gs_masked.argtypes = [POINTER(typbuff), c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 408
for _lib in _libs.values():
    if hasattr(_lib, 'gs_mapcolor'):
        gs_mapcolor = _lib.gs_mapcolor
        gs_mapcolor.restype = c_int
        gs_mapcolor.argtypes = [POINTER(typbuff), POINTER(gsurf_att), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 409
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_zextents'):
        gs_get_zextents = _lib.gs_get_zextents
        gs_get_zextents.restype = c_int
        gs_get_zextents.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 410
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_xextents'):
        gs_get_xextents = _lib.gs_get_xextents
        gs_get_xextents.restype = c_int
        gs_get_xextents.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 411
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_yextents'):
        gs_get_yextents = _lib.gs_get_yextents
        gs_get_yextents.restype = c_int
        gs_get_yextents.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 412
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_zrange0'):
        gs_get_zrange0 = _lib.gs_get_zrange0
        gs_get_zrange0.restype = c_int
        gs_get_zrange0.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 413
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_zrange'):
        gs_get_zrange = _lib.gs_get_zrange
        gs_get_zrange.restype = c_int
        gs_get_zrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 414
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_xrange'):
        gs_get_xrange = _lib.gs_get_xrange
        gs_get_xrange.restype = c_int
        gs_get_xrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 415
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_yrange'):
        gs_get_yrange = _lib.gs_get_yrange
        gs_get_yrange.restype = c_int
        gs_get_yrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 416
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_data_avg_zmax'):
        gs_get_data_avg_zmax = _lib.gs_get_data_avg_zmax
        gs_get_data_avg_zmax.restype = c_int
        gs_get_data_avg_zmax.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 417
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_datacenter'):
        gs_get_datacenter = _lib.gs_get_datacenter
        gs_get_datacenter.restype = c_int
        gs_get_datacenter.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 418
for _lib in _libs.values():
    if hasattr(_lib, 'gs_setall_norm_needupdate'):
        gs_setall_norm_needupdate = _lib.gs_setall_norm_needupdate
        gs_setall_norm_needupdate.restype = c_int
        gs_setall_norm_needupdate.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 419
for _lib in _libs.values():
    if hasattr(_lib, 'gs_point_is_masked'):
        gs_point_is_masked = _lib.gs_point_is_masked
        gs_point_is_masked.restype = c_int
        gs_point_is_masked.argtypes = [POINTER(geosurf), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 420
for _lib in _libs.values():
    if hasattr(_lib, 'gs_distance_onsurf'):
        gs_distance_onsurf = _lib.gs_distance_onsurf
        gs_distance_onsurf.restype = c_int
        gs_distance_onsurf.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 423
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_make_mask'):
        gsbm_make_mask = _lib.gsbm_make_mask
        gsbm_make_mask.restype = POINTER(struct_BM)
        gsbm_make_mask.argtypes = [POINTER(typbuff), c_float, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 424
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_zero_mask'):
        gsbm_zero_mask = _lib.gsbm_zero_mask
        gsbm_zero_mask.restype = None
        gsbm_zero_mask.argtypes = [POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 425
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_or_masks'):
        gsbm_or_masks = _lib.gsbm_or_masks
        gsbm_or_masks.restype = c_int
        gsbm_or_masks.argtypes = [POINTER(struct_BM), POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 426
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_ornot_masks'):
        gsbm_ornot_masks = _lib.gsbm_ornot_masks
        gsbm_ornot_masks.restype = c_int
        gsbm_ornot_masks.argtypes = [POINTER(struct_BM), POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 427
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_and_masks'):
        gsbm_and_masks = _lib.gsbm_and_masks
        gsbm_and_masks.restype = c_int
        gsbm_and_masks.argtypes = [POINTER(struct_BM), POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 428
for _lib in _libs.values():
    if hasattr(_lib, 'gsbm_xor_masks'):
        gsbm_xor_masks = _lib.gsbm_xor_masks
        gsbm_xor_masks.restype = c_int
        gsbm_xor_masks.argtypes = [POINTER(struct_BM), POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 429
for _lib in _libs.values():
    if hasattr(_lib, 'gs_update_curmask'):
        gs_update_curmask = _lib.gs_update_curmask
        gs_update_curmask.restype = c_int
        gs_update_curmask.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 430
for _lib in _libs.values():
    if hasattr(_lib, 'print_bm'):
        print_bm = _lib.print_bm
        print_bm.restype = None
        print_bm.argtypes = [POINTER(struct_BM)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 433
for _lib in _libs.values():
    if hasattr(_lib, 'init_vars'):
        init_vars = _lib.init_vars
        init_vars.restype = None
        init_vars.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 434
for _lib in _libs.values():
    if hasattr(_lib, 'gs_calc_normals'):
        gs_calc_normals = _lib.gs_calc_normals
        gs_calc_normals.restype = c_int
        gs_calc_normals.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 435
for _lib in _libs.values():
    if hasattr(_lib, 'calc_norm'):
        calc_norm = _lib.calc_norm
        calc_norm.restype = c_int
        calc_norm.argtypes = [POINTER(geosurf), c_int, c_int, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 438
for _lib in _libs.values():
    if hasattr(_lib, 'gs_los_intersect1'):
        gs_los_intersect1 = _lib.gs_los_intersect1
        gs_los_intersect1.restype = c_int
        gs_los_intersect1.argtypes = [c_int, POINTER(c_float * 3), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 439
for _lib in _libs.values():
    if hasattr(_lib, 'gs_los_intersect'):
        gs_los_intersect = _lib.gs_los_intersect
        gs_los_intersect.restype = c_int
        gs_los_intersect.argtypes = [c_int, POINTER(POINTER(c_float)), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 440
for _lib in _libs.values():
    if hasattr(_lib, 'RayCvxPolyhedronInt'):
        RayCvxPolyhedronInt = _lib.RayCvxPolyhedronInt
        RayCvxPolyhedronInt.restype = c_int
        RayCvxPolyhedronInt.argtypes = [Point3, Point3, c_double, POINTER(Point4), c_int, POINTER(c_double), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 442
for _lib in _libs.values():
    if hasattr(_lib, 'gs_get_databounds_planes'):
        gs_get_databounds_planes = _lib.gs_get_databounds_planes
        gs_get_databounds_planes.restype = None
        gs_get_databounds_planes.argtypes = [POINTER(Point4)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 443
for _lib in _libs.values():
    if hasattr(_lib, 'gs_setlos_enterdata'):
        gs_setlos_enterdata = _lib.gs_setlos_enterdata
        gs_setlos_enterdata.restype = c_int
        gs_setlos_enterdata.argtypes = [POINTER(Point3)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 446
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_def_cplane'):
        gsd_def_cplane = _lib.gsd_def_cplane
        gsd_def_cplane.restype = None
        gsd_def_cplane.argtypes = [c_int, POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 447
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_update_cplanes'):
        gsd_update_cplanes = _lib.gsd_update_cplanes
        gsd_update_cplanes.restype = None
        gsd_update_cplanes.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 448
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_cplane_on'):
        gsd_cplane_on = _lib.gsd_cplane_on
        gsd_cplane_on.restype = None
        gsd_cplane_on.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 449
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_cplane_off'):
        gsd_cplane_off = _lib.gsd_cplane_off
        gsd_cplane_off.restype = None
        gsd_cplane_off.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 450
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_cplanes_state'):
        gsd_get_cplanes_state = _lib.gsd_get_cplanes_state
        gsd_get_cplanes_state.restype = None
        gsd_get_cplanes_state.argtypes = [POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 451
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_cplanes'):
        gsd_get_cplanes = _lib.gsd_get_cplanes
        gsd_get_cplanes.restype = c_int
        gsd_get_cplanes.argtypes = [POINTER(Point4)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 452
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_update_cpnorm'):
        gsd_update_cpnorm = _lib.gsd_update_cpnorm
        gsd_update_cpnorm.restype = None
        gsd_update_cpnorm.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 453
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_cplane_setrot'):
        gsd_cplane_setrot = _lib.gsd_cplane_setrot
        gsd_cplane_setrot.restype = None
        gsd_cplane_setrot.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 454
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_cplane_settrans'):
        gsd_cplane_settrans = _lib.gsd_cplane_settrans
        gsd_cplane_settrans.restype = None
        gsd_cplane_settrans.argtypes = [c_int, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 455
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_draw_cplane_fence'):
        gsd_draw_cplane_fence = _lib.gsd_draw_cplane_fence
        gsd_draw_cplane_fence.restype = None
        gsd_draw_cplane_fence.argtypes = [POINTER(geosurf), POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 456
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_draw_cplane'):
        gsd_draw_cplane = _lib.gsd_draw_cplane
        gsd_draw_cplane.restype = None
        gsd_draw_cplane.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 459
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_set_font'):
        gsd_set_font = _lib.gsd_set_font
        gsd_set_font.restype = GLuint
        gsd_set_font.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 460
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_txtwidth'):
        gsd_get_txtwidth = _lib.gsd_get_txtwidth
        gsd_get_txtwidth.restype = c_int
        gsd_get_txtwidth.argtypes = [String, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 461
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_txtheight'):
        gsd_get_txtheight = _lib.gsd_get_txtheight
        gsd_get_txtheight.restype = c_int
        gsd_get_txtheight.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 462
for _lib in _libs.values():
    if hasattr(_lib, 'do_label_display'):
        do_label_display = _lib.do_label_display
        do_label_display.restype = None
        do_label_display.argtypes = [GLuint, POINTER(c_float), String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 463
for _lib in _libs.values():
    if hasattr(_lib, 'get_txtdescender'):
        get_txtdescender = _lib.get_txtdescender
        get_txtdescender.restype = c_int
        get_txtdescender.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 464
for _lib in _libs.values():
    if hasattr(_lib, 'get_txtxoffset'):
        get_txtxoffset = _lib.get_txtxoffset
        get_txtxoffset.restype = c_int
        get_txtxoffset.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 467
for _lib in _libs.values():
    if hasattr(_lib, 'GS_write_ppm'):
        GS_write_ppm = _lib.GS_write_ppm
        GS_write_ppm.restype = c_int
        GS_write_ppm.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 468
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_init_mpeg'):
        gsd_init_mpeg = _lib.gsd_init_mpeg
        gsd_init_mpeg.restype = c_int
        gsd_init_mpeg.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 469
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_write_mpegframe'):
        gsd_write_mpegframe = _lib.gsd_write_mpegframe
        gsd_write_mpegframe.restype = c_int
        gsd_write_mpegframe.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 470
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_close_mpeg'):
        gsd_close_mpeg = _lib.gsd_close_mpeg
        gsd_close_mpeg.restype = c_int
        gsd_close_mpeg.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 473
for _lib in _libs.values():
    if hasattr(_lib, 'GS_write_tif'):
        GS_write_tif = _lib.GS_write_tif
        GS_write_tif.restype = c_int
        GS_write_tif.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 476
for _lib in _libs.values():
    if hasattr(_lib, 'gs_put_label'):
        gs_put_label = _lib.gs_put_label
        gs_put_label.restype = None
        gs_put_label.argtypes = [String, GLuint, c_int, c_ulong, POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 477
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_remove_curr'):
        gsd_remove_curr = _lib.gsd_remove_curr
        gsd_remove_curr.restype = None
        gsd_remove_curr.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 478
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_remove_all'):
        gsd_remove_all = _lib.gsd_remove_all
        gsd_remove_all.restype = None
        gsd_remove_all.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 479
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_call_label'):
        gsd_call_label = _lib.gsd_call_label
        gsd_call_label.restype = None
        gsd_call_label.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 482
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_box'):
        gsd_box = _lib.gsd_box
        gsd_box.restype = None
        gsd_box.argtypes = [POINTER(c_float), c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 483
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_plus'):
        gsd_plus = _lib.gsd_plus
        gsd_plus.restype = None
        gsd_plus.argtypes = [POINTER(c_float), c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 484
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_line_onsurf'):
        gsd_line_onsurf = _lib.gsd_line_onsurf
        gsd_line_onsurf.restype = None
        gsd_line_onsurf.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 485
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_nline_onsurf'):
        gsd_nline_onsurf = _lib.gsd_nline_onsurf
        gsd_nline_onsurf.restype = c_int
        gsd_nline_onsurf.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 486
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_x'):
        gsd_x = _lib.gsd_x
        gsd_x.restype = None
        gsd_x.argtypes = [POINTER(geosurf), POINTER(c_float), c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 487
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_diamond'):
        gsd_diamond = _lib.gsd_diamond
        gsd_diamond.restype = None
        gsd_diamond.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 488
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_diamond_lines'):
        gsd_diamond_lines = _lib.gsd_diamond_lines
        gsd_diamond_lines.restype = None
        gsd_diamond_lines.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 489
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_cube'):
        gsd_cube = _lib.gsd_cube
        gsd_cube.restype = None
        gsd_cube.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 490
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_draw_box'):
        gsd_draw_box = _lib.gsd_draw_box
        gsd_draw_box.restype = None
        gsd_draw_box.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 491
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_drawsphere'):
        gsd_drawsphere = _lib.gsd_drawsphere
        gsd_drawsphere.restype = None
        gsd_drawsphere.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 492
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_draw_asterisk'):
        gsd_draw_asterisk = _lib.gsd_draw_asterisk
        gsd_draw_asterisk.restype = None
        gsd_draw_asterisk.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 493
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_draw_gyro'):
        gsd_draw_gyro = _lib.gsd_draw_gyro
        gsd_draw_gyro.restype = None
        gsd_draw_gyro.argtypes = [POINTER(c_float), c_ulong, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 494
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_3dcursor'):
        gsd_3dcursor = _lib.gsd_3dcursor
        gsd_3dcursor.restype = None
        gsd_3dcursor.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 495
for _lib in _libs.values():
    if hasattr(_lib, 'dir_to_slope_aspect'):
        dir_to_slope_aspect = _lib.dir_to_slope_aspect
        dir_to_slope_aspect.restype = None
        dir_to_slope_aspect.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 496
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_north_arrow'):
        gsd_north_arrow = _lib.gsd_north_arrow
        gsd_north_arrow.restype = c_int
        gsd_north_arrow.argtypes = [POINTER(c_float), c_float, GLuint, c_ulong, c_ulong]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 497
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_arrow'):
        gsd_arrow = _lib.gsd_arrow
        gsd_arrow.restype = c_int
        gsd_arrow.argtypes = [POINTER(c_float), c_ulong, c_float, POINTER(c_float), c_float, POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 498
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_arrow_onsurf'):
        gsd_arrow_onsurf = _lib.gsd_arrow_onsurf
        gsd_arrow_onsurf.restype = c_int
        gsd_arrow_onsurf.argtypes = [POINTER(c_float), POINTER(c_float), c_ulong, c_int, POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 499
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_3darrow'):
        gsd_3darrow = _lib.gsd_3darrow
        gsd_3darrow.restype = None
        gsd_3darrow.argtypes = [POINTER(c_float), c_ulong, c_float, c_float, POINTER(c_float), c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 500
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_scalebar'):
        gsd_scalebar = _lib.gsd_scalebar
        gsd_scalebar.restype = c_int
        gsd_scalebar.argtypes = [POINTER(c_float), c_float, GLuint, c_ulong, c_ulong]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 501
for _lib in _libs.values():
    if hasattr(_lib, 'primitive_cone'):
        primitive_cone = _lib.primitive_cone
        primitive_cone.restype = None
        primitive_cone.argtypes = [c_ulong]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 502
for _lib in _libs.values():
    if hasattr(_lib, 'primitive_cylinder'):
        primitive_cylinder = _lib.primitive_cylinder
        primitive_cylinder.restype = None
        primitive_cylinder.argtypes = [c_ulong, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 505
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_flush'):
        gsd_flush = _lib.gsd_flush
        gsd_flush.restype = None
        gsd_flush.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 506
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_colormode'):
        gsd_colormode = _lib.gsd_colormode
        gsd_colormode.restype = None
        gsd_colormode.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 507
for _lib in _libs.values():
    if hasattr(_lib, 'show_colormode'):
        show_colormode = _lib.show_colormode
        show_colormode.restype = None
        show_colormode.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 508
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_circ'):
        gsd_circ = _lib.gsd_circ
        gsd_circ.restype = None
        gsd_circ.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 509
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_disc'):
        gsd_disc = _lib.gsd_disc
        gsd_disc.restype = None
        gsd_disc.argtypes = [c_float, c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 510
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_sphere'):
        gsd_sphere = _lib.gsd_sphere
        gsd_sphere.restype = None
        gsd_sphere.argtypes = [POINTER(c_float), c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 511
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_zwritemask'):
        gsd_zwritemask = _lib.gsd_zwritemask
        gsd_zwritemask.restype = None
        gsd_zwritemask.argtypes = [c_ulong]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 512
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_backface'):
        gsd_backface = _lib.gsd_backface
        gsd_backface.restype = None
        gsd_backface.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 513
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_linewidth'):
        gsd_linewidth = _lib.gsd_linewidth
        gsd_linewidth.restype = None
        gsd_linewidth.argtypes = [c_short]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 514
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgnqstrip'):
        gsd_bgnqstrip = _lib.gsd_bgnqstrip
        gsd_bgnqstrip.restype = None
        gsd_bgnqstrip.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 515
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endqstrip'):
        gsd_endqstrip = _lib.gsd_endqstrip
        gsd_endqstrip.restype = None
        gsd_endqstrip.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 516
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgntmesh'):
        gsd_bgntmesh = _lib.gsd_bgntmesh
        gsd_bgntmesh.restype = None
        gsd_bgntmesh.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 517
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endtmesh'):
        gsd_endtmesh = _lib.gsd_endtmesh
        gsd_endtmesh.restype = None
        gsd_endtmesh.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 518
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgntstrip'):
        gsd_bgntstrip = _lib.gsd_bgntstrip
        gsd_bgntstrip.restype = None
        gsd_bgntstrip.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 519
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endtstrip'):
        gsd_endtstrip = _lib.gsd_endtstrip
        gsd_endtstrip.restype = None
        gsd_endtstrip.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 520
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgntfan'):
        gsd_bgntfan = _lib.gsd_bgntfan
        gsd_bgntfan.restype = None
        gsd_bgntfan.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 521
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endtfan'):
        gsd_endtfan = _lib.gsd_endtfan
        gsd_endtfan.restype = None
        gsd_endtfan.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 522
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_swaptmesh'):
        gsd_swaptmesh = _lib.gsd_swaptmesh
        gsd_swaptmesh.restype = None
        gsd_swaptmesh.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 523
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgnpolygon'):
        gsd_bgnpolygon = _lib.gsd_bgnpolygon
        gsd_bgnpolygon.restype = None
        gsd_bgnpolygon.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 524
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endpolygon'):
        gsd_endpolygon = _lib.gsd_endpolygon
        gsd_endpolygon.restype = None
        gsd_endpolygon.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 525
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgnline'):
        gsd_bgnline = _lib.gsd_bgnline
        gsd_bgnline.restype = None
        gsd_bgnline.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 526
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endline'):
        gsd_endline = _lib.gsd_endline
        gsd_endline.restype = None
        gsd_endline.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 527
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_shademodel'):
        gsd_shademodel = _lib.gsd_shademodel
        gsd_shademodel.restype = None
        gsd_shademodel.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 528
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_getshademodel'):
        gsd_getshademodel = _lib.gsd_getshademodel
        gsd_getshademodel.restype = c_int
        gsd_getshademodel.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 529
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bothbuffer'):
        gsd_bothbuffer = _lib.gsd_bothbuffer
        gsd_bothbuffer.restype = None
        gsd_bothbuffer.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 530
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_frontbuffer'):
        gsd_frontbuffer = _lib.gsd_frontbuffer
        gsd_frontbuffer.restype = None
        gsd_frontbuffer.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 531
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_backbuffer'):
        gsd_backbuffer = _lib.gsd_backbuffer
        gsd_backbuffer.restype = None
        gsd_backbuffer.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 532
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_swapbuffers'):
        gsd_swapbuffers = _lib.gsd_swapbuffers
        gsd_swapbuffers.restype = None
        gsd_swapbuffers.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 533
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_popmatrix'):
        gsd_popmatrix = _lib.gsd_popmatrix
        gsd_popmatrix.restype = None
        gsd_popmatrix.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 534
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_pushmatrix'):
        gsd_pushmatrix = _lib.gsd_pushmatrix
        gsd_pushmatrix.restype = None
        gsd_pushmatrix.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 535
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_scale'):
        gsd_scale = _lib.gsd_scale
        gsd_scale.restype = None
        gsd_scale.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 536
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_translate'):
        gsd_translate = _lib.gsd_translate
        gsd_translate.restype = None
        gsd_translate.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 537
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_rot'):
        gsd_rot = _lib.gsd_rot
        gsd_rot.restype = None
        gsd_rot.argtypes = [c_float, c_char]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 538
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_checkwindow'):
        gsd_checkwindow = _lib.gsd_checkwindow
        gsd_checkwindow.restype = None
        gsd_checkwindow.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 539
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_checkpoint'):
        gsd_checkpoint = _lib.gsd_checkpoint
        gsd_checkpoint.restype = c_int
        gsd_checkpoint.argtypes = [POINTER(c_float), POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 540
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_litvert_func'):
        gsd_litvert_func = _lib.gsd_litvert_func
        gsd_litvert_func.restype = None
        gsd_litvert_func.argtypes = [POINTER(c_float), c_ulong, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 541
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_litvert_func2'):
        gsd_litvert_func2 = _lib.gsd_litvert_func2
        gsd_litvert_func2.restype = None
        gsd_litvert_func2.argtypes = [POINTER(c_float), c_ulong, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 542
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_vert_func'):
        gsd_vert_func = _lib.gsd_vert_func
        gsd_vert_func.restype = None
        gsd_vert_func.argtypes = [POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 543
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_color_func'):
        gsd_color_func = _lib.gsd_color_func
        gsd_color_func.restype = None
        gsd_color_func.argtypes = [c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 544
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_init_lightmodel'):
        gsd_init_lightmodel = _lib.gsd_init_lightmodel
        gsd_init_lightmodel.restype = None
        gsd_init_lightmodel.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 545
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_set_material'):
        gsd_set_material = _lib.gsd_set_material
        gsd_set_material.restype = None
        gsd_set_material.argtypes = [c_int, c_int, c_float, c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 546
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_deflight'):
        gsd_deflight = _lib.gsd_deflight
        gsd_deflight.restype = None
        gsd_deflight.argtypes = [c_int, POINTER(struct_lightdefs)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 547
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_switchlight'):
        gsd_switchlight = _lib.gsd_switchlight
        gsd_switchlight.restype = None
        gsd_switchlight.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 548
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_getimage'):
        gsd_getimage = _lib.gsd_getimage
        gsd_getimage.restype = c_int
        gsd_getimage.argtypes = [POINTER(POINTER(c_ubyte)), POINTER(c_uint), POINTER(c_uint)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 549
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_blend'):
        gsd_blend = _lib.gsd_blend
        gsd_blend.restype = None
        gsd_blend.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 550
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_def_clipplane'):
        gsd_def_clipplane = _lib.gsd_def_clipplane
        gsd_def_clipplane.restype = None
        gsd_def_clipplane.argtypes = [c_int, POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 551
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_set_clipplane'):
        gsd_set_clipplane = _lib.gsd_set_clipplane
        gsd_set_clipplane.restype = None
        gsd_set_clipplane.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 552
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_finish'):
        gsd_finish = _lib.gsd_finish
        gsd_finish.restype = None
        gsd_finish.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 553
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_viewport'):
        gsd_viewport = _lib.gsd_viewport
        gsd_viewport.restype = None
        gsd_viewport.argtypes = [c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 554
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_makelist'):
        gsd_makelist = _lib.gsd_makelist
        gsd_makelist.restype = c_int
        gsd_makelist.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 555
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgnlist'):
        gsd_bgnlist = _lib.gsd_bgnlist
        gsd_bgnlist.restype = None
        gsd_bgnlist.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 556
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_endlist'):
        gsd_endlist = _lib.gsd_endlist
        gsd_endlist.restype = None
        gsd_endlist.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 557
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_calllist'):
        gsd_calllist = _lib.gsd_calllist
        gsd_calllist.restype = None
        gsd_calllist.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 558
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_deletelist'):
        gsd_deletelist = _lib.gsd_deletelist
        gsd_deletelist.restype = None
        gsd_deletelist.argtypes = [GLuint, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 559
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_calllists'):
        gsd_calllists = _lib.gsd_calllists
        gsd_calllists.restype = None
        gsd_calllists.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 560
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_getwindow'):
        gsd_getwindow = _lib.gsd_getwindow
        gsd_getwindow.restype = None
        gsd_getwindow.argtypes = [POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 561
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_writeView'):
        gsd_writeView = _lib.gsd_writeView
        gsd_writeView.restype = c_int
        gsd_writeView.argtypes = [POINTER(POINTER(c_ubyte)), c_uint, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 564
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_surf'):
        gsd_surf = _lib.gsd_surf
        gsd_surf.restype = c_int
        gsd_surf.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 565
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_surf_map'):
        gsd_surf_map = _lib.gsd_surf_map
        gsd_surf_map.restype = c_int
        gsd_surf_map.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 566
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_surf_const'):
        gsd_surf_const = _lib.gsd_surf_const
        gsd_surf_const.restype = c_int
        gsd_surf_const.argtypes = [POINTER(geosurf), c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 567
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_surf_func'):
        gsd_surf_func = _lib.gsd_surf_func
        gsd_surf_func.restype = c_int
        gsd_surf_func.argtypes = [POINTER(geosurf), CFUNCTYPE(UNCHECKED(c_int), )]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 568
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_triangulated_wall'):
        gsd_triangulated_wall = _lib.gsd_triangulated_wall
        gsd_triangulated_wall.restype = c_int
        gsd_triangulated_wall.argtypes = [c_int, c_int, POINTER(geosurf), POINTER(geosurf), POINTER(Point3), POINTER(Point3), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 570
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_setfc'):
        gsd_setfc = _lib.gsd_setfc
        gsd_setfc.restype = None
        gsd_setfc.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 571
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_getfc'):
        gsd_getfc = _lib.gsd_getfc
        gsd_getfc.restype = c_int
        gsd_getfc.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 572
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_ortho_wall'):
        gsd_ortho_wall = _lib.gsd_ortho_wall
        gsd_ortho_wall.restype = c_int
        gsd_ortho_wall.argtypes = [c_int, c_int, POINTER(POINTER(geosurf)), POINTER(POINTER(Point3)), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 573
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wall'):
        gsd_wall = _lib.gsd_wall
        gsd_wall.restype = c_int
        gsd_wall.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 574
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_norm_arrows'):
        gsd_norm_arrows = _lib.gsd_norm_arrows
        gsd_norm_arrows.restype = c_int
        gsd_norm_arrows.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 577
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_los'):
        gsd_get_los = _lib.gsd_get_los
        gsd_get_los.restype = c_int
        gsd_get_los.argtypes = [POINTER(c_float * 3), c_short, c_short]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 578
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_set_view'):
        gsd_set_view = _lib.gsd_set_view
        gsd_set_view.restype = None
        gsd_set_view.argtypes = [POINTER(geoview), POINTER(geodisplay)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 579
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_check_focus'):
        gsd_check_focus = _lib.gsd_check_focus
        gsd_check_focus.restype = None
        gsd_check_focus.argtypes = [POINTER(geoview)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 580
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_get_zup'):
        gsd_get_zup = _lib.gsd_get_zup
        gsd_get_zup.restype = None
        gsd_get_zup.argtypes = [POINTER(geoview), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 581
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_zup_twist'):
        gsd_zup_twist = _lib.gsd_zup_twist
        gsd_zup_twist.restype = c_int
        gsd_zup_twist.argtypes = [POINTER(geoview)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 582
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_do_scale'):
        gsd_do_scale = _lib.gsd_do_scale
        gsd_do_scale.restype = None
        gsd_do_scale.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 583
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_real2model'):
        gsd_real2model = _lib.gsd_real2model
        gsd_real2model.restype = None
        gsd_real2model.argtypes = [Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 584
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_model2real'):
        gsd_model2real = _lib.gsd_model2real
        gsd_model2real.restype = None
        gsd_model2real.argtypes = [Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 585
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_model2surf'):
        gsd_model2surf = _lib.gsd_model2surf
        gsd_model2surf.restype = None
        gsd_model2surf.argtypes = [POINTER(geosurf), Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 586
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_surf2real'):
        gsd_surf2real = _lib.gsd_surf2real
        gsd_surf2real.restype = None
        gsd_surf2real.argtypes = [POINTER(geosurf), Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 587
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_real2surf'):
        gsd_real2surf = _lib.gsd_real2surf
        gsd_real2surf.restype = None
        gsd_real2surf.argtypes = [POINTER(geosurf), Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 590
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wire_surf'):
        gsd_wire_surf = _lib.gsd_wire_surf
        gsd_wire_surf.restype = c_int
        gsd_wire_surf.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 591
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wire_surf_map'):
        gsd_wire_surf_map = _lib.gsd_wire_surf_map
        gsd_wire_surf_map.restype = c_int
        gsd_wire_surf_map.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 592
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_coarse_surf_map'):
        gsd_coarse_surf_map = _lib.gsd_coarse_surf_map
        gsd_coarse_surf_map.restype = c_int
        gsd_coarse_surf_map.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 593
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wire_surf_const'):
        gsd_wire_surf_const = _lib.gsd_wire_surf_const
        gsd_wire_surf_const.restype = c_int
        gsd_wire_surf_const.argtypes = [POINTER(geosurf), c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 594
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wire_surf_func'):
        gsd_wire_surf_func = _lib.gsd_wire_surf_func
        gsd_wire_surf_func.restype = c_int
        gsd_wire_surf_func.argtypes = [POINTER(geosurf), CFUNCTYPE(UNCHECKED(c_int), )]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 595
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_wire_arrows'):
        gsd_wire_arrows = _lib.gsd_wire_arrows
        gsd_wire_arrows.restype = c_int
        gsd_wire_arrows.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 598
for _lib in _libs.values():
    if hasattr(_lib, 'gsdiff_set_SDscale'):
        gsdiff_set_SDscale = _lib.gsdiff_set_SDscale
        gsdiff_set_SDscale.restype = None
        gsdiff_set_SDscale.argtypes = [c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 599
for _lib in _libs.values():
    if hasattr(_lib, 'gsdiff_get_SDscale'):
        gsdiff_get_SDscale = _lib.gsdiff_get_SDscale
        gsdiff_get_SDscale.restype = c_float
        gsdiff_get_SDscale.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 600
for _lib in _libs.values():
    if hasattr(_lib, 'gsdiff_set_SDref'):
        gsdiff_set_SDref = _lib.gsdiff_set_SDref
        gsdiff_set_SDref.restype = None
        gsdiff_set_SDref.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 601
for _lib in _libs.values():
    if hasattr(_lib, 'gsdiff_get_SDref'):
        gsdiff_get_SDref = _lib.gsdiff_get_SDref
        gsdiff_get_SDref.restype = POINTER(geosurf)
        gsdiff_get_SDref.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 602
for _lib in _libs.values():
    if hasattr(_lib, 'gsdiff_do_SD'):
        gsdiff_do_SD = _lib.gsdiff_do_SD
        gsdiff_do_SD.restype = c_float
        gsdiff_do_SD.argtypes = [c_float, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 605
for _lib in _libs.values():
    if hasattr(_lib, 'gsdrape_set_surface'):
        gsdrape_set_surface = _lib.gsdrape_set_surface
        gsdrape_set_surface.restype = c_int
        gsdrape_set_surface.argtypes = [POINTER(geosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 606
for _lib in _libs.values():
    if hasattr(_lib, 'seg_intersect_vregion'):
        seg_intersect_vregion = _lib.seg_intersect_vregion
        seg_intersect_vregion.restype = c_int
        seg_intersect_vregion.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 607
for _lib in _libs.values():
    if hasattr(_lib, 'gsdrape_get_segments'):
        gsdrape_get_segments = _lib.gsdrape_get_segments
        gsdrape_get_segments.restype = POINTER(Point3)
        gsdrape_get_segments.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 608
for _lib in _libs.values():
    if hasattr(_lib, 'gsdrape_get_allsegments'):
        gsdrape_get_allsegments = _lib.gsdrape_get_allsegments
        gsdrape_get_allsegments.restype = POINTER(Point3)
        gsdrape_get_allsegments.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 609
for _lib in _libs.values():
    if hasattr(_lib, 'interp_first_last'):
        interp_first_last = _lib.interp_first_last
        interp_first_last.restype = None
        interp_first_last.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), Point3, Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 610
for _lib in _libs.values():
    if hasattr(_lib, '_viewcell_tri_interp'):
        _viewcell_tri_interp = _lib._viewcell_tri_interp
        _viewcell_tri_interp.restype = c_int
        _viewcell_tri_interp.argtypes = [POINTER(geosurf), Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 611
for _lib in _libs.values():
    if hasattr(_lib, 'viewcell_tri_interp'):
        viewcell_tri_interp = _lib.viewcell_tri_interp
        viewcell_tri_interp.restype = c_int
        viewcell_tri_interp.argtypes = [POINTER(geosurf), POINTER(typbuff), Point3, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 612
for _lib in _libs.values():
    if hasattr(_lib, 'in_vregion'):
        in_vregion = _lib.in_vregion
        in_vregion.restype = c_int
        in_vregion.argtypes = [POINTER(geosurf), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 613
for _lib in _libs.values():
    if hasattr(_lib, 'order_intersects'):
        order_intersects = _lib.order_intersects
        order_intersects.restype = c_int
        order_intersects.argtypes = [POINTER(geosurf), Point3, Point3, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 614
for _lib in _libs.values():
    if hasattr(_lib, 'get_vert_intersects'):
        get_vert_intersects = _lib.get_vert_intersects
        get_vert_intersects.restype = c_int
        get_vert_intersects.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 615
for _lib in _libs.values():
    if hasattr(_lib, 'get_horz_intersects'):
        get_horz_intersects = _lib.get_horz_intersects
        get_horz_intersects.restype = c_int
        get_horz_intersects.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 616
for _lib in _libs.values():
    if hasattr(_lib, 'get_diag_intersects'):
        get_diag_intersects = _lib.get_diag_intersects
        get_diag_intersects.restype = c_int
        get_diag_intersects.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 617
for _lib in _libs.values():
    if hasattr(_lib, 'segs_intersect'):
        segs_intersect = _lib.segs_intersect
        segs_intersect.restype = c_int
        segs_intersect.argtypes = [c_float, c_float, c_float, c_float, c_float, c_float, c_float, c_float, POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 619
for _lib in _libs.values():
    if hasattr(_lib, 'Point_on_plane'):
        Point_on_plane = _lib.Point_on_plane
        Point_on_plane.restype = c_int
        Point_on_plane.argtypes = [Point3, Point3, Point3, Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 620
for _lib in _libs.values():
    if hasattr(_lib, 'XY_intersect_plane'):
        XY_intersect_plane = _lib.XY_intersect_plane
        XY_intersect_plane.restype = c_int
        XY_intersect_plane.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 621
for _lib in _libs.values():
    if hasattr(_lib, 'P3toPlane'):
        P3toPlane = _lib.P3toPlane
        P3toPlane.restype = c_int
        P3toPlane.argtypes = [Point3, Point3, Point3, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 622
for _lib in _libs.values():
    if hasattr(_lib, 'V3Cross'):
        V3Cross = _lib.V3Cross
        V3Cross.restype = c_int
        V3Cross.argtypes = [Point3, Point3, Point3]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 625
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_findh'):
        gsds_findh = _lib.gsds_findh
        gsds_findh.restype = c_int
        gsds_findh.argtypes = [String, POINTER(c_uint), POINTER(c_uint), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 626
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_newh'):
        gsds_newh = _lib.gsds_newh
        gsds_newh.restype = c_int
        gsds_newh.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 627
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_get_typbuff'):
        gsds_get_typbuff = _lib.gsds_get_typbuff
        gsds_get_typbuff.restype = POINTER(typbuff)
        gsds_get_typbuff.argtypes = [c_int, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 628
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_get_name'):
        gsds_get_name = _lib.gsds_get_name
        gsds_get_name.restype = ReturnString
        gsds_get_name.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 629
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_free_datah'):
        gsds_free_datah = _lib.gsds_free_datah
        gsds_free_datah.restype = c_int
        gsds_free_datah.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 630
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_free_data_buff'):
        gsds_free_data_buff = _lib.gsds_free_data_buff
        gsds_free_data_buff.restype = c_int
        gsds_free_data_buff.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 631
for _lib in _libs.values():
    if hasattr(_lib, 'free_data_buffs'):
        free_data_buffs = _lib.free_data_buffs
        free_data_buffs.restype = c_int
        free_data_buffs.argtypes = [POINTER(dataset), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 632
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_alloc_typbuff'):
        gsds_alloc_typbuff = _lib.gsds_alloc_typbuff
        gsds_alloc_typbuff.restype = c_int
        gsds_alloc_typbuff.argtypes = [c_int, POINTER(c_int), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 633
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_get_changed'):
        gsds_get_changed = _lib.gsds_get_changed
        gsds_get_changed.restype = c_int
        gsds_get_changed.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 634
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_set_changed'):
        gsds_set_changed = _lib.gsds_set_changed
        gsds_set_changed.restype = c_int
        gsds_set_changed.argtypes = [c_int, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 635
for _lib in _libs.values():
    if hasattr(_lib, 'gsds_get_type'):
        gsds_get_type = _lib.gsds_get_type
        gsds_get_type.restype = c_int
        gsds_get_type.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 638
for _lib in _libs.values():
    if hasattr(_lib, 'get_mapatt'):
        get_mapatt = _lib.get_mapatt
        get_mapatt.restype = c_int
        get_mapatt.argtypes = [POINTER(typbuff), c_int, POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 641
for _lib in _libs.values():
    if hasattr(_lib, 'gv_get_vect'):
        gv_get_vect = _lib.gv_get_vect
        gv_get_vect.restype = POINTER(geovect)
        gv_get_vect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 642
for _lib in _libs.values():
    if hasattr(_lib, 'gv_get_prev_vect'):
        gv_get_prev_vect = _lib.gv_get_prev_vect
        gv_get_prev_vect.restype = POINTER(geovect)
        gv_get_prev_vect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 643
for _lib in _libs.values():
    if hasattr(_lib, 'gv_num_vects'):
        gv_num_vects = _lib.gv_num_vects
        gv_num_vects.restype = c_int
        gv_num_vects.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 644
for _lib in _libs.values():
    if hasattr(_lib, 'gv_get_last_vect'):
        gv_get_last_vect = _lib.gv_get_last_vect
        gv_get_last_vect.restype = POINTER(geovect)
        gv_get_last_vect.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 645
for _lib in _libs.values():
    if hasattr(_lib, 'gv_get_new_vect'):
        gv_get_new_vect = _lib.gv_get_new_vect
        gv_get_new_vect.restype = POINTER(geovect)
        gv_get_new_vect.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 646
for _lib in _libs.values():
    if hasattr(_lib, 'gv_update_drapesurfs'):
        gv_update_drapesurfs = _lib.gv_update_drapesurfs
        gv_update_drapesurfs.restype = None
        gv_update_drapesurfs.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 647
for _lib in _libs.values():
    if hasattr(_lib, 'gv_set_defaults'):
        gv_set_defaults = _lib.gv_set_defaults
        gv_set_defaults.restype = c_int
        gv_set_defaults.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 648
for _lib in _libs.values():
    if hasattr(_lib, 'gv_init_vect'):
        gv_init_vect = _lib.gv_init_vect
        gv_init_vect.restype = c_int
        gv_init_vect.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 649
for _lib in _libs.values():
    if hasattr(_lib, 'gv_delete_vect'):
        gv_delete_vect = _lib.gv_delete_vect
        gv_delete_vect.restype = None
        gv_delete_vect.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 650
for _lib in _libs.values():
    if hasattr(_lib, 'gv_free_vect'):
        gv_free_vect = _lib.gv_free_vect
        gv_free_vect.restype = c_int
        gv_free_vect.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 651
for _lib in _libs.values():
    if hasattr(_lib, 'gv_free_vectmem'):
        gv_free_vectmem = _lib.gv_free_vectmem
        gv_free_vectmem.restype = None
        gv_free_vectmem.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 652
for _lib in _libs.values():
    if hasattr(_lib, 'gv_set_drapesurfs'):
        gv_set_drapesurfs = _lib.gv_set_drapesurfs
        gv_set_drapesurfs.restype = None
        gv_set_drapesurfs.argtypes = [POINTER(geovect), POINTER(c_int), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 655
for _lib in _libs.values():
    if hasattr(_lib, 'gv_line_length'):
        gv_line_length = _lib.gv_line_length
        gv_line_length.restype = c_float
        gv_line_length.argtypes = [POINTER(geoline)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 656
for _lib in _libs.values():
    if hasattr(_lib, 'gln_num_points'):
        gln_num_points = _lib.gln_num_points
        gln_num_points.restype = c_int
        gln_num_points.argtypes = [POINTER(geoline)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 657
for _lib in _libs.values():
    if hasattr(_lib, 'gv_num_points'):
        gv_num_points = _lib.gv_num_points
        gv_num_points.restype = c_int
        gv_num_points.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 658
for _lib in _libs.values():
    if hasattr(_lib, 'gv_decimate_lines'):
        gv_decimate_lines = _lib.gv_decimate_lines
        gv_decimate_lines.restype = c_int
        gv_decimate_lines.argtypes = [POINTER(geovect)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 661
for _lib in _libs.values():
    if hasattr(_lib, 'gs_clip_segment'):
        gs_clip_segment = _lib.gs_clip_segment
        gs_clip_segment.restype = c_int
        gs_clip_segment.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 662
for _lib in _libs.values():
    if hasattr(_lib, 'gvd_vect'):
        gvd_vect = _lib.gvd_vect
        gvd_vect.restype = c_int
        gvd_vect.argtypes = [POINTER(geovect), POINTER(geosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 663
for _lib in _libs.values():
    if hasattr(_lib, 'gvd_draw_lineonsurf'):
        gvd_draw_lineonsurf = _lib.gvd_draw_lineonsurf
        gvd_draw_lineonsurf.restype = None
        gvd_draw_lineonsurf.argtypes = [POINTER(geosurf), POINTER(c_float), POINTER(c_float), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 666
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_vol'):
        gvl_get_vol = _lib.gvl_get_vol
        gvl_get_vol.restype = POINTER(geovol)
        gvl_get_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 667
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_prev_vol'):
        gvl_get_prev_vol = _lib.gvl_get_prev_vol
        gvl_get_prev_vol.restype = POINTER(geovol)
        gvl_get_prev_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 668
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_getall_vols'):
        gvl_getall_vols = _lib.gvl_getall_vols
        gvl_getall_vols.restype = c_int
        gvl_getall_vols.argtypes = [POINTER(POINTER(geovol))]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 669
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_num_vols'):
        gvl_num_vols = _lib.gvl_num_vols
        gvl_num_vols.restype = c_int
        gvl_num_vols.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 670
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_last_vol'):
        gvl_get_last_vol = _lib.gvl_get_last_vol
        gvl_get_last_vol.restype = POINTER(geovol)
        gvl_get_last_vol.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 671
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_new_vol'):
        gvl_get_new_vol = _lib.gvl_get_new_vol
        gvl_get_new_vol.restype = POINTER(geovol)
        gvl_get_new_vol.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 672
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_init_vol'):
        gvl_init_vol = _lib.gvl_init_vol
        gvl_init_vol.restype = c_int
        gvl_init_vol.argtypes = [POINTER(geovol), c_double, c_double, c_double, c_int, c_int, c_int, c_double, c_double, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 674
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_delete_vol'):
        gvl_delete_vol = _lib.gvl_delete_vol
        gvl_delete_vol.restype = None
        gvl_delete_vol.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 675
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_free_vol'):
        gvl_free_vol = _lib.gvl_free_vol
        gvl_free_vol.restype = c_int
        gvl_free_vol.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 676
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_free_volmem'):
        gvl_free_volmem = _lib.gvl_free_volmem
        gvl_free_volmem.restype = None
        gvl_free_volmem.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 677
for _lib in _libs.values():
    if hasattr(_lib, 'print_vol_fields'):
        print_vol_fields = _lib.print_vol_fields
        print_vol_fields.restype = None
        print_vol_fields.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 678
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_xextents'):
        gvl_get_xextents = _lib.gvl_get_xextents
        gvl_get_xextents.restype = c_int
        gvl_get_xextents.argtypes = [POINTER(geovol), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 679
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_yextents'):
        gvl_get_yextents = _lib.gvl_get_yextents
        gvl_get_yextents.restype = c_int
        gvl_get_yextents.argtypes = [POINTER(geovol), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 680
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_zextents'):
        gvl_get_zextents = _lib.gvl_get_zextents
        gvl_get_zextents.restype = c_int
        gvl_get_zextents.argtypes = [POINTER(geovol), POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 681
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_xrange'):
        gvl_get_xrange = _lib.gvl_get_xrange
        gvl_get_xrange.restype = c_int
        gvl_get_xrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 682
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_yrange'):
        gvl_get_yrange = _lib.gvl_get_yrange
        gvl_get_yrange.restype = c_int
        gvl_get_yrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 683
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_get_zrange'):
        gvl_get_zrange = _lib.gvl_get_zrange
        gvl_get_zrange.restype = c_int
        gvl_get_zrange.argtypes = [POINTER(c_float), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 685
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_init'):
        gvl_isosurf_init = _lib.gvl_isosurf_init
        gvl_isosurf_init.restype = c_int
        gvl_isosurf_init.argtypes = [POINTER(geovol_isosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 686
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_freemem'):
        gvl_isosurf_freemem = _lib.gvl_isosurf_freemem
        gvl_isosurf_freemem.restype = c_int
        gvl_isosurf_freemem.argtypes = [POINTER(geovol_isosurf)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 687
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_get_isosurf'):
        gvl_isosurf_get_isosurf = _lib.gvl_isosurf_get_isosurf
        gvl_isosurf_get_isosurf.restype = POINTER(geovol_isosurf)
        gvl_isosurf_get_isosurf.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 688
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_get_att_src'):
        gvl_isosurf_get_att_src = _lib.gvl_isosurf_get_att_src
        gvl_isosurf_get_att_src.restype = c_int
        gvl_isosurf_get_att_src.argtypes = [POINTER(geovol_isosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 689
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_set_att_src'):
        gvl_isosurf_set_att_src = _lib.gvl_isosurf_set_att_src
        gvl_isosurf_set_att_src.restype = c_int
        gvl_isosurf_set_att_src.argtypes = [POINTER(geovol_isosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 690
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_set_att_const'):
        gvl_isosurf_set_att_const = _lib.gvl_isosurf_set_att_const
        gvl_isosurf_set_att_const.restype = c_int
        gvl_isosurf_set_att_const.argtypes = [POINTER(geovol_isosurf), c_int, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 691
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_set_att_map'):
        gvl_isosurf_set_att_map = _lib.gvl_isosurf_set_att_map
        gvl_isosurf_set_att_map.restype = c_int
        gvl_isosurf_set_att_map.argtypes = [POINTER(geovol_isosurf), c_int, String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 692
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_set_att_changed'):
        gvl_isosurf_set_att_changed = _lib.gvl_isosurf_set_att_changed
        gvl_isosurf_set_att_changed.restype = c_int
        gvl_isosurf_set_att_changed.argtypes = [POINTER(geovol_isosurf), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 694
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_slice_init'):
        gvl_slice_init = _lib.gvl_slice_init
        gvl_slice_init.restype = c_int
        gvl_slice_init.argtypes = [POINTER(geovol_slice)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 695
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_slice_get_slice'):
        gvl_slice_get_slice = _lib.gvl_slice_get_slice
        gvl_slice_get_slice.restype = POINTER(geovol_slice)
        gvl_slice_get_slice.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 696
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_slice_freemem'):
        gvl_slice_freemem = _lib.gvl_slice_freemem
        gvl_slice_freemem.restype = c_int
        gvl_slice_freemem.argtypes = [POINTER(geovol_slice)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 699
for _lib in _libs.values():
    if hasattr(_lib, 'P_scale'):
        P_scale = _lib.P_scale
        P_scale.restype = None
        P_scale.argtypes = [c_float, c_float, c_float]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 700
for _lib in _libs.values():
    if hasattr(_lib, 'P_transform'):
        P_transform = _lib.P_transform
        P_transform.restype = None
        P_transform.argtypes = [c_int, POINTER(c_float * 4), POINTER(c_float * 4)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 701
for _lib in _libs.values():
    if hasattr(_lib, 'P_pushmatrix'):
        P_pushmatrix = _lib.P_pushmatrix
        P_pushmatrix.restype = c_int
        P_pushmatrix.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 702
for _lib in _libs.values():
    if hasattr(_lib, 'P_popmatrix'):
        P_popmatrix = _lib.P_popmatrix
        P_popmatrix.restype = c_int
        P_popmatrix.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 703
for _lib in _libs.values():
    if hasattr(_lib, 'P_rot'):
        P_rot = _lib.P_rot
        P_rot.restype = None
        P_rot.argtypes = [c_float, c_char]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 706
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_volfile'):
        gvl_file_get_volfile = _lib.gvl_file_get_volfile
        gvl_file_get_volfile.restype = POINTER(geovol_file)
        gvl_file_get_volfile.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 707
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_name'):
        gvl_file_get_name = _lib.gvl_file_get_name
        gvl_file_get_name.restype = ReturnString
        gvl_file_get_name.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 708
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_file_type'):
        gvl_file_get_file_type = _lib.gvl_file_get_file_type
        gvl_file_get_file_type.restype = c_int
        gvl_file_get_file_type.argtypes = [POINTER(geovol_file)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 709
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_data_type'):
        gvl_file_get_data_type = _lib.gvl_file_get_data_type
        gvl_file_get_data_type.restype = c_int
        gvl_file_get_data_type.argtypes = [POINTER(geovol_file)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 710
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_newh'):
        gvl_file_newh = _lib.gvl_file_newh
        gvl_file_newh.restype = c_int
        gvl_file_newh.argtypes = [String, c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 711
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_free_datah'):
        gvl_file_free_datah = _lib.gvl_file_free_datah
        gvl_file_free_datah.restype = c_int
        gvl_file_free_datah.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 712
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_start_read'):
        gvl_file_start_read = _lib.gvl_file_start_read
        gvl_file_start_read.restype = c_int
        gvl_file_start_read.argtypes = [POINTER(geovol_file)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 713
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_end_read'):
        gvl_file_end_read = _lib.gvl_file_end_read
        gvl_file_end_read.restype = c_int
        gvl_file_end_read.argtypes = [POINTER(geovol_file)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 714
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_value'):
        gvl_file_get_value = _lib.gvl_file_get_value
        gvl_file_get_value.restype = c_int
        gvl_file_get_value.argtypes = [POINTER(geovol_file), c_int, c_int, c_int, POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 715
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_is_null_value'):
        gvl_file_is_null_value = _lib.gvl_file_is_null_value
        gvl_file_is_null_value.restype = c_int
        gvl_file_is_null_value.argtypes = [POINTER(geovol_file), POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 716
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_set_mode'):
        gvl_file_set_mode = _lib.gvl_file_set_mode
        gvl_file_set_mode.restype = c_int
        gvl_file_set_mode.argtypes = [POINTER(geovol_file), c_uint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 717
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_set_slices_param'):
        gvl_file_set_slices_param = _lib.gvl_file_set_slices_param
        gvl_file_set_slices_param.restype = c_int
        gvl_file_set_slices_param.argtypes = [POINTER(geovol_file), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 718
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_file_get_min_max'):
        gvl_file_get_min_max = _lib.gvl_file_get_min_max
        gvl_file_get_min_max.restype = None
        gvl_file_get_min_max.argtypes = [POINTER(geovol_file), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 721
for _lib in _libs.values():
    if hasattr(_lib, 'Gvl_load_colors_data'):
        Gvl_load_colors_data = _lib.Gvl_load_colors_data
        Gvl_load_colors_data.restype = c_int
        Gvl_load_colors_data.argtypes = [POINTER(POINTER(None)), String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 722
for _lib in _libs.values():
    if hasattr(_lib, 'Gvl_unload_colors_data'):
        Gvl_unload_colors_data = _lib.Gvl_unload_colors_data
        Gvl_unload_colors_data.restype = c_int
        Gvl_unload_colors_data.argtypes = [POINTER(None)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 723
for _lib in _libs.values():
    if hasattr(_lib, 'Gvl_get_color_for_value'):
        Gvl_get_color_for_value = _lib.Gvl_get_color_for_value
        Gvl_get_color_for_value.restype = c_int
        Gvl_get_color_for_value.argtypes = [POINTER(None), POINTER(c_float)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 726
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_isosurf_calc'):
        gvl_isosurf_calc = _lib.gvl_isosurf_calc
        gvl_isosurf_calc.restype = c_int
        gvl_isosurf_calc.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 727
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_slices_calc'):
        gvl_slices_calc = _lib.gvl_slices_calc
        gvl_slices_calc.restype = c_int
        gvl_slices_calc.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 728
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_write_char'):
        gvl_write_char = _lib.gvl_write_char
        gvl_write_char.restype = None
        gvl_write_char.argtypes = [c_int, POINTER(POINTER(c_ubyte)), c_ubyte]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 729
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_read_char'):
        gvl_read_char = _lib.gvl_read_char
        gvl_read_char.restype = c_ubyte
        gvl_read_char.argtypes = [c_int, POINTER(c_ubyte)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 730
for _lib in _libs.values():
    if hasattr(_lib, 'gvl_align_data'):
        gvl_align_data = _lib.gvl_align_data
        gvl_align_data.restype = None
        gvl_align_data.argtypes = [c_int, POINTER(c_ubyte)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 733
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_vol'):
        gvld_vol = _lib.gvld_vol
        gvld_vol.restype = c_int
        gvld_vol.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 734
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_wire_vol'):
        gvld_wire_vol = _lib.gvld_wire_vol
        gvld_wire_vol.restype = c_int
        gvld_wire_vol.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 735
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_isosurf'):
        gvld_isosurf = _lib.gvld_isosurf
        gvld_isosurf.restype = c_int
        gvld_isosurf.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 736
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_wire_isosurf'):
        gvld_wire_isosurf = _lib.gvld_wire_isosurf
        gvld_wire_isosurf.restype = c_int
        gvld_wire_isosurf.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 737
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_slices'):
        gvld_slices = _lib.gvld_slices
        gvld_slices.restype = c_int
        gvld_slices.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 738
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_slice'):
        gvld_slice = _lib.gvld_slice
        gvld_slice.restype = c_int
        gvld_slice.argtypes = [POINTER(geovol), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 739
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_wire_slices'):
        gvld_wire_slices = _lib.gvld_wire_slices
        gvld_wire_slices.restype = c_int
        gvld_wire_slices.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 740
for _lib in _libs.values():
    if hasattr(_lib, 'gvld_wind3_box'):
        gvld_wind3_box = _lib.gvld_wind3_box
        gvld_wind3_box.restype = c_int
        gvld_wind3_box.argtypes = [POINTER(geovol)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 743
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_display_fringe'):
        gsd_display_fringe = _lib.gsd_display_fringe
        gsd_display_fringe.restype = None
        gsd_display_fringe.argtypes = [POINTER(geosurf), c_ulong, c_float, c_int * 4]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 744
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_fringe_horiz_poly'):
        gsd_fringe_horiz_poly = _lib.gsd_fringe_horiz_poly
        gsd_fringe_horiz_poly.restype = None
        gsd_fringe_horiz_poly.argtypes = [c_float, POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 745
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_fringe_horiz_line'):
        gsd_fringe_horiz_line = _lib.gsd_fringe_horiz_line
        gsd_fringe_horiz_line.restype = None
        gsd_fringe_horiz_line.argtypes = [c_float, POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 746
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_fringe_vert_poly'):
        gsd_fringe_vert_poly = _lib.gsd_fringe_vert_poly
        gsd_fringe_vert_poly.restype = None
        gsd_fringe_vert_poly.argtypes = [c_float, POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 747
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_fringe_vert_line'):
        gsd_fringe_vert_line = _lib.gsd_fringe_vert_line
        gsd_fringe_vert_line.restype = None
        gsd_fringe_vert_line.argtypes = [c_float, POINTER(geosurf), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 750
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_put_legend'):
        gsd_put_legend = _lib.gsd_put_legend
        gsd_put_legend.restype = GLuint
        gsd_put_legend.argtypes = [String, GLuint, c_int, POINTER(c_int), POINTER(c_float), POINTER(c_int)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 751
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_bgn_legend_viewport'):
        gsd_bgn_legend_viewport = _lib.gsd_bgn_legend_viewport
        gsd_bgn_legend_viewport.restype = None
        gsd_bgn_legend_viewport.argtypes = [GLint, GLint, GLint, GLint]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 752
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_end_legend_viewport'):
        gsd_end_legend_viewport = _lib.gsd_end_legend_viewport
        gsd_end_legend_viewport.restype = None
        gsd_end_legend_viewport.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\ogsf_proto.h: 753
for _lib in _libs.values():
    if hasattr(_lib, 'gsd_make_nice_number'):
        gsd_make_nice_number = _lib.gsd_make_nice_number
        gsd_make_nice_number.restype = c_int
        gsd_make_nice_number.argtypes = [POINTER(c_float)]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 20
try:
    GS_UNIT_SIZE = 1000.0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 21
def BETWEEN(x, a, b):
    return (((x > a) and (x < b)) or ((x > b) and (x < a)))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_SURFS = 12
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_VECTS = 50
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_SITES = 50
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_VOLS = 12
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_DSP = 12
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_ATTS = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_LIGHTS = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_CPLANES = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_ISOSURFS = 12
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 25
try:
    MAX_SLICES = 12
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 27
try:
    MAX_VOL_SLICES = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 27
try:
    MAX_VOL_FILES = 100
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 29
try:
    DM_GOURAUD = 256
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 29
try:
    DM_FLAT = 512
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 30
try:
    DM_FRINGE = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 31
try:
    DM_WIRE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 31
try:
    DM_COL_WIRE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 31
try:
    DM_POLY = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 31
try:
    DM_WIRE_POLY = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 32
try:
    DM_GRID_WIRE = 1024
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 32
try:
    DM_GRID_SURF = 2048
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 33
try:
    WC_COLOR_ATT = 4278190080L
except:
    pass

IFLAG = c_uint # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 34

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_NORM = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_TOPO = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_COLOR = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_MASK = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_TRANSP = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_SHINE = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
try:
    ATT_EMIT = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 36
def LEGAL_ATT(a):
    return ((a >= 0) and (a < MAX_ATTS))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 38
try:
    NOTSET_ATT = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 38
try:
    MAP_ATT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 38
try:
    CONST_ATT = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 38
try:
    FUNC_ATT = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 38
def LEGAL_SRC(s):
    return ((((s == NOTSET_ATT) or (s == MAP_ATT)) or (s == CONST_ATT)) or (s == FUNC_ATT))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_X = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_BOX = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_SPHERE = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_CUBE = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_DIAMOND = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_DEC_TREE = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_CON_TREE = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_ASTER = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 40
try:
    ST_GYRO = 9
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 41
try:
    ST_HISTOGRAM = 10
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 44
try:
    ST_ATT_NONE = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 44
try:
    ST_ATT_COLOR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 44
try:
    ST_ATT_SIZE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 44
try:
    ST_ATT_MARKER = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 46
try:
    GSD_FRONT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 46
try:
    GSD_BACK = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 46
try:
    GSD_BOTH = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 48
try:
    FC_OFF = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 48
try:
    FC_ABOVE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 48
try:
    FC_BELOW = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 48
try:
    FC_BLEND = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 48
try:
    FC_GREY = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 50
try:
    LT_DISCRETE = 256
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 50
try:
    LT_CONTINUOUS = 512
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 51
try:
    LT_LIST = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 53
try:
    LT_RANGE_LOWSET = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 53
try:
    LT_RANGE_HISET = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 53
try:
    LT_RANGE_LOW_HI = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 53
try:
    LT_INVERTED = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 54
try:
    LT_SHOW_VALS = 4096
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 54
try:
    LT_SHOW_LABELS = 8192
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 56
try:
    VOL_FTYPE_G3D = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 58
try:
    VOL_DTYPE_FLOAT = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 58
try:
    VOL_DTYPE_DOUBLE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    X = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    Y = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    Z = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    W = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    FROM = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 22
try:
    TO = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_COLOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_EMISSION = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_AMBIENT = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_DIFFUSE = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_SPECULAR = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_AD = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 24
try:
    CM_NULL = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 25
try:
    CM_WIRE = CM_COLOR
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 26
try:
    NULL_COLOR = 16777215
except:
    pass

GS_CHAR8 = c_char # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 28

GS_SHORT16 = c_short # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 28

GS_INT32 = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 28

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_NULL = 32
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_MASK = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_FLOAT = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_INT = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_SHORT = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_CHAR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
try:
    ATTY_ANY = 63
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 30
def LEGAL_TYPE(t):
    return (((((t == ATTY_MASK) or (t == ATTY_FLOAT)) or (t == ATTY_INT)) or (t == ATTY_SHORT)) or (t == ATTY_CHAR))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 32
try:
    MAXDIMS = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 33
def FUDGE(gs):
    return ((((gs.contents.zmax_nz).value) - ((gs.contents.zmin_nz).value)) / 500.0)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 33
def DOT3(a, b):
    return ((((a [X]) * (b [X])) + ((a [Y]) * (b [Y]))) + ((a [Z]) * (b [Z])))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 35
try:
    CF_NOT_CHANGED = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 35
try:
    CF_COLOR_PACKED = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 35
try:
    CF_USR_CHANGED = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 35
try:
    CF_CHARSCALED = 256
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 36
try:
    MAX_TF = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 37
try:
    MASK_TL = 268435456
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 37
try:
    MASK_TR = 16777216
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 37
try:
    MASK_BR = 1048576
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 37
try:
    MASK_BL = 65536
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 37
try:
    MASK_NPTS = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 38
try:
    OGSF_POINT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 38
try:
    OGSF_LINE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 38
try:
    OGSF_POLYGON = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 152
try:
    GPT_MAX_ATTR = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 5
try:
    KF_FROMX_MASK = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 5
try:
    KF_FROMY_MASK = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 5
try:
    KF_FROMZ_MASK = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 5
try:
    KF_FROM_MASK = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 6
try:
    KF_DIRX_MASK = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 6
try:
    KF_DIRY_MASK = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 6
try:
    KF_DIRZ_MASK = 32
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 6
try:
    KF_DIR_MASK = 56
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 7
try:
    KF_FOV_MASK = 64
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 7
try:
    KF_TWIST_MASK = 128
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 8
try:
    KF_ALL_MASK = 255
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 9
try:
    KF_NUMFIELDS = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 10
try:
    KF_LINEAR = 111
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 10
try:
    KF_SPLINE = 222
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/keyframe.h: 10
def KF_LEGAL_MODE(m):
    return ((m == KF_LINEAR) or (m == KF_SPLINE))

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_FROMX = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_FROMY = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_FROMZ = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_DIRX = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_DIRY = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_DIRZ = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_FOV = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 8
try:
    KF_TWIST = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 9
try:
    FM_VECT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 9
try:
    FM_SITE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 9
try:
    FM_PATH = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 9
try:
    FM_VOL = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 9
try:
    FM_LABEL = 16
except:
    pass

g_surf = struct_g_surf # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 138

g_line = struct_g_line # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 165

g_vect = struct_g_vect # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 175

g_point = struct_g_point # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 196

g_site = struct_g_site # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 224

g_vol = struct_g_vol # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 294

lightdefs = struct_lightdefs # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gstypes.h: 320

view_node = struct_view_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 26

key_node = struct_key_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/kftypes.h: 28

# No inserted files

