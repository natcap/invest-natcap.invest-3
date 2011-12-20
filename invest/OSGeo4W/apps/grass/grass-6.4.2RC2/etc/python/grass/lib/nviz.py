'''Wrapper for nviz.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_nviz.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/nviz.h -o nviz.py

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

_libs["grass_nviz.6.4.2RC2"] = load_library("grass_nviz.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:/OSGeo4W/include/windef.h: 271
class struct_HBITMAP__(Structure):
    pass

struct_HBITMAP__.__slots__ = [
    'i',
]
struct_HBITMAP__._fields_ = [
    ('i', c_int),
]

HBITMAP = POINTER(struct_HBITMAP__) # c:/OSGeo4W/include/windef.h: 271

# c:/OSGeo4W/include/windef.h: 274
class struct_HDC__(Structure):
    pass

struct_HDC__.__slots__ = [
    'i',
]
struct_HDC__._fields_ = [
    ('i', c_int),
]

HDC = POINTER(struct_HDC__) # c:/OSGeo4W/include/windef.h: 274

# c:/OSGeo4W/include/windef.h: 275
class struct_HGLRC__(Structure):
    pass

struct_HGLRC__.__slots__ = [
    'i',
]
struct_HGLRC__._fields_ = [
    ('i', c_int),
]

HGLRC = POINTER(struct_HGLRC__) # c:/OSGeo4W/include/windef.h: 275

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 77
class struct_anon_155(Structure):
    pass

struct_anon_155.__slots__ = [
    'id',
    'brt',
    'r',
    'g',
    'b',
    'ar',
    'ag',
    'ab',
    'x',
    'y',
    'z',
    'w',
]
struct_anon_155._fields_ = [
    ('id', c_int),
    ('brt', c_float),
    ('r', c_float),
    ('g', c_float),
    ('b', c_float),
    ('ar', c_float),
    ('ag', c_float),
    ('ab', c_float),
    ('x', c_float),
    ('y', c_float),
    ('z', c_float),
    ('w', c_float),
]

light_data = struct_anon_155 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 77

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 79
class struct_fringe_data(Structure):
    pass

struct_fringe_data.__slots__ = [
    'id',
    'color',
    'elev',
    'where',
]
struct_fringe_data._fields_ = [
    ('id', c_int),
    ('color', c_ulong),
    ('elev', c_float),
    ('where', c_int * 4),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 108
class struct_anon_156(Structure):
    pass

struct_anon_156.__slots__ = [
    'zrange',
    'xyrange',
    'num_cplanes',
    'cur_cplane',
    'cp_on',
    'cp_trans',
    'cp_rot',
    'light',
    'num_fringes',
    'fringe',
    'bgcolor',
]
struct_anon_156._fields_ = [
    ('zrange', c_float),
    ('xyrange', c_float),
    ('num_cplanes', c_int),
    ('cur_cplane', c_int),
    ('cp_on', c_int * 6),
    ('cp_trans', (c_float * 3) * 6),
    ('cp_rot', (c_float * 3) * 6),
    ('light', light_data * 3),
    ('num_fringes', c_int),
    ('fringe', POINTER(POINTER(struct_fringe_data))),
    ('bgcolor', c_int),
]

nv_data = struct_anon_156 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 108

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 110
class struct_render_window(Structure):
    pass

struct_render_window.__slots__ = [
    'displayId',
    'contextId',
    'bitmapId',
]
struct_render_window._fields_ = [
    ('displayId', HDC),
    ('contextId', HGLRC),
    ('bitmapId', HBITMAP),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 129
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_resize_window'):
        Nviz_resize_window = _lib.Nviz_resize_window
        Nviz_resize_window.restype = c_int
        Nviz_resize_window.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 130
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_update_ranges'):
        Nviz_update_ranges = _lib.Nviz_update_ranges
        Nviz_update_ranges.restype = c_int
        Nviz_update_ranges.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 131
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_viewpoint_position'):
        Nviz_set_viewpoint_position = _lib.Nviz_set_viewpoint_position
        Nviz_set_viewpoint_position.restype = c_int
        Nviz_set_viewpoint_position.argtypes = [c_double, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 132
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_viewpoint_height'):
        Nviz_set_viewpoint_height = _lib.Nviz_set_viewpoint_height
        Nviz_set_viewpoint_height.restype = c_int
        Nviz_set_viewpoint_height.argtypes = [c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 133
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_viewpoint_persp'):
        Nviz_set_viewpoint_persp = _lib.Nviz_set_viewpoint_persp
        Nviz_set_viewpoint_persp.restype = c_int
        Nviz_set_viewpoint_persp.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 134
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_viewpoint_twist'):
        Nviz_set_viewpoint_twist = _lib.Nviz_set_viewpoint_twist
        Nviz_set_viewpoint_twist.restype = c_int
        Nviz_set_viewpoint_twist.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 135
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_change_exag'):
        Nviz_change_exag = _lib.Nviz_change_exag
        Nviz_change_exag.restype = c_int
        Nviz_change_exag.argtypes = [POINTER(nv_data), c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 138
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_new_cplane'):
        Nviz_new_cplane = _lib.Nviz_new_cplane
        Nviz_new_cplane.restype = c_int
        Nviz_new_cplane.argtypes = [POINTER(nv_data), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 139
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_off_cplane'):
        Nviz_off_cplane = _lib.Nviz_off_cplane
        Nviz_off_cplane.restype = c_int
        Nviz_off_cplane.argtypes = [POINTER(nv_data), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 140
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_cplane'):
        Nviz_draw_cplane = _lib.Nviz_draw_cplane
        Nviz_draw_cplane.restype = c_int
        Nviz_draw_cplane.argtypes = [POINTER(nv_data), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 143
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_all_surf'):
        Nviz_draw_all_surf = _lib.Nviz_draw_all_surf
        Nviz_draw_all_surf.restype = c_int
        Nviz_draw_all_surf.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 144
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_all_vect'):
        Nviz_draw_all_vect = _lib.Nviz_draw_all_vect
        Nviz_draw_all_vect.restype = c_int
        Nviz_draw_all_vect.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 145
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_all_site'):
        Nviz_draw_all_site = _lib.Nviz_draw_all_site
        Nviz_draw_all_site.restype = c_int
        Nviz_draw_all_site.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 146
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_all_vol'):
        Nviz_draw_all_vol = _lib.Nviz_draw_all_vol
        Nviz_draw_all_vol.restype = c_int
        Nviz_draw_all_vol.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 147
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_all'):
        Nviz_draw_all = _lib.Nviz_draw_all
        Nviz_draw_all.restype = c_int
        Nviz_draw_all.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 148
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_draw_quick'):
        Nviz_draw_quick = _lib.Nviz_draw_quick
        Nviz_draw_quick.restype = c_int
        Nviz_draw_quick.argtypes = [POINTER(nv_data), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 151
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_get_exag_height'):
        Nviz_get_exag_height = _lib.Nviz_get_exag_height
        Nviz_get_exag_height.restype = c_int
        Nviz_get_exag_height.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 152
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_get_exag'):
        Nviz_get_exag = _lib.Nviz_get_exag
        Nviz_get_exag.restype = c_double
        Nviz_get_exag.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 155
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_light_position'):
        Nviz_set_light_position = _lib.Nviz_set_light_position
        Nviz_set_light_position.restype = c_int
        Nviz_set_light_position.argtypes = [POINTER(nv_data), c_int, c_double, c_double, c_double, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 156
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_light_bright'):
        Nviz_set_light_bright = _lib.Nviz_set_light_bright
        Nviz_set_light_bright.restype = c_int
        Nviz_set_light_bright.argtypes = [POINTER(nv_data), c_int, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 157
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_light_color'):
        Nviz_set_light_color = _lib.Nviz_set_light_color
        Nviz_set_light_color.restype = c_int
        Nviz_set_light_color.argtypes = [POINTER(nv_data), c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 158
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_light_ambient'):
        Nviz_set_light_ambient = _lib.Nviz_set_light_ambient
        Nviz_set_light_ambient.restype = c_int
        Nviz_set_light_ambient.argtypes = [POINTER(nv_data), c_int, c_double]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 159
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_init_light'):
        Nviz_init_light = _lib.Nviz_init_light
        Nviz_init_light.restype = c_int
        Nviz_init_light.argtypes = [POINTER(nv_data), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 160
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_new_light'):
        Nviz_new_light = _lib.Nviz_new_light
        Nviz_new_light.restype = c_int
        Nviz_new_light.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 163
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_new_map_obj'):
        Nviz_new_map_obj = _lib.Nviz_new_map_obj
        Nviz_new_map_obj.restype = c_int
        Nviz_new_map_obj.argtypes = [c_int, String, c_double, POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 164
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_attr'):
        Nviz_set_attr = _lib.Nviz_set_attr
        Nviz_set_attr.restype = c_int
        Nviz_set_attr.argtypes = [c_int, c_int, c_int, c_int, String, c_double, POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 165
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_surface_attr_default'):
        Nviz_set_surface_attr_default = _lib.Nviz_set_surface_attr_default
        Nviz_set_surface_attr_default.restype = None
        Nviz_set_surface_attr_default.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 166
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_vpoint_attr_default'):
        Nviz_set_vpoint_attr_default = _lib.Nviz_set_vpoint_attr_default
        Nviz_set_vpoint_attr_default.restype = c_int
        Nviz_set_vpoint_attr_default.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 167
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_volume_attr_default'):
        Nviz_set_volume_attr_default = _lib.Nviz_set_volume_attr_default
        Nviz_set_volume_attr_default.restype = c_int
        Nviz_set_volume_attr_default.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 168
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_unset_attr'):
        Nviz_unset_attr = _lib.Nviz_unset_attr
        Nviz_unset_attr.restype = c_int
        Nviz_unset_attr.argtypes = [c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 171
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_init_data'):
        Nviz_init_data = _lib.Nviz_init_data
        Nviz_init_data.restype = None
        Nviz_init_data.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 172
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_destroy_data'):
        Nviz_destroy_data = _lib.Nviz_destroy_data
        Nviz_destroy_data.restype = None
        Nviz_destroy_data.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 173
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_bgcolor'):
        Nviz_set_bgcolor = _lib.Nviz_set_bgcolor
        Nviz_set_bgcolor.restype = None
        Nviz_set_bgcolor.argtypes = [POINTER(nv_data), c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 174
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_get_bgcolor'):
        Nviz_get_bgcolor = _lib.Nviz_get_bgcolor
        Nviz_get_bgcolor.restype = c_int
        Nviz_get_bgcolor.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 175
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_color_from_str'):
        Nviz_color_from_str = _lib.Nviz_color_from_str
        Nviz_color_from_str.restype = c_int
        Nviz_color_from_str.argtypes = [String]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 176
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_new_fringe'):
        Nviz_new_fringe = _lib.Nviz_new_fringe
        Nviz_new_fringe.restype = POINTER(struct_fringe_data)
        Nviz_new_fringe.argtypes = [POINTER(nv_data), c_int, c_ulong, c_double, c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 178
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_fringe'):
        Nviz_set_fringe = _lib.Nviz_set_fringe
        Nviz_set_fringe.restype = POINTER(struct_fringe_data)
        Nviz_set_fringe.argtypes = [POINTER(nv_data), c_int, c_ulong, c_double, c_int, c_int, c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 182
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_init_view'):
        Nviz_init_view = _lib.Nviz_init_view
        Nviz_init_view.restype = None
        Nviz_init_view.argtypes = [POINTER(nv_data)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 183
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_focus_state'):
        Nviz_set_focus_state = _lib.Nviz_set_focus_state
        Nviz_set_focus_state.restype = c_int
        Nviz_set_focus_state.argtypes = [c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 184
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_set_focus_map'):
        Nviz_set_focus_map = _lib.Nviz_set_focus_map
        Nviz_set_focus_map.restype = c_int
        Nviz_set_focus_map.argtypes = [c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 187
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_new_render_window'):
        Nviz_new_render_window = _lib.Nviz_new_render_window
        Nviz_new_render_window.restype = POINTER(struct_render_window)
        Nviz_new_render_window.argtypes = []
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 188
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_init_render_window'):
        Nviz_init_render_window = _lib.Nviz_init_render_window
        Nviz_init_render_window.restype = None
        Nviz_init_render_window.argtypes = [POINTER(struct_render_window)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 189
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_destroy_render_window'):
        Nviz_destroy_render_window = _lib.Nviz_destroy_render_window
        Nviz_destroy_render_window.restype = None
        Nviz_destroy_render_window.argtypes = [POINTER(struct_render_window)]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 190
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_create_render_window'):
        Nviz_create_render_window = _lib.Nviz_create_render_window
        Nviz_create_render_window.restype = c_int
        Nviz_create_render_window.argtypes = [POINTER(struct_render_window), POINTER(None), c_int, c_int]
        break

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 191
for _lib in _libs.values():
    if hasattr(_lib, 'Nviz_make_current_render_window'):
        Nviz_make_current_render_window = _lib.Nviz_make_current_render_window
        Nviz_make_current_render_window.restype = c_int
        Nviz_make_current_render_window.argtypes = [POINTER(struct_render_window)]
        break

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gsurf.h: 20
try:
    GS_UNIT_SIZE = 1000.0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 39
try:
    MAP_OBJ_UNDEFINED = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 39
try:
    MAP_OBJ_SURF = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 39
try:
    MAP_OBJ_VOL = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 39
try:
    MAP_OBJ_VECT = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 39
try:
    MAP_OBJ_SITE = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 40
try:
    DRAW_COARSE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 40
try:
    DRAW_FINE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 40
try:
    DRAW_BOTH = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 42
try:
    DRAW_QUICK_SURFACE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 42
try:
    DRAW_QUICK_VLINES = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 42
try:
    DRAW_QUICK_VPOINTS = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 42
try:
    DRAW_QUICK_VOLUME = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 43
try:
    RANGE = (5 * GS_UNIT_SIZE)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 43
try:
    RANGE_OFFSET = (2 * GS_UNIT_SIZE)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 43
try:
    ZRANGE = (3 * GS_UNIT_SIZE)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 43
try:
    ZRANGE_OFFSET = (1 * GS_UNIT_SIZE)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 44
try:
    DEFAULT_SURF_COLOR = 3390463
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 45
try:
    RED_MASK = 255
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 45
try:
    GRN_MASK = 65280
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 45
try:
    BLU_MASK = 16711680
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 46
try:
    FORMAT_PPM = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 46
try:
    FORMAT_TIF = 2
except:
    pass

fringe_data = struct_fringe_data # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 79

render_window = struct_render_window # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\nviz.h: 110

# No inserted files

