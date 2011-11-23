'''Wrapper for Vect.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_vect.6.4.2RC2 -Ic:/OSGeo4W/include -Ic:/OSGeo4W/include c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/Vect.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h -o vector.py

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

_libs["grass_vect.6.4.2RC2"] = load_library("grass_vect.6.4.2RC2")

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

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/gis.h: 591
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

enum_overlay_operator = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 165

GV_O_AND = 0 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 165

GV_O_OVERLAP = (GV_O_AND + 1) # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 165

OVERLAY_OPERATOR = enum_overlay_operator # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 171

dglByte_t = c_ubyte # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/type.h: 36

dglInt32_t = c_long # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/type.h: 37

dglInt64_t = c_longlong # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/type.h: 38

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 33
class union__dglHeapData(Union):
    pass

union__dglHeapData.__slots__ = [
    'pv',
    'n',
    'un',
    'l',
    'ul',
]
union__dglHeapData._fields_ = [
    ('pv', POINTER(None)),
    ('n', c_int),
    ('un', c_uint),
    ('l', c_long),
    ('ul', c_ulong),
]

dglHeapData_u = union__dglHeapData # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 33

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 42
class struct__dglHeapNode(Structure):
    pass

struct__dglHeapNode.__slots__ = [
    'key',
    'value',
    'flags',
]
struct__dglHeapNode._fields_ = [
    ('key', c_long),
    ('value', dglHeapData_u),
    ('flags', c_ubyte),
]

dglHeapNode_s = struct__dglHeapNode # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 42

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 52
class struct__dglHeap(Structure):
    pass

struct__dglHeap.__slots__ = [
    'index',
    'count',
    'block',
    'pnode',
]
struct__dglHeap._fields_ = [
    ('index', c_long),
    ('count', c_long),
    ('block', c_long),
    ('pnode', POINTER(dglHeapNode_s)),
]

dglHeap_s = struct__dglHeap # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/heap.h: 52

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/tree.h: 165
class struct__dglTreeEdgePri32(Structure):
    pass

struct__dglTreeEdgePri32.__slots__ = [
    'nKey',
    'cnData',
    'pnData',
]
struct__dglTreeEdgePri32._fields_ = [
    ('nKey', dglInt32_t),
    ('cnData', dglInt32_t),
    ('pnData', POINTER(dglInt32_t)),
]

dglTreeEdgePri32_s = struct__dglTreeEdgePri32 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/tree.h: 165

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 135
class struct_anon_8(Structure):
    pass

struct_anon_8.__slots__ = [
    'pvAVL',
]
struct_anon_8._fields_ = [
    ('pvAVL', POINTER(None)),
]

dglNodePrioritizer_s = struct_anon_8 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 135

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 146
class struct_anon_9(Structure):
    pass

struct_anon_9.__slots__ = [
    'cEdge',
    'iEdge',
    'pEdgePri32Item',
    'pvAVL',
]
struct_anon_9._fields_ = [
    ('cEdge', c_int),
    ('iEdge', c_int),
    ('pEdgePri32Item', POINTER(dglTreeEdgePri32_s)),
    ('pvAVL', POINTER(None)),
]

dglEdgePrioritizer_s = struct_anon_9 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 146

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 193
class struct__dglGraph(Structure):
    pass

struct__dglGraph.__slots__ = [
    'iErrno',
    'Version',
    'Endian',
    'NodeAttrSize',
    'EdgeAttrSize',
    'aOpaqueSet',
    'cNode',
    'cHead',
    'cTail',
    'cAlone',
    'cEdge',
    'nnCost',
    'Flags',
    'nFamily',
    'nOptions',
    'pNodeTree',
    'pEdgeTree',
    'pNodeBuffer',
    'iNodeBuffer',
    'pEdgeBuffer',
    'iEdgeBuffer',
    'edgePrioritizer',
    'nodePrioritizer',
]
struct__dglGraph._fields_ = [
    ('iErrno', c_int),
    ('Version', dglByte_t),
    ('Endian', dglByte_t),
    ('NodeAttrSize', dglInt32_t),
    ('EdgeAttrSize', dglInt32_t),
    ('aOpaqueSet', dglInt32_t * 16),
    ('cNode', dglInt32_t),
    ('cHead', dglInt32_t),
    ('cTail', dglInt32_t),
    ('cAlone', dglInt32_t),
    ('cEdge', dglInt32_t),
    ('nnCost', dglInt64_t),
    ('Flags', dglInt32_t),
    ('nFamily', dglInt32_t),
    ('nOptions', dglInt32_t),
    ('pNodeTree', POINTER(None)),
    ('pEdgeTree', POINTER(None)),
    ('pNodeBuffer', POINTER(dglByte_t)),
    ('iNodeBuffer', dglInt32_t),
    ('pEdgeBuffer', POINTER(dglByte_t)),
    ('iEdgeBuffer', dglInt32_t),
    ('edgePrioritizer', dglEdgePrioritizer_s),
    ('nodePrioritizer', dglNodePrioritizer_s),
]

dglGraph_s = struct__dglGraph # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 193

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 243
class struct_anon_10(Structure):
    pass

struct_anon_10.__slots__ = [
    'nStartNode',
    'NodeHeap',
    'pvVisited',
    'pvPredist',
]
struct_anon_10._fields_ = [
    ('nStartNode', dglInt32_t),
    ('NodeHeap', dglHeap_s),
    ('pvVisited', POINTER(None)),
    ('pvPredist', POINTER(None)),
]

dglSPCache_s = struct_anon_10 # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/dgl/graph.h: 243

RectReal = c_double # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/rtree/index.h: 25

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/rtree/index.h: 40
class struct_Rect(Structure):
    pass

struct_Rect.__slots__ = [
    'boundary',
]
struct_Rect._fields_ = [
    ('boundary', RectReal * (2 * 3)),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/rtree/index.h: 56
class struct_Node(Structure):
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/rtree/index.h: 47
class struct_Branch(Structure):
    pass

struct_Branch.__slots__ = [
    'rect',
    'child',
]
struct_Branch._fields_ = [
    ('rect', struct_Rect),
    ('child', POINTER(struct_Node)),
]

struct_Node.__slots__ = [
    'count',
    'level',
    'branch',
]
struct_Node._fields_ = [
    ('count', c_int),
    ('level', c_int),
    ('branch', struct_Branch * ((512 - (2 * sizeof(c_int))) / sizeof(struct_Branch))),
]

OGRFeatureH = POINTER(None) # c:/OSGeo4W/include/ogr_api.h: 220

OGRLayerH = POINTER(None) # c:/OSGeo4W/include/ogr_api.h: 330

OGRDataSourceH = POINTER(None) # c:/OSGeo4W/include/ogr_api.h: 331

plus_t = c_int # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 36

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 55
class struct_bound_box(Structure):
    pass

BOUND_BOX = struct_bound_box # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 38

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 424
class struct_P_node(Structure):
    pass

P_NODE = struct_P_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 40

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 458
class struct_P_area(Structure):
    pass

P_AREA = struct_P_area # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 41

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 438
class struct_P_line(Structure):
    pass

P_LINE = struct_P_line # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 42

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 480
class struct_P_isle(Structure):
    pass

P_ISLE = struct_P_isle # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 43

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 46
class struct_site_att(Structure):
    pass

struct_site_att.__slots__ = [
    'cat',
    'dbl',
    'str',
]
struct_site_att._fields_ = [
    ('cat', c_int),
    ('dbl', POINTER(c_double)),
    ('str', POINTER(POINTER(c_char))),
]

SITE_ATT = struct_site_att # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 53

struct_bound_box.__slots__ = [
    'N',
    'S',
    'E',
    'W',
    'T',
    'B',
]
struct_bound_box._fields_ = [
    ('N', c_double),
    ('S', c_double),
    ('E', c_double),
    ('W', c_double),
    ('T', c_double),
    ('B', c_double),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 65
class struct_gvfile(Structure):
    pass

struct_gvfile.__slots__ = [
    'file',
    'start',
    'current',
    'end',
    'size',
    'alloc',
    'loaded',
]
struct_gvfile._fields_ = [
    ('file', POINTER(FILE)),
    ('start', String),
    ('current', String),
    ('end', String),
    ('size', c_long),
    ('alloc', c_long),
    ('loaded', c_int),
]

GVFILE = struct_gvfile # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 76

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 79
class struct_field_info(Structure):
    pass

struct_field_info.__slots__ = [
    'number',
    'name',
    'driver',
    'database',
    'table',
    'key',
]
struct_field_info._fields_ = [
    ('number', c_int),
    ('name', String),
    ('driver', String),
    ('database', String),
    ('table', String),
    ('key', String),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 89
class struct_dblinks(Structure):
    pass

struct_dblinks.__slots__ = [
    'field',
    'alloc_fields',
    'n_fields',
]
struct_dblinks._fields_ = [
    ('field', POINTER(struct_field_info)),
    ('alloc_fields', c_int),
    ('n_fields', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 96
class struct_Port_info(Structure):
    pass

struct_Port_info.__slots__ = [
    'byte_order',
    'dbl_cnvrt',
    'flt_cnvrt',
    'lng_cnvrt',
    'int_cnvrt',
    'shrt_cnvrt',
    'dbl_quick',
    'flt_quick',
    'lng_quick',
    'int_quick',
    'shrt_quick',
]
struct_Port_info._fields_ = [
    ('byte_order', c_int),
    ('dbl_cnvrt', c_ubyte * 8),
    ('flt_cnvrt', c_ubyte * 4),
    ('lng_cnvrt', c_ubyte * 4),
    ('int_cnvrt', c_ubyte * 4),
    ('shrt_cnvrt', c_ubyte * 2),
    ('dbl_quick', c_int),
    ('flt_quick', c_int),
    ('lng_quick', c_int),
    ('int_quick', c_int),
    ('shrt_quick', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 120
class struct_recycle(Structure):
    pass

struct_recycle.__slots__ = [
    'dummy',
]
struct_recycle._fields_ = [
    ('dummy', c_char),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 357
class struct_Map_info(Structure):
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 126
class struct_dig_head(Structure):
    pass

struct_dig_head.__slots__ = [
    'organization',
    'date',
    'your_name',
    'map_name',
    'source_date',
    'orig_scale',
    'line_3',
    'plani_zone',
    'digit_thresh',
    'Version_Major',
    'Version_Minor',
    'Back_Major',
    'Back_Minor',
    'with_z',
    'size',
    'head_size',
    'port',
    'last_offset',
    'recycle',
    'Map',
]
struct_dig_head._fields_ = [
    ('organization', String),
    ('date', String),
    ('your_name', String),
    ('map_name', String),
    ('source_date', String),
    ('orig_scale', c_long),
    ('line_3', String),
    ('plani_zone', c_int),
    ('digit_thresh', c_double),
    ('Version_Major', c_int),
    ('Version_Minor', c_int),
    ('Back_Major', c_int),
    ('Back_Minor', c_int),
    ('with_z', c_int),
    ('size', c_long),
    ('head_size', c_long),
    ('port', struct_Port_info),
    ('last_offset', c_long),
    ('recycle', POINTER(struct_recycle)),
    ('Map', POINTER(struct_Map_info)),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 165
class struct_Coor_info(Structure):
    pass

struct_Coor_info.__slots__ = [
    'size',
    'mtime',
]
struct_Coor_info._fields_ = [
    ('size', c_long),
    ('mtime', c_long),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 498
class struct_line_pnts(Structure):
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 174
class struct_Format_info_ogr(Structure):
    pass

struct_Format_info_ogr.__slots__ = [
    'dsn',
    'layer_name',
    'ds',
    'layer',
    'lines',
    'lines_types',
    'lines_alloc',
    'lines_num',
    'lines_next',
    'feature_cache',
    'feature_cache_id',
    'offset',
    'offset_num',
    'offset_alloc',
    'next_line',
]
struct_Format_info_ogr._fields_ = [
    ('dsn', String),
    ('layer_name', String),
    ('ds', OGRDataSourceH),
    ('layer', OGRLayerH),
    ('lines', POINTER(POINTER(struct_line_pnts))),
    ('lines_types', POINTER(c_int)),
    ('lines_alloc', c_int),
    ('lines_num', c_int),
    ('lines_next', c_int),
    ('feature_cache', OGRFeatureH),
    ('feature_cache_id', c_int),
    ('offset', POINTER(c_int)),
    ('offset_num', c_int),
    ('offset_alloc', c_int),
    ('next_line', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 220
class struct_Format_info(Structure):
    pass

struct_Format_info.__slots__ = [
    'i',
    'ogr',
]
struct_Format_info._fields_ = [
    ('i', c_int),
    ('ogr', struct_Format_info_ogr),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 227
class struct_Cat_index(Structure):
    pass

struct_Cat_index.__slots__ = [
    'field',
    'n_cats',
    'a_cats',
    'cat',
    'n_ucats',
    'n_types',
    'type',
    'offset',
]
struct_Cat_index._fields_ = [
    ('field', c_int),
    ('n_cats', c_int),
    ('a_cats', c_int),
    ('cat', POINTER(c_int * 3)),
    ('n_ucats', c_int),
    ('n_types', c_int),
    ('type', (c_int * 2) * 7),
    ('offset', c_long),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 239
class struct_Plus_head(Structure):
    pass

struct_Plus_head.__slots__ = [
    'Version_Major',
    'Version_Minor',
    'Back_Major',
    'Back_Minor',
    'spidx_Version_Major',
    'spidx_Version_Minor',
    'spidx_Back_Major',
    'spidx_Back_Minor',
    'cidx_Version_Major',
    'cidx_Version_Minor',
    'cidx_Back_Major',
    'cidx_Back_Minor',
    'with_z',
    'spidx_with_z',
    'head_size',
    'spidx_head_size',
    'cidx_head_size',
    'release_support',
    'port',
    'spidx_port',
    'cidx_port',
    'mode',
    'built',
    'box',
    'Node',
    'Line',
    'Area',
    'Isle',
    'n_nodes',
    'n_edges',
    'n_lines',
    'n_areas',
    'n_isles',
    'n_volumes',
    'n_holes',
    'n_plines',
    'n_llines',
    'n_blines',
    'n_clines',
    'n_flines',
    'n_klines',
    'alloc_nodes',
    'alloc_edges',
    'alloc_lines',
    'alloc_areas',
    'alloc_isles',
    'alloc_volumes',
    'alloc_holes',
    'Node_offset',
    'Edge_offset',
    'Line_offset',
    'Area_offset',
    'Isle_offset',
    'Volume_offset',
    'Hole_offset',
    'Spidx_built',
    'Node_spidx_offset',
    'Edge_spidx_offset',
    'Line_spidx_offset',
    'Area_spidx_offset',
    'Isle_spidx_offset',
    'Volume_spidx_offset',
    'Hole_spidx_offset',
    'Node_spidx',
    'Line_spidx',
    'Area_spidx',
    'Isle_spidx',
    'update_cidx',
    'n_cidx',
    'a_cidx',
    'cidx',
    'cidx_up_to_date',
    'coor_size',
    'coor_mtime',
    'do_uplist',
    'uplines',
    'alloc_uplines',
    'n_uplines',
    'upnodes',
    'alloc_upnodes',
    'n_upnodes',
]
struct_Plus_head._fields_ = [
    ('Version_Major', c_int),
    ('Version_Minor', c_int),
    ('Back_Major', c_int),
    ('Back_Minor', c_int),
    ('spidx_Version_Major', c_int),
    ('spidx_Version_Minor', c_int),
    ('spidx_Back_Major', c_int),
    ('spidx_Back_Minor', c_int),
    ('cidx_Version_Major', c_int),
    ('cidx_Version_Minor', c_int),
    ('cidx_Back_Major', c_int),
    ('cidx_Back_Minor', c_int),
    ('with_z', c_int),
    ('spidx_with_z', c_int),
    ('head_size', c_long),
    ('spidx_head_size', c_long),
    ('cidx_head_size', c_long),
    ('release_support', c_int),
    ('port', struct_Port_info),
    ('spidx_port', struct_Port_info),
    ('cidx_port', struct_Port_info),
    ('mode', c_int),
    ('built', c_int),
    ('box', struct_bound_box),
    ('Node', POINTER(POINTER(P_NODE))),
    ('Line', POINTER(POINTER(P_LINE))),
    ('Area', POINTER(POINTER(P_AREA))),
    ('Isle', POINTER(POINTER(P_ISLE))),
    ('n_nodes', plus_t),
    ('n_edges', plus_t),
    ('n_lines', plus_t),
    ('n_areas', plus_t),
    ('n_isles', plus_t),
    ('n_volumes', plus_t),
    ('n_holes', plus_t),
    ('n_plines', plus_t),
    ('n_llines', plus_t),
    ('n_blines', plus_t),
    ('n_clines', plus_t),
    ('n_flines', plus_t),
    ('n_klines', plus_t),
    ('alloc_nodes', plus_t),
    ('alloc_edges', plus_t),
    ('alloc_lines', plus_t),
    ('alloc_areas', plus_t),
    ('alloc_isles', plus_t),
    ('alloc_volumes', plus_t),
    ('alloc_holes', plus_t),
    ('Node_offset', c_long),
    ('Edge_offset', c_long),
    ('Line_offset', c_long),
    ('Area_offset', c_long),
    ('Isle_offset', c_long),
    ('Volume_offset', c_long),
    ('Hole_offset', c_long),
    ('Spidx_built', c_int),
    ('Node_spidx_offset', c_long),
    ('Edge_spidx_offset', c_long),
    ('Line_spidx_offset', c_long),
    ('Area_spidx_offset', c_long),
    ('Isle_spidx_offset', c_long),
    ('Volume_spidx_offset', c_long),
    ('Hole_spidx_offset', c_long),
    ('Node_spidx', POINTER(struct_Node)),
    ('Line_spidx', POINTER(struct_Node)),
    ('Area_spidx', POINTER(struct_Node)),
    ('Isle_spidx', POINTER(struct_Node)),
    ('update_cidx', c_int),
    ('n_cidx', c_int),
    ('a_cidx', c_int),
    ('cidx', POINTER(struct_Cat_index)),
    ('cidx_up_to_date', c_int),
    ('coor_size', c_long),
    ('coor_mtime', c_long),
    ('do_uplist', c_int),
    ('uplines', POINTER(c_int)),
    ('alloc_uplines', c_int),
    ('n_uplines', c_int),
    ('upnodes', POINTER(c_int)),
    ('alloc_upnodes', c_int),
    ('n_upnodes', c_int),
]

struct_Map_info.__slots__ = [
    'format',
    'temporary',
    'dblnk',
    'plus',
    'graph_line_type',
    'graph',
    'spCache',
    'edge_fcosts',
    'edge_bcosts',
    'node_costs',
    'cost_multip',
    'open',
    'mode',
    'level',
    'head_only',
    'support_updated',
    'next_line',
    'name',
    'mapset',
    'location',
    'gisdbase',
    'Constraint_region_flag',
    'Constraint_type_flag',
    'Constraint_N',
    'Constraint_S',
    'Constraint_E',
    'Constraint_W',
    'Constraint_T',
    'Constraint_B',
    'Constraint_type',
    'proj',
    'dig_fp',
    'head',
    'fInfo',
    'hist_fp',
    'site_att',
    'n_site_att',
    'n_site_dbl',
    'n_site_str',
]
struct_Map_info._fields_ = [
    ('format', c_int),
    ('temporary', c_int),
    ('dblnk', POINTER(struct_dblinks)),
    ('plus', struct_Plus_head),
    ('graph_line_type', c_int),
    ('graph', dglGraph_s),
    ('spCache', dglSPCache_s),
    ('edge_fcosts', POINTER(c_double)),
    ('edge_bcosts', POINTER(c_double)),
    ('node_costs', POINTER(c_double)),
    ('cost_multip', c_int),
    ('open', c_int),
    ('mode', c_int),
    ('level', c_int),
    ('head_only', c_int),
    ('support_updated', c_int),
    ('next_line', plus_t),
    ('name', String),
    ('mapset', String),
    ('location', String),
    ('gisdbase', String),
    ('Constraint_region_flag', c_int),
    ('Constraint_type_flag', c_int),
    ('Constraint_N', c_double),
    ('Constraint_S', c_double),
    ('Constraint_E', c_double),
    ('Constraint_W', c_double),
    ('Constraint_T', c_double),
    ('Constraint_B', c_double),
    ('Constraint_type', c_int),
    ('proj', c_int),
    ('dig_fp', GVFILE),
    ('head', struct_dig_head),
    ('fInfo', struct_Format_info),
    ('hist_fp', POINTER(FILE)),
    ('site_att', POINTER(SITE_ATT)),
    ('n_site_att', c_int),
    ('n_site_dbl', c_int),
    ('n_site_str', c_int),
]

struct_P_node.__slots__ = [
    'x',
    'y',
    'z',
    'alloc_lines',
    'n_lines',
    'lines',
    'angles',
]
struct_P_node._fields_ = [
    ('x', c_double),
    ('y', c_double),
    ('z', c_double),
    ('alloc_lines', plus_t),
    ('n_lines', plus_t),
    ('lines', POINTER(plus_t)),
    ('angles', POINTER(c_float)),
]

struct_P_line.__slots__ = [
    'N1',
    'N2',
    'left',
    'right',
    'N',
    'S',
    'E',
    'W',
    'T',
    'B',
    'offset',
    'type',
]
struct_P_line._fields_ = [
    ('N1', plus_t),
    ('N2', plus_t),
    ('left', plus_t),
    ('right', plus_t),
    ('N', c_double),
    ('S', c_double),
    ('E', c_double),
    ('W', c_double),
    ('T', c_double),
    ('B', c_double),
    ('offset', c_long),
    ('type', c_int),
]

struct_P_area.__slots__ = [
    'N',
    'S',
    'E',
    'W',
    'T',
    'B',
    'n_lines',
    'alloc_lines',
    'lines',
    'centroid',
    'n_isles',
    'alloc_isles',
    'isles',
]
struct_P_area._fields_ = [
    ('N', c_double),
    ('S', c_double),
    ('E', c_double),
    ('W', c_double),
    ('T', c_double),
    ('B', c_double),
    ('n_lines', plus_t),
    ('alloc_lines', plus_t),
    ('lines', POINTER(plus_t)),
    ('centroid', plus_t),
    ('n_isles', plus_t),
    ('alloc_isles', plus_t),
    ('isles', POINTER(plus_t)),
]

struct_P_isle.__slots__ = [
    'N',
    'S',
    'E',
    'W',
    'T',
    'B',
    'n_lines',
    'alloc_lines',
    'lines',
    'area',
]
struct_P_isle._fields_ = [
    ('N', c_double),
    ('S', c_double),
    ('E', c_double),
    ('W', c_double),
    ('T', c_double),
    ('B', c_double),
    ('n_lines', plus_t),
    ('alloc_lines', plus_t),
    ('lines', POINTER(plus_t)),
    ('area', plus_t),
]

struct_line_pnts.__slots__ = [
    'x',
    'y',
    'z',
    'n_points',
    'alloc_points',
]
struct_line_pnts._fields_ = [
    ('x', POINTER(c_double)),
    ('y', POINTER(c_double)),
    ('z', POINTER(c_double)),
    ('n_points', c_int),
    ('alloc_points', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 507
class struct_line_cats(Structure):
    pass

struct_line_cats.__slots__ = [
    'field',
    'cat',
    'n_cats',
    'alloc_cats',
]
struct_line_cats._fields_ = [
    ('field', POINTER(c_int)),
    ('cat', POINTER(c_int)),
    ('n_cats', c_int),
    ('alloc_cats', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 515
class struct_cat_list(Structure):
    pass

struct_cat_list.__slots__ = [
    'field',
    'min',
    'max',
    'n_ranges',
    'alloc_ranges',
]
struct_cat_list._fields_ = [
    ('field', c_int),
    ('min', POINTER(c_int)),
    ('max', POINTER(c_int)),
    ('n_ranges', c_int),
    ('alloc_ranges', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 525
class struct_ilist(Structure):
    pass

struct_ilist.__slots__ = [
    'value',
    'n_values',
    'alloc_values',
]
struct_ilist._fields_ = [
    ('value', POINTER(c_int)),
    ('n_values', c_int),
    ('alloc_values', c_int),
]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 533
class struct_varray(Structure):
    pass

struct_varray.__slots__ = [
    'size',
    'c',
]
struct_varray._fields_ = [
    ('size', c_int),
    ('c', POINTER(c_int)),
]

VARRAY = struct_varray # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 539

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 542
class struct_spatial_index(Structure):
    pass

struct_spatial_index.__slots__ = [
    'root',
]
struct_spatial_index._fields_ = [
    ('root', POINTER(struct_Node)),
]

SPATIAL_INDEX = struct_spatial_index # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 547

GRAPH = dglGraph_s # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 549

# c:/OSGeo4W/include/geos_c.h: 101
class struct_GEOSGeom_t(Structure):
    pass

GEOSGeometry = struct_GEOSGeom_t # c:/OSGeo4W/include/geos_c.h: 101

# c:/OSGeo4W/include/geos_c.h: 103
class struct_GEOSCoordSeq_t(Structure):
    pass

GEOSCoordSequence = struct_GEOSCoordSeq_t # c:/OSGeo4W/include/geos_c.h: 103

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 20
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_line_struct'):
    Vect_new_line_struct = _libs['grass_vect.6.4.2RC2'].Vect_new_line_struct
    Vect_new_line_struct.restype = POINTER(struct_line_pnts)
    Vect_new_line_struct.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 21
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_append_point'):
    Vect_append_point = _libs['grass_vect.6.4.2RC2'].Vect_append_point
    Vect_append_point.restype = c_int
    Vect_append_point.argtypes = [POINTER(struct_line_pnts), c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 22
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_append_points'):
    Vect_append_points = _libs['grass_vect.6.4.2RC2'].Vect_append_points
    Vect_append_points.restype = c_int
    Vect_append_points.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 23
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_insert_point'):
    Vect_line_insert_point = _libs['grass_vect.6.4.2RC2'].Vect_line_insert_point
    Vect_line_insert_point.restype = c_int
    Vect_line_insert_point.argtypes = [POINTER(struct_line_pnts), c_int, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 24
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_delete_point'):
    Vect_line_delete_point = _libs['grass_vect.6.4.2RC2'].Vect_line_delete_point
    Vect_line_delete_point.restype = c_int
    Vect_line_delete_point.argtypes = [POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 25
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_prune'):
    Vect_line_prune = _libs['grass_vect.6.4.2RC2'].Vect_line_prune
    Vect_line_prune.restype = c_int
    Vect_line_prune.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 26
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_prune_thresh'):
    Vect_line_prune_thresh = _libs['grass_vect.6.4.2RC2'].Vect_line_prune_thresh
    Vect_line_prune_thresh.restype = c_int
    Vect_line_prune_thresh.argtypes = [POINTER(struct_line_pnts), c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 27
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_reverse'):
    Vect_line_reverse = _libs['grass_vect.6.4.2RC2'].Vect_line_reverse
    Vect_line_reverse.restype = None
    Vect_line_reverse.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 28
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_xyz_to_pnts'):
    Vect_copy_xyz_to_pnts = _libs['grass_vect.6.4.2RC2'].Vect_copy_xyz_to_pnts
    Vect_copy_xyz_to_pnts.restype = c_int
    Vect_copy_xyz_to_pnts.argtypes = [POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 30
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_pnts_to_xyz'):
    Vect_copy_pnts_to_xyz = _libs['grass_vect.6.4.2RC2'].Vect_copy_pnts_to_xyz
    Vect_copy_pnts_to_xyz.restype = c_int
    Vect_copy_pnts_to_xyz.argtypes = [POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 32
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_reset_line'):
    Vect_reset_line = _libs['grass_vect.6.4.2RC2'].Vect_reset_line
    Vect_reset_line.restype = c_int
    Vect_reset_line.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 33
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_destroy_line_struct'):
    Vect_destroy_line_struct = _libs['grass_vect.6.4.2RC2'].Vect_destroy_line_struct
    Vect_destroy_line_struct.restype = c_int
    Vect_destroy_line_struct.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 34
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_on_line'):
    Vect_point_on_line = _libs['grass_vect.6.4.2RC2'].Vect_point_on_line
    Vect_point_on_line.restype = c_int
    Vect_point_on_line.argtypes = [POINTER(struct_line_pnts), c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 36
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_segment'):
    Vect_line_segment = _libs['grass_vect.6.4.2RC2'].Vect_line_segment
    Vect_line_segment.restype = c_int
    Vect_line_segment.argtypes = [POINTER(struct_line_pnts), c_double, c_double, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 37
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_length'):
    Vect_line_length = _libs['grass_vect.6.4.2RC2'].Vect_line_length
    Vect_line_length.restype = c_double
    Vect_line_length.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 38
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_area_perimeter'):
    Vect_area_perimeter = _libs['grass_vect.6.4.2RC2'].Vect_area_perimeter
    Vect_area_perimeter.restype = c_double
    Vect_area_perimeter.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 39
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_geodesic_length'):
    Vect_line_geodesic_length = _libs['grass_vect.6.4.2RC2'].Vect_line_geodesic_length
    Vect_line_geodesic_length.restype = c_double
    Vect_line_geodesic_length.argtypes = [POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 40
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_distance'):
    Vect_line_distance = _libs['grass_vect.6.4.2RC2'].Vect_line_distance
    Vect_line_distance.restype = c_int
    Vect_line_distance.argtypes = [POINTER(struct_line_pnts), c_double, c_double, c_double, c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 43
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_box'):
    Vect_line_box = _libs['grass_vect.6.4.2RC2'].Vect_line_box
    Vect_line_box.restype = c_int
    Vect_line_box.argtypes = [POINTER(struct_line_pnts), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 44
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_parallel'):
    Vect_line_parallel = _libs['grass_vect.6.4.2RC2'].Vect_line_parallel
    Vect_line_parallel.restype = None
    Vect_line_parallel.argtypes = [POINTER(struct_line_pnts), c_double, c_double, c_int, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 46
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_parallel2'):
    Vect_line_parallel2 = _libs['grass_vect.6.4.2RC2'].Vect_line_parallel2
    Vect_line_parallel2.restype = None
    Vect_line_parallel2.argtypes = [POINTER(struct_line_pnts), c_double, c_double, c_double, c_int, c_int, c_double, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 49
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_buffer'):
    Vect_line_buffer = _libs['grass_vect.6.4.2RC2'].Vect_line_buffer
    Vect_line_buffer.restype = None
    Vect_line_buffer.argtypes = [POINTER(struct_line_pnts), c_double, c_double, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 50
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_buffer2'):
    Vect_line_buffer2 = _libs['grass_vect.6.4.2RC2'].Vect_line_buffer2
    Vect_line_buffer2.restype = None
    Vect_line_buffer2.argtypes = [POINTER(struct_line_pnts), c_double, c_double, c_double, c_int, c_int, c_double, POINTER(POINTER(struct_line_pnts)), POINTER(POINTER(POINTER(struct_line_pnts))), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 54
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_area_buffer2'):
    Vect_area_buffer2 = _libs['grass_vect.6.4.2RC2'].Vect_area_buffer2
    Vect_area_buffer2.restype = None
    Vect_area_buffer2.argtypes = [POINTER(struct_Map_info), c_int, c_double, c_double, c_double, c_int, c_int, c_double, POINTER(POINTER(struct_line_pnts)), POINTER(POINTER(POINTER(struct_line_pnts))), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 58
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_buffer2'):
    Vect_point_buffer2 = _libs['grass_vect.6.4.2RC2'].Vect_point_buffer2
    Vect_point_buffer2.restype = None
    Vect_point_buffer2.argtypes = [c_double, c_double, c_double, c_double, c_double, c_int, c_double, POINTER(POINTER(struct_line_pnts))]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 64
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_cats_struct'):
    Vect_new_cats_struct = _libs['grass_vect.6.4.2RC2'].Vect_new_cats_struct
    Vect_new_cats_struct.restype = POINTER(struct_line_cats)
    Vect_new_cats_struct.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 65
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cat_set'):
    Vect_cat_set = _libs['grass_vect.6.4.2RC2'].Vect_cat_set
    Vect_cat_set.restype = c_int
    Vect_cat_set.argtypes = [POINTER(struct_line_cats), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 66
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cat_get'):
    Vect_cat_get = _libs['grass_vect.6.4.2RC2'].Vect_cat_get
    Vect_cat_get.restype = c_int
    Vect_cat_get.argtypes = [POINTER(struct_line_cats), c_int, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 67
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cat_del'):
    Vect_cat_del = _libs['grass_vect.6.4.2RC2'].Vect_cat_del
    Vect_cat_del.restype = c_int
    Vect_cat_del.argtypes = [POINTER(struct_line_cats), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 68
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_field_cat_del'):
    Vect_field_cat_del = _libs['grass_vect.6.4.2RC2'].Vect_field_cat_del
    Vect_field_cat_del.restype = c_int
    Vect_field_cat_del.argtypes = [POINTER(struct_line_cats), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 69
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_field_cat_get'):
    Vect_field_cat_get = _libs['grass_vect.6.4.2RC2'].Vect_field_cat_get
    Vect_field_cat_get.restype = c_int
    Vect_field_cat_get.argtypes = [POINTER(struct_line_cats), c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 70
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cat_in_array'):
    Vect_cat_in_array = _libs['grass_vect.6.4.2RC2'].Vect_cat_in_array
    Vect_cat_in_array.restype = c_int
    Vect_cat_in_array.argtypes = [c_int, POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 71
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_reset_cats'):
    Vect_reset_cats = _libs['grass_vect.6.4.2RC2'].Vect_reset_cats
    Vect_reset_cats.restype = c_int
    Vect_reset_cats.argtypes = [POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 72
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_destroy_cats_struct'):
    Vect_destroy_cats_struct = _libs['grass_vect.6.4.2RC2'].Vect_destroy_cats_struct
    Vect_destroy_cats_struct.restype = c_int
    Vect_destroy_cats_struct.argtypes = [POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 73
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_cats'):
    Vect_get_area_cats = _libs['grass_vect.6.4.2RC2'].Vect_get_area_cats
    Vect_get_area_cats.restype = c_int
    Vect_get_area_cats.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 74
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_cat'):
    Vect_get_area_cat = _libs['grass_vect.6.4.2RC2'].Vect_get_area_cat
    Vect_get_area_cat.restype = c_int
    Vect_get_area_cat.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 75
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_line_cat'):
    Vect_get_line_cat = _libs['grass_vect.6.4.2RC2'].Vect_get_line_cat
    Vect_get_line_cat.restype = c_int
    Vect_get_line_cat.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 78
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_cat_list'):
    Vect_new_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_new_cat_list
    Vect_new_cat_list.restype = POINTER(struct_cat_list)
    Vect_new_cat_list.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 79
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_str_to_cat_list'):
    Vect_str_to_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_str_to_cat_list
    Vect_str_to_cat_list.restype = c_int
    Vect_str_to_cat_list.argtypes = [String, POINTER(struct_cat_list)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 80
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_array_to_cat_list'):
    Vect_array_to_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_array_to_cat_list
    Vect_array_to_cat_list.restype = c_int
    Vect_array_to_cat_list.argtypes = [POINTER(c_int), c_int, POINTER(struct_cat_list)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 81
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cat_in_cat_list'):
    Vect_cat_in_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_cat_in_cat_list
    Vect_cat_in_cat_list.restype = c_int
    Vect_cat_in_cat_list.argtypes = [c_int, POINTER(struct_cat_list)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 82
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_destroy_cat_list'):
    Vect_destroy_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_destroy_cat_list
    Vect_destroy_cat_list.restype = c_int
    Vect_destroy_cat_list.argtypes = [POINTER(struct_cat_list)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 85
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_varray'):
    Vect_new_varray = _libs['grass_vect.6.4.2RC2'].Vect_new_varray
    Vect_new_varray.restype = POINTER(VARRAY)
    Vect_new_varray.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 86
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_varray_from_cat_string'):
    Vect_set_varray_from_cat_string = _libs['grass_vect.6.4.2RC2'].Vect_set_varray_from_cat_string
    Vect_set_varray_from_cat_string.restype = c_int
    Vect_set_varray_from_cat_string.argtypes = [POINTER(struct_Map_info), c_int, String, c_int, c_int, POINTER(VARRAY)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 88
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_varray_from_cat_list'):
    Vect_set_varray_from_cat_list = _libs['grass_vect.6.4.2RC2'].Vect_set_varray_from_cat_list
    Vect_set_varray_from_cat_list.restype = c_int
    Vect_set_varray_from_cat_list.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_cat_list), c_int, c_int, POINTER(VARRAY)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 90
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_varray_from_db'):
    Vect_set_varray_from_db = _libs['grass_vect.6.4.2RC2'].Vect_set_varray_from_db
    Vect_set_varray_from_db.restype = c_int
    Vect_set_varray_from_db.argtypes = [POINTER(struct_Map_info), c_int, String, c_int, c_int, POINTER(VARRAY)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 94
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_dblinks_struct'):
    Vect_new_dblinks_struct = _libs['grass_vect.6.4.2RC2'].Vect_new_dblinks_struct
    Vect_new_dblinks_struct.restype = POINTER(struct_dblinks)
    Vect_new_dblinks_struct.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 95
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_reset_dblinks'):
    Vect_reset_dblinks = _libs['grass_vect.6.4.2RC2'].Vect_reset_dblinks
    Vect_reset_dblinks.restype = None
    Vect_reset_dblinks.argtypes = [POINTER(struct_dblinks)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 96
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_add_dblink'):
    Vect_add_dblink = _libs['grass_vect.6.4.2RC2'].Vect_add_dblink
    Vect_add_dblink.restype = c_int
    Vect_add_dblink.argtypes = [POINTER(struct_dblinks), c_int, String, String, String, String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 98
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_check_dblink'):
    Vect_check_dblink = _libs['grass_vect.6.4.2RC2'].Vect_check_dblink
    Vect_check_dblink.restype = c_int
    Vect_check_dblink.argtypes = [POINTER(struct_dblinks), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 99
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_map_add_dblink'):
    Vect_map_add_dblink = _libs['grass_vect.6.4.2RC2'].Vect_map_add_dblink
    Vect_map_add_dblink.restype = c_int
    Vect_map_add_dblink.argtypes = [POINTER(struct_Map_info), c_int, String, String, String, String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 102
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_map_del_dblink'):
    Vect_map_del_dblink = _libs['grass_vect.6.4.2RC2'].Vect_map_del_dblink
    Vect_map_del_dblink.restype = c_int
    Vect_map_del_dblink.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 103
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_map_check_dblink'):
    Vect_map_check_dblink = _libs['grass_vect.6.4.2RC2'].Vect_map_check_dblink
    Vect_map_check_dblink.restype = c_int
    Vect_map_check_dblink.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 104
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_dblinks'):
    Vect_read_dblinks = _libs['grass_vect.6.4.2RC2'].Vect_read_dblinks
    Vect_read_dblinks.restype = c_int
    Vect_read_dblinks.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 105
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_write_dblinks'):
    Vect_write_dblinks = _libs['grass_vect.6.4.2RC2'].Vect_write_dblinks
    Vect_write_dblinks.restype = c_int
    Vect_write_dblinks.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 106
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_default_field_info'):
    Vect_default_field_info = _libs['grass_vect.6.4.2RC2'].Vect_default_field_info
    Vect_default_field_info.restype = POINTER(struct_field_info)
    Vect_default_field_info.argtypes = [POINTER(struct_Map_info), c_int, String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 108
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_dblink'):
    Vect_get_dblink = _libs['grass_vect.6.4.2RC2'].Vect_get_dblink
    Vect_get_dblink.restype = POINTER(struct_field_info)
    Vect_get_dblink.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 109
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_field'):
    Vect_get_field = _libs['grass_vect.6.4.2RC2'].Vect_get_field
    Vect_get_field.restype = POINTER(struct_field_info)
    Vect_get_field.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 110
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_db_updated'):
    Vect_set_db_updated = _libs['grass_vect.6.4.2RC2'].Vect_set_db_updated
    Vect_set_db_updated.restype = None
    Vect_set_db_updated.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 111
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_column_names'):
    Vect_get_column_names = _libs['grass_vect.6.4.2RC2'].Vect_get_column_names
    Vect_get_column_names.restype = ReturnString
    Vect_get_column_names.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 112
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_column_types'):
    Vect_get_column_types = _libs['grass_vect.6.4.2RC2'].Vect_get_column_types
    Vect_get_column_types.restype = ReturnString
    Vect_get_column_types.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 113
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_column_names_types'):
    Vect_get_column_names_types = _libs['grass_vect.6.4.2RC2'].Vect_get_column_names_types
    Vect_get_column_names_types.restype = ReturnString
    Vect_get_column_names_types.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 116
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_new_list'):
    Vect_new_list = _libs['grass_vect.6.4.2RC2'].Vect_new_list
    Vect_new_list.restype = POINTER(struct_ilist)
    Vect_new_list.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 117
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_list_append'):
    Vect_list_append = _libs['grass_vect.6.4.2RC2'].Vect_list_append
    Vect_list_append.restype = c_int
    Vect_list_append.argtypes = [POINTER(struct_ilist), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 118
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_list_append_list'):
    Vect_list_append_list = _libs['grass_vect.6.4.2RC2'].Vect_list_append_list
    Vect_list_append_list.restype = c_int
    Vect_list_append_list.argtypes = [POINTER(struct_ilist), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 119
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_list_delete'):
    Vect_list_delete = _libs['grass_vect.6.4.2RC2'].Vect_list_delete
    Vect_list_delete.restype = c_int
    Vect_list_delete.argtypes = [POINTER(struct_ilist), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 120
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_list_delete_list'):
    Vect_list_delete_list = _libs['grass_vect.6.4.2RC2'].Vect_list_delete_list
    Vect_list_delete_list.restype = c_int
    Vect_list_delete_list.argtypes = [POINTER(struct_ilist), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 121
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_val_in_list'):
    Vect_val_in_list = _libs['grass_vect.6.4.2RC2'].Vect_val_in_list
    Vect_val_in_list.restype = c_int
    Vect_val_in_list.argtypes = [POINTER(struct_ilist), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 122
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_reset_list'):
    Vect_reset_list = _libs['grass_vect.6.4.2RC2'].Vect_reset_list
    Vect_reset_list.restype = c_int
    Vect_reset_list.argtypes = [POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 123
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_destroy_list'):
    Vect_destroy_list = _libs['grass_vect.6.4.2RC2'].Vect_destroy_list
    Vect_destroy_list.restype = c_int
    Vect_destroy_list.argtypes = [POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 126
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_in_box'):
    Vect_point_in_box = _libs['grass_vect.6.4.2RC2'].Vect_point_in_box
    Vect_point_in_box.restype = c_int
    Vect_point_in_box.argtypes = [c_double, c_double, c_double, POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 127
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_box_overlap'):
    Vect_box_overlap = _libs['grass_vect.6.4.2RC2'].Vect_box_overlap
    Vect_box_overlap.restype = c_int
    Vect_box_overlap.argtypes = [POINTER(BOUND_BOX), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 128
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_box_copy'):
    Vect_box_copy = _libs['grass_vect.6.4.2RC2'].Vect_box_copy
    Vect_box_copy.restype = c_int
    Vect_box_copy.argtypes = [POINTER(BOUND_BOX), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 129
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_box_extend'):
    Vect_box_extend = _libs['grass_vect.6.4.2RC2'].Vect_box_extend
    Vect_box_extend.restype = c_int
    Vect_box_extend.argtypes = [POINTER(BOUND_BOX), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 130
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_box_clip'):
    Vect_box_clip = _libs['grass_vect.6.4.2RC2'].Vect_box_clip
    Vect_box_clip.restype = c_int
    Vect_box_clip.argtypes = [POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 131
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_region_box'):
    Vect_region_box = _libs['grass_vect.6.4.2RC2'].Vect_region_box
    Vect_region_box.restype = c_int
    Vect_region_box.argtypes = [POINTER(struct_Cell_head), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 134
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_init'):
    Vect_spatial_index_init = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_init
    Vect_spatial_index_init.restype = None
    Vect_spatial_index_init.argtypes = [POINTER(SPATIAL_INDEX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 135
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_destroy'):
    Vect_spatial_index_destroy = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_destroy
    Vect_spatial_index_destroy.restype = None
    Vect_spatial_index_destroy.argtypes = [POINTER(SPATIAL_INDEX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 136
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_add_item'):
    Vect_spatial_index_add_item = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_add_item
    Vect_spatial_index_add_item.restype = None
    Vect_spatial_index_add_item.argtypes = [POINTER(SPATIAL_INDEX), c_int, POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 137
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_del_item'):
    Vect_spatial_index_del_item = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_del_item
    Vect_spatial_index_del_item.restype = None
    Vect_spatial_index_del_item.argtypes = [POINTER(SPATIAL_INDEX), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 138
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_select'):
    Vect_spatial_index_select = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_select
    Vect_spatial_index_select.restype = c_int
    Vect_spatial_index_select.argtypes = [POINTER(SPATIAL_INDEX), POINTER(BOUND_BOX), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 141
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_num_fields'):
    Vect_cidx_get_num_fields = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_num_fields
    Vect_cidx_get_num_fields.restype = c_int
    Vect_cidx_get_num_fields.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 142
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_field_number'):
    Vect_cidx_get_field_number = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_field_number
    Vect_cidx_get_field_number.restype = c_int
    Vect_cidx_get_field_number.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 143
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_field_index'):
    Vect_cidx_get_field_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_field_index
    Vect_cidx_get_field_index.restype = c_int
    Vect_cidx_get_field_index.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 144
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_num_unique_cats_by_index'):
    Vect_cidx_get_num_unique_cats_by_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_num_unique_cats_by_index
    Vect_cidx_get_num_unique_cats_by_index.restype = c_int
    Vect_cidx_get_num_unique_cats_by_index.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 145
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_num_cats_by_index'):
    Vect_cidx_get_num_cats_by_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_num_cats_by_index
    Vect_cidx_get_num_cats_by_index.restype = c_int
    Vect_cidx_get_num_cats_by_index.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 146
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_num_types_by_index'):
    Vect_cidx_get_num_types_by_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_num_types_by_index
    Vect_cidx_get_num_types_by_index.restype = c_int
    Vect_cidx_get_num_types_by_index.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 147
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_type_count_by_index'):
    Vect_cidx_get_type_count_by_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_type_count_by_index
    Vect_cidx_get_type_count_by_index.restype = c_int
    Vect_cidx_get_type_count_by_index.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 149
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_type_count'):
    Vect_cidx_get_type_count = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_type_count
    Vect_cidx_get_type_count.restype = c_int
    Vect_cidx_get_type_count.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 150
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_get_cat_by_index'):
    Vect_cidx_get_cat_by_index = _libs['grass_vect.6.4.2RC2'].Vect_cidx_get_cat_by_index
    Vect_cidx_get_cat_by_index.restype = c_int
    Vect_cidx_get_cat_by_index.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(c_int), POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 152
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_find_next'):
    Vect_cidx_find_next = _libs['grass_vect.6.4.2RC2'].Vect_cidx_find_next
    Vect_cidx_find_next.restype = c_int
    Vect_cidx_find_next.argtypes = [POINTER(struct_Map_info), c_int, c_int, c_int, c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 153
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_find_all'):
    Vect_cidx_find_all = _libs['grass_vect.6.4.2RC2'].Vect_cidx_find_all
    Vect_cidx_find_all.restype = None
    Vect_cidx_find_all.argtypes = [POINTER(struct_Map_info), c_int, c_int, c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 154
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_dump'):
    Vect_cidx_dump = _libs['grass_vect.6.4.2RC2'].Vect_cidx_dump
    Vect_cidx_dump.restype = c_int
    Vect_cidx_dump.argtypes = [POINTER(struct_Map_info), POINTER(FILE)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 155
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_save'):
    Vect_cidx_save = _libs['grass_vect.6.4.2RC2'].Vect_cidx_save
    Vect_cidx_save.restype = c_int
    Vect_cidx_save.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 156
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_cidx_open'):
    Vect_cidx_open = _libs['grass_vect.6.4.2RC2'].Vect_cidx_open
    Vect_cidx_open.restype = c_int
    Vect_cidx_open.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 160
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_header'):
    Vect_read_header = _libs['grass_vect.6.4.2RC2'].Vect_read_header
    Vect_read_header.restype = c_int
    Vect_read_header.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 161
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_write_header'):
    Vect_write_header = _libs['grass_vect.6.4.2RC2'].Vect_write_header
    Vect_write_header.restype = c_int
    Vect_write_header.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 162
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_name'):
    Vect_get_name = _libs['grass_vect.6.4.2RC2'].Vect_get_name
    Vect_get_name.restype = ReturnString
    Vect_get_name.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 163
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_mapset'):
    Vect_get_mapset = _libs['grass_vect.6.4.2RC2'].Vect_get_mapset
    Vect_get_mapset.restype = ReturnString
    Vect_get_mapset.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 164
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_full_name'):
    Vect_get_full_name = _libs['grass_vect.6.4.2RC2'].Vect_get_full_name
    Vect_get_full_name.restype = ReturnString
    Vect_get_full_name.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 165
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_is_3d'):
    Vect_is_3d = _libs['grass_vect.6.4.2RC2'].Vect_is_3d
    Vect_is_3d.restype = c_int
    Vect_is_3d.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 166
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_organization'):
    Vect_set_organization = _libs['grass_vect.6.4.2RC2'].Vect_set_organization
    Vect_set_organization.restype = c_int
    Vect_set_organization.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 167
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_organization'):
    Vect_get_organization = _libs['grass_vect.6.4.2RC2'].Vect_get_organization
    Vect_get_organization.restype = ReturnString
    Vect_get_organization.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 168
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_date'):
    Vect_set_date = _libs['grass_vect.6.4.2RC2'].Vect_set_date
    Vect_set_date.restype = c_int
    Vect_set_date.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 169
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_date'):
    Vect_get_date = _libs['grass_vect.6.4.2RC2'].Vect_get_date
    Vect_get_date.restype = ReturnString
    Vect_get_date.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 170
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_person'):
    Vect_set_person = _libs['grass_vect.6.4.2RC2'].Vect_set_person
    Vect_set_person.restype = c_int
    Vect_set_person.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 171
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_person'):
    Vect_get_person = _libs['grass_vect.6.4.2RC2'].Vect_get_person
    Vect_get_person.restype = ReturnString
    Vect_get_person.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 172
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_map_name'):
    Vect_set_map_name = _libs['grass_vect.6.4.2RC2'].Vect_set_map_name
    Vect_set_map_name.restype = c_int
    Vect_set_map_name.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 173
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_map_name'):
    Vect_get_map_name = _libs['grass_vect.6.4.2RC2'].Vect_get_map_name
    Vect_get_map_name.restype = ReturnString
    Vect_get_map_name.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 174
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_map_date'):
    Vect_set_map_date = _libs['grass_vect.6.4.2RC2'].Vect_set_map_date
    Vect_set_map_date.restype = c_int
    Vect_set_map_date.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 175
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_map_date'):
    Vect_get_map_date = _libs['grass_vect.6.4.2RC2'].Vect_get_map_date
    Vect_get_map_date.restype = ReturnString
    Vect_get_map_date.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 176
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_comment'):
    Vect_set_comment = _libs['grass_vect.6.4.2RC2'].Vect_set_comment
    Vect_set_comment.restype = c_int
    Vect_set_comment.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 177
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_comment'):
    Vect_get_comment = _libs['grass_vect.6.4.2RC2'].Vect_get_comment
    Vect_get_comment.restype = ReturnString
    Vect_get_comment.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 178
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_scale'):
    Vect_set_scale = _libs['grass_vect.6.4.2RC2'].Vect_set_scale
    Vect_set_scale.restype = c_int
    Vect_set_scale.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 179
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_scale'):
    Vect_get_scale = _libs['grass_vect.6.4.2RC2'].Vect_get_scale
    Vect_get_scale.restype = c_int
    Vect_get_scale.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 180
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_zone'):
    Vect_set_zone = _libs['grass_vect.6.4.2RC2'].Vect_set_zone
    Vect_set_zone.restype = c_int
    Vect_set_zone.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 181
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_zone'):
    Vect_get_zone = _libs['grass_vect.6.4.2RC2'].Vect_get_zone
    Vect_get_zone.restype = c_int
    Vect_get_zone.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 182
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_proj'):
    Vect_get_proj = _libs['grass_vect.6.4.2RC2'].Vect_get_proj
    Vect_get_proj.restype = c_int
    Vect_get_proj.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 183
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_proj_name'):
    Vect_get_proj_name = _libs['grass_vect.6.4.2RC2'].Vect_get_proj_name
    Vect_get_proj_name.restype = ReturnString
    Vect_get_proj_name.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 184
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_thresh'):
    Vect_set_thresh = _libs['grass_vect.6.4.2RC2'].Vect_set_thresh
    Vect_set_thresh.restype = c_int
    Vect_set_thresh.argtypes = [POINTER(struct_Map_info), c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 185
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_thresh'):
    Vect_get_thresh = _libs['grass_vect.6.4.2RC2'].Vect_get_thresh
    Vect_get_thresh.restype = c_double
    Vect_get_thresh.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 186
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_constraint_box'):
    Vect_get_constraint_box = _libs['grass_vect.6.4.2RC2'].Vect_get_constraint_box
    Vect_get_constraint_box.restype = c_int
    Vect_get_constraint_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 190
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_level'):
    Vect_level = _libs['grass_vect.6.4.2RC2'].Vect_level
    Vect_level.restype = c_int
    Vect_level.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 191
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_nodes'):
    Vect_get_num_nodes = _libs['grass_vect.6.4.2RC2'].Vect_get_num_nodes
    Vect_get_num_nodes.restype = c_int
    Vect_get_num_nodes.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 192
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_primitives'):
    Vect_get_num_primitives = _libs['grass_vect.6.4.2RC2'].Vect_get_num_primitives
    Vect_get_num_primitives.restype = c_int
    Vect_get_num_primitives.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 193
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_lines'):
    Vect_get_num_lines = _libs['grass_vect.6.4.2RC2'].Vect_get_num_lines
    Vect_get_num_lines.restype = c_int
    Vect_get_num_lines.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 194
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_areas'):
    Vect_get_num_areas = _libs['grass_vect.6.4.2RC2'].Vect_get_num_areas
    Vect_get_num_areas.restype = c_int
    Vect_get_num_areas.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 195
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_kernels'):
    Vect_get_num_kernels = _libs['grass_vect.6.4.2RC2'].Vect_get_num_kernels
    Vect_get_num_kernels.restype = c_int
    Vect_get_num_kernels.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 196
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_faces'):
    Vect_get_num_faces = _libs['grass_vect.6.4.2RC2'].Vect_get_num_faces
    Vect_get_num_faces.restype = c_int
    Vect_get_num_faces.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 197
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_volumes'):
    Vect_get_num_volumes = _libs['grass_vect.6.4.2RC2'].Vect_get_num_volumes
    Vect_get_num_volumes.restype = c_int
    Vect_get_num_volumes.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 198
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_islands'):
    Vect_get_num_islands = _libs['grass_vect.6.4.2RC2'].Vect_get_num_islands
    Vect_get_num_islands.restype = c_int
    Vect_get_num_islands.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 199
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_line_box'):
    Vect_get_line_box = _libs['grass_vect.6.4.2RC2'].Vect_get_line_box
    Vect_get_line_box.restype = c_int
    Vect_get_line_box.argtypes = [POINTER(struct_Map_info), c_int, POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 200
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_box'):
    Vect_get_area_box = _libs['grass_vect.6.4.2RC2'].Vect_get_area_box
    Vect_get_area_box.restype = c_int
    Vect_get_area_box.argtypes = [POINTER(struct_Map_info), c_int, POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 201
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_isle_box'):
    Vect_get_isle_box = _libs['grass_vect.6.4.2RC2'].Vect_get_isle_box
    Vect_get_isle_box.restype = c_int
    Vect_get_isle_box.argtypes = [POINTER(struct_Map_info), c_int, POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 202
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_map_box'):
    Vect_get_map_box = _libs['grass_vect.6.4.2RC2'].Vect_get_map_box
    Vect_get_map_box.restype = c_int
    Vect_get_map_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 203
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V__map_overlap'):
    V__map_overlap = _libs['grass_vect.6.4.2RC2'].V__map_overlap
    V__map_overlap.restype = c_int
    V__map_overlap.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 204
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_release_support'):
    Vect_set_release_support = _libs['grass_vect.6.4.2RC2'].Vect_set_release_support
    Vect_set_release_support.restype = None
    Vect_set_release_support.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 205
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_category_index_update'):
    Vect_set_category_index_update = _libs['grass_vect.6.4.2RC2'].Vect_set_category_index_update
    Vect_set_category_index_update.restype = None
    Vect_set_category_index_update.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 208
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_fatal_error'):
    Vect_set_fatal_error = _libs['grass_vect.6.4.2RC2'].Vect_set_fatal_error
    Vect_set_fatal_error.restype = c_int
    Vect_set_fatal_error.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 209
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_fatal_error'):
    Vect_get_fatal_error = _libs['grass_vect.6.4.2RC2'].Vect_get_fatal_error
    Vect_get_fatal_error.restype = c_int
    Vect_get_fatal_error.argtypes = []

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 212
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_check_input_output_name'):
    Vect_check_input_output_name = _libs['grass_vect.6.4.2RC2'].Vect_check_input_output_name
    Vect_check_input_output_name.restype = c_int
    Vect_check_input_output_name.argtypes = [String, String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 213
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_legal_filename'):
    Vect_legal_filename = _libs['grass_vect.6.4.2RC2'].Vect_legal_filename
    Vect_legal_filename.restype = c_int
    Vect_legal_filename.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 214
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_open_level'):
    Vect_set_open_level = _libs['grass_vect.6.4.2RC2'].Vect_set_open_level
    Vect_set_open_level.restype = c_int
    Vect_set_open_level.argtypes = [c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 215
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_old'):
    Vect_open_old = _libs['grass_vect.6.4.2RC2'].Vect_open_old
    Vect_open_old.restype = c_int
    Vect_open_old.argtypes = [POINTER(struct_Map_info), String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 216
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_old_head'):
    Vect_open_old_head = _libs['grass_vect.6.4.2RC2'].Vect_open_old_head
    Vect_open_old_head.restype = c_int
    Vect_open_old_head.argtypes = [POINTER(struct_Map_info), String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 217
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_new'):
    Vect_open_new = _libs['grass_vect.6.4.2RC2'].Vect_open_new
    Vect_open_new.restype = c_int
    Vect_open_new.argtypes = [POINTER(struct_Map_info), String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 218
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_update'):
    Vect_open_update = _libs['grass_vect.6.4.2RC2'].Vect_open_update
    Vect_open_update.restype = c_int
    Vect_open_update.argtypes = [POINTER(struct_Map_info), String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 219
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_update_head'):
    Vect_open_update_head = _libs['grass_vect.6.4.2RC2'].Vect_open_update_head
    Vect_open_update_head.restype = c_int
    Vect_open_update_head.argtypes = [POINTER(struct_Map_info), String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 220
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_head_data'):
    Vect_copy_head_data = _libs['grass_vect.6.4.2RC2'].Vect_copy_head_data
    Vect_copy_head_data.restype = c_int
    Vect_copy_head_data.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 221
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build'):
    Vect_build = _libs['grass_vect.6.4.2RC2'].Vect_build
    Vect_build.restype = c_int
    Vect_build.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 222
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_built'):
    Vect_get_built = _libs['grass_vect.6.4.2RC2'].Vect_get_built
    Vect_get_built.restype = c_int
    Vect_get_built.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 223
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_partial'):
    Vect_build_partial = _libs['grass_vect.6.4.2RC2'].Vect_build_partial
    Vect_build_partial.restype = c_int
    Vect_build_partial.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 224
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_constraint_region'):
    Vect_set_constraint_region = _libs['grass_vect.6.4.2RC2'].Vect_set_constraint_region
    Vect_set_constraint_region.restype = c_int
    Vect_set_constraint_region.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 226
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_set_constraint_type'):
    Vect_set_constraint_type = _libs['grass_vect.6.4.2RC2'].Vect_set_constraint_type
    Vect_set_constraint_type.restype = c_int
    Vect_set_constraint_type.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 227
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_remove_constraints'):
    Vect_remove_constraints = _libs['grass_vect.6.4.2RC2'].Vect_remove_constraints
    Vect_remove_constraints.restype = c_int
    Vect_remove_constraints.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 228
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_rewind'):
    Vect_rewind = _libs['grass_vect.6.4.2RC2'].Vect_rewind
    Vect_rewind.restype = c_int
    Vect_rewind.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 229
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_close'):
    Vect_close = _libs['grass_vect.6.4.2RC2'].Vect_close
    Vect_close.restype = c_int
    Vect_close.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 233
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_next_line'):
    Vect_read_next_line = _libs['grass_vect.6.4.2RC2'].Vect_read_next_line
    Vect_read_next_line.restype = c_int
    Vect_read_next_line.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 235
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_write_line'):
    Vect_write_line = _libs['grass_vect.6.4.2RC2'].Vect_write_line
    Vect_write_line.restype = c_long
    Vect_write_line.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 238
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_dblinks'):
    Vect_get_num_dblinks = _libs['grass_vect.6.4.2RC2'].Vect_get_num_dblinks
    Vect_get_num_dblinks.restype = c_int
    Vect_get_num_dblinks.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 241
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_line'):
    Vect_read_line = _libs['grass_vect.6.4.2RC2'].Vect_read_line
    Vect_read_line.restype = c_int
    Vect_read_line.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 243
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_rewrite_line'):
    Vect_rewrite_line = _libs['grass_vect.6.4.2RC2'].Vect_rewrite_line
    Vect_rewrite_line.restype = c_int
    Vect_rewrite_line.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 245
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_delete_line'):
    Vect_delete_line = _libs['grass_vect.6.4.2RC2'].Vect_delete_line
    Vect_delete_line.restype = c_int
    Vect_delete_line.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 246
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_restore_line'):
    Vect_restore_line = _libs['grass_vect.6.4.2RC2'].Vect_restore_line
    Vect_restore_line.restype = c_int
    Vect_restore_line.argtypes = [POINTER(struct_Map_info), c_int, c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 248
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_alive'):
    Vect_line_alive = _libs['grass_vect.6.4.2RC2'].Vect_line_alive
    Vect_line_alive.restype = c_int
    Vect_line_alive.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 249
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_node_alive'):
    Vect_node_alive = _libs['grass_vect.6.4.2RC2'].Vect_node_alive
    Vect_node_alive.restype = c_int
    Vect_node_alive.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 250
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_area_alive'):
    Vect_area_alive = _libs['grass_vect.6.4.2RC2'].Vect_area_alive
    Vect_area_alive.restype = c_int
    Vect_area_alive.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 251
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_isle_alive'):
    Vect_isle_alive = _libs['grass_vect.6.4.2RC2'].Vect_isle_alive
    Vect_isle_alive.restype = c_int
    Vect_isle_alive.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 252
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_line_nodes'):
    Vect_get_line_nodes = _libs['grass_vect.6.4.2RC2'].Vect_get_line_nodes
    Vect_get_line_nodes.restype = c_int
    Vect_get_line_nodes.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 253
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_line_areas'):
    Vect_get_line_areas = _libs['grass_vect.6.4.2RC2'].Vect_get_line_areas
    Vect_get_line_areas.restype = c_int
    Vect_get_line_areas.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_int), POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 254
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_line_offset'):
    Vect_get_line_offset = _libs['grass_vect.6.4.2RC2'].Vect_get_line_offset
    Vect_get_line_offset.restype = c_long
    Vect_get_line_offset.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 256
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_node_coor'):
    Vect_get_node_coor = _libs['grass_vect.6.4.2RC2'].Vect_get_node_coor
    Vect_get_node_coor.restype = c_int
    Vect_get_node_coor.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 257
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_node_n_lines'):
    Vect_get_node_n_lines = _libs['grass_vect.6.4.2RC2'].Vect_get_node_n_lines
    Vect_get_node_n_lines.restype = c_int
    Vect_get_node_n_lines.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 258
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_node_line'):
    Vect_get_node_line = _libs['grass_vect.6.4.2RC2'].Vect_get_node_line
    Vect_get_node_line.restype = c_int
    Vect_get_node_line.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 259
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_node_line_angle'):
    Vect_get_node_line_angle = _libs['grass_vect.6.4.2RC2'].Vect_get_node_line_angle
    Vect_get_node_line_angle.restype = c_float
    Vect_get_node_line_angle.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 261
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_points'):
    Vect_get_area_points = _libs['grass_vect.6.4.2RC2'].Vect_get_area_points
    Vect_get_area_points.restype = c_int
    Vect_get_area_points.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 262
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_centroid'):
    Vect_get_area_centroid = _libs['grass_vect.6.4.2RC2'].Vect_get_area_centroid
    Vect_get_area_centroid.restype = c_int
    Vect_get_area_centroid.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 263
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_num_isles'):
    Vect_get_area_num_isles = _libs['grass_vect.6.4.2RC2'].Vect_get_area_num_isles
    Vect_get_area_num_isles.restype = c_int
    Vect_get_area_num_isles.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 264
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_isle'):
    Vect_get_area_isle = _libs['grass_vect.6.4.2RC2'].Vect_get_area_isle
    Vect_get_area_isle.restype = c_int
    Vect_get_area_isle.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 265
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_area'):
    Vect_get_area_area = _libs['grass_vect.6.4.2RC2'].Vect_get_area_area
    Vect_get_area_area.restype = c_double
    Vect_get_area_area.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 266
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_boundaries'):
    Vect_get_area_boundaries = _libs['grass_vect.6.4.2RC2'].Vect_get_area_boundaries
    Vect_get_area_boundaries.restype = c_int
    Vect_get_area_boundaries.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 268
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_isle_points'):
    Vect_get_isle_points = _libs['grass_vect.6.4.2RC2'].Vect_get_isle_points
    Vect_get_isle_points.restype = c_int
    Vect_get_isle_points.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 269
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_isle_area'):
    Vect_get_isle_area = _libs['grass_vect.6.4.2RC2'].Vect_get_isle_area
    Vect_get_isle_area.restype = c_int
    Vect_get_isle_area.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 270
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_isle_boundaries'):
    Vect_get_isle_boundaries = _libs['grass_vect.6.4.2RC2'].Vect_get_isle_boundaries
    Vect_get_isle_boundaries.restype = c_int
    Vect_get_isle_boundaries.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 272
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_centroid_area'):
    Vect_get_centroid_area = _libs['grass_vect.6.4.2RC2'].Vect_get_centroid_area
    Vect_get_centroid_area.restype = c_int
    Vect_get_centroid_area.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 275
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_updated_lines'):
    Vect_get_num_updated_lines = _libs['grass_vect.6.4.2RC2'].Vect_get_num_updated_lines
    Vect_get_num_updated_lines.restype = c_int
    Vect_get_num_updated_lines.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 276
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_updated_line'):
    Vect_get_updated_line = _libs['grass_vect.6.4.2RC2'].Vect_get_updated_line
    Vect_get_updated_line.restype = c_int
    Vect_get_updated_line.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 277
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_num_updated_nodes'):
    Vect_get_num_updated_nodes = _libs['grass_vect.6.4.2RC2'].Vect_get_num_updated_nodes
    Vect_get_num_updated_nodes.restype = c_int
    Vect_get_num_updated_nodes.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 278
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_updated_node'):
    Vect_get_updated_node = _libs['grass_vect.6.4.2RC2'].Vect_get_updated_node
    Vect_get_updated_node.restype = c_int
    Vect_get_updated_node.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 281
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_hist_command'):
    Vect_hist_command = _libs['grass_vect.6.4.2RC2'].Vect_hist_command
    Vect_hist_command.restype = c_int
    Vect_hist_command.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 282
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_hist_write'):
    Vect_hist_write = _libs['grass_vect.6.4.2RC2'].Vect_hist_write
    Vect_hist_write.restype = c_int
    Vect_hist_write.argtypes = [POINTER(struct_Map_info), String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 283
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_hist_copy'):
    Vect_hist_copy = _libs['grass_vect.6.4.2RC2'].Vect_hist_copy
    Vect_hist_copy.restype = c_int
    Vect_hist_copy.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 284
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_hist_rewind'):
    Vect_hist_rewind = _libs['grass_vect.6.4.2RC2'].Vect_hist_rewind
    Vect_hist_rewind.restype = None
    Vect_hist_rewind.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 285
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_hist_read'):
    Vect_hist_read = _libs['grass_vect.6.4.2RC2'].Vect_hist_read
    Vect_hist_read.restype = ReturnString
    Vect_hist_read.argtypes = [String, c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 288
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_lines_by_box'):
    Vect_select_lines_by_box = _libs['grass_vect.6.4.2RC2'].Vect_select_lines_by_box
    Vect_select_lines_by_box.restype = c_int
    Vect_select_lines_by_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX), c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 290
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_areas_by_box'):
    Vect_select_areas_by_box = _libs['grass_vect.6.4.2RC2'].Vect_select_areas_by_box
    Vect_select_areas_by_box.restype = c_int
    Vect_select_areas_by_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 291
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_isles_by_box'):
    Vect_select_isles_by_box = _libs['grass_vect.6.4.2RC2'].Vect_select_isles_by_box
    Vect_select_isles_by_box.restype = c_int
    Vect_select_isles_by_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 292
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_nodes_by_box'):
    Vect_select_nodes_by_box = _libs['grass_vect.6.4.2RC2'].Vect_select_nodes_by_box
    Vect_select_nodes_by_box.restype = c_int
    Vect_select_nodes_by_box.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 293
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_node'):
    Vect_find_node = _libs['grass_vect.6.4.2RC2'].Vect_find_node
    Vect_find_node.restype = c_int
    Vect_find_node.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 294
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_line'):
    Vect_find_line = _libs['grass_vect.6.4.2RC2'].Vect_find_line
    Vect_find_line.restype = c_int
    Vect_find_line.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_int, c_double, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 296
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_line_list'):
    Vect_find_line_list = _libs['grass_vect.6.4.2RC2'].Vect_find_line_list
    Vect_find_line_list.restype = c_int
    Vect_find_line_list.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_int, c_double, c_int, POINTER(struct_ilist), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 298
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_area'):
    Vect_find_area = _libs['grass_vect.6.4.2RC2'].Vect_find_area
    Vect_find_area.restype = c_int
    Vect_find_area.argtypes = [POINTER(struct_Map_info), c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 299
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_island'):
    Vect_find_island = _libs['grass_vect.6.4.2RC2'].Vect_find_island
    Vect_find_island.restype = c_int
    Vect_find_island.argtypes = [POINTER(struct_Map_info), c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 300
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_lines_by_polygon'):
    Vect_select_lines_by_polygon = _libs['grass_vect.6.4.2RC2'].Vect_select_lines_by_polygon
    Vect_select_lines_by_polygon.restype = c_int
    Vect_select_lines_by_polygon.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), c_int, POINTER(POINTER(struct_line_pnts)), c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 302
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_areas_by_polygon'):
    Vect_select_areas_by_polygon = _libs['grass_vect.6.4.2RC2'].Vect_select_areas_by_polygon
    Vect_select_areas_by_polygon.restype = c_int
    Vect_select_areas_by_polygon.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), c_int, POINTER(POINTER(struct_line_pnts)), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 306
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_in_area'):
    Vect_point_in_area = _libs['grass_vect.6.4.2RC2'].Vect_point_in_area
    Vect_point_in_area.restype = c_int
    Vect_point_in_area.argtypes = [POINTER(struct_Map_info), c_int, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 307
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_tin_get_z'):
    Vect_tin_get_z = _libs['grass_vect.6.4.2RC2'].Vect_tin_get_z
    Vect_tin_get_z.restype = c_int
    Vect_tin_get_z.argtypes = [POINTER(struct_Map_info), c_double, c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 309
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_point_in_area'):
    Vect_get_point_in_area = _libs['grass_vect.6.4.2RC2'].Vect_get_point_in_area
    Vect_get_point_in_area.restype = c_int
    Vect_get_point_in_area.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 312
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_find_poly_centroid'):
    Vect_find_poly_centroid = _libs['grass_vect.6.4.2RC2'].Vect_find_poly_centroid
    Vect_find_poly_centroid.restype = c_int
    Vect_find_poly_centroid.argtypes = [POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 313
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_point_in_poly_isl'):
    Vect_get_point_in_poly_isl = _libs['grass_vect.6.4.2RC2'].Vect_get_point_in_poly_isl
    Vect_get_point_in_poly_isl.restype = c_int
    Vect_get_point_in_poly_isl.argtypes = [POINTER(struct_line_pnts), POINTER(POINTER(struct_line_pnts)), c_int, POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 315
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect__intersect_line_with_poly'):
    Vect__intersect_line_with_poly = _libs['grass_vect.6.4.2RC2'].Vect__intersect_line_with_poly
    Vect__intersect_line_with_poly.restype = c_int
    Vect__intersect_line_with_poly.argtypes = [POINTER(struct_line_pnts), c_double, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 317
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_point_in_poly'):
    Vect_get_point_in_poly = _libs['grass_vect.6.4.2RC2'].Vect_get_point_in_poly
    Vect_get_point_in_poly.restype = c_int
    Vect_get_point_in_poly.argtypes = [POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 318
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_in_poly'):
    Vect_point_in_poly = _libs['grass_vect.6.4.2RC2'].Vect_point_in_poly
    Vect_point_in_poly.restype = c_int
    Vect_point_in_poly.argtypes = [c_double, c_double, POINTER(struct_line_pnts)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 319
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_in_area_outer_ring'):
    Vect_point_in_area_outer_ring = _libs['grass_vect.6.4.2RC2'].Vect_point_in_area_outer_ring
    Vect_point_in_area_outer_ring.restype = c_int
    Vect_point_in_area_outer_ring.argtypes = [c_double, c_double, POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 320
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_point_in_island'):
    Vect_point_in_island = _libs['grass_vect.6.4.2RC2'].Vect_point_in_island
    Vect_point_in_island.restype = c_int
    Vect_point_in_island.argtypes = [c_double, c_double, POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 323
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_break_lines'):
    Vect_break_lines = _libs['grass_vect.6.4.2RC2'].Vect_break_lines
    Vect_break_lines.restype = None
    Vect_break_lines.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 324
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_break_lines_list'):
    Vect_break_lines_list = _libs['grass_vect.6.4.2RC2'].Vect_break_lines_list
    Vect_break_lines_list.restype = c_int
    Vect_break_lines_list.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), POINTER(struct_ilist), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 326
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_merge_lines'):
    Vect_merge_lines = _libs['grass_vect.6.4.2RC2'].Vect_merge_lines
    Vect_merge_lines.restype = c_int
    Vect_merge_lines.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_int), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 327
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_break_polygons'):
    Vect_break_polygons = _libs['grass_vect.6.4.2RC2'].Vect_break_polygons
    Vect_break_polygons.restype = None
    Vect_break_polygons.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 328
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_remove_duplicates'):
    Vect_remove_duplicates = _libs['grass_vect.6.4.2RC2'].Vect_remove_duplicates
    Vect_remove_duplicates.restype = None
    Vect_remove_duplicates.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 329
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_check_duplicate'):
    Vect_line_check_duplicate = _libs['grass_vect.6.4.2RC2'].Vect_line_check_duplicate
    Vect_line_check_duplicate.restype = c_int
    Vect_line_check_duplicate.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 331
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_snap_lines'):
    Vect_snap_lines = _libs['grass_vect.6.4.2RC2'].Vect_snap_lines
    Vect_snap_lines.restype = None
    Vect_snap_lines.argtypes = [POINTER(struct_Map_info), c_int, c_double, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 332
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_snap_lines_list'):
    Vect_snap_lines_list = _libs['grass_vect.6.4.2RC2'].Vect_snap_lines_list
    Vect_snap_lines_list.restype = None
    Vect_snap_lines_list.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), c_double, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 334
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_remove_dangles'):
    Vect_remove_dangles = _libs['grass_vect.6.4.2RC2'].Vect_remove_dangles
    Vect_remove_dangles.restype = None
    Vect_remove_dangles.argtypes = [POINTER(struct_Map_info), c_int, c_double, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 335
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_chtype_dangles'):
    Vect_chtype_dangles = _libs['grass_vect.6.4.2RC2'].Vect_chtype_dangles
    Vect_chtype_dangles.restype = None
    Vect_chtype_dangles.argtypes = [POINTER(struct_Map_info), c_double, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 336
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_select_dangles'):
    Vect_select_dangles = _libs['grass_vect.6.4.2RC2'].Vect_select_dangles
    Vect_select_dangles.restype = None
    Vect_select_dangles.argtypes = [POINTER(struct_Map_info), c_int, c_double, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 337
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_remove_bridges'):
    Vect_remove_bridges = _libs['grass_vect.6.4.2RC2'].Vect_remove_bridges
    Vect_remove_bridges.restype = None
    Vect_remove_bridges.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 338
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_chtype_bridges'):
    Vect_chtype_bridges = _libs['grass_vect.6.4.2RC2'].Vect_chtype_bridges
    Vect_chtype_bridges.restype = None
    Vect_chtype_bridges.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 339
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_remove_small_areas'):
    Vect_remove_small_areas = _libs['grass_vect.6.4.2RC2'].Vect_remove_small_areas
    Vect_remove_small_areas.restype = c_int
    Vect_remove_small_areas.argtypes = [POINTER(struct_Map_info), c_double, POINTER(struct_Map_info), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 341
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_clean_small_angles_at_nodes'):
    Vect_clean_small_angles_at_nodes = _libs['grass_vect.6.4.2RC2'].Vect_clean_small_angles_at_nodes
    Vect_clean_small_angles_at_nodes.restype = c_int
    Vect_clean_small_angles_at_nodes.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 345
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_overlay_str_to_operator'):
    Vect_overlay_str_to_operator = _libs['grass_vect.6.4.2RC2'].Vect_overlay_str_to_operator
    Vect_overlay_str_to_operator.restype = c_int
    Vect_overlay_str_to_operator.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 346
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_overlay'):
    Vect_overlay = _libs['grass_vect.6.4.2RC2'].Vect_overlay
    Vect_overlay.restype = c_int
    Vect_overlay.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_ilist), POINTER(struct_ilist), POINTER(struct_Map_info), c_int, POINTER(struct_ilist), POINTER(struct_ilist), c_int, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 349
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_overlay_and'):
    Vect_overlay_and = _libs['grass_vect.6.4.2RC2'].Vect_overlay_and
    Vect_overlay_and.restype = c_int
    Vect_overlay_and.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_ilist), POINTER(struct_ilist), POINTER(struct_Map_info), c_int, POINTER(struct_ilist), POINTER(struct_ilist), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 354
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_graph_init'):
    Vect_graph_init = _libs['grass_vect.6.4.2RC2'].Vect_graph_init
    Vect_graph_init.restype = None
    Vect_graph_init.argtypes = [POINTER(GRAPH), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 355
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_graph_build'):
    Vect_graph_build = _libs['grass_vect.6.4.2RC2'].Vect_graph_build
    Vect_graph_build.restype = None
    Vect_graph_build.argtypes = [POINTER(GRAPH)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 356
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_graph_add_edge'):
    Vect_graph_add_edge = _libs['grass_vect.6.4.2RC2'].Vect_graph_add_edge
    Vect_graph_add_edge.restype = None
    Vect_graph_add_edge.argtypes = [POINTER(GRAPH), c_int, c_int, c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 357
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_graph_set_node_costs'):
    Vect_graph_set_node_costs = _libs['grass_vect.6.4.2RC2'].Vect_graph_set_node_costs
    Vect_graph_set_node_costs.restype = None
    Vect_graph_set_node_costs.argtypes = [POINTER(GRAPH), c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 358
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_graph_shortest_path'):
    Vect_graph_shortest_path = _libs['grass_vect.6.4.2RC2'].Vect_graph_shortest_path
    Vect_graph_shortest_path.restype = c_int
    Vect_graph_shortest_path.argtypes = [POINTER(GRAPH), c_int, c_int, POINTER(struct_ilist), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 361
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_build_graph'):
    Vect_net_build_graph = _libs['grass_vect.6.4.2RC2'].Vect_net_build_graph
    Vect_net_build_graph.restype = c_int
    Vect_net_build_graph.argtypes = [POINTER(struct_Map_info), c_int, c_int, c_int, String, String, String, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 363
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_shortest_path'):
    Vect_net_shortest_path = _libs['grass_vect.6.4.2RC2'].Vect_net_shortest_path
    Vect_net_shortest_path.restype = c_int
    Vect_net_shortest_path.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(struct_ilist), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 365
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_get_line_cost'):
    Vect_net_get_line_cost = _libs['grass_vect.6.4.2RC2'].Vect_net_get_line_cost
    Vect_net_get_line_cost.restype = c_int
    Vect_net_get_line_cost.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 366
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_get_node_cost'):
    Vect_net_get_node_cost = _libs['grass_vect.6.4.2RC2'].Vect_net_get_node_cost
    Vect_net_get_node_cost.restype = c_int
    Vect_net_get_node_cost.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 367
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_nearest_nodes'):
    Vect_net_nearest_nodes = _libs['grass_vect.6.4.2RC2'].Vect_net_nearest_nodes
    Vect_net_nearest_nodes.restype = c_int
    Vect_net_nearest_nodes.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_int, c_double, POINTER(c_int), POINTER(c_int), POINTER(c_int), POINTER(c_double), POINTER(c_double), POINTER(struct_line_pnts), POINTER(struct_line_pnts), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 370
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_shortest_path_coor'):
    Vect_net_shortest_path_coor = _libs['grass_vect.6.4.2RC2'].Vect_net_shortest_path_coor
    Vect_net_shortest_path_coor.restype = c_int
    Vect_net_shortest_path_coor.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, POINTER(c_double), POINTER(struct_line_pnts), POINTER(struct_ilist), POINTER(struct_line_pnts), POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 375
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_net_shortest_path_coor2'):
    Vect_net_shortest_path_coor2 = _libs['grass_vect.6.4.2RC2'].Vect_net_shortest_path_coor2
    Vect_net_shortest_path_coor2.restype = c_int
    Vect_net_shortest_path_coor2.argtypes = [POINTER(struct_Map_info), c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, POINTER(c_double), POINTER(struct_line_pnts), POINTER(struct_ilist), POINTER(struct_ilist), POINTER(struct_line_pnts), POINTER(struct_line_pnts), POINTER(c_double), POINTER(c_double)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 382
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_topo_dump'):
    Vect_topo_dump = _libs['grass_vect.6.4.2RC2'].Vect_topo_dump
    Vect_topo_dump.restype = c_int
    Vect_topo_dump.argtypes = [POINTER(struct_Map_info), POINTER(FILE)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 383
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_points_distance'):
    Vect_points_distance = _libs['grass_vect.6.4.2RC2'].Vect_points_distance
    Vect_points_distance.restype = c_double
    Vect_points_distance.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 385
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_option_to_types'):
    Vect_option_to_types = _libs['grass_vect.6.4.2RC2'].Vect_option_to_types
    Vect_option_to_types.restype = c_int
    Vect_option_to_types.argtypes = [POINTER(struct_Option)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 386
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_map_lines'):
    Vect_copy_map_lines = _libs['grass_vect.6.4.2RC2'].Vect_copy_map_lines
    Vect_copy_map_lines.restype = c_int
    Vect_copy_map_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 387
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy'):
    Vect_copy = _libs['grass_vect.6.4.2RC2'].Vect_copy
    Vect_copy.restype = c_int
    Vect_copy.argtypes = [String, String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 388
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_rename'):
    Vect_rename = _libs['grass_vect.6.4.2RC2'].Vect_rename
    Vect_rename.restype = c_int
    Vect_rename.argtypes = [String, String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 389
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_table'):
    Vect_copy_table = _libs['grass_vect.6.4.2RC2'].Vect_copy_table
    Vect_copy_table.restype = c_int
    Vect_copy_table.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info), c_int, c_int, String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 391
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_table_by_cats'):
    Vect_copy_table_by_cats = _libs['grass_vect.6.4.2RC2'].Vect_copy_table_by_cats
    Vect_copy_table_by_cats.restype = c_int
    Vect_copy_table_by_cats.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info), c_int, c_int, String, c_int, POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 393
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_copy_tables'):
    Vect_copy_tables = _libs['grass_vect.6.4.2RC2'].Vect_copy_tables
    Vect_copy_tables.restype = c_int
    Vect_copy_tables.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 394
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_delete'):
    Vect_delete = _libs['grass_vect.6.4.2RC2'].Vect_delete
    Vect_delete.restype = c_int
    Vect_delete.argtypes = [String]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 395
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_segment_intersection'):
    Vect_segment_intersection = _libs['grass_vect.6.4.2RC2'].Vect_segment_intersection
    Vect_segment_intersection.restype = c_int
    Vect_segment_intersection.argtypes = [c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, c_double, POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), POINTER(c_double), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 399
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_intersection'):
    Vect_line_intersection = _libs['grass_vect.6.4.2RC2'].Vect_line_intersection
    Vect_line_intersection.restype = c_int
    Vect_line_intersection.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), POINTER(POINTER(POINTER(struct_line_pnts))), POINTER(POINTER(POINTER(struct_line_pnts))), POINTER(c_int), POINTER(c_int), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 402
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_check_intersection'):
    Vect_line_check_intersection = _libs['grass_vect.6.4.2RC2'].Vect_line_check_intersection
    Vect_line_check_intersection.restype = c_int
    Vect_line_check_intersection.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 403
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_get_intersections'):
    Vect_line_get_intersections = _libs['grass_vect.6.4.2RC2'].Vect_line_get_intersections
    Vect_line_get_intersections.restype = c_int
    Vect_line_get_intersections.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 405
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_subst_var'):
    Vect_subst_var = _libs['grass_vect.6.4.2RC2'].Vect_subst_var
    Vect_subst_var.restype = ReturnString
    Vect_subst_var.argtypes = [String, POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 410
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_print_header'):
    Vect_print_header = _libs['grass_vect.6.4.2RC2'].Vect_print_header
    Vect_print_header.restype = c_int
    Vect_print_header.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 411
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect__init_head'):
    Vect__init_head = _libs['grass_vect.6.4.2RC2'].Vect__init_head
    Vect__init_head.restype = c_int
    Vect__init_head.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 414
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_coor_info'):
    Vect_coor_info = _libs['grass_vect.6.4.2RC2'].Vect_coor_info
    Vect_coor_info.restype = c_int
    Vect_coor_info.argtypes = [POINTER(struct_Map_info), POINTER(struct_Coor_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 415
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_maptype_info'):
    Vect_maptype_info = _libs['grass_vect.6.4.2RC2'].Vect_maptype_info
    Vect_maptype_info.restype = ReturnString
    Vect_maptype_info.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 416
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_topo'):
    Vect_open_topo = _libs['grass_vect.6.4.2RC2'].Vect_open_topo
    Vect_open_topo.restype = c_int
    Vect_open_topo.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 417
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_save_topo'):
    Vect_save_topo = _libs['grass_vect.6.4.2RC2'].Vect_save_topo
    Vect_save_topo.restype = c_int
    Vect_save_topo.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 418
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_open_spatial_index'):
    Vect_open_spatial_index = _libs['grass_vect.6.4.2RC2'].Vect_open_spatial_index
    Vect_open_spatial_index.restype = c_int
    Vect_open_spatial_index.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 419
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_save_spatial_index'):
    Vect_save_spatial_index = _libs['grass_vect.6.4.2RC2'].Vect_save_spatial_index
    Vect_save_spatial_index.restype = c_int
    Vect_save_spatial_index.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 420
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_spatial_index_dump'):
    Vect_spatial_index_dump = _libs['grass_vect.6.4.2RC2'].Vect_spatial_index_dump
    Vect_spatial_index_dump.restype = c_int
    Vect_spatial_index_dump.argtypes = [POINTER(struct_Map_info), POINTER(FILE)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 421
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_sidx_from_topo'):
    Vect_build_sidx_from_topo = _libs['grass_vect.6.4.2RC2'].Vect_build_sidx_from_topo
    Vect_build_sidx_from_topo.restype = c_int
    Vect_build_sidx_from_topo.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 422
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_spatial_index'):
    Vect_build_spatial_index = _libs['grass_vect.6.4.2RC2'].Vect_build_spatial_index
    Vect_build_spatial_index.restype = c_int
    Vect_build_spatial_index.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 424
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect__write_head'):
    Vect__write_head = _libs['grass_vect.6.4.2RC2'].Vect__write_head
    Vect__write_head.restype = c_int
    Vect__write_head.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 425
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect__read_head'):
    Vect__read_head = _libs['grass_vect.6.4.2RC2'].Vect__read_head
    Vect__read_head.restype = c_int
    Vect__read_head.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 426
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_open_old_nat'):
    V1_open_old_nat = _libs['grass_vect.6.4.2RC2'].V1_open_old_nat
    V1_open_old_nat.restype = c_int
    V1_open_old_nat.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 427
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_open_old_ogr'):
    V1_open_old_ogr = _libs['grass_vect.6.4.2RC2'].V1_open_old_ogr
    V1_open_old_ogr.restype = c_int
    V1_open_old_ogr.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 428
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_open_old_ogr'):
    V2_open_old_ogr = _libs['grass_vect.6.4.2RC2'].V2_open_old_ogr
    V2_open_old_ogr.restype = c_int
    V2_open_old_ogr.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 429
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_open_new_nat'):
    V1_open_new_nat = _libs['grass_vect.6.4.2RC2'].V1_open_new_nat
    V1_open_new_nat.restype = c_int
    V1_open_new_nat.argtypes = [POINTER(struct_Map_info), String, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 430
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_rewind_nat'):
    V1_rewind_nat = _libs['grass_vect.6.4.2RC2'].V1_rewind_nat
    V1_rewind_nat.restype = c_int
    V1_rewind_nat.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 431
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_rewind_ogr'):
    V1_rewind_ogr = _libs['grass_vect.6.4.2RC2'].V1_rewind_ogr
    V1_rewind_ogr.restype = c_int
    V1_rewind_ogr.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 432
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_rewind_nat'):
    V2_rewind_nat = _libs['grass_vect.6.4.2RC2'].V2_rewind_nat
    V2_rewind_nat.restype = c_int
    V2_rewind_nat.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 433
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_rewind_ogr'):
    V2_rewind_ogr = _libs['grass_vect.6.4.2RC2'].V2_rewind_ogr
    V2_rewind_ogr.restype = c_int
    V2_rewind_ogr.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 434
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_close_nat'):
    V1_close_nat = _libs['grass_vect.6.4.2RC2'].V1_close_nat
    V1_close_nat.restype = c_int
    V1_close_nat.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 435
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_close_ogr'):
    V1_close_ogr = _libs['grass_vect.6.4.2RC2'].V1_close_ogr
    V1_close_ogr.restype = c_int
    V1_close_ogr.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 436
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_close_ogr'):
    V2_close_ogr = _libs['grass_vect.6.4.2RC2'].V2_close_ogr
    V2_close_ogr.restype = c_int
    V2_close_ogr.argtypes = [POINTER(struct_Map_info)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 439
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_read_line_nat'):
    V1_read_line_nat = _libs['grass_vect.6.4.2RC2'].V1_read_line_nat
    V1_read_line_nat.restype = c_int
    V1_read_line_nat.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats), c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 441
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_read_next_line_nat'):
    V1_read_next_line_nat = _libs['grass_vect.6.4.2RC2'].V1_read_next_line_nat
    V1_read_next_line_nat.restype = c_int
    V1_read_next_line_nat.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 443
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_read_next_line_ogr'):
    V1_read_next_line_ogr = _libs['grass_vect.6.4.2RC2'].V1_read_next_line_ogr
    V1_read_next_line_ogr.restype = c_int
    V1_read_next_line_ogr.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 445
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_read_line_nat'):
    V2_read_line_nat = _libs['grass_vect.6.4.2RC2'].V2_read_line_nat
    V2_read_line_nat.restype = c_int
    V2_read_line_nat.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 447
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_read_line_ogr'):
    V2_read_line_ogr = _libs['grass_vect.6.4.2RC2'].V2_read_line_ogr
    V2_read_line_ogr.restype = c_int
    V2_read_line_ogr.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 449
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_read_next_line_nat'):
    V2_read_next_line_nat = _libs['grass_vect.6.4.2RC2'].V2_read_next_line_nat
    V2_read_next_line_nat.restype = c_int
    V2_read_next_line_nat.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 451
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_read_next_line_ogr'):
    V2_read_next_line_ogr = _libs['grass_vect.6.4.2RC2'].V2_read_next_line_ogr
    V2_read_next_line_ogr.restype = c_int
    V2_read_next_line_ogr.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 454
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_delete_line_nat'):
    V1_delete_line_nat = _libs['grass_vect.6.4.2RC2'].V1_delete_line_nat
    V1_delete_line_nat.restype = c_int
    V1_delete_line_nat.argtypes = [POINTER(struct_Map_info), c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 455
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_delete_line_nat'):
    V2_delete_line_nat = _libs['grass_vect.6.4.2RC2'].V2_delete_line_nat
    V2_delete_line_nat.restype = c_int
    V2_delete_line_nat.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 456
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_restore_line_nat'):
    V1_restore_line_nat = _libs['grass_vect.6.4.2RC2'].V1_restore_line_nat
    V1_restore_line_nat.restype = c_int
    V1_restore_line_nat.argtypes = [POINTER(struct_Map_info), c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 457
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_restore_line_nat'):
    V2_restore_line_nat = _libs['grass_vect.6.4.2RC2'].V2_restore_line_nat
    V2_restore_line_nat.restype = c_int
    V2_restore_line_nat.argtypes = [POINTER(struct_Map_info), c_int, c_long]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 458
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_write_line_nat'):
    V1_write_line_nat = _libs['grass_vect.6.4.2RC2'].V1_write_line_nat
    V1_write_line_nat.restype = c_long
    V1_write_line_nat.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 460
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_write_line_nat'):
    V2_write_line_nat = _libs['grass_vect.6.4.2RC2'].V2_write_line_nat
    V2_write_line_nat.restype = c_long
    V2_write_line_nat.argtypes = [POINTER(struct_Map_info), c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 466
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V1_rewrite_line_nat'):
    V1_rewrite_line_nat = _libs['grass_vect.6.4.2RC2'].V1_rewrite_line_nat
    V1_rewrite_line_nat.restype = c_long
    V1_rewrite_line_nat.argtypes = [POINTER(struct_Map_info), c_long, c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 468
if hasattr(_libs['grass_vect.6.4.2RC2'], 'V2_rewrite_line_nat'):
    V2_rewrite_line_nat = _libs['grass_vect.6.4.2RC2'].V2_rewrite_line_nat
    V2_rewrite_line_nat.restype = c_int
    V2_rewrite_line_nat.argtypes = [POINTER(struct_Map_info), c_int, c_int, POINTER(struct_line_pnts), POINTER(struct_line_cats)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 476
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_nat'):
    Vect_build_nat = _libs['grass_vect.6.4.2RC2'].Vect_build_nat
    Vect_build_nat.restype = c_int
    Vect_build_nat.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 477
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_ogr'):
    Vect_build_ogr = _libs['grass_vect.6.4.2RC2'].Vect_build_ogr
    Vect_build_ogr.restype = c_int
    Vect_build_ogr.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 478
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_build_line_area'):
    Vect_build_line_area = _libs['grass_vect.6.4.2RC2'].Vect_build_line_area
    Vect_build_line_area.restype = c_int
    Vect_build_line_area.argtypes = [POINTER(struct_Map_info), c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 479
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_isle_find_area'):
    Vect_isle_find_area = _libs['grass_vect.6.4.2RC2'].Vect_isle_find_area
    Vect_isle_find_area.restype = c_int
    Vect_isle_find_area.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 480
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_attach_isle'):
    Vect_attach_isle = _libs['grass_vect.6.4.2RC2'].Vect_attach_isle
    Vect_attach_isle.restype = c_int
    Vect_attach_isle.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 481
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_attach_isles'):
    Vect_attach_isles = _libs['grass_vect.6.4.2RC2'].Vect_attach_isles
    Vect_attach_isles.restype = c_int
    Vect_attach_isles.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 482
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_attach_centroids'):
    Vect_attach_centroids = _libs['grass_vect.6.4.2RC2'].Vect_attach_centroids
    Vect_attach_centroids.restype = c_int
    Vect_attach_centroids.argtypes = [POINTER(struct_Map_info), POINTER(BOUND_BOX)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 486
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_line_geos'):
    Vect_read_line_geos = _libs['grass_vect.6.4.2RC2'].Vect_read_line_geos
    Vect_read_line_geos.restype = POINTER(GEOSGeometry)
    Vect_read_line_geos.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 487
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_line_to_geos'):
    Vect_line_to_geos = _libs['grass_vect.6.4.2RC2'].Vect_line_to_geos
    Vect_line_to_geos.restype = POINTER(GEOSGeometry)
    Vect_line_to_geos.argtypes = [POINTER(struct_Map_info), POINTER(struct_line_pnts), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 488
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_read_area_geos'):
    Vect_read_area_geos = _libs['grass_vect.6.4.2RC2'].Vect_read_area_geos
    Vect_read_area_geos.restype = POINTER(GEOSGeometry)
    Vect_read_area_geos.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 489
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_area_points_geos'):
    Vect_get_area_points_geos = _libs['grass_vect.6.4.2RC2'].Vect_get_area_points_geos
    Vect_get_area_points_geos.restype = POINTER(GEOSCoordSequence)
    Vect_get_area_points_geos.argtypes = [POINTER(struct_Map_info), c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\Vect.h: 490
if hasattr(_libs['grass_vect.6.4.2RC2'], 'Vect_get_isle_points_geos'):
    Vect_get_isle_points_geos = _libs['grass_vect.6.4.2RC2'].Vect_get_isle_points_geos
    Vect_get_isle_points_geos.restype = POINTER(GEOSCoordSequence)
    Vect_get_isle_points_geos.argtypes = [POINTER(struct_Map_info), c_int]

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 1
try:
    GRASS_OK = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 1
try:
    GRASS_ERR = (-1)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 2
try:
    GV_FATAL_EXIT = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 2
try:
    GV_FATAL_PRINT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 2
try:
    GV_FATAL_RETURN = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_DIRECTORY = 'vector'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_FRMT_ELEMENT = 'frmt'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_COOR_ELEMENT = 'coor'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_HEAD_ELEMENT = 'head'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_DBLN_ELEMENT = 'dbln'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GRASS_VECT_HIST_ELEMENT = 'hist'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GV_TOPO_ELEMENT = 'topo'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GV_SIDX_ELEMENT = 'sidx'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 3
try:
    GV_CIDX_ELEMENT = 'cidx'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 4
try:
    ENDIAN_LITTLE = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 4
try:
    ENDIAN_BIG = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 4
try:
    ENDIAN_OTHER = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_DOUBLE = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_FLOAT = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_LONG = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_INT = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_SHORT = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 7
try:
    PORT_CHAR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 9
try:
    DBL_SIZ = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 9
try:
    FLT_SIZ = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 9
try:
    LNG_SIZ = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 9
try:
    SHRT_SIZ = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_DOUBLE_MAX = 1.7976931348623157e+308
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_DOUBLE_MIN = 2.2250738585072014e-308
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_FLOAT_MAX = 3.4028234699999998e+038
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_FLOAT_MIN = 1.17549435e-038
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_LONG_MAX = 2147483647L
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_LONG_MIN = (-2147483647L)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_INT_MAX = 2147483647
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_INT_MIN = (-2147483647)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_SHORT_MAX = 32767
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_SHORT_MIN = (-32768)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_CHAR_MAX = 127
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 47
try:
    PORT_CHAR_MIN = (-128)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 50
try:
    GV_FORMAT_NATIVE = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 50
try:
    GV_FORMAT_OGR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 52
try:
    GV_1TABLE = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 52
try:
    GV_MTABLE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 53
try:
    GV_MODE_READ = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 53
try:
    GV_MODE_WRITE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 53
try:
    GV_MODE_RW = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 54
try:
    VECT_OPEN_CODE = 1428335138
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 54
try:
    VECT_CLOSED_CODE = 581575253
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 55
try:
    LEVEL_1 = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 55
try:
    LEVEL_2 = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 55
try:
    LEVEL_3 = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_NONE = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_BASE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_AREAS = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_ATTACH_ISLES = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_CENTROIDS = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 57
try:
    GV_BUILD_ALL = GV_BUILD_CENTROIDS
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 58
def VECT_OPEN(Map):
    return (((Map.contents.open).value) == VECT_OPEN_CODE)

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 60
try:
    GV_MEMORY_ALWAYS = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 60
try:
    GV_MEMORY_NEVER = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 60
try:
    GV_MEMORY_AUTO = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 61
try:
    GV_COOR_HEAD_SIZE = 14
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 62
try:
    GRASS_V_VERSION = '5.0'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 63
try:
    GV_COOR_VER_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 63
try:
    GV_COOR_VER_MINOR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_TOPO_VER_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_TOPO_VER_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_SIDX_VER_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_SIDX_VER_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_CIDX_VER_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 64
try:
    GV_CIDX_VER_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 66
try:
    GV_COOR_EARLIEST_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 66
try:
    GV_COOR_EARLIEST_MINOR = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_TOPO_EARLIEST_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_TOPO_EARLIEST_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_SIDX_EARLIEST_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_SIDX_EARLIEST_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_CIDX_EARLIEST_MAJOR = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 67
try:
    GV_CIDX_EARLIEST_MINOR = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 68
try:
    WITHOUT_Z = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 68
try:
    WITH_Z = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 69
try:
    DIGITIZER = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 69
try:
    MOUSE = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 70
try:
    ON = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 70
try:
    OFF = 0
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 72
try:
    THRESH_FUDGE = 0.029999999999999999
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 73
try:
    GV_LEFT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 73
try:
    GV_RIGHT = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 74
try:
    GV_FORWARD = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 74
try:
    GV_BACKWARD = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_POINT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_LINE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_BOUNDARY = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_CENTROID = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_FACE = 16
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_KERNEL = 32
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_AREA = 64
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 76
try:
    GV_VOLUME = 128
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 77
try:
    GV_POINTS = (GV_POINT | GV_CENTROID)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 77
try:
    GV_LINES = (GV_LINE | GV_BOUNDARY)
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_POINT = 1
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_LINE = 2
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_BOUNDARY = 3
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_CENTROID = 4
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_FACE = 5
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_KERNEL = 6
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_AREA = 7
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 79
try:
    GV_STORE_VOLUME = 8
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 81
try:
    GV_ON_AND = 'AND'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 81
try:
    GV_ON_OVERLAP = 'OVERLAP'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 90
try:
    ESC = 33
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 201
try:
    GV_NCATS_MAX = PORT_INT_MAX
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 201
try:
    GV_FIELD_MAX = PORT_INT_MAX
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 201
try:
    GV_CAT_MAX = PORT_INT_MAX
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_defines.h: 202
try:
    BUILD_PROG = 'v.build'
except:
    pass

# c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 25
try:
    HEADSTR = 50
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 1
try:
    GRASS_OK = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 1
try:
    GRASS_ERR = (-1)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 2
try:
    GV_FATAL_EXIT = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 2
try:
    GV_FATAL_PRINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 2
try:
    GV_FATAL_RETURN = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_DIRECTORY = 'vector'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_FRMT_ELEMENT = 'frmt'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_COOR_ELEMENT = 'coor'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_HEAD_ELEMENT = 'head'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_DBLN_ELEMENT = 'dbln'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GRASS_VECT_HIST_ELEMENT = 'hist'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GV_TOPO_ELEMENT = 'topo'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GV_SIDX_ELEMENT = 'sidx'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 3
try:
    GV_CIDX_ELEMENT = 'cidx'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 4
try:
    ENDIAN_LITTLE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 4
try:
    ENDIAN_BIG = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 4
try:
    ENDIAN_OTHER = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_DOUBLE = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_FLOAT = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_LONG = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_INT = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_SHORT = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 7
try:
    PORT_CHAR = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 9
try:
    DBL_SIZ = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 9
try:
    FLT_SIZ = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 9
try:
    LNG_SIZ = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 9
try:
    SHRT_SIZ = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_DOUBLE_MAX = 1.7976931348623157e+308
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_DOUBLE_MIN = 2.2250738585072014e-308
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_FLOAT_MAX = 3.4028234699999998e+038
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_FLOAT_MIN = 1.17549435e-038
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_LONG_MAX = 2147483647L
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_LONG_MIN = (-2147483647L)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_INT_MAX = 2147483647
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_INT_MIN = (-2147483647)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_SHORT_MAX = 32767
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_SHORT_MIN = (-32768)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_CHAR_MAX = 127
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 47
try:
    PORT_CHAR_MIN = (-128)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 50
try:
    GV_FORMAT_NATIVE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 50
try:
    GV_FORMAT_OGR = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 52
try:
    GV_1TABLE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 52
try:
    GV_MTABLE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 53
try:
    GV_MODE_READ = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 53
try:
    GV_MODE_WRITE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 53
try:
    GV_MODE_RW = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 54
try:
    VECT_OPEN_CODE = 1428335138
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 54
try:
    VECT_CLOSED_CODE = 581575253
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 55
try:
    LEVEL_1 = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 55
try:
    LEVEL_2 = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 55
try:
    LEVEL_3 = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_NONE = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_BASE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_AREAS = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_ATTACH_ISLES = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_CENTROIDS = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 57
try:
    GV_BUILD_ALL = GV_BUILD_CENTROIDS
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 58
def VECT_OPEN(Map):
    return (((Map.contents.open).value) == VECT_OPEN_CODE)

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 60
try:
    GV_MEMORY_ALWAYS = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 60
try:
    GV_MEMORY_NEVER = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 60
try:
    GV_MEMORY_AUTO = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 61
try:
    GV_COOR_HEAD_SIZE = 14
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 62
try:
    GRASS_V_VERSION = '5.0'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 63
try:
    GV_COOR_VER_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 63
try:
    GV_COOR_VER_MINOR = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_TOPO_VER_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_TOPO_VER_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_SIDX_VER_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_SIDX_VER_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_CIDX_VER_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 64
try:
    GV_CIDX_VER_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 66
try:
    GV_COOR_EARLIEST_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 66
try:
    GV_COOR_EARLIEST_MINOR = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_TOPO_EARLIEST_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_TOPO_EARLIEST_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_SIDX_EARLIEST_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_SIDX_EARLIEST_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_CIDX_EARLIEST_MAJOR = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 67
try:
    GV_CIDX_EARLIEST_MINOR = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 68
try:
    WITHOUT_Z = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 68
try:
    WITH_Z = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 69
try:
    DIGITIZER = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 69
try:
    MOUSE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 70
try:
    ON = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 70
try:
    OFF = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 72
try:
    THRESH_FUDGE = 0.029999999999999999
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 73
try:
    GV_LEFT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 73
try:
    GV_RIGHT = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 74
try:
    GV_FORWARD = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 74
try:
    GV_BACKWARD = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_POINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_LINE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_BOUNDARY = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_CENTROID = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_FACE = 16
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_KERNEL = 32
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_AREA = 64
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 76
try:
    GV_VOLUME = 128
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 77
try:
    GV_POINTS = (GV_POINT | GV_CENTROID)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 77
try:
    GV_LINES = (GV_LINE | GV_BOUNDARY)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_POINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_LINE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_BOUNDARY = 3
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_CENTROID = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_FACE = 5
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_KERNEL = 6
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_AREA = 7
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 79
try:
    GV_STORE_VOLUME = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 81
try:
    GV_ON_AND = 'AND'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 81
try:
    GV_ON_OVERLAP = 'OVERLAP'
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 90
try:
    ESC = 33
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 201
try:
    GV_NCATS_MAX = PORT_INT_MAX
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 201
try:
    GV_FIELD_MAX = PORT_INT_MAX
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 201
try:
    GV_CAT_MAX = PORT_INT_MAX
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vect\\dig_defines.h: 202
try:
    BUILD_PROG = 'v.build'
except:
    pass

bound_box = struct_bound_box # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 55

P_node = struct_P_node # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 424

P_area = struct_P_area # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 458

P_line = struct_P_line # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 438

P_isle = struct_P_isle # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 480

site_att = struct_site_att # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 46

gvfile = struct_gvfile # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 65

field_info = struct_field_info # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 79

dblinks = struct_dblinks # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 89

Port_info = struct_Port_info # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 96

recycle = struct_recycle # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 120

Map_info = struct_Map_info # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 357

dig_head = struct_dig_head # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 126

Coor_info = struct_Coor_info # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 165

line_pnts = struct_line_pnts # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 498

Format_info_ogr = struct_Format_info_ogr # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 174

Format_info = struct_Format_info # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 220

Cat_index = struct_Cat_index # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 227

Plus_head = struct_Plus_head # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 239

line_cats = struct_line_cats # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 507

cat_list = struct_cat_list # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 515

ilist = struct_ilist # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 525

varray = struct_varray # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 533

spatial_index = struct_spatial_index # c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vect/dig_structs.h: 542

# No inserted files

