'''Wrapper for stats.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_stats.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/stats.h -o stats.py

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

_libs["grass_stats.6.4.2RC2"] = load_library("grass_stats.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

DCELL = c_double # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 257

stat_func = CFUNCTYPE(UNCHECKED(None), POINTER(DCELL), POINTER(DCELL), c_int, POINTER(None)) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 7

stat_func_w = CFUNCTYPE(UNCHECKED(None), POINTER(DCELL), POINTER(DCELL * 2), c_int, POINTER(None)) # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 8

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 10
try:
    c_ave = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_ave')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 11
try:
    c_count = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_count')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 12
try:
    c_divr = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_divr')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 13
try:
    c_intr = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_intr')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 14
try:
    c_max = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_max')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 15
try:
    c_maxx = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_maxx')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 16
try:
    c_median = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_median')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 17
try:
    c_min = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_min')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 18
try:
    c_minx = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_minx')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 19
try:
    c_mode = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_mode')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 20
try:
    c_stddev = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_stddev')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 21
try:
    c_sum = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_sum')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 22
try:
    c_thresh = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_thresh')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 23
try:
    c_var = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_var')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 24
try:
    c_range = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_range')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 25
try:
    c_reg_m = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_reg_m')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 26
try:
    c_reg_c = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_reg_c')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 27
try:
    c_reg_r2 = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_reg_r2')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 28
try:
    c_quart1 = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_quart1')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 29
try:
    c_quart3 = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_quart3')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 30
try:
    c_perc90 = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_perc90')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 31
try:
    c_quant = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_quant')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 32
try:
    c_skew = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_skew')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 33
try:
    c_kurt = (stat_func).in_dll(_libs['grass_stats.6.4.2RC2'], 'c_kurt')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 35
try:
    w_ave = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_ave')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 36
try:
    w_count = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_count')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 37
try:
    w_median = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_median')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 38
try:
    w_mode = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_mode')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 39
try:
    w_quart1 = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_quart1')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 40
try:
    w_quart3 = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_quart3')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 41
try:
    w_perc90 = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_perc90')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 42
try:
    w_reg_m = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_reg_m')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 43
try:
    w_reg_c = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_reg_c')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 44
try:
    w_reg_r2 = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_reg_r2')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 45
try:
    w_stddev = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_stddev')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 46
try:
    w_sum = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_sum')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 47
try:
    w_var = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_var')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 48
try:
    w_skew = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_skew')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 49
try:
    w_kurt = (stat_func_w).in_dll(_libs['grass_stats.6.4.2RC2'], 'w_kurt')
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 51
if hasattr(_libs['grass_stats.6.4.2RC2'], 'sort_cell'):
    sort_cell = _libs['grass_stats.6.4.2RC2'].sort_cell
    sort_cell.restype = c_int
    sort_cell.argtypes = [POINTER(DCELL), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\stats.h: 52
if hasattr(_libs['grass_stats.6.4.2RC2'], 'sort_cell_w'):
    sort_cell_w = _libs['grass_stats.6.4.2RC2'].sort_cell_w
    sort_cell_w.restype = c_int
    sort_cell_w.argtypes = [POINTER(DCELL * 2), c_int]

# No inserted files

