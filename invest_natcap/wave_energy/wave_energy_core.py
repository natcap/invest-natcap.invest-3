"""InVEST Wave Energy Model Core Code"""
import math
import os
import re
import logging

import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_Update
import osgeo.osr as osr
from osgeo import ogr
from scipy.interpolate import LinearNDInterpolator as ip
from scipy import stats

from invest_natcap.dbfpy import dbf
import invest_cython_core
from invest_natcap.invest_core import invest_core

logger = logging.getLogger('wave_energy_core')

def biophysical(args):
    """Runs the biophysical part of the Wave Energy Model (WEM). 
    Generates a wave power raster, wave energy capacity raster, 
    and a wave data shapefile that hosts various attributes for
    wave farm locations, such as depth, wave height, and wave period.
    args - A python dictionary that has as least the following required 
           inputs:
    Required:
    args['workspace_dir'] - the workspace path where Output/Intermediate
                            files will be written
    args['wave_base_data'] - a dictionary of seastate bin data.
    args['analysis_area'] - a point geometry shapefile representing the 
                            relevant WW3 points
    args['analysis_area_extract'] - a polygon geometry shapefile encompassing 
                                    the broader range of interest.
    args['machine_perf'] - a 2D array representing the machine performance table.
    args['machine_param'] - a dictionary which holds the machine parameter values.
    args['dem'] - a GIS raster file of the global elevation model
    
    Optional (but required for valuation):
    args['aoi'] - a polygon geometry shapefile outlining a more 
                  specific area of interest.

    returns - Nothing
    """
    #Set variables for output paths
    #Workspace Directory path
    workspace_dir = args['workspace_dir']
    #Intermediate Directory path to store information
    intermediate_dir = workspace_dir + os.sep + 'Intermediate'
    #Output Directory path to store output rasters
    output_dir = workspace_dir + os.sep + 'Output'
    #Path for clipped wave point shapefile holding wave attribute information
    prj_shape_path = intermediate_dir + os.sep + 'WEM_InputOutput_Pts.shp'
    #Temporary shapefile needed for an intermediate step
    wave_shape_path = intermediate_dir + os.sep + 'WaveData_clipZ.shp'
    #Paths for wave energy and wave power raster
    wave_energy_path = output_dir + os.sep + 'capwe_mwh.tif'
    wave_power_path = output_dir + os.sep + 'wp_kw.tif'
    global_dem = args['dem']
    #Set nodata value and datatype for new rasters
    nodata = 0
    datatype = gdal.GDT_Float32
    #Since the global dem is the finest resolution we get as an input,
    #use its pixel sizes as the sizes for the new rasters
    dem_gt = global_dem.GetGeoTransform()
    #Set the source projection for a coordinate transformation
    #to the input projection from the point shapefile
    source_sr = args['analysis_area'].GetLayer(0).GetSpatialRef()
    #Determine which shapefile will be used to determine area of interest
    if 'aoi' in args:
        #The polygon shapefile that specifies the area of interest
        cutter = args['aoi']
        #Set the wave data shapefile to the same projection as the area of interest
        analysis_shape = change_shape_projection(args['analysis_area'],
                                                 args['aoi'].GetLayer(0).GetSpatialRef(),
                                                 wave_shape_path)
        #Clip the wave data shape by the bounds provided from the area of interest
        area_shape = clip_shape(analysis_shape, cutter, prj_shape_path)
        #Get the coordinates of a point from the wave data shapefile
        area_layer = area_shape.GetLayer(0)
        analysis_feat = area_layer.GetNextFeature()
        analysis_geom = analysis_feat.GetGeometryRef()
        analysis_lat = analysis_geom.GetX()
        analysis_long = analysis_geom.GetY()
        #Create a coordinate transformation from lat/long to area of interest's projection
        target_sr = cutter.GetLayer(0).GetSpatialRef()
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
        #Convert the point from meters to lat/long
        analysis_point = coord_trans_opposite.TransformPoint(analysis_lat, analysis_long)
        #Get the size of the pixels in meters, to be used for creating rasters
        pixel_size_tuple = invest_cython_core.pixel_size_in_meters(global_dem, coord_trans,
                                                                   analysis_point)
        pixel_xsize = pixel_size_tuple[0]
        pixel_ysize = pixel_size_tuple[1]
        logger.debug('X pixel size in meters : %f', pixel_xsize)
        logger.debug('Y pixel size in meters : %f', pixel_ysize)
        #Reset the layer to point at the first feature and clean up
        #variables
        area_layer.ResetReading()
        analysis_layer = None
        analysis_feat.Destroy()
        analysis_geom = None
    else:
        #The polygon shapefile that specifies the area of interest
        cutter = args['analysis_area_extract']
        #Not sure if this is needed, as cutter is already an outline of analysis_area
        area_shape = clip_shape(args['analysis_area'], cutter, prj_shape_path)
        area_layer = area_shape.GetLayer(0)
        #Set the pixel size to that of DEM, to be used for creating rasters
        pixel_xsize = float(dem_gt[1])
        pixel_ysize = np.absolute(float(dem_gt[5]))
        #Create a coordinate transformation, because it is expected below
        target_sr = cutter.GetLayer(0).GetSpatialRef()
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
    #We do all wave power calculations by manipulating the fields in
    #the wave data shapefile, thus we need to add proper depth values
    #from the raster DEM
    logger.debug('Adding a depth field to the shapefile from the DEM raster')
    dem_band = global_dem.GetRasterBand(1)
    dem_matrix = dem_band.ReadAsArray()
    #Create a new field for the depth attribute
    field_defn = ogr.FieldDefn('Depth_M', ogr.OFTReal)
    area_layer.CreateField(field_defn)
    feature = area_layer.GetNextFeature()
    #For all the features (points) add the proper depth value from the DEM
    while feature is not None:
        depth_index = feature.GetFieldIndex('Depth_M')    
        geom = feature.GetGeometryRef()
        lat = geom.GetX()
        longitude = geom.GetY()
        #Transform two points into meters
        point_decimal_degree = coord_trans_opposite.TransformPoint(lat, longitude)
        #To get proper depth value we must index into the dem matrix
        #by getting where the point is located in terms of the matrix
        i = int((point_decimal_degree[0] - dem_gt[0]) / dem_gt[1])
        j = int((point_decimal_degree[1] - dem_gt[3]) / dem_gt[5])
        depth = dem_matrix[j][i]        
        feature.SetField(depth_index, depth)        
        area_layer.SetFeature(feature)
        feature.Destroy()
        feature = area_layer.GetNextFeature()
    logger.debug('Finished adding depth field to shapefile from DEM raster')
    #Generate an interpolate object for wave_energy_capacity
    logger.debug('Interpolating machine performance table')
    energy_interp = wave_energy_interp(args['wave_base_data'], args['machine_perf'])
    #Create a dictionary with the wave energy capacity sums from each location
    logger.debug('Summing the wave energy capacity at each wave farm and saving to dictionary')
    logger.info('Calculating Captured Wave Energy.')
    energy_cap = compute_wave_energy_capacity(args['wave_base_data'],
                                              energy_interp, args['machine_param'])
    #Add the sum as a field to the shapefile for the corresponding points
    logger.debug('Adding the wave energy sums to the WaveData shapefile')
    captured_wave_energy_to_shape(energy_cap, area_shape)
    #Calculate wave power for each wave point and add it as a field to the shapefile
    logger.debug('Calculating wave power for each farm site and saving as field to shapefile')
    logger.info('Calculating Wave Power.')
    area_shape = wave_power(area_shape)
    #Create blank rasters bounded by the shape file of analyis area
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                              datatype, nodata, wave_energy_path, cutter)
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                              datatype, nodata, wave_power_path, cutter)
    #Open created rasters
    wave_power_raster = gdal.Open(wave_power_path, GA_Update)
    wave_energy_raster = gdal.Open(wave_energy_path, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    logger.debug('Getting the points and corresponding values of wave power and captured wave energy')
    energy_sum_array = get_points_values(area_shape, 'capWE_Sum')
    wave_power_array = get_points_values(area_shape, 'wp_Kw')
    #Interpolate wave energy and wave power from the shapefile over the rasters
    logger.debug('Interpolate wave power and wave energy capacity onto rasters')
    logger.info('Generating Wave Power and Captured Wave Energy rasters.')
    interp_points_over_raster(energy_sum_array[0], energy_sum_array[1], wave_energy_raster)
    interp_points_over_raster(wave_power_array[0], wave_power_array[1], wave_power_raster)
    #Clip the wave energy and wave power rasters so that they are confined to the AOI
    wave_power_raster = clip_raster_from_polygon(cutter, wave_power_raster, wave_power_path)
    wave_energy_raster = clip_raster_from_polygon(cutter, wave_energy_raster, wave_energy_path)
   
    wave_energy_raster.FlushCache()    
    wave_power_raster.FlushCache()
    wp_rc_path = workspace_dir + os.sep + 'Output/wp_rc.tif'
    capwe_rc_path = workspace_dir + os.sep + 'Output/capwe_rc.tif'

    capwe_rc = create_percentile_rasters(wave_energy_raster, capwe_rc_path, 
                                         ' (MWh/yr)', ' megawatt hours per year (MWh/yr)')
    wp_rc = create_percentile_rasters(wave_power_raster, wp_rc_path,
                                      ' (kW/m)', ' wave power per unit width of wave crest length (kW/m)')

    #Clean up Shapefiles and Rasters
    area_shape.Destroy()
    cutter.Destroy()
    wave_energy_raster = None
    wave_power_raster = None
    wp_rc_raster = None
    capwe_rc = None
    #Clean up temporary files on disk
    pattern = wave_shape_path[wave_shape_path.rfind(os.sep) + 1:
                              len(wave_shape_path) - 4] + ".*"
    logging.debug('Regex file pattern : %s', pattern)
    for f in os.listdir(intermediate_dir):
        if re.search(pattern, f):
            os.remove(os.path.join(intermediate_dir, f))

def create_percentile_rasters(raster_dataset, output_path, units_short, units_long):
    if os.path.isfile(output_path):
        os.remove(output_path)
    percentile_raster = invest_cython_core.newRasterFromBase(raster_dataset, output_path, 
                                                        'GTiff', 0, gdal.GDT_Int32)
    percentile_band = percentile_raster.GetRasterBand(1)
    dataset_band = raster_dataset.GetRasterBand(1)
    #Generate Percentiles
    percentiles = []
    counter = [0,0,0,0,0]
    def raster_percentile(band):
        if band > percentiles[3]:
            counter[4] = counter[4]+1
            return 5
        elif band > percentiles[2]:
            counter[3] = counter[3]+1
            return 4
        elif band > percentiles[1]:
            counter[2] = counter[2]+1
            return 3
        elif band > percentiles[0]:
            counter[1] = counter[1]+1
            return 2
        elif band > 0:
            counter[0] = counter[0]+1
            return 1
        else:
            return 0
    
    matrix = np.array(dataset_band.ReadAsArray())    
    dataset_array = matrix.flatten()
    dataset_mask = np.ma.masked_array(dataset_array, mask=dataset_array == 0)
    dataset_comp = np.ma.compressed(dataset_mask)
    percentiles = get_percentiles(dataset_comp)
    logger.debug('wp_percentiles : %s', percentiles)
    invest_core.vectorize1ArgOp(dataset_band, raster_percentile, percentile_band)
    logging.debug('counter : %s', counter)

    attribute_values = create_percentile_ranges(percentiles, units_short, units_long)
    create_attribute_table(output_path, attribute_values, counter)
    
    return percentile_raster

def get_percentiles(value_list):
    pct_list = []
    pct_list.append(int(stats.scoreatpercentile(value_list, 25)))
    pct_list.append(int(stats.scoreatpercentile(value_list, 50)))
    pct_list.append(int(stats.scoreatpercentile(value_list, 75)))
    pct_list.append(int(stats.scoreatpercentile(value_list, 90)))
    return pct_list
    
def create_percentile_ranges(percentiles, units_short, units_long):
    range_one = '1 - ' + str(percentiles[0]) + units_long
    range_two = str(percentiles[0]) + ' - ' + str(percentiles[1]) + units_short
    range_three = str(percentiles[1]) + ' - ' + str(percentiles[2]) + units_short
    range_four = str(percentiles[2]) + ' - ' + str(percentiles[3]) + units_short
    range_five = 'Greater than ' + str(percentiles[3]) + units_short
    attribute_values = [range_one, range_two, range_three, range_four, range_five]
    return attribute_values

def create_attribute_table(raster_uri, attribute_values, counter):
    output_path = raster_uri + '.vat.dbf'
    #Create a new dbf file with the same name as the GTiff plus a .vat.dbf
    if os.path.isfile(output_path):
        os.remove(output_path)
    dataset_attribute_table = dbf.Dbf(output_path, new=True)
    dataset_attribute_table.addField(
                 #integer field
                 ("VALUE", "N", 9),
                 #integer field
                 ("COUNT", "N", 9),
                 #character field, I think header names need to be short?
                 ("VAL_RANGE", "C", 254))
    #Add all the records
    for id_value in range(len(attribute_values)):
        logging.debug('id_value: %s', id_value)
        rec = dataset_attribute_table.newRecord()
        rec["VALUE"] = id_value+1
        rec["COUNT"] = int(counter[id_value])
        rec["VAL_RANGE"] = attribute_values[id_value]

        rec.store()
    dataset_attribute_table.close()
    
def wave_power(shape):
    """Calculates the wave power from the fields in the shapefile
    and writes the wave power value to a field for the corresponding
    feature. 
    
    shape - A Shapefile that has all the attributes represented in fields
            to calculate wave power at a specific wave farm
    
    returns - The shape that was just edited with the new wave power field
              and corresponding value    
    """
    #Sea water density constant (kg/m^3)
    swd = 1028
    #Gravitational acceleration (m/s^2)
    grav = 9.8
    #Constant determining the shape of a wave spectrum (see users guide pg 23)
    alfa = 0.86
    #Add a waver power field to the shapefile.
    layer = shape.GetLayer(0)
    field_defn = ogr.FieldDefn('wp_Kw', ogr.OFTReal)
    layer.CreateField(field_defn)
    layer.ResetReading()
    feat = layer.GetNextFeature()
    #For ever feature (point) calculate the wave power and add the value
    #to itself in a new field
    while feat is not None:
        height_index = feat.GetFieldIndex('HSAVG_M')
        period_index = feat.GetFieldIndex('TPAVG_S')
        depth_index = feat.GetFieldIndex('Depth_M')
        wp_index = feat.GetFieldIndex('wp_Kw')
        height = feat.GetFieldAsDouble(height_index)
        period = feat.GetFieldAsDouble(period_index)
        depth = feat.GetFieldAsInteger(depth_index)

        depth = np.absolute(depth)
        #wave frequency calculation (used to calculate wave number k)
        tem = (2.0 * math.pi) / (period * alfa)
        #wave number calculation (expressed as a function of 
        #wave frequency and water depth)
        k = np.square(tem) / (grav * np.sqrt(np.tanh((np.square(tem)) * (depth / grav))))
        #wave group velocity calculation (expressed as a 
        #function of wave energy period and water depth)
        wave_group_velocity = ((1 + ((2 * k * depth) / np.sinh(2 * k * depth))) 
                               * np.sqrt((grav / k) * np.tanh(k * depth))) / 2
        #wave power calculation
        wave_pow = (((swd * grav) / 16) * (np.square(height)) * wave_group_velocity) / 1000
        
        feat.SetField(wp_index, wave_pow)
        layer.SetFeature(feat)
        feat.Destroy()
        feat = layer.GetNextFeature()
    
    return shape
    
def clip_raster_from_polygon(shape, raster, path):
    """Returns a raster where any value outside the bounds of the
    polygon shape are set to nodata values. This represents clipping 
    the raster to the dimensions of the polygon.
    
    shape - A polygon shapefile representing the bounds for the raster
    raster - A raster to be bounded by shape
    path - The path for the clipped output raster
    
    returns - The clipped raster    
    """
    #Create a new raster as a copy from 'raster'
    copy_raster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    copy_band = copy_raster.GetRasterBand(1)
    #Set the copied rasters values to nodata to create a blank raster.
    nodata = copy_band.GetNoDataValue()
    copy_band.Fill(nodata)
    #Rasterize the polygon layer onto the copied raster
    gdal.RasterizeLayer(copy_raster, [1], shape.GetLayer(0))
    def fill_bound_data(value, copy_value):
        """If the copied raster's value is nodata then the pixel is not within
        the polygon and should write nodata back. If copied raster's value
        is not nodata, then pixel lies within polygon and the value from 'raster'
        should be written out.
        
        value - The pixel value of the raster to be bounded by the shape
        copy_value - The pixel value of a copied raster where every pixel
                     is nodata except for where the polygon was rasterized
        
        returns - Either a nodata value or relevant pixel value
        """
        if copy_value == nodata:
            return copy_value
        else:
            return value
    #Vectorize the two rasters using the operation fill_bound_data
    invest_core.vectorize2ArgOp(raster.GetRasterBand(1), copy_band,
                                fill_bound_data, copy_band)
    return copy_raster
    
def clip_shape(shape_to_clip, binding_shape, output_path):
    """Copies a polygon or point geometry shapefile, only keeping the features
    that intersect or are within a binding polygon shape.
    
    shape_to_clip - A point or polygon shapefile to clip
    binding_shape - A polygon shapefile indicating the bounds for the
                    shape_to_clip features
    output_path  - The path for the clipped output shapefile
    
    returns - A shapefile representing the clipped version of shape_to_clip
    """
    shape_source = output_path
    #If the output_path is already a file, remove it
    if os.path.isfile(shape_source):
        os.remove(shape_source)
    #Get the layer of points from the current point geometry shape
    in_layer = shape_to_clip.GetLayer(0)
    #Get the layer definition which holds needed attribute values
    in_defn = in_layer.GetLayerDefn()
    #Get the layer of the polygon (binding) geometry shape
    clip_layer = binding_shape.GetLayer(0)
    #Create a new shapefile with similar properties of the 
    #current point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(),
                                   in_layer.GetSpatialRef(), in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd_def = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd_def.SetWidth(src_fd.GetWidth())
        fd_def.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd_def)
    #Retrieve the binding polygon feature and get it's geometry reference
    clip_feat = clip_layer.GetNextFeature()
    while clip_feat is not None:
        clip_geom = clip_feat.GetGeometryRef()
        #Get the spatial reference of the geometry to use in transforming
        source_sr = clip_geom.GetSpatialReference()
        #Retrieve the current point shapes feature and get it's geometry reference
        in_layer.ResetReading()
        in_feat = in_layer.GetNextFeature()
        geom = in_feat.GetGeometryRef()
        #Get the spatial reference of the geometry to use in transforming
        target_sr = geom.GetSpatialReference()
        #Create a coordinate transformation
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        #Transform the polygon geometry into the same format as the 
        #point shape geometry
        clip_geom.Transform(coord_trans)
        #For all the features in the current point shape (for all the points)
        #Check to see if they Intersect with the binding polygons geometry and
        #if they do, then add all of the fields and values from that 
        #point to the new shape
        while in_feat is not None:
            geom = in_feat.GetGeometryRef()
            #Intersection returns a new geometry if they intersect
            geom = geom.Intersection(clip_geom)
            if(geom.GetGeometryCount() + geom.GetPointCount()) != 0:
                #Create a new feature from the input feature and set its geometry
                out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
                out_feat.SetFrom(in_feat)
                out_feat.SetGeometryDirectly(geom)
                #For all the fields in the feature set the field values from the source field
                for fld_index2 in range(out_feat.GetFieldCount()):
                    src_field = in_feat.GetField(fld_index2)
                    out_feat.SetField(fld_index2, src_field)

                shp_layer.CreateFeature(out_feat)
                out_feat.Destroy()

            in_feat.Destroy()
            in_feat = in_layer.GetNextFeature()
        clip_feat.Destroy()
        clip_feat = clip_layer.GetNextFeature()

    return shp_ds

def get_points_values(shape, field):
    """Generates a list of points and a list of values based on a point
    geometry shapefile
    
    shape - A point geometry shapefile of which to gather the information from
    field - A string representing a field in the shapefile 'shape' 
    
    returns - A list of points and values (points represented as 2D list, 
              values as list)
     """
    #Retrieve the layer from the shapefile and reset the reader head
    #incase it has been iterated through earlier.
    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    #Get the first point from the shape layer
    shape_feat = shape_layer.GetNextFeature()
    points = []
    values = []
    while shape_feat is not None:
        #May want to check to make sure field is in shape layer
        #Get the specified field and append its value
        #to a list
        field_index = shape_feat.GetFieldIndex(field)
        value = shape_feat.GetField(field_index)
        values.append(value)
        #Get the X,Y coordinate of the geometry of
        #the point and append it as a list [X,Y] to
        #the list 'points'
        geom = shape_feat.GetGeometryRef()
        longitude = geom.GetX()
        latitude = geom.GetY()
        points.append([longitude, latitude])
        geom = None
        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()

    results = [points, values]
    return results

def interp_points_over_raster(points, values, raster):
    """Interpolates a given set of points and values over new points
    provided by the raster and writes the interpolated matrix to the raster band.
    
    points - A 2D array of points, where the points are represented as [x,y]
    values - A list of values corresponding to the points of 'points'
    raster - A raster to write the interpolated values too and to get the
             new dimensions from
    
    returns - Nothing
    """
    #Set the points and values to numpy arrays
    points = np.array(points)
    values = np.array(values)
    #Get the dimensions from the raster as well as the GeoTransform information
    geo_tran = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    size_x = band.XSize
    logger.debug('Size of X dimension of raster : %s', size_x)
    size_y = band.YSize
    logger.debug('Size of Y dimension of raster : %s', size_y)
    logger.debug('gt[0], [1], [3], [5] : %f : %f : %f : %f',
                 geo_tran[0], geo_tran[1], geo_tran[3], geo_tran[5])
    #Make a numpy array representing the points of the raster (the points are the pixels)
    new_points = np.array([[geo_tran[0] + geo_tran[1] * i,
                            geo_tran[3] + geo_tran[5] * j] 
                           for i in np.arange(size_x) for j in np.arange(size_y)])
    logger.debug('New points from raster : %s', new_points)
    #Interpolate the points and values from the shapefile from earlier
    spl = ip(points, values, fill_value=0)
    #Run the interpolator object over the new set of points from the raster. 
    #Will return a list of values.
    spl = spl(new_points)
    #Reshape the list of values to the dimensions of the raster for writing.
    #Transpose the matrix provided from 'reshape' because gdal thinks of x,y opposite of humans
    spl = spl.reshape(size_x, size_y).transpose()
    #Write interpolated matrix of values to raster
    band.WriteArray(spl, 0, 0)

def wave_energy_interp(wave_data, machine_perf):
    """Generates a matrix representing the interpolation of the
    machine performance table using new ranges from wave watch data.
    
    wave_data - A dictionary holding the new x range and y range values
    machine_perf - A 2D array representation of the machine performance
                   table that also includes the ranges
    
    returns - The interpolated matrix
    """
    #Get ranges and matrix for machine performance table
    x_range = np.array(machine_perf.pop(0), dtype='f')
    y_range = np.array(machine_perf.pop(0), dtype='f')
    z_matrix = np.array(machine_perf, dtype='f')
    #Get new ranges to interpolate to, from wave_data table
    new_x = wave_data[0]
    new_y = wave_data[1]
    #Interpolate machine performance table and return the interpolated matrix
    interp_z = invest_cython_core.interpolateMatrix(x_range, y_range, z_matrix, new_x, new_y)
    return interp_z

def compute_wave_energy_capacity(wave_data, interp_z, machine_param):
    """Computes the wave energy capacity for each point and
    generates a dictionary whos keys are the points (I,J) and whos value
    is the wave energy capacity.
    
    wave_data - A dictionary containing wave watch data
    interp_z - A 2D array of the interpolated values for the machine
                performance table
    machine_param - A dictionary containing the restrictions for the machines
                    (CapMax, TpMax, HsMax)
                    
    returns - A dictionary representing the wave energy capacity at each wave point
    """
    #It seems that the capacity max is already set to it's limit in
    #the machine performance table. However, if it needed to be
    #restricted the following line could be used:
    #interp_z = np.where(interp_z>cap_max, cap_max, interp_z)
    
    energy_cap = {}
    #Get the row,col headers (ranges) for the wave watch data
    wave_row = wave_data.pop(0)
    wave_column = wave_data.pop(1)
    #Get the machine parameter restriction values
    cap_max = float(machine_param['capmax'])
    period_max = float(machine_param['tpmax'])
    height_max = float(machine_param['hsmax'])
    #Set position variables to use as a check and as an end
    #point for rows/cols if restrictions limit the ranges
    period_max_pos = -1
    height_max_pos = -1
    #Using the restrictions find the max position (index) for period and height
    #in the wave_row/wave_column ranges
    for index_pos, value in enumerate(wave_row):
        if (value > period_max):
            period_max_pos = index_pos
            break
    for index_pos, value in enumerate(wave_column):
        if (value > height_max):
            height_max_pos = index_pos
            break
    logger.debug('Position of max period : %f', period_max_pos)
    logger.debug('Position of max height : %f', height_max_pos)
    #For all the wave watch points, multiply the occurence matrix by the interpolated
    #machine performance matrix to get the captured wave energy
    for key, val in wave_data.iteritems():
        #Convert all values to type float
        temp_array = np.array(val, dtype='f')
        mult_array = np.multiply(temp_array, interp_z)
        #Set any value that is outside the restricting ranges provided by 
        #machine parameters to zero
        if period_max_pos != -1:
            mult_array[:, period_max_pos:] = 0
        if height_max_pos != -1:
            mult_array[height_max_pos:, :] = 0
        #Divide the matrix by 5 to get the yearly values
        valid_array = np.divide(mult_array, 5.0)
        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero. So here
        #we drive any negative values to zero.
        valid_array = np.where(valid_array < 0, 0, valid_array)
        #Sum all of the values from the matrix to get the total captured wave energy
        #and convert into mega watts
        sum_we = (valid_array.sum() / 1000)
        energy_cap[key] = sum_we

    return energy_cap

def captured_wave_energy_to_shape(energy_cap, wave_shape):
    """Adds each captured wave energy value from the dictionary
    energy_cap to a field of the shapefile wave_shape. The values are
    set corresponding to the same I,J values which is the key of the
    dictionary and used as the unique identier of the shape.
    
    energy_cap - A dictionary with keys (I,J), representing the wave energy capacity
                values.
    wave_shape  - A point geometry shapefile to write the new field/values to
    
    returns - Nothing    
    """
    wave_layer = wave_shape.GetLayer(0)
    #Incase the layer has already been read through earlier in the program
    #reset it to start from the beginning
    wave_layer.ResetReading()
    #Create a new field for the shapefile
    field_def = ogr.FieldDefn('capWE_Sum', ogr.OFTReal)
    wave_layer.CreateField(field_def)
    #For all of the features (points) in the shapefile, get the 
    #corresponding point/value from the dictionary and set the 'capWE_Sum'
    #field as the value from the dictionary
    for feat in wave_layer:
        index_i = feat.GetFieldIndex('I')
        index_j = feat.GetFieldIndex('J')
        value_i = feat.GetField(index_i)
        value_j = feat.GetField(index_j)
        we_value = energy_cap[(value_i, value_j)]
        
        index = feat.GetFieldIndex('capWE_Sum')
        feat.SetField(index, we_value)
        #Save the feature modifications to the layer.
        wave_layer.SetFeature(feat)
        feat.Destroy()

def valuation(args):
    """Executes the valuation calculations for the Wave Energy Model.
    The Net Present Value (npv) is calculated for each wave farm site
    and then a raster is created based off of the interpolation of these
    points. This function requires the following arguments:
    
    args - A python dictionary that has at least the following arguments:
    args['workspace_dir'] - A path to where the Output and Intermediate folders
                            will be placed or currently are.
    args['wave_data_shape'] - A file path to the shapefile generated from the biophysical run
                              which holds various attributes of each wave farm.
    args['number_machines'] - An integer representing the number of machines to make up a farm.
    args['machine_econ'] - A dictionary holding the machine economic parameters.
    args['land_gridPts'] - A dictionary holidng the landing point and grid point
                           information and location.
    args['global_dem'] - A raster of the global DEM

    returns - Nothing
    """
    #Set variables for common output paths
    #Workspace Directory path
    workspace_dir = args['workspace_dir']
    #Intermediate Directory path to store information
    inter_dir = workspace_dir + os.sep + 'Intermediate'
    #Output Directory path to store output rasters
    output_dir = workspace_dir + os.sep + 'Output'
    #Output path for landing point shapefile
    land_pt_path = output_dir + os.sep + 'LandPts_prj.shp'
    #Output path for grid point shapefile
    grid_pt_path = output_dir + os.sep + 'GridPts_prj.shp'
    #Output path for the projected net present value raster
    raster_projected_path = output_dir + os.sep + 'npv_usd.tif'
    
    wave_data_shape = args['wave_data_shape']
    #Since the global_dem is the only input raster, we base the pixel
    #size of our output raster from the global_dem
    dem = args['global_dem']
    #Create a coordinate transformation for lat/long to meters
    srs_prj = osr.SpatialReference()
    #Using 'WGS84' as our well known lat/long projection
    srs_prj.SetWellKnownGeogCS("WGS84")
    source_sr = srs_prj
    target_sr = wave_data_shape.GetLayer(0).GetSpatialRef()
    coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
    coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
    #Get a point from the wave data shapefile
    wave_data_layer = wave_data_shape.GetLayer(0)
    wave_data_feat = wave_data_layer.GetNextFeature()
    wave_data_geom = wave_data_feat.GetGeometryRef()
    wave_data_lat = wave_data_geom.GetX()
    wave_data_long = wave_data_geom.GetY()
    wave_data_point = coord_trans_opposite.TransformPoint(wave_data_lat, wave_data_long)
    #Get the size of the pixels in meters
    pixel_size_tuple = invest_cython_core.pixel_size_in_meters(dem, coord_trans, wave_data_point)
    pixel_xsize = pixel_size_tuple[0]
    pixel_ysize = pixel_size_tuple[1]
    logger.debug('X pixel size of DEM : %f', pixel_xsize)
    logger.debug('Y pixel size of DEM : %f', pixel_ysize)
    #Reset variables to be used later
    wave_data_layer.ResetReading()
    wave_data_feat.Destroy()
    wave_data_geom = None
    #Number of machines for a given wave farm
    units = args['number_machines']
    #Extract the machine economic parameters
    machine_econ = args['machine_econ']
    cap_max = float(machine_econ['capmax'])
    capital_cost = float(machine_econ['cc'])
    cml = float(machine_econ['cml'])
    cul = float(machine_econ['cul'])
    col = float(machine_econ['col'])
    omc = float(machine_econ['omc'])
    price = float(machine_econ['p'])
    drate = float(machine_econ['r'])
    smlpm = float(machine_econ['smlpm'])
    #The NPV is for a 25 year period
    year = 25.0
    #A numpy array of length 25, representing the npv of a farm for each year
    time = np.linspace(0.0, year - 1.0, year)
    #The discount rate calculation for the npv equations
    rho = 1.0 / (1.0 + drate)
    #Extract the landing and grid points data
    land_grid_pts = args['land_gridPts']
    grid_pts = {}
    land_pts = {}
    for key, value in land_grid_pts.iteritems():
        grid_pts[key] = [value['GRID'][0], value['GRID'][1]]
        land_pts[key] = [value['LAND'][0], value['LAND'][1]]
    #If either shapefile, landing or grid exist, remove them
    if os.path.isfile(land_pt_path):
        os.remove(land_pt_path)
    if os.path.isfile(grid_pt_path):
        os.remove(grid_pt_path)
    #Make a point shapefile for landing points.
    logger.info('Creating Landing Points Shapefile.')
    landing_shape = build_point_shapefile('ESRI Shapefile', 'landpoints',
                                          land_pt_path, land_pts, target_sr, coord_trans)
    #Make a point shapefile for grid points
    logger.info('Creating Grid Points Shapefile.')
    grid_shape = build_point_shapefile('ESRI Shapefile', 'gridpoints',
                                       grid_pt_path, grid_pts, target_sr, coord_trans)
    #Get the coordinates of points of wave_data_shape, landing_shape,
    #and grid_shape
    we_points = get_points_geometries(wave_data_shape)
    landing_points = get_points_geometries(landing_shape)
    grid_point = get_points_geometries(grid_shape)
    logger.info('Calculating Distances.')
    #Calculate the distances between the relative point groups
    wave_to_land_dist, wave_to_land_id = calculate_distance(we_points, landing_points)
    land_to_grid_dist, land_to_grid_id = calculate_distance(landing_points, grid_point)
    #Add three new fields to the shapefile that will store the distances
    for field in ['W2L_MDIST', 'LAND_ID', 'L2G_MDIST']:
        field_defn = ogr.FieldDefn(field, ogr.OFTReal)
        wave_data_layer.CreateField(field_defn)
    #For each feature in the shapefile add the corresponding distances
    #from wave_to_land_dist and land_to_grid_dist that was calculated above
    iterate_feat = 0
    wave_data_layer.ResetReading()
    feature = wave_data_layer.GetNextFeature()
    while feature is not None:
        wave_to_land_index = feature.GetFieldIndex('W2L_MDIST')
        land_to_grid_index = feature.GetFieldIndex('L2G_MDIST')
        id_index = feature.GetFieldIndex('LAND_ID')    
        
        land_id = int(wave_to_land_id[iterate_feat])
        
        feature.SetField(wave_to_land_index, wave_to_land_dist[iterate_feat])
        feature.SetField(land_to_grid_index, land_to_grid_dist[land_id])
        feature.SetField(id_index, land_id)
        
        iterate_feat = iterate_feat + 1
        
        wave_data_layer.SetFeature(feature)
        feature.Destroy()
        feature = wave_data_layer.GetNextFeature()
    
    def npv_wave(annual_revenue, annual_cost):
        """Calculates the NPV for a wave farm site based on the
        annual revenue and annual cost
        
        annual_revenue - A numpy array of the annual revenue for the first 25 years
        annual_cost - A numpy array of the annual cost for the first 25 years
        
        returns - The Total NPV which is the sum of all 25 years
        """
        npv = []
        for i in range(len(time)):
            npv.append(rho ** i * (annual_revenue[i] - annual_cost[i]))
        return sum(npv)
    #Add Net Present Value field to shapefile
    field_defn_npv = ogr.FieldDefn('NPV_25Y', ogr.OFTReal)
    wave_data_layer.CreateField(field_defn_npv)
    wave_data_layer.ResetReading()
    feat_npv = wave_data_layer.GetNextFeature()
    #For all the wave farm sites, calculate npv and write to shapefile
    logger.info('Calculating the Net Present Value.')
    while feat_npv is not None:
        depth_index = feat_npv.GetFieldIndex('Depth_M')
        wave_to_land_index = feat_npv.GetFieldIndex('W2L_MDIST')
        land_to_grid_index = feat_npv.GetFieldIndex('L2G_MDIST')
        captured_wave_energy_index = feat_npv.GetFieldIndex('CapWE_Sum')
        npv_index = feat_npv.GetFieldIndex('NPV_25Y')
        
        depth = feat_npv.GetFieldAsDouble(depth_index)
        wave_to_land = feat_npv.GetFieldAsDouble(wave_to_land_index)
        land_to_grid = feat_npv.GetFieldAsDouble(land_to_grid_index)
        captured_wave_energy = feat_npv.GetFieldAsDouble(captured_wave_energy_index)
        #Create a numpy array of length 25, filled with the captured wave energy
        #in kW/h. Represents the lifetime of this wave farm.
        captured_we = np.ones(len(time)) * int(captured_wave_energy) * 1000.0
        #It is expected that there is no revenue from the first year
        captured_we[0] = 0
        #Compute values to determine NPV
        lenml = 3.0 * np.absolute(depth)
        install_cost = units * cap_max * capital_cost
        mooring_cost = smlpm * lenml * cml * units
        trans_cost = (wave_to_land * cul / 1000.0) + (land_to_grid * col / 1000.0)
        initial_cost = install_cost + mooring_cost + trans_cost
        annual_revenue = price * units * captured_we
        annual_cost = omc * captured_we * units
        #The first year's costs are the initial start up costs
        annual_cost[0] = initial_cost
        
        npv_result = npv_wave(annual_revenue, annual_cost) / 1000.0
        feat_npv.SetField(npv_index, npv_result)
        
        wave_data_layer.SetFeature(feat_npv)
        feat_npv.Destroy()
        feat_npv = wave_data_layer.GetNextFeature()

    datatype = gdal.GDT_Float32
    nodata = 0
    #Create a blank raster from the extents of the wave farm shapefile
    logger.debug('Creating Raster From Vector Extents')
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                                     datatype, nodata, raster_projected_path, wave_data_shape)
    logger.debug('Completed Creating Raster From Vector Extents')
    wave_farm_value_raster = gdal.Open(raster_projected_path, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    wave_farm_value_array = get_points_values(wave_data_shape, 'NPV_25Y')
    #Interpolate the NPV values based on the dimensions and 
    #corresponding points of the raster, then write the interpolated 
    #values to the raster
    logger.info('Generating Net Present Value Raster.')
    interp_points_over_raster(wave_farm_value_array[0],
                              wave_farm_value_array[1], wave_farm_value_raster)
    logger.debug('Done interpolating NPV over raster.')
    wave_farm_value_raster = None
    wave_data_shape.Destroy()
    logger.debug('End of wave_energy_core.valuation')
    
def build_point_shapefile(driver_name, layer_name, path, data, prj, coord_trans):
    """This function creates and saves a point geometry shapefile to disk.
    It specifically only creates one 'Id' field and creates as many features
    as specified in 'data'
    
    driver_name - A string specifying a valid ogr driver type
    layer_name - A string representing the name of the layer
    path - A string of the output path of the file
    data - A dictionary who's keys are the Id's for the field
           and who's values are arrays with two elements being
           latitude and longitude
    prj - A spatial reference acting as the projection/datum
    coord_trans - A coordinate transformation
    
    returns - The created shapefile
    """
    #Make a point shapefile for landing points.
    driver = ogr.GetDriverByName(driver_name)
    data_source = driver.CreateDataSource(path)
    layer = data_source.CreateLayer(layer_name, prj, ogr.wkbPoint)    
    field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer.CreateField(field_defn)
    #For all of the landing points create a point feature on the layer
    for key, value in data.iteritems():
        lat = value[0]
        long = value[1]
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(float(long), float(lat))
        geom.Transform(coord_trans)
        #Create the feature, setting the id field to the corresponding id
        #field from the csv file
        feat = ogr.Feature(layer.GetLayerDefn())
        layer.CreateFeature(feat)
        index = feat.GetFieldIndex('Id')
        feat.SetField(index, key)
        feat.SetGeometryDirectly(geom)
        #Save the feature modifications to the layer.
        layer.SetFeature(feat)
        feat.Destroy()
    layer.ResetReading()
    return data_source

def get_points_geometries(shape):
    """This function takes a shapefile and for each feature retrieves
    the X and Y value from it's geometry. The X and Y value are stored in
    a numpy array as a point [x_location,y_location], which is returned when all the features
    have been iterated through.
    
    shape - A shapefile
    
    returns - A numpy array of points, which represent the shape's feature's
              geometries.
    """
    point = []
    layer = shape.GetLayer(0)
    layer.ResetReading()
    feat = layer.GetNextFeature()
    while feat is not None:
        x_location = float(feat.GetGeometryRef().GetX())
        y_location = float(feat.GetGeometryRef().GetY())
        point.append([x_location, y_location])
        feat.Destroy()
        feat = layer.GetNextFeature()
    
    return np.array(point)
    
def calculate_distance(xy_1, xy_2):
    """For all points in xy_1, this function calculates the distance
    from point xy_1 to various points in xy_2,
    and stores the shortest distances found in a list min_dist.
    The function also stores the index from which ever point in xy_2
    was closest, as an id in a list that corresponds to min_dist.
    
    xy_1 - A numpy array of points in the form [x,y]
    xy_2 - A numpy array of points in the form [x,y]
    
    returns - A numpy array of shortest distances and a numpy array
              of id's corresponding to the array of shortest distances  
    """
    #Create two numpy array of zeros with length set to as many points in xy_1
    min_dist = np.zeros(len(xy_1))
    min_id = np.zeros(len(xy_1))
    #For all points xy_point in xy_1 calcuate the distance from xy_point to xy_2
    #and save the shortest distance found.
    for index, xy_point in enumerate(xy_1):
        dists = np.sqrt(np.sum((xy_point - xy_2) ** 2, axis=1))
        min_dist[index], min_id[index] = dists.min(), dists.argmin()
    return min_dist, min_id

def change_shape_projection(shape_to_reproject, srs_prj, output_path):
    """Changes the projection of a shapefile by creating a new shapefile based on
    the projection passed in.  The new shapefile then copies all the features and fields of
    the shapefile to reproject as its own. The reprojected shapefile is written to 'outputpath'
    and is returned.
    
    shape_to_reproject - A shapefile to be copied and reprojected.
    srs_prj - The desired projection as a SpatialReference from a WKT string.
    output_path - The path to where the new shapefile should be written to disk.
    
    returns - The reprojected shapefile.
    """
    shape_source = output_path
    #If this file already exists, then remove it
    if os.path.isfile(shape_source):
        os.remove(shape_source)
    #Get the layer of points from the current point geometry shape
    in_layer = shape_to_reproject.GetLayer(0)
    #Get the layer definition which holds needed attribute values
    in_defn = in_layer.GetLayerDefn()
    #Create a new shapefile with similar properties of the current point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    #Create the new layer for the shapefile using same name and geometry type from
    #shape_to_reproject, but different projection
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), srs_prj, in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd_def = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd_def.SetWidth(src_fd.GetWidth())
        fd_def.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd_def)
    
    in_layer.ResetReading()
    in_feat = in_layer.GetNextFeature()
    #Copy all of the features in shape_to_reproject to the new shapefile
    while in_feat is not None:
        geom = in_feat.GetGeometryRef()
        #Get the spatial reference of the source geometry to use in transforming
        source_sr = geom.GetSpatialReference()
        #Get the spatial reference of the target geometry to use in transforming
        target_sr = srs_prj
        #Create a coordinate transformation
        coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
        #Transform the geometry into a format desired for the new projection
        geom.Transform(coord_trans)
        #Copy shape_to_reproject's feature and set as new shapes feature
        out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
        out_feat.SetFrom(in_feat)
        out_feat.SetGeometry(geom)
        #For all the fields in the feature set the field values from the source field
        for fld_index2 in range(out_feat.GetFieldCount()):
            src_field = in_feat.GetField(fld_index2)
            out_feat.SetField(fld_index2, src_field)

        shp_layer.CreateFeature(out_feat)
        out_feat.Destroy()

        in_feat.Destroy()
        in_feat = in_layer.GetNextFeature()

    return shp_ds
