"""
recreation_server_core
"""

import os
import math

from osgeo import ogr, osr, gdal

from urllib2 import urlopen

import logging

import socket

from psycopg2.extensions import register_adapter, AsIs

logging.basicConfig(format = '%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level = logging.DEBUG, datefmt = '%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_server_core')


class NoQuotes(object):
    def __init__(self, string):
        self.string = string

def adapt_no_quotes(no_quotes):
    return AsIs(no_quotes.string)

register_adapter(NoQuotes, adapt_no_quotes)

###geometry tools###
def stats_box(points):
    """Returns the extrema and dimensions for a box enclosing the points

   :param points: a list of points in [(x1, y1),(x2, y2),(xN, yN)] form
   :type points: list

   :return: min_x, min_y, max_x, max_y, width, height
   :rtype: list"""

    x_coordinates = []
    y_coordinates = []
    for x_coordinate, y_coordinate in points:
        x_coordinates.append(x_coordinate)
        y_coordinates.append(y_coordinate)

    min_x = min(x_coordinates)
    max_x = max(x_coordinates)
    min_y = min(y_coordinates)
    max_y = max(y_coordinates)

    return min_x, min_y, max_x, max_y, abs(max_x - min_x), abs(max_y - min_y)


def bounding_box(points):
    """Returns a bounding box for the points

    :param points: a list of points in [(x1, y1),(x2, y2),(xN, yN)] form
    :type points: list

    :return: a closed coordinate list for the bounding box in
    [(x1, y1),(x2, y2),(xN, yN)] form
    :rtype: list"""

    min_x, min_y, max_x, max_y = stats_box(points)[:-2]

    return ((min_x, min_y),
            (min_x, max_y),
            (max_x, max_y),
            (max_x, min_y),
            (min_x, min_y))


###sql formatting###
def format_points_sql(points):
    """Returns a list of points in the PostGIS sql format

    :param points: a list of points in [(x1, y1),(x2, y2),(xN, yN)] form
    :type points: list

    :return: a sql fragment
    :rtype: str"""

    sql = ", ".join(["%i %i" % point for point in points])

    return sql


def format_polygon_sql(points, srid = 900913):
    """Returns a polygon in a PostGIS sql format

    :param points: a list of points in [(x1, y1),(x2, y2),(xN, yN)] form
    :type points: list
    :param srid: the PostGIS spatial reference identifier, defaults to OSM's
    :type srid: int

    :return: a sql fragment
    :rtype: str"""

    sql = "ST_GeomFromText(\'POLYGON((%s))\', %i)"
    sql = sql % (format_points_sql(points), srid)

    return sql


def format_feature_sql(feature):
    """Returns a feature type in the OSM PostGIS sql format

    :param feature: the name of a feature tag and value in "tag_value" format
    :type feature: str

    :return: a sql fragment
    :rtype: str"""

    sql = "osm.%s = \'%s\'"
    sql = sql % tuple(feature.split('_'))

    return sql


def category_table(osm_table_name):
    """Returns a OSM category table definition

    :param osm_table_name: a OSM PostGIS table name
    :type osm_table_name: str

    :return: a sql statement
    :rtype: str"""

    sql = ("CREATE TEMPORARY TABLE category_%s "
           "(osm_id integer, "
           "cat smallint, "
           "PRIMARY KEY (osm_id))")
    sql = sql % (osm_table_name)

    return sql


def category_table_build(osm_table_name, categorysql):
    """Returns a SQL OSM category table builder

    :param osm_table_name: a OSM PostGIS table name
    :type osm_table_name: str

    :return: a sql statement
    :rtype: str"""

    sql = ("INSERT INTO category_%s (osm_id, cat) "
           "SELECT DISTINCT osm_id, "
           "%s as cat "
           "FROM %s as osm")
    sql = sql % (osm_table_name, categorysql, osm_table_name)

    return sql


def category_dict(tsv_file_name):
    """Returns the category definitions and class numbering derived from
    a categorization table

    :param tsv_file_name: the file name for categorization table
    :type tsv_file_name: str

    :return: a tuple containing a category dictionary in
    [column][value]=class number form and a class dictionary in
    [category name]=class number?
    :rtype: tuple
    """
    tsv_file = open(tsv_file_name, 'r')
    tsv_file.readline()

    classes = {}
    class_count = 0
    categories = {}
    LOGGER.debug("Parsing categorization table.")
    for line in tsv_file:
        column, value, category = line.strip("\n").split("\t")[:3]
        if len(column) >10:
            err_msg = "Column %s exceeds the maximum length of 10." % column
            raise ValueError, err_msg

        if not column in categories:
            LOGGER.debug("Adding new category column %s.", repr(column))
            categories[column] = {}

        if not category in classes:
            LOGGER.debug("Adding new class %s.", category)
            classes[category] = class_count
            class_count += 1

        if value in categories[column]:
            err_msg = (
                "Duplicate category definition %s-%s:%s." %
                (column, value, category))
            raise ValueError, err_msg
        else:
            categories[column][value] = classes[category]

    LOGGER.debug("Constructed category dictionary: %s.",
                 str(categories).replace(".", "||").replace(",", "|"))
    LOGGER.debug("Constructed class dictionary: %s.",
                 str(classes).replace(".", "||").replace(",", "|"))

    LOGGER.debug("Checking for duplicate default category.")
    if len(categories[""].keys()) != 1:
        raise ValueError, "The default category was defined more than once."

    return categories, classes


def categorize_execute(cur, table_name, category_dictionary, classes_dictionary,
                       category_format, class_format):
    """Generates tables with the categorization schema
    """
    LOGGER.info("Checking column types.")
    delimiter = {}
    sql = "SELECT * FROM %s LIMIT 0" % table_name
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    for desc in cur.description:
        if desc[0] in category_dictionary:
            #int
            if desc[1] == 23:
                LOGGER.debug("Found integer column %s.", desc[0])
                delimiter[desc[0]] = ""
            #str
            elif desc[1] == 25:
                LOGGER.debug("Found string column %s.", desc[0])
                delimiter[desc[0]] = "\'"
            #float
            elif desc[1] == 701:
                LOGGER.debug("Found float column %s.", desc[0])
                delimiter[desc[0]] = ""
            elif desc[1] == 1700:
                LOGGER.debug("Found numeric column %s.", desc[0])
                delimiter[desc[0]] = ""
            else:
                LOGGER.debug("Found column %s with oid %i.", desc[0], desc[1])

    LOGGER.info("Processing category definitions.")
    LOGGER.debug("The following columns can be used in rules: %s",
                 "|".join(delimiter.keys()))

    LOGGER.info("Creating class table.")
    sql = ("CREATE TEMPORARY TABLE %s "
           "(id INT NOT NULL, "
           "field VARCHAR(10), "
           "PRIMARY KEY(id))")
    sql = sql % (class_format % table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    classes = [(classes_dictionary[key], key)
               for key in classes_dictionary.keys()]
    sql = "INSERT INTO %s VALUES " + ','.join([str(classes_element)
                                               for classes_element in classes])
    sql = sql % (class_format % table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


    sql = "CASE"

    columns = category_dictionary.keys()
    #make sure default value comes at end of sql statement
    columns.sort(reverse = True)
    for column in columns:
        LOGGER.debug("Creating clauses for column %s.", str(column))
        values = category_dictionary[column].keys()
        values.sort(reverse = True)
        if column == "":
            LOGGER.debug("Creating clause for default value.")
            sql = sql + (" ELSE %i END" % category_dictionary[""][""])
        else:
            LOGGER.debug("Creating clauses for values: %s.",
                         str(values).replace(",", "|"))
            for value in values:
                if value != "":
                    sql = sql + (" WHEN layer.%s = %s%s%s THEN %i" %
                                 (column, delimiter[column], value,
                                  delimiter[column],
                                  category_dictionary[column][value]))
                else:
                    sql = sql + (" WHEN layer.%s IS NOT NULL THEN %i" %
                                 (column, category_dictionary[column][value]))

    LOGGER.info("Creating category table.")
    sql = "CREATE TEMPORARY TABLE %s AS (SELECT id, " + sql + " AS cat FROM %s AS layer)"
    sql = sql % (category_format%table_name, table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def format_categories_sql(tsv_file_name, custom_sql = "see code"):
    """Returns a sql fragment with OSM PostGIS category definitions

    :param tsv_file_name: the tab delimited string quoted category definitions
    :type tsv_file_name: str
    :param custom_sql: a sql case statement fragment containing additional
    category definitions
    :type custom_sql: str

    :return: a sql fragment
    :rtype: str"""


    # custom sql classifies features with values not explicitly categorized
    if custom_sql == "see code":
        custom_sql = (" WHEN LENGTH(osm.aerialway) IS NOT NULL THEN 4"
        " WHEN LENGTH(osm.aeroway) IS NOT NULL THEN 2"
        " WHEN LENGTH(osm.highway) IS NOT NULL THEN 1"
        " WHEN LENGTH(osm.historic) IS NOT NULL THEN 4"
        " WHEN LENGTH(osm.leisure) IS NOT NULL THEN 4"
        " WHEN LENGTH(osm.man_made) IS NOT NULL THEN 2"
        " WHEN LENGTH(osm.military) IS NOT NULL THEN 2"
        " WHEN LENGTH(osm.natural) IS NOT NULL THEN 3"
        " WHEN LENGTH(osm.railway) IS NOT NULL THEN 1"
        " WHEN LENGTH(osm.shop) IS NOT NULL THEN 1"
        " WHEN LENGTH(osm.tourism) IS NOT NULL THEN 4")

    #begin case statement
    sql = "CASE"

    tsv_file = open(tsv_file_name, 'r')
    #skip header row
    tsv_file.readline()

    #get category definitions
    for line in tsv_file:
        #print sql
        line = line.split('\t')

        try:
            column = line[0].strip("\"").strip()
            value = line[1].strip("\"").strip()
            category = line[3].strip("\"").strip()

            if column != "" and value != "User Defined" and category != "":
                if category == "cultural":
                    category_code = 1
                elif category == "industrial":
                    category_code = 2
                elif category == "natural":
                    category_code = 3
                elif category == "superstructure":
                    category_code = 4
                else:
                    raise ValueError, "Unknown category type"

                sql = sql + (" WHEN osm.%s = \'%s\' THEN %s" %\
                             (column, value, str(category_code)))
        except IndexError:
            print "A row is missing the minimum required columns."

    tsv_file.close()

    #add custom sql to statement and default value
    sql = sql + custom_sql + " ELSE 0 END"
    return sql


def calculate_grid(origin_x, origin_y, column, row, cell_size):
    """Returns the Cartesian coordinates for the specified cell in the grid

    :param origin_x: the lower left X coordinate of the origin of the grid
    :type origin_x: float
    :param origin_y: the lower left Y coordinate of the origin of the grid
    :type origin_y: float
    :param column: the column number desired
    :type column: int
    :param row: the row number desired
    :type row: int
    :param cell_size: the size of a grid cell in map units
    :type cell_size: float

    :return: a closed coordinate list for the grid cell in
    [(x1, y1),(x2, y2),(xN, yN)] form
    :rtype: list"""

    return bounding_box([(origin_x + (column * cell_size),
                          origin_y + (row * cell_size)),
                         (origin_x + ((column + 1) * cell_size),
                          origin_y + ((row + 1) * cell_size))])


###OGR calls###
def create_polygon_feature_ogr(layer, points, results):
    """Returns a OGR polygon feature from the specified points with the
    specified values

    :param layer: a OGR layer
    :type layer: object
    :param points: a closed coordinate list in [(x1, y1),(x2, y2),(xN, yN)] form
    :type points: list
    :param results: the values for the fields in [(field name, value)] form
    :type results: list

    :return: a OGR polygon feature
    :rtype: object"""
    # create a new point object
    polygon = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)

    for x_coordinate, y_coordinate in points:
        ring.AddPoint(x_coordinate, y_coordinate)

    ring.CloseRings()
    polygon.AddGeometry(ring)

    feature_defn = layer.GetLayerDefn()

    # create a new feature
    feature = ogr.Feature(feature_defn)
    feature.SetGeometry(polygon)

    #set field values
    for field, value in enumerate(results):
        feature.SetField(field, value)

    layer.CreateFeature(feature)

    polygon.Destroy()
    feature.Destroy()


def pixel_coordinate(origin_x, scale_x, theta_y, origin_y, theta_x, scale_y,
                     i, j):
    """Returns the Cartesian coordinate for a pixel

    http://www.gdal.org/gdal_datamodel.html

    :param origin_x: the X dimension of the spatial coordinate for the top left
    pixel
    :type origin_x: float
    :param scale_x: the spatial width of pixels in the X dimension
    :type scale_x: float
    :param theta_y: the spatial offset in the Y dimension caused by rotation
    :type theta_y: float
    :param origin_y: the Y dimension of the spatial coordinate for the top left
    pixel
    :type origin_y: float
    :param theta_x: the spatial offset in the X dimension caused by rotation
    :type theta_x: float
    :param scale_y: the spatial height of pixels in the Y dimension
    :type scale_y: float
    :param i: the X dimension grid index for the desired pixel
    :type i: int
    :param j: the Y dimension grid index for the desired pixel
    :type j: int

    :return: the Cartesian coordinate for the pixel in (x, y) form
    :rtype: tuple"""

    x_coordinate = origin_x + (i * scale_x) + (j * theta_y)
    y_coordinate = origin_y + (i * theta_x) + (j * scale_y)

    return (x_coordinate, y_coordinate)


###Pyscopg2 calls###
def category_builder_osm():
    """Returns a sql statement the builds a feature type list to be categorized

    The function reads in the list of OSM columns to check from the osm.txt file
    and generates a sql statement the will select the distinct values for those
    columns.

    :return: a sql statement
    :rtype: str"""

    in_file_name = os.sys.argv[0][:-10] + "osm.txt"
    in_file = open(in_file_name, 'r')

    column_names = in_file.readlines()
    column_select = []

    for column_name in column_names:
        column_name = column_name.strip()
        column_select.append(
            "SELECT DISTINCT \'%s\' AS \"column\", osm.%s AS \"value\" "
            "FROM planet_osm_point AS osm" %
            (column_name.strip("\""), column_name))
        column_select.append(
            "SELECT DISTINCT \'%s\' AS \"column\", osm.%s AS \"value\" "
            "FROM planet_osm_line AS osm" %
            (column_name.strip("\""), column_name))
        column_select.append(
            "SELECT DISTINCT \'%s\' AS \"column\", osm.%s AS \"value\" "
            "FROM planet_osm_polygon AS osm" %
            (column_name.strip("\""), column_name))

    sql = "(" + " UNION ".join(column_select)
    sql = sql + ") ORDER BY \"column\",\"value\""

    return sql


def temp_shapefile_db(
    cur, shapefile_name, table_name, attributes = False, srid = 0):
    """Loads the shapefile into a PostGIS table

    :param cur: a PostGIS database cursor
    :type cur: object
    :param shapefile_name: the full path and file name for the shapefile
    :type shapefile_name: str
    :param attributes: boolean to include attribute table
    :type attributes: bool
    :param srid: the srid value
    :type srid: int

    :return: a PostGIS table name
    :rtype: str

    :raise: ValueError when no projection definition"""

    shapefile_name = str(shapefile_name)
    
    LOGGER.info("Loading shapefile into database.")
    LOGGER.debug("Opening shapefile %s.", repr(shapefile_name))
    shp = ogr.Open(shapefile_name)
    lyr = shp.GetLayer()

##    if srs == None and srid == 0:
##        raise (ValueError,
##               "The shapefile must have a spatial reference system (.prj)")
##    else:
##        wkt = srs.ExportToWkt()
##        srid = wkt_to_srid(cur, wkt)
##        LOGGER.debug("Detected projection %i" % (srid))

    prj_path = shapefile_name[:-3] + "prj"
    if os.path.exists(prj_path):
        prj_file = open(prj_path, 'r')
        wkt = prj_file.read()
        srid = wkt_to_srid(cur, wkt)
        LOGGER.debug("Detected projection %i", srid)
    else:
        LOGGER.error("The shapefile must have a prj file.")
        err_msg = "The shapefile must have a spatial reference system (prj)."
        raise ValueError, err_msg

##
##    #check for projection
##    srs = lyr.GetSpatialRef()
##    if srs == None and srid == 0:
##        raise (ValueError,
##               "The shapefile must have a spatial reference system (.prj)")
##    else:
##        wkt = srs.ExportToWkt()
##        LOGGER.debug("WKT: %s" % repr(wkt).replace(",", "|").replace(".", "||"))
##        #srs.AutoIdentifysrid()
##        #srid = int(srs.GetAttrValue("AUTHORITY", 1))
##        srid = wkt_to_srid(cur, wkt)
##        LOGGER.debug("Detected projection %i" % (srid))

    #build field definitions
    fields = []
    casts = []
    if lyr.GetFeatureCount() < 1:
        LOGGER.warn("Empty shapefile.")
    elif attributes:
        LOGGER.debug("Constructing table definition.")
        feat_defn = lyr.GetLayerDefn()
        for i in range(feat_defn.GetFieldCount()):
            field_defn = feat_defn.GetFieldDefn(i)
            field_name = field_defn.GetName()

            if field_defn.GetType() == ogr.OFTInteger:
                field_type = "integer"
                casts.append(lambda s: "%s" % (s))
            elif field_defn.GetType() == ogr.OFTReal:
                field_type = "double precision"
                casts.append(lambda s: "%s" % (s))
            elif field_defn.GetType() == ogr.OFTString:
                field_type = "text"
                casts.append(lambda s: "\'%s\'" % (s))
            elif field_defn.GetType() == ogr.OFTBinary:
                raise ValueError, "Unknown sql Conversion"
            elif field_defn.GetType() == ogr.OFTDate:
                raise ValueError, "Unknown sql Conversion"
            else:
                raise ValueError, "Unknown Type"

            fields.append("%s %s" % (field_name, field_type))

    LOGGER.debug("Found the following attribute columns: %s",
                 str(fields).replace(",", "|"))

    #create table
    LOGGER.info("Creating database table.")
    sql = "CREATE TEMPORARY TABLE %s (%s)"
    sql = sql % (table_name, ', '.join(fields + ["way geometry"]))
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    #insert features
    for id_number, feat in enumerate(lyr):
        geom = feat.GetGeometryRef()
        if not geom is None:
            if attributes:
                attrb = []
                for i, cast in enumerate(casts):
                    attrb.append(cast(feat.GetFieldAsString(i)))

                sql = "INSERT INTO %s VALUES(%s, ST_GeomFromText(\'%s\',%s))"
                sql = sql % (table_name, ", ".join(attrb),
                             geom.ExportToWkt(), str(srid))
            else:
                sql = "INSERT INTO %s VALUES(ST_GeomFromText(\'%s\',%s))"
                sql = sql % (table_name, geom.ExportToWkt(), str(srid))
            LOGGER.debug("Inserting feature %i", id_number)
            LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
            cur.execute(sql)

    return int(srid)


def temp_grid_db(cur, in_table_name, in_column_name, out_table_name,
                 out_column_name, cell_size):
    """Creates a PostGIS table with the AOI grid

    :param cur: A PostGIS database cursor
    :type cur: object
    :param aoi_name: the AOI PostGIS table name
    :type aoi_name: str
    :param grid_name: the desired grid PostGIS table name
    :type grid_name: str
    :param cell_size: the size of grid cells
    :type cell_size: float

    :return: None
    :rtype: None"""

    #get spatial extent of AOI
    sql = "SELECT Box2D(ST_Union(%s)) from %s"
    sql = sql % (in_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    bbox, = cur.fetchone()
    LOGGER.debug("SQL result: %s", bbox)
    (min_x, min_y), (max_x, max_y) = [(float(x_extrema), float(y_extrema))
                                      for (x_extrema, y_extrema)
                                      in [point.split(" ")
                                          for point
                                          in bbox[4:-1].split(",")]]
    width, height = abs(max_x - min_x), abs(max_y - min_y)

    #calculate dimensions of grid
    columns = int(math.floor(width / cell_size))
    rows = int(math.floor(height / cell_size))

    #get AOI projection
    sql = "SELECT ST_srid(%s) FROM %s LIMIT 1" % (in_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)
    srid, = cur.fetchone()
    LOGGER.debug("SQL result: %s", srid)

    #create grid table
    sql = "CREATE TEMPORARY TABLE %s (%s geometry, id integer)"
    sql = sql % (out_table_name, out_column_name)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)

    #insert grid cells if covered by AOI
    for i in range(columns):
        for j in range(rows):
            box = calculate_grid(min_x, min_y, i, j, cell_size)
            boxsql = format_polygon_sql(box, srid)

            sql = "INSERT INTO %s SELECT %s, %i as id FROM %s as %s,"% \
            (out_table_name, out_column_name, (i * rows) + j, boxsql,
             out_column_name)
            sql = sql + " %s WHERE ST_Covers(%s.%s,%s)" % \
                  (in_table_name, in_table_name, in_column_name,
                   out_column_name)

##            LOGGER.debug("Executing SQL: %s",
##                         sql.replace(",", "|").replace(".", "||"))
            LOGGER.debug("Checking if extent grid cell %i in AOI." % (i * rows) + j)
            cur.execute(sql)

    sort_grid(cur, out_table_name, out_column_name)


def hex_grid(cur, in_table_name, in_column_name, out_table_name,
             out_column_name, cell_size):
    """Creates a table with a hexagonal grid contained within an AOI
    """
    #get spatial extent of AOI
    sql = "SELECT Box2D(ST_Union(%s)) from %s"
    sql = sql % (in_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)
    bbox, = cur.fetchone()
    LOGGER.debug("SQL result: %s", bbox)
    (min_x, min_y), (max_x, max_y) = [(float(x_extrema), float(y_extrema))
                                      for (x_extrema, y_extrema)
                                      in [point.split(" ")
                                          for point
                                          in bbox[4:-1].split(",")]]
    width, height = abs(max_x - min_x), abs(max_y - min_y)

    #calculate offsets for cell
    delta_short_x = cell_size * 0.25
    delta_long_x = cell_size * 0.5
    delta_y = cell_size * 0.25 * (3 ** 0.5)

    #calculate size of grid
    columns = int(math.floor(width/(3 * delta_long_x)) + 1)
    rows = int(math.floor(height/delta_y) + 1)

    #get AOI projection
    sql = "SELECT ST_srid(%s) FROM %s LIMIT 1" % (in_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)
    srid, = cur.fetchone()
    LOGGER.debug("SQL result: %s", srid)

    #create grid table
    sql = "CREATE TEMPORARY TABLE %s (%s geometry, id INTEGER)" % \
    (out_table_name, out_column_name)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)

    #insert grid cells if covered by AOI
    for j in range(columns):
        for i in range(rows):
            if (i + 1) % 2:
                centroid = (min_x + (delta_long_x * (1 + (3 * j))),
                            min_y + (delta_y * (i + 1)))
            else:
                centroid = (min_x + (delta_long_x * (2.5 + (3 * j))),
                            min_y + (delta_y * (i + 1)))

            x_coordinate, y_coordinate = centroid
            hexagon = [(x_coordinate - delta_long_x, y_coordinate),
                     (x_coordinate - delta_short_x, y_coordinate + delta_y),
                     (x_coordinate + delta_short_x, y_coordinate + delta_y),
                     (x_coordinate + delta_long_x, y_coordinate),
                     (x_coordinate + delta_short_x, y_coordinate - delta_y),
                     (x_coordinate - delta_short_x, y_coordinate - delta_y),
                     (x_coordinate - delta_long_x, y_coordinate)]
            hexagonsql = format_polygon_sql(hexagon, srid)

            sql = "INSERT INTO %s SELECT %s, %i as id FROM %s as %s," % \
            (out_table_name, out_column_name,
             (j * rows) + i, hexagonsql, out_column_name)
            sql = sql + " %s WHERE ST_Covers(%s.%s,%s)" % \
            (in_table_name, in_table_name, in_column_name, out_column_name)
##            LOGGER.debug("Executing SQL: %s",
##                         sql.replace(",", "|").replace(".", "||"))
            LOGGER.debug("Checking if extent grid cell %i in AOI." % (i * rows) + j)            
            cur.execute(sql)

    sort_grid(cur, out_table_name, out_column_name)


def sort_grid(cur, out_table_name, out_column_name):
    """Renumbers a table by spatial order.
    """
    sql = ("SELECT %s, "
           "row_number() OVER (ORDER BY ST_YMin(box2d(%s)), "
           "ST_XMin(box2d(%s)) ASC) FROM %s")
    sql = sql % ("id", out_column_name, out_column_name, out_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    renumber = cur.fetchall()

    sql = "ALTER TABLE %s ADD new_id integer"
    sql = sql % (out_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    sql = "UPDATE %s SET new_id = %i WHERE id = %i"
    for old_id, new_id in renumber:
        #LOGGER.debug("Executing SQL: %s." % (sql % (out_table_name, new_id, old_id)).replace(".", "||").replace(",", "|"))
        LOGGER.debug("Renumbering cell %i to %i." % (old_id, new_id))
        cur.execute(sql % (out_table_name, new_id, old_id))

    sql = "ALTER TABLE %s DROP COLUMN %s"
    sql = sql % (out_table_name, "id")
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    sql = "ALTER TABLE %s RENAME COLUMN %s to %s"
    sql = sql % (out_table_name, "new_id", "id")
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def table_shapefile(cur, sql, column_names, ogr_type_list, out_file_name,
                    srid = 0):
    """Creates a shapefile from the specified table and columns

    :param cur: A PostGIS database cursor
    :type cur: object
    :param sql: a sql statement that selects the appropriate rows
    :type sql: str
    :param column_names: the names as they should appear in the shapefile
    :type column_names: list
    :param ogr_type_list: the data types as they should appear in the shapefile
    :type ogr_type_list: list
    :param out_file_name: the full path and file name for the shapefile
    :type out_file_name: str

    :return: None
    :rtype: None

    :raise: IOError when file cannot be created"""

    driver = ogr.GetDriverByName('ESRI Shapefile')

    #delete existing file if it exists
    if os.path.exists(out_file_name):
        driver.DeleteDataSource(out_file_name)
    dataset = driver.CreateDataSource(out_file_name)

    if dataset is None:
        raise IOError, "Could not create file"

    #set projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srid)

    #create geometry layer
    column_names.pop(0)
    layer = dataset.CreateLayer(out_file_name, geom_type = ogr_type_list.pop(0),
                           srs = srs)

    #create attribute fields
    for field_name, field_type in zip(column_names, ogr_type_list):
        field_defn = ogr.FieldDefn(field_name, field_type)
        layer.CreateField(field_defn)

    feature_defn = layer.GetLayerDefn()

    #create each feature from the sql query
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    for row in cur:
        row = list(row)

        polygon = ogr.CreateGeometryFromWkt(row.pop(0))

        # create a new feature
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(polygon)

        #set field values
        for field, value in enumerate(row):
            feature.SetField(field, value)

        layer.CreateFeature(feature)

        polygon.Destroy()
        feature.Destroy()

    #write the shapefile
    dataset.Destroy()


def dump_execute(cur, in_table_name, out_file_name, column_alias = {}):
    """Creates a shapefile from a PostGIS table.
    """

    out_file_name = str(out_file_name)

    sql = "SELECT atttypid FROM pg_attribute WHERE attrelid =" +\
    " (SELECT oid FROM pg_class WHERE relname = 'photos_gis')" +\
    " AND attname = 'way'"
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    geom_oid,=cur.fetchone()

    LOGGER.debug("Creating shapefile from %s.", in_table_name)

    #check for empty table
    sql = "SELECT * FROM %s LIMIT 1"
    sql = sql % in_table_name
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    empty = not len(cur.fetchall())
    if empty:
        LOGGER.info("Table %s is empty.", in_table_name)
        return

    #get table description
    sql = "SELECT * FROM %s LIMIT 0"
    sql = sql % in_table_name
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))    
    cur.execute(sql)

    column_names = []
    ogr_type_list = []
    geometry_column_name = ""
    geometry_column_index = 0
    for i, desc in enumerate(cur.description):
        #int
        if desc[1] == 23:
            LOGGER.debug("Found integer column %s.", desc[0])
            column_names.append(desc[0])
            ogr_type_list.append(ogr.OFTInteger)
        #str
        elif desc[1] == 25:
            LOGGER.debug("Found string column %s.", desc[0])
            column_names.append(desc[0])
            ogr_type_list.append(ogr.OFTString)
        #float
        elif desc[1] == 701:
            LOGGER.debug("Found float column %s.", desc[0])
            column_names.append(desc[0])
            ogr_type_list.append(ogr.OFTReal)
        #geometry?
        elif desc[1] == geom_oid:
            geometry_column_index = i
            geometry_column_name = desc[0]
            LOGGER.debug("Found geometry column %s.", geometry_column_name)
        #None?
        elif desc[1] == 20:
            LOGGER.debug("Found None (integer) column %s.", desc[0])
            column_names.append(desc[0])
            ogr_type_list.append(ogr.OFTInteger)
        else:
            err_msg = "Column %s has a unknown type (OID) %i." % \
                      (desc[0], desc[1])
            raise Exception, err_msg


    #get geometry type
    sql = "SELECT ST_Dimension(%s) FROM %s LIMIT 1"
    sql = sql % (geometry_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    results = cur.fetchone()
    LOGGER.debug("Results: %s.", repr(results))
    geom_type, = results
    LOGGER.debug("Detected dimenion %i.", geom_type)
    if geom_type == -1:
        LOGGER.error("Null geometry cannot be exported.")
        raise ValueError, "Null geometry cannot be exported."
    elif geom_type == 0:
        LOGGER.info("Output shapefile will contain points.")
        geom_type = ogr.wkbPoint
    elif geom_type == 1:
        LOGGER.info("Output shapefile will contain lines.")
        geom_type = ogr.wkbLineString
    elif geom_type == 2:
        LOGGER.info("Output shapefile will contain polygons.")
        geom_type = ogr.wkbPolygon
    else:
        LOGGER.error("Unknown dimesionality %i.", geom_type)
        raise ValueError, "Unknown dimesionality %i." % geom_type

    #get projection
    sql = "SELECT ST_srid(%s) FROM %s LIMIT 1"
    sql = sql % (geometry_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    results = cur.fetchone()
    LOGGER.debug("Results: %s.", repr(results))
    srid, = results
    LOGGER.debug("Detected srid %i.", srid)

    sql = "SELECT ST_AsText(%s),* FROM %s"
    sql = sql % (geometry_column_name, in_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    LOGGER.debug("Loading OGR ESRI Shapefile driver.")
    #select shapefile output
    driver = ogr.GetDriverByName('ESRI Shapefile')

    #delete existing file if it exists
    if os.path.exists(out_file_name):
        driver.DeleteDataSource(out_file_name)
    dataset = driver.CreateDataSource(out_file_name)

    if dataset is None:
        LOGGER.error("Could not create file.")
        raise IOError, "Could not create file."

    LOGGER.debug("Setting projection.")
    #set projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srid)

    LOGGER.debug("Creating geometry layer.")
    #create geometry layer
    layer = dataset.CreateLayer(out_file_name, geom_type = geom_type, srs = srs)

    LOGGER.debug("Creating attribute columns.")
    #create attribute fields
    for field_name, field_type in zip(column_names, ogr_type_list):
        if field_name in column_alias:
            field_defn = ogr.FieldDefn(column_alias[field_name], field_type)
        else:
            field_defn = ogr.FieldDefn(field_name, field_type)
        layer.CreateField(field_defn)

    feature_defn = layer.GetLayerDefn()

    LOGGER.debug("Creating features.")
    #create each feature from the sql query
    for i, row in enumerate(cur):
        row = list(row)

        LOGGER.debug("Creating shape %i." % i)
        row.pop(geometry_column_index + 1)
        geom = row.pop(0)
        #LOGGER.debug("Found geometry %s.", geom)
        polygon = ogr.CreateGeometryFromWkt(geom)


        #LOGGER.debug("Creating feature.")
        # create a new feature
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(polygon)

        #LOGGER.debug("Setting attributes.")
        #set field values
        for field, value in enumerate(row):
            feature.SetField(field, value)

        #LOGGER.debug("Saving feature.")
        layer.CreateFeature(feature)

        #LOGGER.debug("Shape garbage collection.")
        polygon.Destroy()
        #LOGGER.debug("Feature garbage collection.")
        feature.Destroy()

    #write the shapefile
    dataset.Destroy()


def raster_table(cur, in_file_name, table_name, srid = -1):
    """Creates a PostGIS table from a raster

    :param cur: a PostGIS database cursor
    :type cur: object
    :param in_file_name: the full path and file name for a GeoTiff
    :type in_file_name: str

    :raise: ValueError when raster has more than 1 band
    :raise: IOError when raster cannot be opened
    """

    #Python register all drivers by default
    #gdal.GDALAllRegister()
    #driver = gdal.GetDriverByName("GTiff")
    #driver.Register()

    dataset = gdal.Open(in_file_name, gdal.GA_ReadOnly)
    wkt = dataset.GetProjectionRef()
    LOGGER.debug("Raster has WKT %s", repr(wkt).replace(",", "|").replace(".", "||"))
    if wkt != "":
        srid = wkt_to_srid(cur, wkt)
    elif srid == -1:
        err_msg = "The projection cannot be detected and is not specified"
        raise ValueError, err_msg
    LOGGER.debug("Detected projection %i", srid)

    if not dataset is None:
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        bands = dataset.RasterCount
        if bands != 1:
            raise ValueError, "The raster should contain exactly 1 band"

        sql = "CREATE TEMPORARY TABLE %s (pixel integer, way geometry)" % (table_name)
        LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))        
        cur.execute(sql)

        band = dataset.GetRasterBand(1)
        ds_transform = dataset.GetGeoTransform()
        origin_x, scale_x, theta_y, origin_y, theta_x, scale_y = ds_transform

        for i in range(cols):
            for j in range(rows):
                pixel = band.ReadAsArray(i, j, 1, 1)[0][0]

                way = []
                way.append(pixel_coordinate(origin_x, scale_x, theta_y,
                                            origin_y, theta_x, scale_y,
                                            i, j))
                way.append(pixel_coordinate(origin_x, scale_x, theta_y,
                                            origin_y, theta_x, scale_y,
                                            i + 1, j))
                way.append(pixel_coordinate(origin_x, scale_x, theta_y,
                                            origin_y, theta_x, scale_y,
                                            i + 1, j + 1))
                way.append(pixel_coordinate(origin_x, scale_x, theta_y,
                                            origin_y, theta_x, scale_y,
                                            i, j + 1))
                way.append(pixel_coordinate(origin_x, scale_x, theta_y,
                                            origin_y, theta_x, scale_y,
                                            i, j))
                waysql = format_polygon_sql(way, srid)

                sql = "INSERT INTO %s VALUES(%s, %s)"
                sql = sql % (table_name, str(pixel), waysql)
                LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
                cur.execute(sql)

    else:
        raise IOError, "Could not open raster file."


def lulc_area_sql(grid_name, lulc_name):
    """Returns a sql statement that intersects a grid with the LULC table and
    sums the areas

    :param grid_name: the PostGIS table name for the grid
    :type grid_name: str
    :param lulc_name: the PostGIS table name for the LULC table
    :type lulc_name: str

    :return: a sql statement
    :rtype: str"""

    sql = ("SELECT grid.i, "
           "grid.j, "
           "SUM(CASE WHEN pixel = 1 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Agriculture, "
           "SUM(CASE WHEN pixel = 2 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Bare, "
           "SUM(CASE WHEN pixel = 3 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Forest, "
           "SUM(CASE WHEN pixel = 4 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Grassland, "
           "SUM(CASE WHEN pixel = 5 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Shrubland, "
           "SUM(CASE WHEN pixel = 6 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Frozen, "
           "SUM(CASE WHEN pixel = 7 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Urban, "
           "SUM(CASE WHEN pixel = 8 "
           "THEN ST_Area(ST_Intersection(grid.way, lulc.way)) "
           "ELSE 0 END) AS Water, "
           "grid.way FROM %s AS grid, "
           "%s AS lulc "
           "WHERE ST_Intersects(grid.way, lulc.way) "
           "GROUP BY grid.i, grid.j, grid.way ORDER BY grid.j, grid.i ASC")

    sql = sql % (grid_name, lulc_name)

    return sql


def grid_union(cur, grid_name, grid_union_name):
    """Creates a table from a dissolved grid

    :param cur: a PostGIS database cursor
    :type cur: object
    :param  grid_name: the table name of the grid to dissolve
    :type grid_name: str
    :param grid_union_name: the table name to contain the dissolved grid
    :type grid_union_name: str

    :return: None
    :rtype: None"""

    grid_union_name = grid_name + "_union"
    sql = ("CREATE TEMPORARY TABLE %s AS "
           "(SELECT 0 as id, "
           "ST_Union(grid.cell) AS cell "
           "FROM %s AS grid)")
    sql = sql % (grid_union_name, grid_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)



def grid_transform(cur, grid_name, grid_transform_name, srid):
    """Creates a table with a reprojected grid

    :param cur: a PostGIS database cursor
    :type cur: object
    :param grid_name: the table name of the grid to project
    :type grid_name: str
    :param gridTansform_name: the table name to contain the projected grid
    :type gridTansform_name: str
    :param srid: the Spatial Reference Identification for the destination
    projection
    :type srid: int

    :return: None
    :rtype: None"""

    sql = ("SELECT EXISTS "
           "(SELECT * "
           "FROM INFORMATION_SCHEMA.TABLES "
           "WHERE TABLE_SCHEMA = 'public' AND TABLE_NAME = '%s')")
    sql = sql % (grid_transform_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    exists, = cur.fetchone()

    if not exists:
        sql = ("CREATE TEMPORARY TABLE %s AS "
               "(SELECT grid.id, "
               "ST_Transform(grid.cell,%s) as cell "
               "FROM %s AS grid)")
        sql = sql % (grid_transform_name, srid, grid_name)
        LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
        cur.execute(sql)
    else:
        LOGGER.debug("Attempted to create additional table name %s",
                     grid_transform_name)


def transform(cur, osm_name, transform_name, srid):
    """Creates a table with reprojected OSM data

    :param cur: a PostGIS database cursor
    :type cur: object
    :param osm_name: the table name of the OSM data
    :type osm_name: str
    :param transform_name: the table name to contain the reprojected OSM data
    :param srid: the Spatial Reference Identification for the destination
    projection
    :type srid: int

    :return: None
    :rtype: None"""

    sql = ("CREATE TEMPORARY TABLE %s AS "
           "(SELECT osm_id, "
           "ST_Transform(layer.way,%s) as way "
           "FROM %s AS layer)")
    sql = sql % (transform_name, srid, osm_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def transform_sql(in_table_name, out_table_name, geometry_column, srid,
                  extra_columns = []):
    """Constructs a SQL query to do a spatial transform using PostGIS.
    """
    columnsql = ",".join(["ST_Transform(%s.%s,%i) AS %s"] + extra_columns)
    sql = "CREATE TEMPORARY TABLE %s AS (SELECT " + columnsql + " FROM %s)"
    sql = sql % (out_table_name,
                 in_table_name, geometry_column, srid, geometry_column,
                 in_table_name)
    return sql


def transform_execute(cur, in_table_name, out_table_name, geometry_column, srid,
                      extra_columns = []):
    """Executes a SQL query to do a spatial transform using PostGIS.
    """
    sql = transform_sql(in_table_name, out_table_name, geometry_column, srid,
                        extra_columns)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)


def union_execute(cur, in_table_name, out_table_name, geometry_column):
    """Executes a SQL query to do a spatial dissolve using PostGIS.
    """
    sql = "CREATE TEMPORARY TABLE %s AS (SELECT ST_Union(%s.%s) as %s FROM %s)"
    sql = sql % (out_table_name, in_table_name, geometry_column,
                 geometry_column, in_table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def clip_sql(in_table_name, in_table_column, mask_name, mask_column,
             out_table_name, extra_columns = []):
    """Constructs a SQL query to do a spatial clip using PostGIS.
    """
    columnsql = ",".join(["ST_Intersection(%s.%s,%s.%s) AS %s"] + extra_columns)
    LOGGER.debug("Constructing SQL query for clip.")
    sql = "CREATE TEMPORARY TABLE %s AS (SELECT "
    sql = sql + columnsql
    sql = sql + (" FROM %s, %s WHERE ST_Intersects(%s.%s,%s.%s) "
                 "AND ST_IsValid(%s.%s))")
    sql = sql % (out_table_name,
                 mask_name, mask_column,
                 in_table_name, in_table_column,
                 in_table_column,
                 in_table_name,
                 mask_name,
                 mask_name, mask_column,
                 in_table_name, in_table_column,
                 in_table_name, in_table_column)
    return sql


def clip_execute(cur, in_table_name, in_table_column, mask_name, mask_column,
                 out_table_name, extra_columns = []):
    """Executes a SQL query to do a spatial clip using PostGIS.
    """
    sql = clip_sql(in_table_name, in_table_column, mask_name, mask_column,
                   out_table_name, extra_columns)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def osm_point_clip(cur, aoi_name, point_name):
    """Creates a table with the OSM point features cliped by an AOI

    :param cur: a PostGIS cursor
    :type cur: object
    :param aoi_name: a PostGIS table name containing the AOI
    :type aoi_name: str
    :param point_name: a PostGIS table name containg the OSM point features
    :type point_name: str

    :return: None
    :rtype: None"""
    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT osm.osm_id, osm.way"
    " FROM planet_osm_point as osm, %s as aoi"
    " WHERE ST_Intersects(aoi.cell, osm.way))")
    sql = sql % (point_name, aoi_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def osm_line_clip(cur, aoi_name, line_name):
    """Creates a table with the OSM line features cliped by an AOI

    :param cur: a PostGIS cursor
    :type cur: object
    :param aoi_name: a PostGIS table name containing the AOI
    :type aoi_name: str
    :param line_name: a PostGIS table name containg the OSM line features
    :type line_name: str

    :return: None
    :rtype: None"""

    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT osm.osm_id, ST_Intersection(aoi.cell, osm.way) AS way"
    " FROM planet_osm_line as osm, %s as aoi"
    " WHERE ST_Intersects(aoi.cell, osm.way))")
    sql = sql % (line_name, aoi_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def osm_poly_clip(cur, aoi_name, poly_name):
    """Creates a table with the OSM polygon features cliped by an AOI

    :param cur: a PostGIS cursor
    :type cur: object
    :param aoi_name: a PostGIS table name containing the AOI
    :type aoi_name: str
    :param poly_name: a PostGIS table name containg the OSM polygon features
    :type poly_name: str

    :return: None
    :rtype: None"""

    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT osm.osm_id, ST_Intersection(aoi.cell, osm.way) AS way"
    " FROM planet_osm_polygon as osm, %s as aoi"
    " WHERE ST_Intersects(aoi.cell, osm.way) AND ST_IsValid(osm.way))")
    sql = sql % (poly_name, aoi_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def osm_count_sql(grid, osm, cat):
    """Returns a sql fragment that counts OSM point features per grid cell by
    category

    :param grid: a PostGIS table name containing the grid
    :type grid: str
    :param osm: a PostGIS table name containing the OSM point features
    :type osm: str
    :param cat: a PostGIS table containing the OSM point features' categories
    :type cat: str

    :return: a sql fragment
    :rtype: str"""

    sql = ("SELECT"
    " SUM(CASE WHEN cat.cat = 1 THEN 1 ELSE 0 END) AS pointCult,"
    " SUM(CASE WHEN cat.cat = 2 THEN 1 ELSE 0 END) AS pointIndus,"
    " SUM(CASE WHEN cat.cat = 3 THEN 1 ELSE 0 END) AS pointNat,"
    " SUM(CASE WHEN cat.cat = 4 THEN 1 ELSE 0 END) AS pointStruct,"
    " SUM(CASE WHEN cat.cat = 0 THEN 1 ELSE 0 END) AS pointMisc,"
    " grid.id AS id"
    " FROM %s as grid,"
    " %s AS osm,"
    " %s AS cat"
    " WHERE cat.osm_id = osm.osm_id AND ST_Intersects(grid.cell, osm.way)"
    " GROUP BY"
    " id")

    return sql % (grid, osm, cat)


def osm_length_sql(grid, osm, cat):
    """Returns a sql fragment that sums the length of OSM line features per grid
    cell by category

    :param grid: a PostGIS table name containing the grid
    :type grid: str
    :param osm: a PostGIS table name containing the OSM line features
    :type osm: str
    :param cat: a PostGIS table containing the OSM line features' categories
    :type cat: str

    :return: a sql fragment
    :rtype: str"""

    sql = ("SELECT "
           "SUM(CASE WHEN cat.cat = 1 "
           "THEN ST_Length(ST_Intersection(grid.cell, osm.way)) "
           "ELSE 0 END) AS lineCult, "
           "SUM(CASE WHEN cat.cat = 2 "
           "THEN ST_Length(ST_Intersection(grid.cell, osm.way)) "
           "ELSE 0 END) AS lineIndus, "
           "SUM(CASE WHEN cat.cat = 3 "
           "THEN ST_Length(ST_Intersection(grid.cell, osm.way)) "
           "ELSE 0 END) AS lineNat, "
           "SUM(CASE WHEN cat.cat = 4 "
           "THEN ST_Length(ST_Intersection(grid.cell, osm.way)) "
           "ELSE 0 END) AS lineStruct, "
           "SUM(CASE WHEN cat.cat = 0 "
           "THEN ST_Length(ST_Intersection(grid.cell, osm.way)) "
           "ELSE 0 END) AS lineMisc, grid.id AS id "
           "FROM %s AS grid, "
           "%s AS osm, "
           "%s AS cat "
           "WHERE cat.osm_id = osm.osm_id AND ST_Intersects(grid.cell, osm.way)"
           " GROUP BY id")

    return sql % (grid, osm, cat)


def osm_area_sql(grid, osm, cat):
    """Returns a sql fragment that sums the total area by category of a grid
    cell coverd by OSM polygon features

    :param grid: a PostGIS table name containing the grid
    :type grid: str
    :param osm: a PostGIS table name containing the OSM polygon features
    :type osm: str
    :param cat: a PostGIS table containing the OSM polygon features' categories
    :type cat: str

    :return: a sql fragment
    :rtype: str"""

    sql = ("SELECT polyunion.id, "
           "SUM(CASE WHEN polyunion.cat = 1 THEN polyunion.area "
           "ELSE 0 END) AS polyCult, "
           "SUM(CASE WHEN polyunion.cat = 2 THEN polyunion.area "
           "ELSE 0 END) AS polyIndus, "
           "SUM(CASE WHEN polyunion.cat = 3 THEN polyunion.area "
           "ELSE 0 END) AS polyNat, "
           "SUM(CASE WHEN polyunion.cat = 4 THEN polyunion.area "
           "ELSE 0 END) AS polyStruct, "
           "SUM(CASE WHEN polyunion.cat = 0 THEN polyunion.area "
           "ELSE 0 END) AS polyMisc "
           "FROM ("
           "SELECT grid.id, "
           "cat.cat , "
           "ST_Area(ST_Union(ST_Intersection(grid.cell, osm.way))) AS area"
           " FROM"
           " %s AS grid,"
           " %s AS osm,"
           " %s AS cat"
           " WHERE"
           " osm.osm_id = cat.osm_id AND"
           " ST_Intersects(grid.cell, osm.way)"
           " GROUP BY grid.id, cat.cat) AS polyunion"
           " GROUP BY polyunion.id")

    return sql % (grid, osm, cat)


def join_results_sql(predictors, grid, results_format, result_column,
                     results_name, attributes = []):
    """Constructs a SQL query to do a table join on recreation model results.
    """
    create = "CREATE TEMPORARY TABLE %s AS (SELECT" % results_name
    create = create + " grid.cell AS cell, grid.id AS \"cellID\","
    create = create + " ST_Area(grid.cell) AS \"cellArea\""
    columns = ""
    joins = ""
    values = {}
    for i, predictor in enumerate(predictors):
        values[predictor] = [", predictor%i.%s AS \"%s\"" %
                             (i, result_column, predictor),
                           (" LEFT JOIN %s AS predictor%i "
                            "ON grid.id = predictor%i.id") %
                             (results_format%predictor, i, i)]
    for attr in attributes:
        LOGGER.debug("Adding grid attribute %s.", attr)
        values[attr] = [", grid.%s AS %s" % (attr, attr), ""]

    keys = values.keys()
    keys.sort()
    for k in keys:
        column, join = values[k]
        columns += column
        joins += join

    sql = "%s%s FROM %s AS grid%s)" % (create, columns, grid, joins)
    return sql


def join_results_execute(cur, predictors, grid, results_format, result_column,
                         results_name, attributes = []):
    """Executes a SQL query to do a table join on recreation model results.
    """
    sql = join_results_sql(predictors, grid, results_format, result_column,
                           results_name, attributes)
    LOGGER.debug("Executing SQL: %s", sql.replace(",", "|").replace(".", "||"))
    cur.execute(sql)


def grid_osm_sql(grid_name, point_sql, line_sql, polygon_sql):
    """Returns a sql statement that counts points, sums lengths, and sums areas
    of OSM features by catergory per grid cell

    :param grid_name: a PostGIS table name containing the grid
    :type grid_name: str
    :param point_sql: a sql fragment counting OSM point features by category per
    grid cell
    :type point_sql: str
    :param line_sql: a sql fragment summing OSM line features' lengths by
    category per grid cell
    :type line_sql: str
    :param polygon_sql: a sql fragment summing OSM polygon features' areas
    coverd by category per grid cell
    :type polygon_sql: str

    :return: a sql fragment
    :rtype: str"""

    sql = ("SELECT"
    " ST_AsText(grid.cell) AS cell,"
    " grid.id AS \"cellID\","
    " ST_Area(grid.cell) AS \"cellArea\","
    " point.pointCult AS \"pointCult\","
    " point.pointIndus AS \"pointIndus\","
    " point.pointNat AS \"pointNat\","
    " point.pointStruct AS \"pointStruct\","
    " point.pointMisc AS \"pointMisc\","
    " line.lineCult AS \"lineCult\","
    " line.lineIndus AS \"lineIndus\","
    " line.lineNat AS \"lineNat\","
    " line.lineStruct AS \"lineStruct\","
    " line.lineMisc AS \"lineMisc\","
    " poly.polyCult AS \"polyCult\","
    " poly.polyIndus AS \"polyIndus\","
    " poly.polyNat AS \"polyNat\","
    " poly.polyStruct AS \"polyStruct\","
    " poly.polyMisc AS \"polyMisc\""
    " FROM"
    " %s AS grid"
    " LEFT JOIN (%s)"
    " AS point"
    " ON grid.id = point.id"
    " LEFT JOIN (%s)"
    " AS line"
    " ON grid.id = line.id"
    " LEFT JOIN (%s)"
    " AS poly"
    " ON grid.id = poly.id")

    sql = sql % (grid_name, point_sql, line_sql, polygon_sql)

    return sql


def flickr_grid_table(cur, grid_name, flickr_name, out_file_name,
                      before_year = 2013):
    """Creates a CSV file with the daily grid cell visitation by Flickr users

    :param cur: a PostGIS cursor
    :type cur: object
    :param grid_name: a PostGIS table name for a grid
    :type grid_name: str
    :param flickr_name: a PostGIS table name for the Flickr data
    :type flickr_name: str
    :param out_file_name: the full path and file name for the output CSV
    :type out_file_name: str

    :return: None
    :rtype: None"""

    sql = ("SELECT \"gridID\", date_taken, count(owner_name)"
    " FROM (SELECT DISTINCT grid.id AS \"gridID\", "
           "flickr.owner_name AS owner_name, "
           "LEFT(flickr.date_taken,10) AS date_taken"
    " FROM %s AS grid, %s AS flickr"
    " WHERE (ST_Intersects(grid.cell, flickr.way)) "
           "AND (LEFT(flickr.date_taken,10) < '%i')) AS flickr_summary"
    " GROUP BY \"gridID\", date_taken"
    " ORDER BY \"gridID\", date_taken ASC")
    sql = sql % (grid_name, flickr_name, before_year)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    out_file = open(out_file_name, 'w')
    out_file.write("cellID, date_taken, piclen\n")
    for row in cur:
        out_file.write(",".join([str(row_element)
                                 for row_element in row]) + "\n")
    out_file.close()


def wkt_to_srid(cur, wkt):
    """Retreive srid srid from Esri Shapefile PRJ file

    :param cur: a PostGIS cursor
    :type cur: object
    :param wkt: a WKT projection
    :type wkt: str

    :return: a Spatial Reference Identification
    :rtype: int"""

    LOGGER.debug("Checking for srid of WKT %s", repr(wkt).replace(",", "|").replace(".", "||"))

    #check if WKT projection is already known
    sql = "SELECT COUNT(*) FROM prj_srid WHERE wkt = %s"
    LOGGER.debug("Executing SQL: %s." % (sql % wkt).replace(".", "||").replace(",", "|"))
    cur.execute(sql, (wkt,))
    known, = cur.fetchone()

    #fetch unknown WKT projection auth_srid
    if not known:
        LOGGER.debug("No matching WKT found.")
        #check srid_name
        name = wkt.split("\"")[1]
        sql = "SELECT COUNT(*) FROM srid_name WHERE name = %s"
        LOGGER.debug("Executing SQL: %s." % (sql % name).replace(".", "||").replace(",", "|"))
        cur.execute(sql, (name,))
        known, = cur.fetchone()

        if not known:
            LOGGER.error("WKT %s unknown.", repr(wkt).replace(",", "|").replace(".", "||"))
            raise ValueError, ("WKT %s unknown." % repr(wkt).replace(",", "|").replace(".", "||"))
        else:
            sql = "SELECT srid FROM srid_name WHERE name = %s"
            LOGGER.debug("Executing SQL: %s." % (sql % name).replace(".", "||").replace(",", "|"))
            cur.execute(sql, (name,))
            srid, = cur.fetchone()

            sql = "INSERT INTO prj_srid VALUES(%s,%s,'user')"
            LOGGER.debug("Executing SQL: %s." % (sql % (wkt, srid)).replace(".", "||").replace(",", "|"))
            cur.execute(sql, (wkt, srid))

##        query = urlencode({
##            'exact' : True,
##            'error' : True,
##            'mode' : 'wkt',
##            'terms' : wkt})
##
##      LOGGER.debug("Opening http://prj2srid.org/search.json?%s", repr(query))
##        webres = urlopen('http://prj2srid.org/search.json', query)
##        jres = json.loads(webres.read())
##        auth_srid = int(jres['codes'][0]['code'])
##
##        sql = "INSERT INTO prj_srid VALUES(\'%s\',%i)"
##        sql = sql % (wkt.replace("\'","\'\'"),auth_srid)
##        print sql
##        cur.execute(sql)

    #fetch known WKT projection auth_srid
    else:
        LOGGER.debug("Found matching WKT.")
        sql = "SELECT auth_srid FROM prj_srid WHERE wkt = %s"
        LOGGER.debug("Executing SQL: %s." % (sql % wkt).replace(".", "||").replace(",", "|"))
        cur.execute(sql, (wkt,))
        srid, = cur.fetchone()
        LOGGER.debug("Found corresponding SRID %i.", srid)

    #ensure spatial_ref_sys has  srid for auth_srid
    #srid2sql(cur, auth_srid)

    sql = "SELECT COUNT(*) FROM spatial_ref_sys WHERE auth_srid = %s"
    LOGGER.debug("Executing SQL: %s." % (sql % srid).replace(".", "||").replace(",", "|"))
    cur.execute(sql, (srid,))
    known, = cur.fetchone()

    if known:
        LOGGER.debug("SRID %i is defined in the PostGIS database.", srid)
    else:
        LOGGER.error("SRID %i is not defined in the PostGIS database.", srid)
        err_msg = "SRID %i is not registered in the PostGIS database." % srid
        raise ValueError, err_msg

    return srid


def srid2sql(cur, auth_srid):
    """Checks for srid srid entry in spatial_ref_sys and scrapes from web
    if needed

    :param cur: a PostGIS cursor
    :type cur: object
    :param auth_srid: a srid Spatial Reference Identification
    :type auth_srid: int

    :return: None
    :rtype: None"""

    sql = "SELECT COUNT(*) FROM spatial_ref_sys WHERE auth_srid = %i"
    LOGGER.debug("Executing SQL: %s." % (sql % auth_srid).replace(".", "||").replace(",", "|"))
    cur.execute(sql, (auth_srid,))
    known, = cur.fetchone()
    if not known:
        webpage = urlopen("http://spatialreference.org/ref/epsg/%i/postgis/" %
                    (auth_srid))
        sql = webpage.read()
        webpage.close()
        LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
        cur.execute(sql)


def utm_geography_table(cur):
    """Creates a table with the srid and geographic bounds of the UTM zones

    :param cur: a PostGIS cursor
    :type cur: object

    :return: None
    :rtype: None"""
    geography_srid = 4326
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)

    for i, srid in enumerate(range(32601, 32661)):
        sql = "INSERT INTO srid_geom VALUES(%s, %s)"
        cur.execute(sql, (srid,
                          format_polygon_sql(bounding_box([(-180 + (6 * i), 0),
                                                           (-174 + (6 * i), 84)]),
                                             geography_srid)))

    srid = 32661
    sql = "INSERT INTO srid_geom VALUES(%s, %s)"
    cur.execute(sql, (srid,
                      format_polygon_sql(bounding_box([(-180, 60), (180, 90)]),
                                         geography_srid)))

    for i, srid in enumerate(range(32701, 32761)):
        sql = "INSERT INTO srid_geom VALUES(%s, %s)"
        cur.execute(sql, (srid,
                          format_polygon_sql(bounding_box([(-180 + (6 * i), -80),
                                                           (-174 + (6 * i), 0)]),
                                             geography_srid)))

    srid = 32761
    sql = "INSERT INTO srid_geom VALUES(%s, %s)"
    sql = cur.execute(sql, (srid,
                            format_polygon_sql(bounding_box([(-180, -90), (180, -60)]),
                                               geography_srid)))


def destination_srid(cur, aoi_name):
    """Returns the srid for the UTM zone that covers the AOI

    :param cur: a PostGIS cursor
    :type cur: object
    :param aoi_name: a PostGIS table name
    :type aoi_name: str

    :return: the Spatial Reference Identification
    :rtype: int
    """
    sql = ("SELECT srid FROM "
           "%s AS projections, "
           "%s AS aoi "
           "WHERE ST_Covers(projections.geom, aoi.way)")
    sql = sql % ("srid_geom", aoi_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))    
    cur.execute(sql)
    srid, = cur.fetchone()

    return srid


def get_utm_srid(cur, aoi_table, geom_table):
    """Returns the list or SRIDs for the UTM zones with which a PostGIS
    table intersects.
    """
    sql = ("SELECT srid FROM "
           "%s as zones, "
           "%s as aoi "
           "WHERE ST_Intersects(aoi.way, zones.geom)")
    sql = sql % (geom_table, aoi_table)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    utmsrid = cur.fetchall()

    return utmsrid


def get_intersects_covers(cur, aoi_name, borders_name):
    """Returns the number of objects that cover and interesect with the AOI
    """
    sql = ("SELECT COUNT(*) FROM "
           "%s AS aoi, "
           "%s AS borders "
           "WHERE ST_Intersects(aoi.way, borders.way)")
    sql = sql % (aoi_name, borders_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    intersects, = cur.fetchone()

    sql = ("SELECT COUNT(*) FROM "
           "%s AS aoi, "
           "%s AS borders "
           "WHERE ST_Covers(borders.way, aoi.way)")
    sql = sql % (aoi_name, borders_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    covers, = cur.fetchone()

    return (intersects, covers)


def grid_point_execute(cur, grid, point_name, results_name):
    """Executes the SQL to count the number of points in a grid cell.
    """
    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT grid.id AS id,"
    " COUNT(*) as result"
    " FROM %s as grid,"
    " %s as layer"
    " WHERE ST_Intersects(grid.cell, layer.way)"
    " GROUP BY id)")
    sql = sql % (results_name, grid, point_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def grid_line_execute(cur, grid, line_name, results_name):
    """Executes the SQL to add up the length of lines in a grid cell.
    """
    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT grid.id AS id,"
    " SUM(ST_Length(ST_Intersection(grid.cell, layer.way))) as result"
    " FROM %s as grid,"
    " %s as layer"
    " WHERE ST_Intersects(grid.cell, layer.way)"
    " GROUP BY id)")
    sql = sql % (results_name, grid, line_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def grid_polygon_execute(cur, grid, polygon_name, results_name):
    """Executes the SQL to add up the areas of polygons in a grid cell.
    """
    sql = ("CREATE TEMPORARY TABLE %s AS"
    " (SELECT grid.id AS id,"
    " ST_Area(ST_Union(ST_Intersection(grid.cell, layer.way))) as result"
    " FROM %s as grid,"
    " %s as layer"
    " WHERE ST_Intersects(grid.cell, layer.way)"
    " GROUP BY id)")
    sql = sql % (results_name, grid, polygon_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)


def dimension_execute(cur, table_name, geo_column_name):
    """Executes the SQL to get the number of dimensions of a geometry object
    in a table
    """
    sql = "SELECT ST_Dimension(%s) FROM %s LIMIT 1"
    sql = sql % (geo_column_name, table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    dim = cur.fetchone()

    if dim is None:
        return -1
    else:
        dim, = dim
        return dim


def single_area_execute(cur, table_name, geo_column_name):
    """Executes the SQL to get the area of PostGIS objects in a table.
    """
    sql = "SELECT ST_Area(%s) FROM %s"
    sql = sql % (geo_column_name, table_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
    area, = cur.fetchone()

    return area

def raster_clip_sql(raster_name, rast_column_name, aoi_name, geo_column_name, clip_name):
    sql = "CREATE TEMPORARY TABLE %s AS"
    " (SELECT (ST_Intersection(%s.%s, %s.%s)).*"
    " FROM %s, %s WHERE ST_Intersects(%s.%s, %s.%s))"

    sql = sql % (clip_name,
                 raster_name, raster_column_name, aoi_name, geo_column_name,
                 raster_name, raster_column_name, aoi_name, geo_column_name)

def raster_clip_execute(cur, raster_name, rast_column_name, aoi_name, geo_column_name, clip_name):
    sql = raster_clip_sql(raster_name, rast_column_name, aoi_name, geo_column_name, clip_name)
    LOGGER.debug("Executing SQL: %s." % sql.replace(".", "||").replace(",", "|"))
    cur.execute(sql)
