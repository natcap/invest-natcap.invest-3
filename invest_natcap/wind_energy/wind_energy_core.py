"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging

from osgeo import gdal
from osgeo import ogr
import numpy as np
import scipy.ndimage as ndimage
from scipy import signal
from scipy import integrate

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
        gdal.RasterizeLayer(land_ds, [1], aoi.GetLayer(), burn_values = [1])

        # Create a nodata mask so nodata values can be set back later
        aoi_nodata_mask = land_ds.GetRasterBand(1).ReadAsArray() == out_nodata
        
        # Burn the land polygon ontop of the ocean values as 1 so that we now
        # have an accurate mask of where the land, ocean, and nodata values
        # should be
        gdal.RasterizeLayer(
                land_ds, [1], land_polygon.GetLayer(), burn_values = [0])
        
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
    """This is where the doc string lives"""

    # fill in skeleton below
