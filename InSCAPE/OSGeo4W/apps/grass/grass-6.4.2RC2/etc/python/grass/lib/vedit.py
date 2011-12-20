'''Wrapper for vedit.h

Generated with:
./ctypesgen.py --cpp gcc -E -I/c/OSGeo4W/include     -DPACKAGE="grasslibs" -DPACKAGE="grasslibs"  -I/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include -lgrass_vedit.6.4.2RC2 -Ic:/OSGeo4W/include -Ic:/OSGeo4W/include c:/osgeo4w/usr/src/release_20111115_grass_6_4_2RC2/dist.i686-pc-mingw32/include/grass/vedit.h -o vedit.py

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

_libs["grass_vedit.6.4.2RC2"] = load_library("grass_vedit.6.4.2RC2")

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

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 45
class struct_rpoint(Structure):
    pass

struct_rpoint.__slots__ = [
    'x',
    'y',
]
struct_rpoint._fields_ = [
    ('x', c_int),
    ('y', c_int),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 50
class struct_robject(Structure):
    pass

struct_robject.__slots__ = [
    'fid',
    'type',
    'npoints',
    'point',
]
struct_robject._fields_ = [
    ('fid', c_int),
    ('type', c_int),
    ('npoints', c_int),
    ('point', POINTER(struct_rpoint)),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 58
class struct_robject_list(Structure):
    pass

struct_robject_list.__slots__ = [
    'nitems',
    'item',
]
struct_robject_list._fields_ = [
    ('nitems', c_int),
    ('item', POINTER(POINTER(struct_robject))),
]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 65
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_split_lines'):
    Vedit_split_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_split_lines
    Vedit_split_lines.restype = c_int
    Vedit_split_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), POINTER(struct_line_pnts), c_double, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 67
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_connect_lines'):
    Vedit_connect_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_connect_lines
    Vedit_connect_lines.restype = c_int
    Vedit_connect_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 70
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_modify_cats'):
    Vedit_modify_cats = _libs['grass_vedit.6.4.2RC2'].Vedit_modify_cats
    Vedit_modify_cats.restype = c_int
    Vedit_modify_cats.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), c_int, c_int, POINTER(struct_cat_list)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 74
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_copy_lines'):
    Vedit_copy_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_copy_lines
    Vedit_copy_lines.restype = c_int
    Vedit_copy_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_Map_info), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 77
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_chtype_lines'):
    Vedit_chtype_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_chtype_lines
    Vedit_chtype_lines.restype = c_int
    Vedit_chtype_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 81
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_delete_lines'):
    Vedit_delete_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_delete_lines
    Vedit_delete_lines.restype = c_int
    Vedit_delete_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 84
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_get_min_distance'):
    Vedit_get_min_distance = _libs['grass_vedit.6.4.2RC2'].Vedit_get_min_distance
    Vedit_get_min_distance.restype = c_double
    Vedit_get_min_distance.argtypes = [POINTER(struct_line_pnts), POINTER(struct_line_pnts), c_int, POINTER(c_int)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 88
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_flip_lines'):
    Vedit_flip_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_flip_lines
    Vedit_flip_lines.restype = c_int
    Vedit_flip_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 91
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_merge_lines'):
    Vedit_merge_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_merge_lines
    Vedit_merge_lines.restype = c_int
    Vedit_merge_lines.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 94
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_move_lines'):
    Vedit_move_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_move_lines
    Vedit_move_lines.restype = c_int
    Vedit_move_lines.argtypes = [POINTER(struct_Map_info), POINTER(POINTER(struct_Map_info)), c_int, POINTER(struct_ilist), c_double, c_double, c_double, c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 98
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_render_map'):
    Vedit_render_map = _libs['grass_vedit.6.4.2RC2'].Vedit_render_map
    Vedit_render_map.restype = POINTER(struct_robject_list)
    Vedit_render_map.argtypes = [POINTER(struct_Map_info), POINTER(struct_bound_box), c_int, c_double, c_double, c_int, c_int, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 102
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_select_by_query'):
    Vedit_select_by_query = _libs['grass_vedit.6.4.2RC2'].Vedit_select_by_query
    Vedit_select_by_query.restype = c_int
    Vedit_select_by_query.argtypes = [POINTER(struct_Map_info), c_int, c_int, c_double, c_int, POINTER(struct_ilist)]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 106
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_snap_point'):
    Vedit_snap_point = _libs['grass_vedit.6.4.2RC2'].Vedit_snap_point
    Vedit_snap_point.restype = c_int
    Vedit_snap_point.argtypes = [POINTER(struct_Map_info), c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double), c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 108
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_snap_line'):
    Vedit_snap_line = _libs['grass_vedit.6.4.2RC2'].Vedit_snap_line
    Vedit_snap_line.restype = c_int
    Vedit_snap_line.argtypes = [POINTER(struct_Map_info), POINTER(POINTER(struct_Map_info)), c_int, c_int, POINTER(struct_line_pnts), c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 110
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_snap_lines'):
    Vedit_snap_lines = _libs['grass_vedit.6.4.2RC2'].Vedit_snap_lines
    Vedit_snap_lines.restype = c_int
    Vedit_snap_lines.argtypes = [POINTER(struct_Map_info), POINTER(POINTER(struct_Map_info)), c_int, POINTER(struct_ilist), c_double, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 114
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_move_vertex'):
    Vedit_move_vertex = _libs['grass_vedit.6.4.2RC2'].Vedit_move_vertex
    Vedit_move_vertex.restype = c_int
    Vedit_move_vertex.argtypes = [POINTER(struct_Map_info), POINTER(POINTER(struct_Map_info)), c_int, POINTER(struct_ilist), POINTER(struct_line_pnts), c_double, c_double, c_double, c_double, c_double, c_int, c_int]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 118
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_add_vertex'):
    Vedit_add_vertex = _libs['grass_vedit.6.4.2RC2'].Vedit_add_vertex
    Vedit_add_vertex.restype = c_int
    Vedit_add_vertex.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), POINTER(struct_line_pnts), c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 120
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_remove_vertex'):
    Vedit_remove_vertex = _libs['grass_vedit.6.4.2RC2'].Vedit_remove_vertex
    Vedit_remove_vertex.restype = c_int
    Vedit_remove_vertex.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), POINTER(struct_line_pnts), c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 124
if hasattr(_libs['grass_vedit.6.4.2RC2'], 'Vedit_bulk_labeling'):
    Vedit_bulk_labeling = _libs['grass_vedit.6.4.2RC2'].Vedit_bulk_labeling
    Vedit_bulk_labeling.restype = c_int
    Vedit_bulk_labeling.argtypes = [POINTER(struct_Map_info), POINTER(struct_ilist), c_double, c_double, c_double, c_double, c_double, c_double]

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 7
try:
    NO_SNAP = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 7
try:
    SNAP = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 7
try:
    SNAPVERTEX = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 8
try:
    QUERY_UNKNOWN = (-1)
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 8
try:
    QUERY_LENGTH = 0
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 8
try:
    QUERY_DANGLE = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_POINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_LINE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_BOUNDARYNO = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_BOUNDARYTWO = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_BOUNDARYONE = 16
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_CENTROIDIN = 32
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_CENTROIDOUT = 64
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_CENTROIDDUP = 128
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_NODEONE = 256
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_NODETWO = 512
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_VERTEX = 1024
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_AREA = 2048
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_ISLE = 4096
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 10
try:
    TYPE_DIRECTION = 8192
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_POINT = 1
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_LINE = 2
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_BOUNDARYNO = 4
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_BOUNDARYTWO = 8
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_BOUNDARYONE = 16
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_CENTROIDIN = 32
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_CENTROIDOUT = 64
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_CENTROIDDUP = 128
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_NODEONE = 256
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_NODETWO = 512
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_VERTEX = 1024
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_AREA = 2048
except:
    pass

# c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 11
try:
    DRAW_DIRECTION = 4096
except:
    pass

rpoint = struct_rpoint # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 45

robject = struct_robject # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 50

robject_list = struct_robject_list # c:\\osgeo4w\\usr\\src\\release_20111115_grass_6_4_2RC2\\dist.i686-pc-mingw32\\include\\grass\\vedit.h: 58

# No inserted files

