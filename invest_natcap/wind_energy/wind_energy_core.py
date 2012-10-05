"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging

from osgeo import osr
from osgeo import gdal
from osgeo import ogr
import numpy as np
import scipy.ndimage as ndimage
from scipy import signal
from scipy import integrate
from scipy import spatial

from invest_natcap import raster_utils
LOGGER = logging.getLogger('wind_energy_core')

def biophysical(args):
    """Handles the core functionality for the biophysical part of the wind
        energy model
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[aoi] - an OGR datasource of type polygon of the area of interest
            (required)
        args[bathymetry] - a GDAL dataset of elevation values that encompasses
            the area of interest (required)
        args[bottom_type] - an OGR datasource of type polygon that depicts the 
            subsurface geology type (optional)
        args[hub_height] - a float value for the hub height of the turbines
            (meters) (required)
        args[cut_in_wspd] - a float value for the cut in wind speed of the
            (meters / second) turbine (required)
        args[cut_out_wspd] - a float value for the cut out wind speed of the
            (meteres / second) turbine (required)
        args[rated_wspd] - a float value for the rated wind speed of the 
            (meters / second) turbine (required)
        args[turbine_rated_pwr] - a float value for the turbine rated power
            (MW) (required)
        args[exp_out_pwr_curve] - a float value for the exponent output power
            curve (required)
        args[num_days] - an integer value for the number of days for harvested
            wind energy calculation (days) (required)
        args[air_density] - a float value for the air density of standard 
            atmosphere (kilograms / cubic meter) (required)
        args[min_depth] - a float value for the minimum depth for offshore wind
            farm installation (meters) (required)
        args[max_depth] - a float value for the maximum depth for offshore wind
            farm installation (meters) (required)
        args[land_polygon_uri] - an OGR datasource of type polygon that
            provides a coastline for determining distances from wind farm bins
            (optional)
        args[min_distance] - a float value for the minimum distance from shore
            for offshore wind farm installation (meters) (optional)
        args[max_distance] - a float value for the maximum distance from shore
            for offshore wind farm installation (meters) (optional)
        
        returns - nothing"""

    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')

    bathymetry = args['bathymetry']
    aoi = args['aoi']
    min_depth = args['min_depth']
    max_depth = args['max_depth']
    
    bathymetry_band, out_nodata = raster_utils.extract_band_and_nodata(
            bathymetry)
    
    def depth_op(bath):
        """A vectorized function that takes one argument and uses a range to
            determine if that value falls within the range
            
            bath - an integer value of either positive or negative
            min_depth - a float value specifying the lower limit of the range.
                this value is set above
            max_depth - a float value specifying the upper limit of the range
                this value is set above
            out_nodata - a int or float for the nodata value described above

            returns - out_nodata if 'bath' does not fall within the range, or
                'bath' if it does"""
        if bath >= max_depth and bath <= min_depth:
            return bath
        else:
            return out_nodata

    depth_mask_uri = os.path.join(intermediate_dir, 'depth_mask.tif')
    
    # Mask out any values that are out of the range of the depth values
    depth_mask = raster_utils.vectorize_rasters(
            [bathymetry], depth_op, raster_out_uri = depth_mask_uri, 
            nodata = out_nodata)

    # If the distance inputs are present try and create a mask for the output
    # area that restricts where the wind energy farms can be based on distance
    try:
        min_distance = args['min_distance']
        max_distance = args['max_distance']
        land_polygon = args['land_polygon']
        
        bath_prop = raster_utils.get_raster_properties(bathymetry)
        land_ds_uri = os.path.join(intermediate_dir, 'land_ds.tif')
        
        # Make a raster from the AOI and then rasterize land polygon ontop of it
        land_ds = raster_utils.create_raster_from_vector_extents(
                bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
                out_nodata, land_ds_uri, aoi)

        # Burn the whole area of interest onto the raster setting everything to
        # 0 which will represent our ocean values.
        gdal.RasterizeLayer(
                land_ds, [1], aoi.GetLayer(), burn_values = [1], 
                options = ['ALL_TOUCHED=TRUE'])

        # Create a nodata mask so nodata values can be set back later
        aoi_nodata_mask = land_ds.GetRasterBand(1).ReadAsArray() == out_nodata
        
        # Burn the land polygon ontop of the ocean values as 1 so that we now
        # have an accurate mask of where the land, ocean, and nodata values
        # should be
        gdal.RasterizeLayer(
                land_ds, [1], land_polygon.GetLayer(), burn_values = [0],
                options = ['ALL_TOUCHED=TRUE'])
        
        # Read in the raster so we can set back the nodata values
        # I don't think that reading back in the whole raster is a great idea
        # maybe there is a better way to handle this
        land_ds_array = land_ds.GetRasterBand(1).ReadAsArray()
        
        # Reset our nodata values
        land_ds_array[aoi_nodata_mask] = out_nodata
        aoi_nodata_mask = None

        # Write back our matrix to the band
        land_ds.GetRasterBand(1).WriteArray(land_ds_array)
        
        distance_mask_uri = os.path.join(intermediate_dir, 'distance_mask.tif')
        
        distance_mask = raster_utils.new_raster_from_base(
                land_ds, distance_mask_uri, 'GTiff', out_nodata, 
                gdal.GDT_Float32)
       
        dist_band = distance_mask.GetRasterBand(1)

        dist_matrix = np.copy(land_ds_array)
        land_ds_array = None
        
        np.putmask(dist_matrix, dist_matrix == out_nodata, 1)
        
        pixel_size = raster_utils.pixel_size(land_ds)
        
        # Calculate distances using distance transform and multiply by the pixel
        # size to get the proper distances in meters
        dist_matrix = \
                ndimage.distance_transform_edt(dist_matrix) * pixel_size
                
        # Create a mask for min and max distances 
        mask_min = dist_matrix <= min_distance
        mask_max = dist_matrix >= max_distance
        mask_dist = np.ma.mask_or(mask_min, mask_max)
        np.putmask(dist_matrix, mask_dist, out_nodata)

        dist_band.WriteArray(dist_matrix)
        dist_matrix = None

    except KeyError:
        # Looks like distances weren't provided, too bad!
        pass

    hub_height = args['hub_height']

    # Based on the hub height input construct a String to represent the field
    # name in the point shapefile to get the scale value for that height
    scale_key = 'Ram-0' + str(int(hub_height)) + 'm'
    LOGGER.debug('SCALE_key : %s', scale_key)

    # The String name for the shape field
    shape_key = 'K-010m'

    # Weibull probability function to integrate over
    def weibull_probability(v_speed, k_shape, l_scale, is_density):
        """Calculate the probability density function of a weibull variable
            v_speed
            
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution
            is_density - a boolean value determining which equation to return
  
            returns - a float
            """
        if is_density:
            return ((k_shape / l_scale) * (v_speed / l_scale)**(k_shape - 1) *
                    (math.exp(-1 * (v_speed/l_scale)**k_shape))) * v_speed**3
        else:
            return ((k_shape / l_scale) * (v_speed / l_scale)**(k_shape - 1) *
                    (math.exp(-1 * (v_speed/l_scale)**k_shape)))

    # Harvested wind energy function to integrate over
    def harvested_wind_energy_fun(v_speed, k_shape, l_scale):
        """Calculate the harvested wind energy
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution

            returns - a float
        """
        fract = ((v_speed**exp_pwr_curve - v_in**exp_pwr_curve) /
            (v_rate**exp_pwr_curve - v_in**exp_pwr_curve))
   
        return fract * weibull_probability(v_speed, k_shape, l_scale, False) 
   

    # Compute the mean air density
    air_density_mean = 1.225 - (1.194*10**-4) * hub_height

    # Get the wind points shapefile and layer
    wind_points = args['wind_data_points']
    wind_points_layer = wind_points.GetLayer(0)
   
    density_field_name = 'Density'
    harvest_field_name = 'HarvEnergy'

    # Create new fields for the density and harvested values
    for new_field_name in [density_field_name, harvest_field_name]:
        new_field = ogr.FieldDefn(new_field_name, ogr.OFTReal)
        wind_points_layer.CreateField(new_field)
    
    # Get the inputs needed to compute harvested wind energy
    exp_pwr_curve = args['exp_out_pwr_curve']
    num_days = args['num_days']
    rated_power = args['turbine_rated_pwr']
    air_density_standard = args['air_density']
    v_rate = args['rated_wspd']
    v_out = args['cut_out_wspd']
    v_in = args['cut_in_wspd']

    # Fractional coefficient that lives outside the intregation for computing
    # the harvested wind energy
    fract_coef = rated_power * (air_density_mean / air_density_standard)
    
    # The coefficient that is multiplied by the integration portion of the
    # harvested wind energy equation
    scalar = num_days * 24 * fract_coef

    # Get the indexes for the scale and shape parameters
    feature = wind_points_layer.GetFeature(0)
    scale_index = feature.GetFieldIndex(scale_key)
    shape_index = feature.GetFieldIndex(shape_key)
    LOGGER.debug('scale/shape index : %s:%s', scale_index, shape_index)
    wind_points_layer.ResetReading()

    # For all the locations compute the weibull density and 
    # harvested wind energy. save in a field of the feature
    for feat in wind_points_layer:
        # Get the scale and shape values
        scale_value = feat.GetField(scale_index)
        shape_value = feat.GetField(shape_index)
        
        # Integrate over the weibull probability function
        density_results = integrate.quad(weibull_probability, 1, 50,
                (shape_value, scale_value, True))

        # Compute the final wind power density value
        density_results = 0.5 * air_density_mean * density_results[0]

        # Integrate over the harvested wind energy function
        harv_results = integrate.quad(
                harvested_wind_energy_fun, v_in, v_rate, 
                (shape_value, scale_value))
        
        # Integrate over the weibull probability function
        weibull_results = integrate.quad(weibull_probability, v_rate, v_out,
                (shape_value, scale_value, False))
        
        # Compute the final harvested wind energy value
        harvested_wind_energy = scalar * (harv_results[0] + weibull_results[0])
        
        # Save the results to their respective fields 
        for field_name, result_value in [(density_field_name, density_results),
                (harvest_field_name, harvested_wind_energy)]:
            out_index = feat.GetFieldIndex(field_name)
            feat.SetField(out_index, result_value)

        # Save the feature and set to None to clean up
        wind_points_layer.SetFeature(feat)
        feat = None

    wind_points_layer.ResetReading()

    # Create rasters for density and harvested values
    bath_prop = raster_utils.get_raster_properties(bathymetry)
    density_ds_uri = os.path.join(intermediate_dir, 'density_ds.tif')
    harvested_ds_uri = os.path.join(intermediate_dir, 'harvested_ds.tif')
    
    density_ds = raster_utils.create_raster_from_vector_extents(
            bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
            out_nodata, density_ds_uri, wind_points)
    
    harvested_ds = raster_utils.create_raster_from_vector_extents(
            bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
            out_nodata, harvested_ds_uri, wind_points)

    # Interpolate points onto raster for density values and harvested values:
    raster_utils.vectorize_points(wind_points, density_field_name, density_ds)
    raster_utils.vectorize_points(wind_points, harvest_field_name, harvested_ds)

    # Mask out any areas where distance or depth has determined that wind farms
    # cannot be located

    def mask_out_depth_dist(out_ds, depth_ds, dist_ds):
        """Returns the value of 'out_ds' if and only if all three rasters are
            not a nodata value
            
            out_ds - 
            depth_ds - 
            dist_ds -

            returns - a float of either out_nodata or out_ds
            """
        if (out_ds == out_nodata) or (depth_ds == out_nodata) or (dist_ds ==
            out_nodata):
            return out_nodata
        else:
            return out_ds

    density_masked_uri = os.path.join(intermediate_dir, 'density_masked.tif')
    harvested_masked_uri = os.path.join(intermediate_dir, 'harvested_masked.tif')

    _ = raster_utils.vectorize_rasters(
            [density_ds, depth_mask, distance_mask], mask_out_depth_dist, 
            raster_out_uri = density_masked_uri, nodata = out_nodata)

    _ = raster_utils.vectorize_rasters(
            [harvested_ds, depth_mask, distance_mask], mask_out_depth_dist, 
            raster_out_uri = harvested_masked_uri, nodata = out_nodata)


def valuation(args):
    """Handles the core functionality for the valuation part of twind energy
        model

        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[harvested_energy] - a GDAL dataset from the biophysical run of 
            the wind energy model that has the per pixel harvested wind energy
            (required)
        args[distance] - a GDAL dataset from the biophysical run of
            the wind energy model that depicts the distances of pixels 
            from shore (required)
        args[biophysical_data] - an OGR datasource of type point
            from the output of the biophysical model run (required) 
        args[turbine_dict] - a dictionary that has the parameters
            for the type of turbine (required)
        args[grid_dict] - a dictionary that specifies the landing
            and grid point locations (optional)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required)
        args[suffix] - a string for the suffix to be appended to the output
            names (optional) 

        returns - Nothing
    """

    # fill in skeleton below


    # Get constants from turbine_dict
    turbine_dict = args['turbine_dict']

    infield_length = float(turbine_dict['Siemens']['infield_length'])
    infield_cost = float(turbine_dict['Siemens']['infield_cost'])
    foundation_cost = float(turbine_dict['Siemens']['foundation_cost'])
    unit_cost = float(turbine_dict['Siemens']['unit_cost'])
    install_cost = float(turbine_dict['Siemens']['install_cost']) / 100.00
    misc_capex_cost = float(turbine_dict['Siemens']['misc_capex']) / 100.00
    op_maint_cost = float(turbine_dict['Siemens']['op_maint']) / 100.00
    discount_rate = float(turbine_dict['Siemens']['discount_rate']) / 100.00
    decom = float(turbine_dict['Siemens']['decom']) / 100.00
    turbine_name = turbine_dict['Siemens']['type']
    mega_watt = float(turbine_dict['Siemens']['mw'])
    avg_land_cable_dist = float(turbine_dict['Siemens']['avg_land_cable_dist'])
    mean_land_dist = float(turbine_dict['Siemens']['mean_land_dist'])
    time = float(turbine_dict['Siemens']['time'])

    number_turbines = args['number_of_machines']

    # Construct as many parts of the NPV equation as possible without needing to
    # vectorize over harvested energy and distance

    cap_less_dist = ((infield_length * infield_cost * number_turbines) + 
            ((foundation_cost + unit_cost) * number_turbines))


    disc_const = discount_rate + 1.0
    disc_time = disc_const**time

    
    # Create vectorize operation that takes distance and harvested energy
    # raster, outputting another raster with the NPV


    #capex = cap / (1.0 - install_rate - misc_capex_cost)

      
    wind_energy_points = args['biophysical_data']

    # Using 'WGS84' as our well known lat/long projection
    wgs84_srs = osr.SpatialReference()
    wgs84_srs.SetWellKnownGeogCS("WGS84")
    
    proj_srs = wind_energy_points.GetLayer().GetSpatialRef()
    
    # Create coordinate transformation to get point geometries from meters to
    # lat / long
    coord_transform = osr.CoordinateTransformation(proj_srs, wgs84_srs)
    
    # Get a numpy array of the wind energy points
    points_array = get_points_geometries(wind_energy_points)

    # Transform the points into lat / long
    new_points = transform_array_of_points(points_array, proj_srs, wgs84_srs)

    # Conver points from degrees to radians
    radian_points = convert_degrees_to_radians(new_points)

    ocean_cartesian = lat_long_to_cartesian(radian_points)

    try:
        grid_land_points_dict = args['grid_dict']
        
        land_dict = {}
        land_array = []
        grid_dict = {}
        grid_array = []
        
        # These indexes will be the keys in the individual dictionaries.
        # Starting from zero allows us to relate these keys to indexes in an
        # array
        land_index = 0 
        grid_index = 0

        for key, val in grid_land_points_dict.iteritems():
            if val['type'].lower() == 'land':
                land_dict[land_index] = val
                land_array.append([float(val['long']), float(val['lati']), 0])
                land_index = land_index + 1
            else:
                grid_dict[grid_index] = val
                grid_array.append([float(val['long']), float(val['lati']), 0])
                grid_index = grid_index + 1

        LOGGER.debug('Land Dict : %s', land_dict)
        land_nparray = np.array(land_array)
        land_radians = convert_degrees_to_radians(land_nparray)
        land_cartesian = lat_long_to_cartesian(land_radians)
        LOGGER.debug('land_cartesian : %s', land_cartesian)
        land_tree = spatial.KDTree(land_cartesian)
        dist, closest_index = land_tree.query(ocean_cartesian)
        LOGGER.debug('Distances : %s ', dist) 
    
        wind_layer = wind_energy_points.GetLayer()
        wind_layer.ResetReading()
        
        new_field_list = ['O2L_Dist', 'Land_Id']
        
        for field_name in new_field_list:
            new_field = ogr.FieldDefn(field_name, ogr.OFTReal)
            wind_layer.CreateField(new_field)

        dist_index = 0
        id_index = 0
        
        for feat in wind_layer:
            ocean_to_land_dist = dist[dist_index]
            land_id = land_dict[closest_index[id_index]]['id']
            
            value_list = [ocean_to_land_dist, land_id]
            
            for field_name, field_value in zip(new_field_list, value_list):
                field_index = feat.GetFieldIndex(field_name)
                feat.SetField(field_index, field_value)

            wind_layer.SetFeature(feat)
            dist_index = dist_index + 1
            id_index = id_index + 1

        wind_energy_points = None
    except KeyError:
        pass


def lat_long_to_cartesian(points):
    """Convert a numpy array of points that are in radians to cartesian
        coordinates

        points - a numpy array of points in radians

        returns - a numpy array of points in cartesian coordinates"""

    radius = 6378.1 # km

    cartesian_points = np.zeros(points.shape)
    index = 0

    for point in points:
        x = radius * math.cos(point[0]) * math.sin(point[1])
        y = radius * math.sin(point[0]) * math.sin(point[1])
        z = radius * math.cos(point[1])
        cartesian_points[index] = [x, y, z]
    
        index = index + 1

    return cartesian_points

def convert_degrees_to_radians(points):
    """Convert a numpy array of points that are in degrees to radians

        points - a numpy array of points that are in degrees

        returns - a numpy array of points that are in radians
        """

    radian_points = np.zeros(points.shape)
    
    def vop(deg):
        return math.pi * deg / 180.0

    vectorized_op = np.vectorize(vop)
    
    index = 0

    for point in points:
        radian_points[index] = vectorized_op(point)
        index = index + 1

    return radian_points

def transform_array_of_points(points, source_srs, target_srs):
    """Transform an array of points into another spatial reference

        points - a numpy array of points. ex : [[1,1], [1,5]...]
        source_srs - the current Spatial Reference
        target_srs - the desired Spatial Reference

        returns - a numpy array of points tranformed to the target_srs
        """

    coord_transform = osr.CoordinateTransformation(source_srs, target_srs)

    points_copy = np.copy(points)

    return np.array(coord_transform.TransformPoints(points_copy))

def get_points_geometries(shape):
    """This function takes a shapefile and for each feature retrieves
    the X and Y value from it's geometry. The X and Y value are stored in
    a numpy array as a point [x_location,y_location], which is returned 
    when all the features have been iterated through.
    
    shape - An OGR shapefile datasource
    
    returns - A numpy array of points, which represent the shape's feature's
              geometries.
    """
    layer = shape.GetLayer()
    layer.ResetReading()
    feat_count = layer.GetFeatureCount() 
    points = np.zeros((feat_count, 2))
    index = 0

    for feat in layer:    
        geom = feat.GetGeometryRef()
        x_location = geom.GetX()
        y_location = geom.GetY()
        points[index] = [x_location, y_location]
        index = index + 1

    return np.array(points)
