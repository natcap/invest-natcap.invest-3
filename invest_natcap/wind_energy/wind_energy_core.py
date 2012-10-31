"""InVEST Wind_Energy model core function  module"""
import math
import os.path
import logging
import tempfile
import shutil

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
        args[wind_data_points] - an OGR point geometry shapefile of the wind
            energy points of interest (required)
        args[aoi] - an OGR datasource of type polygon of the area of interest
            (optional)
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
        args[suffix] - a String to append to the end of the filenames (required)
        args[land_polygon_uri] - an OGR datasource of type polygon that
            provides a coastline for determining distances from wind farm bins
            (optional)
        args[min_distance] - a float value for the minimum distance from shore
            for offshore wind farm installation (meters) (optional)
        args[max_distance] - a float value for the maximum distance from shore
            for offshore wind farm installation (meters) (optional)
        
        returns - nothing"""

    LOGGER.info('Entering core calculations for Biophysical')
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')

    tif_suffix = suffix + '.tif'

    bathymetry = args['bathymetry']
    min_depth = args['min_depth']
    max_depth = args['max_depth']
    
    bathymetry_band, out_nodata = raster_utils.extract_band_and_nodata(
            bathymetry)
    bath_prop = raster_utils.get_raster_properties(bathymetry)
    
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

    depth_mask_uri = os.path.join(intermediate_dir, 'depth_mask' + tif_suffix)
    
    LOGGER.info('Vectorize Depth Mask')
    # Create a mask for any values that are out of the range of the depth values
    depth_mask = raster_utils.vectorize_rasters(
            [bathymetry], depth_op, raster_out_uri = depth_mask_uri, 
            nodata = out_nodata)

    try:
        aoi = args['aoi']

        LOGGER.info('AOI provided')

        # If the distance inputs are present create a mask for the output
        # area that restricts where the wind energy farms can be based
        # on distance
        try:
            min_distance = args['min_distance']
            max_distance = args['max_distance']
            land_polygon = args['land_polygon']
            
            LOGGER.info('Distance Parameters Provided')
            
            aoi_raster_uri = os.path.join(
                    intermediate_dir, 'aoi_raster' + tif_suffix)

            LOGGER.info('Create Raster From AOI')
            # Make a raster from the AOI 
            aoi_raster = raster_utils.create_raster_from_vector_extents(
                    bath_prop['width'], abs(bath_prop['height']), 
                    gdal.GDT_Float32, out_nodata, aoi_raster_uri, aoi)
            
            LOGGER.info('Rasterize AOI onto raster')
            # Burn the area of interest onto the raster 
            gdal.RasterizeLayer(
                    aoi_raster, [1], aoi.GetLayer(), burn_values = [1], 
                    options = ['ALL_TOUCHED=TRUE'])

            LOGGER.info('Rasterize Land Polygon onto raster')
            # Burn the land polygon onto the raster, covering up the AOI values
            # where they overlap
            gdal.RasterizeLayer(
                    aoi_raster, [1], land_polygon.GetLayer(), burn_values = [0],
                    options = ['ALL_TOUCHED=TRUE'])

            dist_mask_uri = os.path.join(
                    intermediate_dir, 'distance_mask' + tif_suffix)
            
            LOGGER.info('Generate Distance Mask')
            # Create a distance mask
            distance_mask = distance_transform_dataset(
                    aoi_raster, min_distance, max_distance, 
                    out_nodata, dist_mask_uri)

            distance_mask.FlushCache()

        except KeyError:
            # Looks like distances weren't provided, too bad!
            LOGGER.info('Distance parameters not provided')

    except KeyError:
        LOGGER.info('AOI not provided')

    hub_height = args['hub_height']

    # Based on the hub height input construct a String to represent the field
    # name in the point shapefile to get the scale value for that height
    scale_key = 'Ram-0' + str(int(hub_height)) + 'm'
    LOGGER.debug('SCALE_key : %s', scale_key)

    # The String name for the shape field. So far this is a default from the
    # text file given by CK. I guess we could search for the 'K' if needed.
    shape_key = 'K-010m'

    # Weibull probability function to integrate over
    def weibull_probability(v_speed, k_shape, l_scale):
        """Calculate the weibull probability function of variable v_speed
            
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution
  
            returns - a float"""
        return ((k_shape / l_scale) * (v_speed / l_scale)**(k_shape - 1) *
                (math.exp(-1 * (v_speed/l_scale)**k_shape)))

    # Density wind energy function to integrate over
    def density_wind_energy_fun(v_speed, k_shape, l_scale):
        """Calculate the probability density function of a weibull variable
            v_speed
            
            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution
  
            returns - a float"""
        return ((k_shape / l_scale) * (v_speed / l_scale)**(k_shape - 1) *
                (math.exp(-1 * (v_speed/l_scale)**k_shape))) * v_speed**3
    
    # Harvested wind energy function to integrate over
    def harvested_wind_energy_fun(v_speed, k_shape, l_scale):
        """Calculate the harvested wind energy

            v_speed - a number representing wind speed
            k_shape - a float for the shape parameter
            l_scale - a float for the scale parameter of the distribution

            returns - a float"""
        fract = ((v_speed**exp_pwr_curve - v_in**exp_pwr_curve) /
            (v_rate**exp_pwr_curve - v_in**exp_pwr_curve))
   
        return fract * weibull_probability(v_speed, k_shape, l_scale) 

    # Get the wind points shapefile and layer
    wind_points = args['wind_data_points']
    wind_points_layer = wind_points.GetLayer(0)
   
    density_field_name = 'Density'
    harvest_field_name = 'HarvEnergy'

    LOGGER.info('Creating Harvest and Density Fields')
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

    # Compute the mean air density, given by CKs formulas
    mean_air_density = air_density_standard - (1.194*10**-4) * hub_height
    LOGGER.info('mean_air_density : %s', mean_air_density)

    # Fractional coefficient that lives outside the intregation for computing
    # the harvested wind energy
    fract_coef = rated_power * (mean_air_density / air_density_standard)
    
    # The coefficient that is multiplied by the integration portion of the
    # harvested wind energy equation
    scalar = num_days * 24 * fract_coef

    # Get the indexes for the scale and shape parameters
    feature = wind_points_layer.GetFeature(0)
    scale_index = feature.GetFieldIndex(scale_key)
    shape_index = feature.GetFieldIndex(shape_key)
    LOGGER.debug('scale/shape index : %s:%s', scale_index, shape_index)
    wind_points_layer.ResetReading()

    LOGGER.info('Entering Density and Harvest Calculations for each point')
    # For all the locations compute the weibull density and 
    # harvested wind energy. save in a field of the feature
    for feat in wind_points_layer:
        # Get the scale and shape values
        scale_value = feat.GetField(scale_index)
        shape_value = feat.GetField(shape_index)
        
        # Integrate over the probability density function. 0 and 50 are hard
        # coded values set in CKs documentation
        density_results = integrate.quad(
                density_wind_energy_fun, 0, 50, (shape_value, scale_value))

        # Compute the final wind power density value
        density_results = 0.5 * mean_air_density * density_results[0]

        # Integrate over the harvested wind energy function
        harv_results = integrate.quad(
                harvested_wind_energy_fun, v_in, v_rate, 
                (shape_value, scale_value))
        
        # Integrate over the weibull probability function
        weibull_results = integrate.quad(weibull_probability, v_rate, v_out,
                (shape_value, scale_value))
        
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
    density_temp_uri = os.path.join(
            intermediate_dir, 'density_temp' + tif_suffix)
    harvested_temp_uri = os.path.join(
            intermediate_dir, 'harvested_temp' + tif_suffix)
    
    LOGGER.info('Create Density Raster')
    density_temp = raster_utils.create_raster_from_vector_extents(
            bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
            out_nodata, density_temp_uri, wind_points)
    
    LOGGER.info('Create Harvested Raster')
    harvested_temp = raster_utils.create_raster_from_vector_extents(
            bath_prop['width'], abs(bath_prop['height']), gdal.GDT_Float32,
            out_nodata, harvested_temp_uri, wind_points)

    # Interpolate points onto raster for density values and harvested values:
    LOGGER.info('Vectorize Density Points')
    raster_utils.vectorize_points(wind_points, density_field_name, density_temp)
    
    LOGGER.info('Vectorize Harvested Points')
    raster_utils.vectorize_points(
            wind_points, harvest_field_name, harvested_temp)

    def mask_out_depth_dist(*rasters):
        """Returns the value of the first item in the list if and only if all 
            other values are not a nodata value. 
            
            *rasters - a list of values as follows:
                rasters[0] - the desired output value (required)
                rasters[1] - the depth mask value (required)
                rasters[2] - the distance mask value (optional)

            returns - a float of either out_nodata or rasters[0]"""
        
        if out_nodata in rasters:
            return out_nodata
        else:
            return rasters[0] 

    density_masked_uri = os.path.join(output_dir, 'density' + tif_suffix)
    harvested_masked_uri = os.path.join(
            output_dir, 'harvested_energy' + tif_suffix)

    density_mask_list = [density_temp, depth_mask]
    harvest_mask_list = [harvested_temp, depth_mask]

    # If a distance mask was created then add it to the raster list to pass in
    # for masking out the output datasets
    try:
        density_mask_list.append(distance_mask)
        harvest_mask_list.append(distance_mask)
    except NameError:
        LOGGER.info('NO Distance Mask')

    # Mask out any areas where distance or depth has determined that wind farms
    # cannot be located
    LOGGER.info('Vectorize Rasters on Density using depth and distance mask')
    _ = raster_utils.vectorize_rasters(
            density_mask_list, mask_out_depth_dist, 
            raster_out_uri = density_masked_uri, nodata = out_nodata)

    LOGGER.info('Vectorize Rasters on Harvested using depth and distance mask')
    _ = raster_utils.vectorize_rasters(
            harvest_mask_list, mask_out_depth_dist, 
            raster_out_uri = harvested_masked_uri, nodata = out_nodata)

def distance_transform_dataset(
        dataset, min_dist, max_dist, out_nodata, out_uri):
    """A memory efficient distance transform function that operates on 
       the dataset level and creates a new dataset that's transformed.
       It will treat any nodata value in dataset as 0, and re-nodata
       that area after the filter.

       dataset - a gdal dataset
       min_dist - an integer of the minimum distance allowed in meters
       max_dist - an integer of the maximum distance allowed in meters
       out_uri - the uri output of the transformed dataset
       out_nodata - the nodata value of dataset

       returns the transformed dataset created at out_uri"""
    
    temp_dir = tempfile.mkdtemp()
    source_filename = os.path.join(temp_dir, 'source.dat')
    nodata_mask_filename = os.path.join(temp_dir, 'nodata_mask.dat')
    dest_filename = os.path.join(temp_dir, 'dest.dat')

    mask_leq_min_dist_filename = os.path.join(temp_dir, 'mask_leq_min_dist.dat')
    mask_geq_max_dist_filename = os.path.join(temp_dir, 'mask_geq_max_dist.dat')
    dest_mask_filename = os.path.join(temp_dir, 'dest_mask.dat')


    source_band, source_nodata = raster_utils.extract_band_and_nodata(dataset)
    pixel_size = raster_utils.pixel_size(dataset)
    LOGGER.debug('Pixel Size : %s', pixel_size)

    out_dataset = raster_utils.new_raster_from_base(
        dataset, out_uri, 'GTiff', out_nodata, gdal.GDT_Float32)
    out_band, out_nodata = raster_utils.extract_band_and_nodata(out_dataset)

    shape = (source_band.YSize, source_band.XSize)
    LOGGER.info('shape %s' % str(shape))

    LOGGER.info('make the source memmap at %s' % source_filename)
    source_array = np.memmap(
        source_filename, dtype='float32', mode='w+', shape = shape)
    nodata_mask_array = np.memmap(
        nodata_mask_filename, dtype='bool', mode='w+', shape = shape)
    dest_array = np.memmap(
        dest_filename, dtype='float32', mode='w+', shape = shape)
    mask_leq_min_dist_array = np.memmap(
        mask_leq_min_dist_filename, dtype='bool', mode='w+', shape = shape)
    mask_geq_max_dist_array = np.memmap(
        mask_geq_max_dist_filename, dtype='bool', mode='w+', shape = shape)
    dest_mask_array = np.memmap(
        dest_mask_filename, dtype='bool', mode='w+', shape = shape)

    LOGGER.info('load dataset into source array')
    for row_index in xrange(source_band.YSize):
        #Load a row so we can mask
        row_array = source_band.ReadAsArray(0, row_index, source_band.XSize, 1)
        #Just the mask for this row
        mask_row = row_array == source_nodata
        row_array[mask_row] = 1.0
        source_array[row_index, :] = row_array

        #remember the mask in the memory mapped array
        nodata_mask_array[row_index, :] = mask_row
    LOGGER.info('distance transform operation')
    # Calculate distances using distance transform and multiply by the pixel
    # size to get the proper distances in meters
    dest_array = ndimage.distance_transform_edt(source_array) * pixel_size
    np.less_equal(dest_array, min_dist, out = mask_leq_min_dist_array)
    np.greater_equal(dest_array, max_dist, out = mask_geq_max_dist_array)
    np.logical_or(
            mask_leq_min_dist_array, mask_geq_max_dist_array,
            out = dest_mask_array)
    dest_array[dest_mask_array] = out_nodata

    LOGGER.info('mask the result back to nodata where originally nodata')
    dest_array[nodata_mask_array] = out_nodata
    LOGGER.info('write to gdal object')
    out_band.WriteArray(dest_array)
    out_dataset.FlushCache()
    raster_utils.calculate_raster_stats(out_dataset)

    LOGGER.info('deleting %s' % temp_dir)
    dest_array = None
    nodata_mask_array = None
    source_array = None
    out_band = None
    mask_leq_min_dist_array = None
    mask_geq_max_dist_array = None
    dest_mask_array = None
    #Turning on ignore_errors = True in case we can't remove the 
    #the temporary directory
    shutil.rmtree(temp_dir, ignore_errors = True)

    out_dataset.FlushCache()
    return out_dataset

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
    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')


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
    time = int(turbine_dict['Siemens']['time'])

    number_turbines = args['number_of_machines']
    mega_watt = mega_watt * number_turbines
    dollar_per_kwh = args['dollar_per_kWh']
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

    # Convert points from degrees to radians
    radian_points = convert_degrees_to_radians(new_points)
    
    # Convert points from radians to cartesian
    ocean_cartesian = lat_long_to_cartesian(radian_points)

    try:
        grid_land_points_dict = args['grid_dict']
        
        # Create individual dictionaries for land and grid points
        land_dict = build_subset_dictionary(
                grid_land_points_dict, 'type', 'land')
        grid_dict = build_subset_dictionary(
                grid_land_points_dict, 'type', 'grid')
        LOGGER.debug('Land Dict : %s', land_dict)
        # Create numpy arrays representing the points for land and
        # grid locations
        land_array = np.array(build_list_points_from_dict(land_dict))
        grid_array = np.array(build_list_points_from_dict(grid_dict))
        
        grid_radians = convert_degrees_to_radians(grid_array)
        grid_cartesian = lat_long_to_cartesian(grid_radians)

        land_radians = convert_degrees_to_radians(land_array)
        land_cartesian = lat_long_to_cartesian(land_radians)

        # Compute the distance between grid and land cartesian points 
        grid_dist_index = distance_kd(grid_cartesian, land_cartesian)
        
        # Separate out the tuple
        grid_dist, closest_grid = grid_dist_index[0], grid_dist_index[1] 
        LOGGER.debug('Grid Distance : %s', grid_dist)
        LOGGER.debug('Grid Closest Index : %s', closest_grid)
        
        # Add the distance from each landing point to its closest grid point as
        # a property in the land_dict
        index_x = 0
        for item in grid_dist:
            land_dict[closest_grid[index_x]]['g2l'] = item
            index_x = index_x + 1

        LOGGER.debug('Land Dict : %s', land_dict)
        
        dist_index = distance_kd(land_cartesian, ocean_cartesian) 
        dist, closest_index = dist_index[0], dist_index[1] 
        LOGGER.debug('Distances : %s ', dist) 
    
        # Get the wind points layer and reset the feature head in anticipation
        # of adding the distances and landing id to the points
        wind_layer = wind_energy_points.GetLayer()
        wind_layer.ResetReading()
        
        new_field_list = ['O2L_Dist', 'Land_Id', 'G2L_Dist']
        
        # Create new fields for ocean to land distance and the landing point id
        # to add to the shapefile
        for field_name in new_field_list:
            new_field = ogr.FieldDefn(field_name, ogr.OFTReal)
            wind_layer.CreateField(new_field)

        dist_index = 0
        id_index = 0
        
        for feat in wind_layer:
            ocean_to_land_dist = dist[dist_index]
            # Grab the landing point id by indexing into the dictionary using
            # the value from the closest_index
            land_id = land_dict[closest_index[id_index]]['id']
            g2l_dist = land_dict[closest_index[id_index]]['g2l']

            value_list = [ocean_to_land_dist, land_id, g2l_dist]
            
            for field_name, field_value in zip(new_field_list, value_list):
                field_index = feat.GetFieldIndex(field_name)
                feat.SetField(field_index, field_value)

            wind_layer.SetFeature(feat)
            dist_index = dist_index + 1
            id_index = id_index + 1

        #wind_energy_points = None

        out_nodata = -1.0
        
        o2l_uri = os.path.join(intermediate_dir, 'o2l.tif')
        l2g_uri = os.path.join(intermediate_dir, 'l2g.tif')
        energy_uri = os.path.join(intermediate_dir, 'val_energy.tif')
        
        ocean_land_ds = raster_utils.create_raster_from_vector_extents(
                30, 30, gdal.GDT_Float32,
                out_nodata, o2l_uri, wind_energy_points)
        
        land_grid_ds = raster_utils.create_raster_from_vector_extents(
                30, 30, gdal.GDT_Float32,
                out_nodata, l2g_uri, wind_energy_points)

        energy_ds = raster_utils.create_raster_from_vector_extents(
                30, 30, gdal.GDT_Float32,
                out_nodata, energy_uri, wind_energy_points)
        
        # Interpolate points onto raster for density values and
        # harvested values:
        raster_utils.vectorize_points(
                wind_energy_points, 'O2L_Dist', ocean_land_ds)
        raster_utils.vectorize_points(
                wind_energy_points, 'G2L_Dist', land_grid_ds)
        raster_utils.vectorize_points(
                wind_energy_points, 'HarvEnergy', energy_ds)

        def npv_op(dist_ocean, dist_land, energy):
            total_cable_dist = dist_ocean + dist_land
            cable_cost = 0
            if total_cable_dist <= 60:
                cable_cost = (.81 * mega_watt) + (1.36 * total_cable_dist)
            else:
                cable_cost = (1.09 * mega_watt) + (.89 * total_cable_dist)

            cap = cap_less_dist + cable_cost

            capex = cap / (1.0 - install_cost - misc_capex_cost) 
    
            npv = 0

            for t in range(1, time + 1):
                rev = energy * dollar_per_kwh 
                comp_one = (rev - op_maint_cost * capex) / disc_const**t
                comp_two = decom * capex / disc_time
                npv = npv + (comp_one - comp_two - capex)
   
            return npv

        npv_uri = os.path.join(intermediate_dir, 'npv.tif')
        
        _ = raster_utils.vectorize_rasters(
                [ocean_land_ds, land_grid_ds, energy_ds], npv_op, 
                raster_out_uri = npv_uri, nodata = -1.0)

    except KeyError:
        pass

def build_subset_dictionary(main_dict, key_field, value_field):
    """Take the main dictionary and build a subset dictionary depending on the
        key of the inner dictionary and corresponding value 
        
        main_dict - a dictionary that has keys which point to dictionaries
        key_field - the key of the inner dictionaries which are of interest
        value_field - the value that corresponds to the key_field

        returns - a dictionary"""

    subset_dict = {}
    index = 0
    for key, val in main_dict.iteritems():
        if val[key_field].lower() == value_field:
            subset_dict[index] = val
            index = index + 1
    return subset_dict

def build_list_points_from_dict(main_dict):
    """Builds a list of latitude and longitude points from a dictionary
    
        main_dict - a dictionary where keys point to a dictionary that have a
            'long' and 'lati' key:value pair

        returns - a list of points"""

    points_list = []
    sorted_keys = main_dict.keys()
    sorted_keys.sort()

    for key in sorted_keys:
        val = main_dict[key]
        points_list.append([float(val['long']), float(val['lati']), 0])

    return points_list

def distance_kd(array_one, array_two):
    """Computes the closest distance between to arrays of points using a k-d
        tree data structure.
    
        array_one - a numpy array of the points to build the k-d tree from
        array_two - a numpy array of points

        returns - a numpy array of distances and a numpy array of the closest
            indices"""

    tree = spatial.KDTree(array_one)
    dist, closest_index = tree.query(array_two)
    LOGGER.debug('KD Distance: %s', dist)
    LOGGER.debug('KD Closest Index: %s', closest_index)
    dist_and_index = [ dist, closest_index ]
    return dist_and_index

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

    radian_points = math.pi * points / 180.0

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
