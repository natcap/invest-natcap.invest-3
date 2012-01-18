import math
import sys
import os
import logging

import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_Update
import osgeo.osr as osr
from osgeo import ogr
from scipy.interpolate import LinearNDInterpolator as ip

import invest_cython_core
from invest_natcap.invest_core import invest_core

logger = logging.getLogger('wave_energy_core')

def biophysical(args):
    """Runs the biophysical part of the Wave Energy Model (WEM). 
    Generates a wave power raster, wave energy capacity raster, 
    and a wave data shapefile that hosts various attributes for
    wave farm locations, such as depth, wave height, and wave period.
    Required:
    args['workspace_dir'] - the workspace path
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
                  specific area of interest (Optional).

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
    wave_shape_path = intermediate_dir + os.sep + 'WaveData_clipZ.shp'
    #Path for 'new' AOI, see comment below 'if AOI in args'
    wave_aoi_path = intermediate_dir + os.sep + 'waveAOIShape.shp'
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
    pixel_xsize = float(dem_gt[1])
    pixel_ysize = np.absolute(float(dem_gt[5]))
    #Determine which shapefile will be used to determine area of interest
    if 'aoi' in args:
        #The AOI shapefile has a different projection than lat/long so by calling
        #the clip_shape function with analysis_area_extract (which has lat/long projection
        #which we would expect) and AOI, I am making a new AOI with the proper projection
        cutter = clip_shape(args['analysis_area_extract'], args['aoi'], wave_aoi_path)        
    else:
        cutter = args['analysis_area_extract']
    #Create a new shapefile that is a copy of analysis_area but bounded by AOI
    area_shape = clip_shape(args['analysis_area'], cutter, wave_shape_path)
    area_layer = area_shape.GetLayer(0)
    #We do all wave power calculations by manipulating the fields in
    #the wave data shapefile, thus we need to add proper depth values
    #from the raster DEM
    dem_band = global_dem.GetRasterBand(1)
    xsize = dem_band.XSize
    ysize = dem_band.YSize
    dem_matrix = dem_band.ReadAsArray()
    #Create a new field for the depth attribute
    field_defn = ogr.FieldDefn('Depth_M', ogr.OFTReal)
    area_layer.CreateField(field_defn)
    #ResetReading to make sure we start reading from the first feature
    area_layer.ResetReading()
    feature = area_layer.GetNextFeature()
    #For all the features (points) add the proper depth value from the DEM
    while feature is not None:
        depth_index = feature.GetFieldIndex('Depth_M')    
        geom = feature.GetGeometryRef()
        lat = geom.GetX()
        long = geom.GetY()
        #To get proper depth value we must index into the dem matrix
        #by getting where the point is located in terms of the matrix
        i = int((lat - dem_gt[0]) / dem_gt[1])
        j = int((long - dem_gt[3]) / dem_gt[5])
        depth = dem_matrix[j][i]        
        feature.SetField(depth_index, depth)        
        area_layer.SetFeature(feature)
        feature.Destroy()
        feature = area_layer.GetNextFeature()
    #We close and open the same shapefile to make sure all data is officially written to disk
    #Not sure if this is absolutely necessary, should test to make sure we aren't doing extra work.
    area_shape.Destroy()
    area_shape = ogr.Open(wave_shape_path, 1)
    area_layer = area_shape.GetLayer(0)
    #Generate an interpolate object for waveEnergyCap
    energy_interp = wave_energy_interp(args['wave_base_data'], args['machine_perf'])
    #Create a dictionary with the wave energy capacity sums from each location
    energy_cap = compute_wave_energy_capacity(args['wave_base_data'], energy_interp, args['machine_param'])
    #Add the sum as a field to the shapefile for the corresponding points
    captured_wave_energy_to_shape(energy_cap, area_shape)
    #Calculate wave power for each wave point and add it as a field to the shapefile
    area_shape = wave_power(area_shape)
    #Create blank rasters bounded by the shape file of analyis area
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                              datatype, nodata, wave_energy_path, area_shape)
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                              datatype, nodata, wave_power_path, area_shape)
    #Open created rasters
    wave_power_raster = gdal.Open(wave_power_path, GA_Update)
    wave_energy_raster = gdal.Open(wave_energy_path, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    energy_sum_array = get_points_values(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'capWE_Sum'], 'capWE_Sum')
    wave_power_array = get_points_values(area_shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'wp_Kw'], 'wp_Kw')
    #Interpolate wave energy and wave power from the shapefile over the rasters
    interp_points_over_raster(energy_sum_array[0], energy_sum_array[1], wave_energy_raster)
    interp_points_over_raster(wave_power_array[0], wave_power_array[1], wave_power_raster)
    #Clip the wave energy and wave power rasters so that they are confined to the AOI
    wave_power_raster = clip_raster_from_polygon(cutter, wave_power_raster, wave_power_path)
    wave_energy_raster = clip_raster_from_polygon(cutter, wave_energy_raster, wave_energy_path)
    #Clean up Shapefiles and Rasters
    area_shape.Destroy()
    cutter.Destroy()
    wave_energy_raster = None
    wave_power_raster = None
    
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
    p = 1028
    #Gravitational acceleration (m/s^2)
    g = 9.8
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
        k = np.square(tem) / (g * np.sqrt(np.tanh((np.square(tem)) * (depth / g))))
        #wave group velocity calculation (expressed as a 
        #function of wave energy period and water depth)
        wave_group_velocity = ((1 + ((2 * k * depth) / np.sinh(2 * k * depth))) * np.sqrt((g / k) * np.tanh(k * depth))) / 2
        #wave power calculation
        wp = (((p * g) / 16) * (np.square(height)) * wave_group_velocity) / 1000
        
        feat.SetField(wp_index, wp)
        
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
    #Get the pixel size from the raster to clip.
    gt = raster.GetGeoTransform()
    pixel_x = gt[1]
    pixel_y = gt[5]
    #Create a new raster as a copy from 'raster'
    copy_raster = gdal.GetDriverByName('GTIFF').CreateCopy(path, raster)
    copy_band = copy_raster.GetRasterBand(1)
    #Set the copied rasters values to nodata to create a blank raster.
    nodata = copy_band.GetNoDataValue()
    copy_band.Fill(nodata)
    #Rasterize the polygon layer onto the copied raster
    gdal.RasterizeLayer(copy_raster, [1], shape.GetLayer(0))
    #If the copied raster's value is nodata then the pixel is not within
    #the polygon and should write nodata back. If copied raster's value
    #is not nodata, then pixel lies within polygon and the value from 'raster'
    #should be written out.
    def fill_bound_data(value, copy_value):
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
        fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd.SetWidth(src_fd.GetWidth())
        fd.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd)
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

def get_points_values(shape, key, value_array, value):
    """Generates a list of points and a list of values based on a point
    geometry shapefile
    
    shape - A point geometry shapefile of which to gather the information from
    key   - A list of fields from shapefile shape whose values will be the points
    value_array - A list of fields, where the list contains the fields used in
                  key and value
    value - A string representing the field from shapefile shape that is
            to be returned
    
    returns - A list of points and values (points represented as 2D list, values as list)
     """
    #Retrieve the layer from the shapefile and reset the reader head
    #incase it has been iterated through earlier.
    shape_layer = shape.GetLayer(0)
    shape_layer.ResetReading()
    #Get the first point from the shape layer
    shape_feat = shape_layer.GetNextFeature()
    field_dict = {}
    #For all the points in the layer add the desired 
    #'key' and 'value' to the dictionary.
    while shape_feat is not None:
        #This dictionary is used to store the needed values 
        #of the desired fields from 'value_array'
        value_dict = {}
        #May want to check to make sure field is in shape layer
        #For the relevant field in the list value_array, 
        #add the fields value to the dictionary
        for field in value_array:
            field_index = shape_feat.GetFieldIndex(field)
            value_dict[field] = shape_feat.GetField(field_index)
        key_list = []
        #Create a tuple from the elements of the provided key list
        for k in key:
            key_list.append(value_dict[k])
        tupled_key = tuple(key_list)
        #Set the created tuple as the key of this dictionary 
        #and set its value to desired element from value_dict
        field_dict[tupled_key] = value_dict[value]

        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()
    
    points = []
    values = []
    #Construct two arrays, one a list of all the points from field_dict, and the other a list
    #of all the values corresponding the points from field_dict
    for id, val in field_dict.iteritems():
        points.append(list(id))
        values.append(val)

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
    gt = raster.GetGeoTransform()
    band = raster.GetRasterBand(1)
    size_x = band.XSize
    size_y = band.YSize
    #Make a numpy array representing the points of the raster (the points are the pixels)
    new_points = np.array([[gt[0] + gt[1] * i, gt[3] + gt[5] * j] for i in np.arange(size_x) for j in np.arange(size_y)])
    #Interpolate the points and values from the shapefile from earlier
    spl = ip(points, values, fill_value=0)
    #Run the interpolator object over the new set of points from the raster. Will return a list of values.
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
    cap_max = float(machine_param['CapMax']['VALUE'])
    period_max = float(machine_param['TpMax']['VALUE'])
    height_max = float(machine_param['HsMax']['VALUE'])
    #Set position variables to use as a check and as an end
    #point for rows/cols if restrictions limit the ranges
    period_max_pos = -1
    height_max_pos = -1
    #Using the restrictions find the max position (index) for period and height
    #in the wave_row/wave_column ranges
    for i, v in enumerate(wave_row):
        if (v > period_max) and (period_max_pos == -1):
            period_max_pos = i
    for i, v in enumerate(wave_column):
        if (v > height_max) and (height_max_pos == -1):
            height_max_pos = i
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
        sum = (valid_array.sum() / 1000)
        energy_cap[key] = sum

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
    wave_Layer = wave_shape.GetLayer(0)
    #Incase the layer has already been read through earlier in the program
    #reset it to start from the beginning
    wave_Layer.ResetReading()
    #Create a new field for the shapefile
    field_def = ogr.FieldDefn('capWE_Sum', ogr.OFTReal)
    wave_Layer.CreateField(field_def)
    #For all of the features (points) in the shapefile, get the 
    #corresponding point/value from the dictionary and set the 'capWE_Sum'
    #field as the value from the dictionary
    for feat in wave_Layer:
        index_i = feat.GetFieldIndex('I')
        index_j = feat.GetFieldIndex('J')
        value_i = feat.GetField(index_i)
        value_j = feat.GetField(index_j)
        we_value = energy_cap[(value_i, value_j)]
        
        index = feat.GetFieldIndex('capWE_Sum')
        feat.SetField(index, we_value)
        #Save the feature modifications to the layer.
        wave_Layer.SetFeature(feat)
        feat.Destroy()

def valuation(args):
    """Executes the valuation calculations for the Wave Energy Model.
    The Net Present Value (npv) is calculated for each wave farm site
    and then a raster is created based off of the interpolation of these
    points. This function requires the following arguments:
    
    args['workspace_dir'] - A path to where the Output and Intermediate folders
                            will be placed or currently are.
    args['wave_data_shape'] - A file path to the shapefile generated from the biophysical run
                              which holds various attributes of each wave farm.
    args['number_machines'] - An integer representing the number of machines to make up a farm.
    args['machine_econ'] - A dictionary holding the machine economic parameters.
    args['land_gridPts'] - A dictionary holidng the landing point and grid point
                           information and location.
    args['projection'] - A file path to the projection that allows to calculate
                         distances in Meters.
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
    #Output path for projected wave point shapefile holding values of interest
    projected_shape_path = inter_dir + os.sep + 'WaveData_prj.shp'
    #Output path for landing point shapefile
    land_pt_path = output_dir + os.sep + 'LandPts_prj.shp'
    #Output path for grid point shapefile
    grid_pt_path = output_dir + os.sep + 'GridPt_prj.shp'
    #Output path for net present value raster
    wave_farm_value_path = inter_dir + os.sep + 'wave_energy_npv.tif'
    #Output path for the projected net present value raster
    raster_projected_path = output_dir + os.sep + 'npv_usd.tif'
    
    wave_data_shape = args['wave_data_shape']
    prj_file_path = args['projection']
    #Since the global_dem is the only input raster, we base the pixel
    #size of our output raster from the global_dem
    dem = args['global_dem']
    gt = dem.GetGeoTransform()
    pixel_xsize = float(gt[1])
    pixel_ysize = np.absolute(float(gt[5]))
    #If either shapefile, landing or grid exist, remove them
    if os.path.isfile(land_pt_path):
        os.remove(land_pt_path)
    if os.path.isfile(grid_pt_path):
        os.remove(grid_pt_path)
    #Number of machines for a given wave farm
    units = args['number_machines']
    #Extract the machine economic parameters
    machine_econ = args['machine_econ']
    cap_max = float(machine_econ['CapMax']['VALUE'])
    capital_cost = float(machine_econ['cc']['VALUE'])
    cml = float(machine_econ['cml']['VALUE'])
    cul = float(machine_econ['cul']['VALUE'])
    col = float(machine_econ['col']['VALUE'])
    omc = float(machine_econ['omc']['VALUE'])
    price = float(machine_econ['p']['VALUE'])
    drate = float(machine_econ['r']['VALUE'])
    smlpm = float(machine_econ['smlpm']['VALUE'])
    #The NPV is for a 25 year period
    year = 25.0
    #A numpy array of length 25, representing the npv of a farm for each year
    time = np.linspace(0.0, year - 1.0, year)
    #The discount rate calculation for the npv equations
    rho = 1.0 / (1.0 + drate)
    #Extract the landing and grid points data
    land_grid_pts = args['land_gridPts']
    grid_pt = {}
    land_pts = {}
    for key, value in land_grid_pts.iteritems():
        if value['TYPE'] == 'GRID':
            grid_pt = value
        else:
            land_pts[key] = value            
    #Create a coordinate transformation for lat/long to meters
    prj_file = open(prj_file_path)
    prj = prj_file.read()
    srs_prj = osr.SpatialReference()
    srs_prj.ImportFromWkt(prj)
    source_sr = wave_data_shape.GetLayer(0).GetSpatialRef()
    target_sr = srs_prj
    coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
    coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
    #Make a point shapefile for landing points.
    drv_landing = ogr.GetDriverByName('ESRI Shapefile')
    ds_landing = drv_landing.CreateDataSource(land_pt_path)
    layer_landing = ds_landing.CreateLayer('landpoints', srs_prj, ogr.wkbPoint)    
    field_defn_landing = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer_landing.CreateField(field_defn_landing)
    #For all of the landing points create a point feature on the layer
    for key, value in land_pts.iteritems():
        landing_lat = value['LAT']
        landing_long = value['LONG']
        landing_geom = ogr.Geometry(ogr.wkbPoint)
        landing_geom.AddPoint_2D(float(landing_long), float(landing_lat))
        landing_geom.Transform(coord_trans)
        #Create the feature, setting the id field to the corresponding id
        #field from the csv file
        feat_landing = ogr.Feature(layer_landing.GetLayerDefn())
        layer_landing.CreateFeature(feat_landing)
        index = feat_landing.GetFieldIndex('Id')
        feat_landing.SetField(index, value['ID'])
        feat_landing.SetGeometryDirectly(landing_geom)
        #Save the feature modifications to the layer.
        layer_landing.SetFeature(feat_landing)
        feat_landing.Destroy()
    layer_landing = None
    drv_landing = None
    ds_landing.Destroy()
    #Create geometry for grid point location:
    grid_lat = grid_pt['LAT']
    grid_long = grid_pt['LONG']
    grid_geom = ogr.Geometry(ogr.wkbPoint)
    grid_geom.AddPoint_2D(float(grid_long), float(grid_lat))    
    grid_geom.Transform(coord_trans)
    #Make a point shapefile for grid points
    drv_grid = ogr.GetDriverByName('ESRI Shapefile')
    ds_grid = drv_grid.CreateDataSource(grid_pt_path)
    layer_grid = ds_grid.CreateLayer('gridpoint', srs_prj, ogr.wkbPoint)
    field_defn_grid = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer_grid.CreateField(field_defn_grid)
    #Create the feature, setting the id field to the corresponding id
    #field from the csv file
    feat_grid = ogr.Feature(layer_grid.GetLayerDefn())
    layer_grid.CreateFeature(feat_grid)
    index = feat_grid.GetFieldIndex('Id')
    feat_grid.SetField(index, grid_pt['ID'])    
    feat_grid.SetGeometryDirectly(grid_geom)
    #Save the feature modifications to the layer.
    layer_grid.SetFeature(feat_grid)
    feat_grid.Destroy()
    #Close the necessary files and objects
    prj_file.close()
    layer_grid = None
    drv_grid = None
    ds_grid.Destroy()
    #Reproject the shapefile so that it's geometry is in meters
    wave_data_layer = wave_data_shape.GetLayer(0)
    shape = change_shape_projection(wave_data_shape, prj_file_path, projected_shape_path)
    shape.Destroy()
    shape = ogr.Open(projected_shape_path, 1)
    shape_layer = shape.GetLayer(0)
    
    landing_shape = ogr.Open(land_pt_path)
    grid_shape = ogr.Open(grid_pt_path)
    
    we_points = get_points_geometries(shape)
    landing_points = get_points_geometries(landing_shape)
    grid_point = get_points_geometries(grid_shape)
    
    W2L_Dist, W2L_ID = calculate_distance(we_points, landing_points)
    L2G_Dist, L2G_ID = calculate_distance(landing_points, grid_point)
    #Add three new fields to the shapefile that will store the distances
    for field in ['W2L_MDIST', 'LAND_ID', 'L2G_MDIST']:
        field_defn = ogr.FieldDefn(field, ogr.OFTReal)
        shape_layer.CreateField(field_defn)
    #For each feature in the shapefile add the corresponding distances
    #from W2L_Dist and L2G_Dist that was calculated above
    j = 0
    shape_layer.ResetReading()
    feature = shape_layer.GetNextFeature()
    while feature is not None:
        W2L_index = feature.GetFieldIndex('W2L_MDIST')
        L2G_index = feature.GetFieldIndex('L2G_MDIST')
        ID_index = feature.GetFieldIndex('LAND_ID')    
        
        land_id = int(W2L_ID[j])
        
        feature.SetField(W2L_index, W2L_Dist[j])
        feature.SetField(L2G_index, L2G_Dist[land_id])
        feature.SetField(ID_index, land_id)
        
        j = j + 1
        
        shape_layer.SetFeature(feature)
        feature.Destroy()
        feature = shape_layer.GetNextFeature()
    shape.Destroy()
    shape = ogr.Open(projected_shape_path, 1)
    shape_layer = shape.GetLayer(0)
    
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
    
    field_defn_npv = ogr.FieldDefn('NPV_25Y', ogr.OFTReal)
    shape_layer.CreateField(field_defn_npv)
    shape_layer.ResetReading()
    feat_grid = shape_layer.GetNextFeature()
    #For all the wave farm sites, calculate npv and write to shapefile
    while feat_grid is not None:
        depth_index = feat_grid.GetFieldIndex('Depth_M')
        wave_to_land_index = feat_grid.GetFieldIndex('W2L_MDIST')
        land_to_grid_index = feat_grid.GetFieldIndex('L2G_MDIST')
        captured_wave_energy_index = feat_grid.GetFieldIndex('CapWE_Sum')
        npv_index = feat_grid.GetFieldIndex('NPV_25Y')
        
        depth = feat_grid.GetFieldAsDouble(depth_index)
        wave_to_land = feat_grid.GetFieldAsDouble(wave_to_land_index)
        land_to_grid = feat_grid.GetFieldAsDouble(land_to_grid_index)
        captured_wave_energy = feat_grid.GetFieldAsDouble(captured_wave_energy_index)
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
        feat_grid.SetField(npv_index, npv_result)
        
        shape_layer.SetFeature(feat_grid)
        feat_grid.Destroy()
        feat_grid = shape_layer.GetNextFeature()

    datatype = gdal.GDT_Float32
    nodata = 0
    #Create a blank raster from the extents of the wave farm shapefile
    invest_cython_core.createRasterFromVectorExtents(pixel_xsize, pixel_ysize,
                                              datatype, nodata, wave_farm_value_path, wave_data_shape)
    wave_farm_value_raster = gdal.Open(wave_farm_value_path, GA_Update)
    #Get the corresponding points and values from the shapefile to be used for interpolation
    wave_farm_value_array = get_points_values(shape, ['LONG', 'LATI'], ['LONG', 'LATI', 'NPV_25Y'], 'NPV_25Y')
    #Interpolate the NPV values based on the dimensions and corresponding points of the raster, then
    #write the interpolated values to the raster
    interp_points_over_raster(wave_farm_value_array[0], wave_farm_value_array[1], wave_farm_value_raster)
    #Reproject the raster into a meters format
    virtual = gdal.AutoCreateWarpedVRT(wave_farm_value_raster,
                                       wave_farm_value_raster.GetProjectionRef(),
                                       prj)
    #Since the reprojection is just a virtual copy we must save it to disk
    drv_grid = gdal.GetDriverByName('GTIFF')
    drv_grid.CreateCopy(raster_projected_path, virtual, True)
    
def get_points_geometries(shape):
    """This function takes a shapefile and for each feature retrieves
    the X and Y value from it's geometry. The X and Y value are stored in
    a numpy array as a point [x,y], which is returned when all the features
    have been iterated through.
    
    shape - A shapefile
    
    returns - A numpy array of points, which represent the shape's feature's
              geometries.
    """
    point = []
    layer = shape.GetLayer(0)
    feat = layer.GetNextFeature()
    while feat is not None:
        x = float(feat.GetGeometryRef().GetX())
        y = float(feat.GetGeometryRef().GetY())
        point.append([x, y])
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
    #For all points xy in xy_1 calcuate the distance from xy to xy_2
    #and save the shortest distance found.
    for i, xy in enumerate(xy_1):
        dists = np.sqrt(np.sum((xy - xy_2) ** 2, axis=1))
        min_dist[i], min_id[i] = dists.min(), dists.argmin()
    return min_dist, min_id

def change_shape_projection(shape_to_reproject, projection, output_path):
    """Changes the projection of a shapefile by creating a new shapefile based on
    the projection passed in.  The new shapefile then copies all the features and fields of
    the shapefile to reproject as its own. The reprojected shapefile is written to 'outputpath'
    and is returned.
    
    shape_to_reproject - A shapefile to be copied and reprojected.
    projection - A file path to the location of the desired projection.
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
    #Open the projection file and read in contents as a string
    prj_file = open(projection)
    prj = prj_file.read()
    #Create a new spatial reference and set it from 'prj' string
    srs_prj = osr.SpatialReference()
    srs_prj.ImportFromWkt(prj)
    #Create the new layer for the shapefile using same name and geometry type from
    #shape_to_reproject, but different projection
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), srs_prj, in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd.SetWidth(src_fd.GetWidth())
        fd.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd)
    
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
