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
    """This is where the doc string lives
    
        args[workspace_dir] - uri for workspace directory
        args[bathymetry] - a GDAL raster of elevation values
        args[aoi] - an OGR polygon shapefile of the area of interest
        args[min_depth] - a float of the minimum depth required for the turbines
        args[max_depth] - a float of the maximum depth the turbines can be
            placed
        args[min_distance] - a float of the minimum distance the farms have
            to be away from the coastline (m)
        args[max_distance] - a float of the maximum distance the farms can 
            be placed away from the coastline (m)
        args[land_polygon] - an OGR polygon shapefile of the land polygon

        returns - 
    """
    workspace = args['workspace_dir']
    inter_dir = os.path.join(workspace, 'intermediate')

    # get a mask for the min and max depths allowed for the turbines
    bathymetry = args['bathymetry']
    aoi = args['aoi']
    min_depth = args['min_depth'] * -1.0
    max_depth = args['max_depth'] * -1.0
    
    out_nodata = bathymetry.GetRasterBand(1).GetNoDataValue()
    
    # mask out any values that are out of the range of the depth values
    def depth_op(bath):
        if bath >= max_depth and bath <= min_depth:
            return bath
        else:
            return out_nodata

    depth_mask_uri = os.path.join(inter_dir, 'depth_mask.tif')
    depth_mask = \
        raster_utils.vectorize_rasters([bathymetry], depth_op, \
            raster_out_uri = depth_mask_uri, nodata = out_nodata)

    # construct the coastline from the AOI and bathymetry using the min and max
    # distance values provided
    try:
        # do some awesome coastline finding if distances are provided
        min_distance = args['min_distance']
        max_distance = args['max_distance']
        land_polygon = args['land_polygon']
        
        # make raster from the AOI and then rasterize land polygon ontop of it
        bath_prop = raster_utils.get_raster_properties(bathymetry)
        land_ds_uri = os.path.join(inter_dir, 'land_ds.tif')
        land_ds = raster_utils.create_raster_from_vector_extents(
                bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
                out_nodata, land_ds_uri, aoi)

        # burn the whole area of interest onto the raster setting everything to
        # 0 which will represent our ocean values.
        gdal.RasterizeLayer(land_ds, [1], aoi.GetLayer(), burn_values = [1])
        # create a nodata mask
        aoi_nodata_mask = land_ds.GetRasterBand(1).ReadAsArray() == out_nodata
        # burn the land polygon ontop of the ocean values as 1 so that we now
        # have an accurate mask of where the land, ocean, and nodata values
        # should be
        gdal.RasterizeLayer(
                land_ds, [1], land_polygon.GetLayer(), burn_values = [0])
        # read in the raster so we can set back the nodata values
        # I don't think that reading back in the whole raster is a great idea
        # maybe there is a better way to handle this
        land_ds_array = land_ds.GetRasterBand(1).ReadAsArray()
        # reset our nodata values
        land_ds_array[aoi_nodata_mask] = out_nodata
        # write back our matrix to the band
        land_ds.GetRasterBand(1).WriteArray(land_ds_array)
        
        # calculate distances using distance transform
        
        distance_calc_uri = os.path.join(inter_dir, 'distance_factored.tif')
        dist_raster = raster_utils.new_raster_from_base(land_ds,
                distance_calc_uri, 'GTiff', out_nodata, gdal.GDT_Float32)
       
        dist_band = dist_raster.GetRasterBand(1)

        dist_matrix = np.copy(land_ds_array)
        np.putmask(dist_matrix, dist_matrix == out_nodata, 1)
        
        pixel_size = raster_utils.pixel_size(land_ds)
        
        dist_matrix = \
                ndimage.distance_transform_edt(dist_matrix) * pixel_size
                
        LOGGER.debug('minimum distance : %s', dist_matrix.min()) 
        LOGGER.debug('maximum distance : %s', dist_matrix.max()) 
        dist_copy = np.copy(dist_matrix)

        mask_min = dist_matrix <= min_distance
        mask_max = dist_matrix >= max_distance
        mask_dist = np.ma.mask_or(mask_min, mask_max)
        LOGGER.debug('any distances work? : %s', mask_dist.all())
        np.putmask(dist_matrix, mask_dist, out_nodata)

        dist_band.WriteArray(dist_matrix)

    except KeyError:
        # looks like distances weren't provided, too bad!
        pass

    # fill in skeleton below

    # compute wind density
    hub_height = args['hub_height']

    # based on the hub height input construct a String to represent the field
    # name in the point shapefile to get the scale value for that height
    scale_key = 'Ram-0' + str(int(hub_height)) + 'm'
    LOGGER.debug('SCALE_key : %s', scale_key)

    # the String name for the shape field
    shape_key = 'K-010m'

    # weibull densitiy probability function to integrate over
    def weibull_probability(v_speed, k_shape, l_scale):
        """Calculate the probability density function of a weibull variable
            v_speed
            
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution

            returns - a float
            """
        return ((k_shape / l_scale) * (v_speed / l_scale)**(k_shape - 1) *
            (math.exp(-1 * (v_speed/l_scale)**k_shape)))

    # harvested wind energy function to integrate over
    def harvested_wind_energy_fun(v_speed, k_shape, l_scale):
        """Calculate the harvested wind energy
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution

            returns - a float
        """
        fract = (v_speed**exp_pwr_curve - v_in) / (v_rate**exp_pwr_curve - v_in)
        return fract * weibull_probability(v_speed, k_shape, l_scale)
    
    # compute the mean air density
    air_density_mean = 1.225 - (1.194*10**-4) * hub_height

    # get the wind points shapefile and layer
    wind_points = args['wind_data_points']
    wind_points_layer = wind_points.GetLayer(0)
   
    density_field_name = 'Density'
    harvest_field_name = 'HarvEnergy'

    # create new fields for the density and harvested values
    for new_field_name in [density_field_name, harvest_field_name]:
        new_field = ogr.FieldDefn(new_field_name, ogr.OFTReal)
        wind_points_layer.CreateField(new_field)
    
    # get the inputs needed to compute harvested wind energy
    exp_pwr_curve = args['exp_out_pwr_curve']
    num_days = args['num_days']
    rated_power = args['turbine_rated_pwr']
    air_density_standard = args['air_density']
    v_rate = args['rated_wspd']
    v_out = args['cut_out_wspd']
    v_in = args['cut_in_wspd'] * exp_pwr_curve

    # fractional coefficient that lives outside the intregation for computing
    # the harvested wind energy
    fract_coef = rated_power * (air_density_mean / air_density_standard)
    # the coefficient that is multiplied by the integration portion of the
    # harvested wind energy equation
    scalar = num_days * 24 * fract_coef

    # get the indexes for the scale and shape parameters
    feature = wind_points_layer.GetFeature(0)
    scale_index = feature.GetFieldIndex(scale_key)
    shape_index = feature.GetFieldIndex(shape_key)
    LOGGER.debug('scale/shape index : %s:%s', scale_index, shape_index)
    wind_points_layer.ResetReading()

    # for all the locations compute the weibull density and 
    # harvested wind energy. save in a field of the feature
    for feat in wind_points_layer:
        # get the scale and shape values
        scale_value = feat.GetField(scale_index)
        shape_value = feat.GetField(shape_index)
        
        # integrate over the weibull probability function
        density_results = integrate.quad(weibull_probability, 1, 50,
                (shape_value, scale_value))

        # compute the final wind power density value
        density_results = 0.5 * air_density_mean * density_results[0]

        # integrate over the harvested wind energy function
        harv_results = integrate.quad(
                harvested_wind_energy_fun, v_out, v_rate, 
                (shape_value, scale_value))
        
        # integrate over the weibull probability function
        weibull_results = integrate.quad(weibull_probability, v_rate, v_out,
                (shape_value, scale_value))
        
        # compute the final harvested wind energy value
        harvested_wind_energy = scalar * (harv_results[0] + weibull_results[0])
        
        # save the results to their respective fields 
        for field_name, result_value in [(density_field_name, density_results),
                (harvest_field_name, harvested_wind_energy)]:
            out_index = feat.GetFieldIndex(field_name)
            feat.SetField(out_index, result_value)

        # save the feature and set to None to clean up
        wind_points_layer.SetFeature(feat)
        feat = None

def valuation(args):
    """This is where the doc string lives"""

    # fill in skeleton below
