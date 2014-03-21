import os
import math

import numpy as np
import scipy.stats
import shutil
import logging

from osgeo import gdal
from osgeo import ogr
from osgeo import osr

from invest_natcap import raster_utils
from invest_natcap.scenic_quality import scenic_quality_core
#from invest_natcap.overlap_analysis import overlap_analysis

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('scenic_quality')

def reproject_dataset_uri(original_dataset_uri, *args, **kwargs):
    """A URI wrapper for reproject dataset that opens the original_dataset_uri
        before passing it to reproject_dataset.

       original_dataset_uri - a URI to a gdal Dataset on disk

       All other arguments to reproject_dataset are passed in.

       return - nothing"""

    original_dataset = gdal.Open(original_dataset_uri)
    reproject_dataset(original_dataset, *args, **kwargs)

    raster_utils.calculate_raster_stats_uri(original_dataset_uri)

def reproject_dataset(original_dataset, output_wkt, output_uri,
                      output_type = gdal.GDT_Float32):
    """A function to reproject and resample a GDAL dataset given an output pixel size
        and output reference and uri.

       original_dataset - a gdal Dataset to reproject
       pixel_spacing - output dataset pixel size in projected linear units (probably meters)
       output_wkt - output project in Well Known Text (the result of ds.GetProjection())
       output_uri - location on disk to dump the reprojected dataset
       output_type - gdal type of the output    

       return projected dataset"""

    original_sr = osr.SpatialReference()
    original_sr.ImportFromWkt(original_dataset.GetProjection())

    output_sr = osr.SpatialReference()
    output_sr.ImportFromWkt(output_wkt)

    vrt = gdal.AutoCreateWarpedVRT(original_dataset, None, output_wkt, gdal.GRA_Bilinear) 

    # Get the Geotransform vector
    geo_t = vrt.GetGeoTransform()
    x_size = vrt.RasterXSize # Raster xsize
    y_size = vrt.RasterYSize # Raster ysize

    # Work out the boundaries of the new dataset in the target projection
    

    gdal_driver = gdal.GetDriverByName('GTiff')
    # The size of the raster is given the new projection and pixel spacing
    # Using the values we calculated above. Also, setting it to store one band
    # and to use Float32 data type.

    output_dataset = gdal_driver.Create(output_uri, x_size, 
                              y_size, 1, output_type)

    # Set the nodata value
    out_nodata = original_dataset.GetRasterBand(1).GetNoDataValue()
    output_dataset.GetRasterBand(1).SetNoDataValue(out_nodata)

    # Set the geotransform
    output_dataset.SetGeoTransform(geo_t)
    output_dataset.SetProjection (output_sr.ExportToWkt())

    # Perform the projection/resampling 
    gdal.ReprojectImage(original_dataset, output_dataset,
                        original_sr.ExportToWkt(), output_sr.ExportToWkt(),
                        gdal.GRA_Bilinear)
    
    return output_dataset


def reclassify_quantile_dataset_uri(dataset_uri, quantile_list, dataset_out_uri, datatype_out, nodata_out):
    nodata_ds = raster_utils.get_nodata_from_uri(dataset_uri)

    memory_file_uri = raster_utils.temporary_filename()
    memory_array = raster_utils.load_memory_mapped_array(dataset_uri, memory_file_uri)
    memory_array_flat = memory_array.reshape((-1,))

    quantile_breaks = [0]
    for quantile in quantile_list:
        LOGGER.debug('quantile %f' % quantile)
        quantile_breaks.append(scipy.stats.scoreatpercentile(
                memory_array_flat, quantile, (0.0, np.amax(memory_array_flat))))

    def reclass(value):
        if value == nodata_ds:
            return nodata_out
        else:
            for new_value,quantile_break in enumerate(quantile_breaks):
                if value <= quantile_break:
                    return new_value
        raise ValueError, "Value was not within quantiles."

    cell_size = raster_utils.get_cell_size_from_uri(dataset_uri)

    raster_utils.vectorize_datasets([dataset_uri],
                                    reclass,
                                    dataset_out_uri,
                                    datatype_out,
                                    nodata_out,
                                    cell_size,
                                    "union",
                                    dataset_to_align_index=0)

    raster_utils.calculate_raster_stats_uri(dataset_out_uri)

def get_data_type_uri(ds_uri):
    raster_ds = gdal.Open(ds_uri)
    raster_data_type = raster_ds.GetRasterBand(1).DataType
    raster_ds = None

    return raster_data_type

def compute_viewshed_uri(in_dem_uri, out_viewshed_uri, in_structure_uri, 
    curvature_correction, refr_coeff, args):
    """ Compute the viewshed as it is defined in ArcGIS where the inputs are:

        -in_dem_uri: URI to input surface raster
        -out_viewshed_uri: URI to the output raster
        -in_structure_uri: URI to a point shapefile that contains the location
        of the observers and the viewshed radius in (negative) meters
        -curvature_correction: flag for the curvature of the earth. Either
        FLAT_EARTH or CURVED_EARTH. Not used yet.
        -refraction: refraction index between 0 (max effect) and 1 (no effect).
        Default is 0.13."""

    # Extract cell size from input DEM
    cell_size = raster_utils.get_cell_size_from_uri(in_dem_uri)

    # Extract nodata
    nodata = raster_utils.get_nodata_from_uri(in_dem_uri)
    
    # Build I and J arrays, and save them to disk
    rows, cols = raster_utils.get_row_col_from_uri(in_dem_uri)
    I, J = np.meshgrid(range(rows), range(cols), indexing = 'ij')
    I_uri = raster_utils.temporary_filename()
    J_uri = raster_utils.temporary_filename()
    shutil.copy(in_dem_uri, I_uri)
    I_raster = gdal.Open(I_uri, gdal.GA_Update)
    I_raster.GetRasterBand(1).WriteArray(I)
    I_raster = None
    shutil.copy(in_dem_uri, J_uri)
    J_raster = gdal.Open(J_uri, gdal.GA_Update)
    J_raster.GetRasterBand(1).WriteArray(J)
    J_raster = None

    # Extract the input raster geotransform
    GT = raster_utils.get_geotransform_uri(in_dem_uri)

    # Open the input URI and extract the numpy array
    input_raster = gdal.Open(in_dem_uri)
    input_array = input_raster.GetRasterBand(1).ReadAsArray()
    input_raster = None

    # Create a raster from base before passing it to viewshed
    visibility_uri = out_viewshed_uri #raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(in_dem_uri, visibility_uri, 'GTiff', \
        255, gdal.GDT_Byte, fill_value = 255)

    # Call the non-uri version of viewshed.
    compute_viewshed(input_array, visibility_uri, in_structure_uri,
    cell_size, rows, cols, nodata, GT, I_uri, J_uri, curvature_correction, 
    refr_coeff, args)


def compute_viewshed(input_array, visibility_uri, in_structure_uri, \
    cell_size, rows, cols, nodata, GT, I_uri, J_uri, curvature_correction, \
    refr_coeff, args):
    """ array-based function that computes the viewshed as is defined in ArcGIS
    """
    # default parameter values that are not passed to this function but that
    # scenic_quality_core.viewshed needs
    obs_elev = 1.0 # Observator's elevation in meters
    tgt_elev = 0.0  # Extra elevation applied to all the DEM
    max_dist = -1.0 # max. viewing distance(m). Distance is infinite if negative
    coefficient = 1.0 # Used to weight the importance of individual viewsheds
    height = 0.0 # Per viewpoint height offset--updated as we read file info

    # Compute the distance for each point
    def compute_distance(vi, vj, cell_size):
        def compute(i, j, v):
            if v == 1:
                return ((vi - i)**2 + (vj - j)**2)**.5 * cell_size
            else:
                return -1.
        return compute

    # Apply the valuation functions to the distance
    def polynomial(a, b, c, d, max_valuation_radius):
        def compute(x, v):
            if v==1:
                if x < 1000:
                    return a + b*1000 + c*1000**2 + d*1000**3 - \
                        (b + 2*c*1000 + 3*d*1000**2)*(1000-x)
                elif x <= max_valuation_radius:
                    return a + b*x + c*x**2 + d*x**3
                else:
                    return 0.
            else:
                return 0.
        return compute

    def logarithmic(a, b, max_valuation_radius):
        def compute(x, v):
            if v==1:
                if x < 1000:
                    return a + b*math.log(1000) - (b/1000)*(1000-x)
                elif x <= max_valuation_radius:
                    return a + b*math.log(x)
                else:
                    return 0.
            else:
                return 0.
        return compute

    # Multiply a value by a constant
    def multiply(c):
        def compute(x):
            return x*c
        return compute


    # Setup valuation function
    a = args["a_coefficient"]
    b = args["b_coefficient"]
    c = args["c_coefficient"]
    d = args["d_coefficient"]

    valuation_function = None
    max_valuation_radius = args['max_valuation_radius']
    if "polynomial" in args["valuation_function"]:
        print("Polynomial")
        valuation_function = polynomial(a, b, c, d, max_valuation_radius)
    elif "logarithmic" in args['valuation_function']:
        print("logarithmic")
        valuation_function = logarithmic(a, b, max_valuation_radius)

    assert valuation_function is not None
    
    # Make sure the values don't become too small at max_valuation_radius:
    edge_value = valuation_function(max_valuation_radius, 1)
    message = "Valuation function can't be negative if evaluated at " + \
    str(max_valuation_radius) + " meters (value is " + str(edge_value) + ")"
    assert edge_value >= 0., message
        
    # Base path uri
    base_uri = os.path.split(visibility_uri)[0]

    # Temporary files that will be used 
    distance_uri = raster_utils.temporary_filename()
    viewshed_uri = raster_utils.temporary_filename()

    # The model extracts each viewpoint from the shapefile
    point_list = []
    shapefile = ogr.Open(in_structure_uri)
    assert shapefile is not None
    layer = shapefile.GetLayer(0)
    assert layer is not None
    iGT = gdal.InvGeoTransform(GT)[1]
    feature_count = layer.GetFeatureCount()
    viewshed_uri_list = []
    print('Number of viewpoints: ' + str(feature_count))
    for f in range(feature_count):
        print("feature " + str(f))
        feature = layer.GetFeature(f)
        field_count = feature.GetFieldCount()
        # Check for feature information (radius, coeff, height)
        for field in range(field_count):
            field_def = feature.GetFieldDefnRef(field)
            field_name = field_def.GetNameRef()
            if (field_name.upper() == 'RADIUS2') or \
                (field_name.upper() == 'RADIUS'):
                field_type = field_def.GetType()
                message = 'Wrong field type for radius: ' + str(field_type) + \
                ' expected 0 (ogr.OFTInteger)'
                assert field_type == ogr.OFTInteger, message
                max_dist = abs(feature.GetFieldAsInteger(field))
                assert max_dist is not None, "max distance can't be None"
                max_dist = int(max_dist/cell_size)
            if field_name.lower() == 'coeff':
                field_type = field_def.GetType()
                message = 'Wrong field type for coeff: ' + str(field_type) + \
                ' expected 2 (ogr.OFTReal)'
                assert field_type == ogr.OFTReal, message
                coefficient = feature.GetFieldAsDouble(field)    
                assert coefficient is not None, "feature coeff can't be None"
            if field_name.lower() == 'height':
                field_type = field_def.GetType()
                message = 'Wrong field type for height: ' + str(field_type) + \
                ' expected 2 (ogr.OFTReal)'
                assert field_type == ogr.OFTReal, message
                height = feature.GetFieldAsDouble(field)
                assert height is not None, "height can't be None"
                
        geometry = feature.GetGeometryRef()
        assert geometry is not None
        message = 'geometry type is ' + str(geometry.GetGeometryName()) + \
        ' point is "POINT"'
        assert geometry.GetGeometryName() == 'POINT', message
        x = geometry.GetX()
        y = geometry.GetY()
        j = int((iGT[0] + x*iGT[1] + y*iGT[2]))
        i = int((iGT[3] + x*iGT[4] + y*iGT[5]))
        #print('Computing viewshed from viewpoint ' + str(i) + ' ' + str(j), \
        #'distance radius is ' + str(max_dist) + " pixels.")

        array_shape = (rows, cols)
    
        tmp_visibility_uri = raster_utils.temporary_filename() #os.path.join(base_uri, 'visibility_' + str(f) + '.tif')
        raster_utils.new_raster_from_base_uri(visibility_uri, \
        tmp_visibility_uri, 'GTiff', \
        255, gdal.GDT_Byte, fill_value = 255)
        scenic_quality_core.viewshed(input_array, cell_size, \
        array_shape, nodata, tmp_visibility_uri, (i,j), obs_elev, tgt_elev, \
        max_dist, refr_coeff)
        # Compute the distance
        tmp_distance_uri = raster_utils.temporary_filename() #os.path.join(base_uri, 'distance_' + str(f) + '.tif')
        raster_utils.new_raster_from_base_uri(visibility_uri, \
        tmp_distance_uri, 'GTiff', \
        255, gdal.GDT_Byte, fill_value = 255)
        distance_fn = compute_distance(i,j, cell_size)
        raster_utils.vectorize_datasets([I_uri, J_uri, tmp_visibility_uri], \
        distance_fn, tmp_distance_uri, gdal.GDT_Float64, -1., cell_size, "union")
        # Apply the valuation function
        tmp_viewshed_uri = raster_utils.temporary_filename() #os.path.join(base_uri, 'viewshed_' + str(f) + '.tif')

        raster_utils.vectorize_datasets(
            [tmp_distance_uri, tmp_visibility_uri],
            valuation_function, tmp_viewshed_uri, gdal.GDT_Float64, -9999.0, cell_size, 
            "union")


        # Multiply the viewshed by its coefficient
        scaled_viewshed_uri = raster_utils.temporary_filename() #os.path.join(base_uri, 'vshed_' + str(f) + '.tif') #raster_utils.temporary_filename()
        apply_coefficient = multiply(coefficient)
        raster_utils.vectorize_datasets([tmp_viewshed_uri], apply_coefficient, \
        scaled_viewshed_uri, gdal.GDT_Float64, 0., cell_size, "union")
        viewshed_uri_list.append(scaled_viewshed_uri)
    # Accumulate result to combined raster
    ## The vectorize_dataset method segfaults--trying with numpy instead.
    #def accumulate(*x):
    #    #print('type of x', type(x), type(x[0]), x)
    #    x = np.array(x)
    #    #result = np.sum(x)
    #    #print('result', result)
    #    #return raster_utils.gdal_cast(result, gdal.GDT_Float64)
    #    return 0.
    ##raster_utils.vectorize_datasets(viewshed_uri_list, lambda *x: 0., \
    ##visibility_uri, gdal.GDT_Float64, 0., cell_size, "union")
    # Numpy method:
    #Create the output raster from the first in the input list
    raster_utils.new_raster_from_base_uri(viewshed_uri_list[0], \
    visibility_uri, 'GTiff', 0., gdal.GDT_Float64)
    # Open the first raster and sum up the values using numpy
    raster = gdal.Open(viewshed_uri_list[0])
    accum_array = raster.GetRasterBand(1).ReadAsArray()
    for uri in viewshed_uri_list[1:]:
        nodata = raster_utils.get_nodata_from_uri(uri)
        raster = gdal.Open(uri)
        array = raster.GetRasterBand(1).ReadAsArray()
        accum_array += array
    # Store the accumulated value in the output uri
    raster = gdal.Open(visibility_uri, gdal.GA_Update)
    band = raster.GetRasterBand(1)
    band.WriteArray(accum_array)

def add_field_feature_set_uri(fs_uri, field_name, field_type):
    shapefile = ogr.Open(fs_uri, 1)
    layer = shapefile.GetLayer()
    new_field = ogr.FieldDefn(field_name, field_type)
    layer.CreateField(new_field)
    shapefile = None    

def add_id_feature_set_uri(fs_uri, id_name):
    shapefile = ogr.Open(fs_uri, 1)
    message = "Failed to open " + fs_uri + ": can't add new field."
    assert shapefile is not None, message
    layer = shapefile.GetLayer()
    new_field = ogr.FieldDefn(id_name, ogr.OFTInteger)
    layer.CreateField(new_field)

    for feature_id in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_id)
        feature.SetField(id_name, feature_id)
        layer.SetFeature(feature)
    shapefile = None

def set_field_by_op_feature_set_uri(fs_uri, value_field_name, op):
    shapefile = ogr.Open(fs_uri, 1)
    layer = shapefile.GetLayer()

    for feature_id in xrange(layer.GetFeatureCount()):
        feature = layer.GetFeature(feature_id)
        feature.SetField(value_field_name, op(feature))
        layer.SetFeature(feature)
    shapefile = None

def get_count_feature_set_uri(fs_uri):
    shapefile = ogr.Open(fs_uri)
    layer = shapefile.GetLayer()
    count = layer.GetFeatureCount()
    shapefile = None

    return count
    
def execute(args):
    """DOCSTRING"""
    LOGGER.info("Start Scenic Quality Model")

    #create copy of args
    aq_args=args.copy()

    #validate input
    LOGGER.debug("Validating parameters.")
    dem_cell_size=raster_utils.get_cell_size_from_uri(args['dem_uri'])
    LOGGER.debug("DEM cell size: %f" % dem_cell_size)
    if "cell_size" in aq_args:
        if aq_args['cell_size'] < dem_cell_size:
            raise ValueError, "The cell size cannot be downsampled below %f" % dem_cell_size
    else:
        aq_args['cell_size'] = dem_cell_size

    intermediate_dir = os.path.join(aq_args['workspace_dir'], 'intermediate')
    if not os.path.isdir(intermediate_dir):
        os.makedirs(intermediate_dir)

    output_dir = os.path.join(aq_args['workspace_dir'], 'output')
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    #local variables
    LOGGER.debug("Setting local variables.")
    z_factor=1
    curvature_correction=aq_args['refraction']

    #intermediate files
    aoi_dem_uri=os.path.join(intermediate_dir,"aoi_dem.shp")
    aoi_pop_uri=os.path.join(intermediate_dir,"aoi_pop.shp")

    viewshed_dem_uri=os.path.join(intermediate_dir,"dem_vs.tif")
    viewshed_dem_reclass_uri=os.path.join(intermediate_dir,"dem_vs_re.tif")

    pop_clip_uri=os.path.join(intermediate_dir,"pop_clip.tif")
    pop_prj_uri=os.path.join(intermediate_dir,"pop_prj.tif")
    pop_vs_uri=os.path.join(intermediate_dir,"pop_vs.tif")

    viewshed_reclass_uri=os.path.join(intermediate_dir,"vshed_bool.tif")
    viewshed_polygon_uri=os.path.join(intermediate_dir,"vshed.shp")

    #outputs
    viewshed_uri=os.path.join(output_dir,"vshed.tif")
    viewshed_quality_uri=os.path.join(output_dir,"vshed_qual.tif")    
    pop_stats_uri=os.path.join(output_dir,"populationStats.html")
    overlap_uri=os.path.join(output_dir,"vp_overlap.shp")

    #determining best data type for viewshed
    features = get_count_feature_set_uri(aq_args['structure_uri'])
    if features < 2 ** 16:
        viewshed_type = gdal.GDT_UInt16
        viewshed_nodata = (2 ** 16) - 1
    elif features < 2 ** 32:
        viewshed_type = gdal.GDT_UInt32
        viewshed_nodata = (2 ** 32) - 1
    else:
        raise ValueError, "Too many structures."
    
    #clip DEM by AOI and reclass
    LOGGER.info("Clipping DEM by AOI.")

    LOGGER.debug("Projecting AOI for DEM.")
    dem_wkt = raster_utils.get_dataset_projection_wkt_uri(aq_args['dem_uri'])
    raster_utils.reproject_datasource_uri(aq_args['aoi_uri'], dem_wkt, aoi_dem_uri)

    LOGGER.debug("Clipping DEM by projected AOI.")
    raster_utils.clip_dataset_uri(aq_args['dem_uri'], aoi_dem_uri, viewshed_dem_uri, False)

    LOGGER.info("Reclassifying DEM to account for water at sea-level and resampling to specified cell size.")
    LOGGER.debug("Reclassifying DEM so negative values zero and resampling to save on computation.")

    nodata_dem = raster_utils.get_nodata_from_uri(aq_args['dem_uri'])

    def no_zeros(value):
        if value == nodata_dem:
            return nodata_dem
        elif value < 0:
            return 0
        else:
            return value

    raster_utils.vectorize_datasets([viewshed_dem_uri],
                                    no_zeros,
                                    viewshed_dem_reclass_uri,
                                    get_data_type_uri(viewshed_dem_uri),
                                    nodata_dem,
                                    aq_args["cell_size"],
                                    "union")

    #calculate viewshed
    LOGGER.info("Calculating viewshed.")
    compute_viewshed_uri(viewshed_dem_reclass_uri,
             viewshed_uri,
             aq_args['structure_uri'],
             curvature_correction,
             aq_args['refraction'],
             aq_args)

    LOGGER.info("Ranking viewshed.")
    #rank viewshed
    quantile_list = [25,50,75,100]
    print('Trying to open', viewshed_uri)
    reclassify_quantile_dataset_uri(viewshed_uri,
                                    quantile_list,
                                    viewshed_quality_uri,
                                    viewshed_type,
                                    viewshed_nodata)

    if "pop_uri" in args:
        #tabulate population impact
        LOGGER.info("Tabulating population impact.")
        LOGGER.debug("Tabulating unaffected population.")
        nodata_pop = raster_utils.get_nodata_from_uri(aq_args["pop_uri"])
        LOGGER.debug("The no data value for the population raster is %s.", str(nodata_pop))
        nodata_viewshed = raster_utils.get_nodata_from_uri(viewshed_uri)
        LOGGER.debug("The no data value for the viewshed raster is %s.", str(nodata_viewshed))

        #clip population
        LOGGER.debug("Projecting AOI for population raster clip.")
        pop_wkt = raster_utils.get_dataset_projection_wkt_uri(aq_args['pop_uri'])
        raster_utils.reproject_datasource_uri(aq_args['aoi_uri'],
                                              pop_wkt,
                                              aoi_pop_uri)

        LOGGER.debug("Clipping population raster by projected AOI.")
        raster_utils.clip_dataset_uri(aq_args['pop_uri'],
                                      aoi_pop_uri,
                                      pop_clip_uri,
                                      False)
        
        #reproject clipped population
        LOGGER.debug("Reprojecting clipped population raster.")
        vs_wkt = raster_utils.get_dataset_projection_wkt_uri(viewshed_uri)
        reproject_dataset_uri(pop_clip_uri,
                                           vs_wkt,
                                           pop_prj_uri,
                                           get_data_type_uri(pop_clip_uri))

        #align and resample population
        def copy(value1, value2):
            if value2 == nodata_viewshed:
                return nodata_pop
            else:
                return value1
        
        LOGGER.debug("Resampling and aligning population raster.")
        raster_utils.vectorize_datasets([pop_prj_uri, viewshed_uri],
                                       copy,
                                       pop_vs_uri,
                                       get_data_type_uri(pop_prj_uri),
                                       nodata_pop,
                                       aq_args["cell_size"],
                                       "intersection",
                                       ["bilinear", "bilinear"],
                                       1)
        
        pop = gdal.Open(pop_vs_uri)
        #LOGGER.debug(pop)
        pop_band = pop.GetRasterBand(1)
        #LOGGER.debug(pop_band)
        vs = gdal.Open(viewshed_uri)
        vs_band = vs.GetRasterBand(1)

        affected_pop = 0
        unaffected_pop = 0
        for row_index in range(vs_band.YSize):
            pop_row = pop_band.ReadAsArray(0, row_index, pop_band.XSize, 1)
            vs_row = vs_band.ReadAsArray(0, row_index, vs_band.XSize, 1).astype(np.float64)

            pop_row[pop_row == nodata_pop]=0.0
            vs_row[vs_row == nodata_viewshed]=-1

            affected_pop += np.sum(pop_row[vs_row > 0])
            unaffected_pop += np.sum(pop_row[vs_row == 0])

        pop_band = None
        pop = None
        vs_band = None
        vs = None

        table="""
        <html>
        <title>Marine InVEST</title>
        <center><H1>Scenic Quality Model</H1><H2>(Visual Impact from Objects)</H2></center>
        <br><br><HR><br>
        <H2>Population Statistics</H2>

        <table border="1", cellpadding="0">
        <tr><td align="center"><b>Number of Features Visible</b></td><td align="center"><b>Population (estimate)</b></td></tr>
        <tr><td align="center">None visible<br> (unaffected)</td><td align="center">%i</td>
        <tr><td align="center">1 or more<br>visible</td><td align="center">%i</td>
        </table>
        </html>
        """

        outfile = open(pop_stats_uri, 'w')
        outfile.write(table % (unaffected_pop, affected_pop))
        outfile.close()

    #perform overlap analysis
    LOGGER.info("Performing overlap analysis.")

    LOGGER.debug("Reclassifying viewshed")

    nodata_vs_bool = 0
    def non_zeros(value):
        if value == nodata_vs_bool:
            return nodata_vs_bool
        elif value > 0:
            return 1
        else:
            return nodata_vs_bool

    raster_utils.vectorize_datasets([viewshed_uri],
                                    non_zeros,
                                    viewshed_reclass_uri,
                                    gdal.GDT_Byte,
                                    nodata_vs_bool,
                                    aq_args["cell_size"],
                                    "union")

    if "overlap_uri" in aq_args:  
        LOGGER.debug("Copying overlap analysis features.")
        raster_utils.copy_datasource_uri(aq_args["overlap_uri"], overlap_uri)

        LOGGER.debug("Adding id field to overlap features.")
        id_name = "investID"
        add_id_feature_set_uri(overlap_uri, id_name)

        LOGGER.debug("Add area field to overlap features.")
        area_name = "overlap"
        add_field_feature_set_uri(overlap_uri, area_name, ogr.OFTReal)
        
        LOGGER.debug("Count overlapping pixels per area.")
        values = raster_utils.aggregate_raster_values_uri(
            viewshed_reclass_uri, overlap_uri, id_name, ignore_nodata=True).total

        def calculate_percent(feature):
            if feature.GetFieldAsInteger(id_name) in values:
                return (values[feature.GetFieldAsInteger(id_name)] * \
                aq_args["cell_size"]) / feature.GetGeometryRef().GetArea()
            else:
                return 0
            
        LOGGER.debug("Set area field values.")
        set_field_by_op_feature_set_uri(overlap_uri, area_name, calculate_percent)