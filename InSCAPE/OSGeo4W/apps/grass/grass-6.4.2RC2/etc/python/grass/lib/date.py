'''Wrapper for datetime.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_datetime.6.4.2RC2 c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/datetime.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h -o date.py

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

_libs["grass_datetime.6.4.2RC2"] = load_library("grass_datetime.6.4.2RC2")

# 1 libraries
# End libraries

# No modules

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 25
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

DateTime = struct_anon_1 # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 25

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 6
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_between'):
    datetime_is_between = _libs['grass_datetime.6.4.2RC2'].datetime_is_between
    datetime_is_between.restype = c_int
    datetime_is_between.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 9
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_change_from_to'):
    datetime_change_from_to = _libs['grass_datetime.6.4.2RC2'].datetime_change_from_to
    datetime_change_from_to.restype = c_int
    datetime_change_from_to.argtypes = [POINTER(DateTime), c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 12
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_copy'):
    datetime_copy = _libs['grass_datetime.6.4.2RC2'].datetime_copy
    datetime_copy.restype = None
    datetime_copy.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 15
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_difference'):
    datetime_difference = _libs['grass_datetime.6.4.2RC2'].datetime_difference
    datetime_difference.restype = c_int
    datetime_difference.argtypes = [POINTER(DateTime), POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 19
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_error'):
    datetime_error = _libs['grass_datetime.6.4.2RC2'].datetime_error
    datetime_error.restype = c_int
    datetime_error.argtypes = [c_int, String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 20
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_error_code'):
    datetime_error_code = _libs['grass_datetime.6.4.2RC2'].datetime_error_code
    datetime_error_code.restype = c_int
    datetime_error_code.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 21
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_error_msg'):
    datetime_error_msg = _libs['grass_datetime.6.4.2RC2'].datetime_error_msg
    datetime_error_msg.restype = ReturnString
    datetime_error_msg.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 22
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_clear_error'):
    datetime_clear_error = _libs['grass_datetime.6.4.2RC2'].datetime_clear_error
    datetime_clear_error.restype = None
    datetime_clear_error.argtypes = []

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 25
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_format'):
    datetime_format = _libs['grass_datetime.6.4.2RC2'].datetime_format
    datetime_format.restype = c_int
    datetime_format.argtypes = [POINTER(DateTime), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 28
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_increment'):
    datetime_increment = _libs['grass_datetime.6.4.2RC2'].datetime_increment
    datetime_increment.restype = c_int
    datetime_increment.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 31
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_valid_increment'):
    datetime_is_valid_increment = _libs['grass_datetime.6.4.2RC2'].datetime_is_valid_increment
    datetime_is_valid_increment.restype = c_int
    datetime_is_valid_increment.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 32
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_increment'):
    datetime_check_increment = _libs['grass_datetime.6.4.2RC2'].datetime_check_increment
    datetime_check_increment.restype = c_int
    datetime_check_increment.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 35
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_increment_type'):
    datetime_get_increment_type = _libs['grass_datetime.6.4.2RC2'].datetime_get_increment_type
    datetime_get_increment_type.restype = c_int
    datetime_get_increment_type.argtypes = [POINTER(DateTime), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 37
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_increment_type'):
    datetime_set_increment_type = _libs['grass_datetime.6.4.2RC2'].datetime_set_increment_type
    datetime_set_increment_type.restype = c_int
    datetime_set_increment_type.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 40
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_local_timezone'):
    datetime_get_local_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_get_local_timezone
    datetime_get_local_timezone.restype = c_int
    datetime_get_local_timezone.argtypes = [POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 41
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_local_time'):
    datetime_get_local_time = _libs['grass_datetime.6.4.2RC2'].datetime_get_local_time
    datetime_get_local_time.restype = None
    datetime_get_local_time.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 44
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_days_in_month'):
    datetime_days_in_month = _libs['grass_datetime.6.4.2RC2'].datetime_days_in_month
    datetime_days_in_month.restype = c_int
    datetime_days_in_month.argtypes = [c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 45
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_leap_year'):
    datetime_is_leap_year = _libs['grass_datetime.6.4.2RC2'].datetime_is_leap_year
    datetime_is_leap_year.restype = c_int
    datetime_is_leap_year.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 46
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_days_in_year'):
    datetime_days_in_year = _libs['grass_datetime.6.4.2RC2'].datetime_days_in_year
    datetime_days_in_year.restype = c_int
    datetime_days_in_year.argtypes = [c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 49
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_same'):
    datetime_is_same = _libs['grass_datetime.6.4.2RC2'].datetime_is_same
    datetime_is_same.restype = c_int
    datetime_is_same.argtypes = [POINTER(DateTime), POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 52
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_scan'):
    datetime_scan = _libs['grass_datetime.6.4.2RC2'].datetime_scan
    datetime_scan.restype = c_int
    datetime_scan.argtypes = [POINTER(DateTime), String]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 55
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_positive'):
    datetime_is_positive = _libs['grass_datetime.6.4.2RC2'].datetime_is_positive
    datetime_is_positive.restype = c_int
    datetime_is_positive.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 56
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_negative'):
    datetime_is_negative = _libs['grass_datetime.6.4.2RC2'].datetime_is_negative
    datetime_is_negative.restype = c_int
    datetime_is_negative.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 57
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_positive'):
    datetime_set_positive = _libs['grass_datetime.6.4.2RC2'].datetime_set_positive
    datetime_set_positive.restype = None
    datetime_set_positive.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 58
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_negative'):
    datetime_set_negative = _libs['grass_datetime.6.4.2RC2'].datetime_set_negative
    datetime_set_negative.restype = None
    datetime_set_negative.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 59
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_invert_sign'):
    datetime_invert_sign = _libs['grass_datetime.6.4.2RC2'].datetime_invert_sign
    datetime_invert_sign.restype = None
    datetime_invert_sign.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 62
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_type'):
    datetime_set_type = _libs['grass_datetime.6.4.2RC2'].datetime_set_type
    datetime_set_type.restype = c_int
    datetime_set_type.argtypes = [POINTER(DateTime), c_int, c_int, c_int, c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 63
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_type'):
    datetime_get_type = _libs['grass_datetime.6.4.2RC2'].datetime_get_type
    datetime_get_type.restype = c_int
    datetime_get_type.argtypes = [POINTER(DateTime), POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 65
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_valid_type'):
    datetime_is_valid_type = _libs['grass_datetime.6.4.2RC2'].datetime_is_valid_type
    datetime_is_valid_type.restype = c_int
    datetime_is_valid_type.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 66
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_type'):
    datetime_check_type = _libs['grass_datetime.6.4.2RC2'].datetime_check_type
    datetime_check_type.restype = c_int
    datetime_check_type.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 67
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_in_interval_year_month'):
    datetime_in_interval_year_month = _libs['grass_datetime.6.4.2RC2'].datetime_in_interval_year_month
    datetime_in_interval_year_month.restype = c_int
    datetime_in_interval_year_month.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 68
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_in_interval_day_second'):
    datetime_in_interval_day_second = _libs['grass_datetime.6.4.2RC2'].datetime_in_interval_day_second
    datetime_in_interval_day_second.restype = c_int
    datetime_in_interval_day_second.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 69
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_absolute'):
    datetime_is_absolute = _libs['grass_datetime.6.4.2RC2'].datetime_is_absolute
    datetime_is_absolute.restype = c_int
    datetime_is_absolute.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 70
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_relative'):
    datetime_is_relative = _libs['grass_datetime.6.4.2RC2'].datetime_is_relative
    datetime_is_relative.restype = c_int
    datetime_is_relative.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 73
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_timezone'):
    datetime_check_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_check_timezone
    datetime_check_timezone.restype = c_int
    datetime_check_timezone.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 74
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_timezone'):
    datetime_get_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_get_timezone
    datetime_get_timezone.restype = c_int
    datetime_get_timezone.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 75
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_timezone'):
    datetime_set_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_set_timezone
    datetime_set_timezone.restype = c_int
    datetime_set_timezone.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 76
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_unset_timezone'):
    datetime_unset_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_unset_timezone
    datetime_unset_timezone.restype = c_int
    datetime_unset_timezone.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 77
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_is_valid_timezone'):
    datetime_is_valid_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_is_valid_timezone
    datetime_is_valid_timezone.restype = c_int
    datetime_is_valid_timezone.argtypes = [c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 80
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_change_timezone'):
    datetime_change_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_change_timezone
    datetime_change_timezone.restype = c_int
    datetime_change_timezone.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 81
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_change_to_utc'):
    datetime_change_to_utc = _libs['grass_datetime.6.4.2RC2'].datetime_change_to_utc
    datetime_change_to_utc.restype = c_int
    datetime_change_to_utc.argtypes = [POINTER(DateTime)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 82
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_decompose_timezone'):
    datetime_decompose_timezone = _libs['grass_datetime.6.4.2RC2'].datetime_decompose_timezone
    datetime_decompose_timezone.restype = None
    datetime_decompose_timezone.argtypes = [c_int, POINTER(c_int), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 85
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_year'):
    datetime_check_year = _libs['grass_datetime.6.4.2RC2'].datetime_check_year
    datetime_check_year.restype = c_int
    datetime_check_year.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 86
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_month'):
    datetime_check_month = _libs['grass_datetime.6.4.2RC2'].datetime_check_month
    datetime_check_month.restype = c_int
    datetime_check_month.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 87
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_day'):
    datetime_check_day = _libs['grass_datetime.6.4.2RC2'].datetime_check_day
    datetime_check_day.restype = c_int
    datetime_check_day.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 88
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_hour'):
    datetime_check_hour = _libs['grass_datetime.6.4.2RC2'].datetime_check_hour
    datetime_check_hour.restype = c_int
    datetime_check_hour.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 89
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_minute'):
    datetime_check_minute = _libs['grass_datetime.6.4.2RC2'].datetime_check_minute
    datetime_check_minute.restype = c_int
    datetime_check_minute.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 90
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_second'):
    datetime_check_second = _libs['grass_datetime.6.4.2RC2'].datetime_check_second
    datetime_check_second.restype = c_int
    datetime_check_second.argtypes = [POINTER(DateTime), c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 91
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_check_fracsec'):
    datetime_check_fracsec = _libs['grass_datetime.6.4.2RC2'].datetime_check_fracsec
    datetime_check_fracsec.restype = c_int
    datetime_check_fracsec.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 92
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_year'):
    datetime_get_year = _libs['grass_datetime.6.4.2RC2'].datetime_get_year
    datetime_get_year.restype = c_int
    datetime_get_year.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 93
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_year'):
    datetime_set_year = _libs['grass_datetime.6.4.2RC2'].datetime_set_year
    datetime_set_year.restype = c_int
    datetime_set_year.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 94
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_month'):
    datetime_get_month = _libs['grass_datetime.6.4.2RC2'].datetime_get_month
    datetime_get_month.restype = c_int
    datetime_get_month.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 95
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_month'):
    datetime_set_month = _libs['grass_datetime.6.4.2RC2'].datetime_set_month
    datetime_set_month.restype = c_int
    datetime_set_month.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 96
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_day'):
    datetime_get_day = _libs['grass_datetime.6.4.2RC2'].datetime_get_day
    datetime_get_day.restype = c_int
    datetime_get_day.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 97
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_day'):
    datetime_set_day = _libs['grass_datetime.6.4.2RC2'].datetime_set_day
    datetime_set_day.restype = c_int
    datetime_set_day.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 98
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_hour'):
    datetime_get_hour = _libs['grass_datetime.6.4.2RC2'].datetime_get_hour
    datetime_get_hour.restype = c_int
    datetime_get_hour.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 99
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_hour'):
    datetime_set_hour = _libs['grass_datetime.6.4.2RC2'].datetime_set_hour
    datetime_set_hour.restype = c_int
    datetime_set_hour.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 100
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_minute'):
    datetime_get_minute = _libs['grass_datetime.6.4.2RC2'].datetime_get_minute
    datetime_get_minute.restype = c_int
    datetime_get_minute.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 101
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_minute'):
    datetime_set_minute = _libs['grass_datetime.6.4.2RC2'].datetime_set_minute
    datetime_set_minute.restype = c_int
    datetime_set_minute.argtypes = [POINTER(DateTime), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 102
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_second'):
    datetime_get_second = _libs['grass_datetime.6.4.2RC2'].datetime_get_second
    datetime_get_second.restype = c_int
    datetime_get_second.argtypes = [POINTER(DateTime), POINTER(c_double)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 103
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_second'):
    datetime_set_second = _libs['grass_datetime.6.4.2RC2'].datetime_set_second
    datetime_set_second.restype = c_int
    datetime_set_second.argtypes = [POINTER(DateTime), c_double]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 104
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_get_fracsec'):
    datetime_get_fracsec = _libs['grass_datetime.6.4.2RC2'].datetime_get_fracsec
    datetime_get_fracsec.restype = c_int
    datetime_get_fracsec.argtypes = [POINTER(DateTime), POINTER(c_int)]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/P_datetime.h: 105
if hasattr(_libs['grass_datetime.6.4.2RC2'], 'datetime_set_fracsec'):
    datetime_set_fracsec = _libs['grass_datetime.6.4.2RC2'].datetime_set_fracsec
    datetime_set_fracsec.restype = c_int
    datetime_set_fracsec.argtypes = [POINTER(DateTime), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 3
try:
    DATETIME_ABSOLUTE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 3
try:
    DATETIME_RELATIVE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_YEAR = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_MONTH = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_DAY = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_HOUR = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_MINUTE = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\datetime.h: 5
try:
    DATETIME_SECOND = 6
except:
    pass

# No inserted files

