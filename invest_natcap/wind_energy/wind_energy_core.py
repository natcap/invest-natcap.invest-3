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
import shapely.wkt
import shapely.ops
from shapely import speedups

from invest_natcap import raster_utils
LOGGER = logging.getLogger('wind_energy_core')
speedups.enable()

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

    tif_suffix = args['suffix'] + '.tif'

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
    
    LOGGER.info('Creating Depth Mask')
    # Create a mask for any values that are out of the range of the depth values
    depth_mask = raster_utils.vectorize_rasters(
            [bathymetry], depth_op, raster_out_uri = depth_mask_uri, 
            nodata = out_nodata)

    # Handle the AOI if it was passed in with the dictionary
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
    scale_key = str(int(hub_height))
    if len(scale_key) <= 2:
        scale_key = 'Ram-0' + scale_key + 'm'
    else:
        scale_key = 'Ram-' + scale_key + 'm'
    
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
    LOGGER.debug('mean_air_density : %s', mean_air_density)

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
    
    # Define URI paths for the numpy arrays on disk
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
    LOGGER.debug('shape %s' % str(shape))

    LOGGER.debug('make the source memmap at %s' % source_filename)
    # Create the numpy memory maps
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

    LOGGER.debug('load dataset into source array')
    # Load the dataset into the first memory map
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
    
    # Use conditional operations to properly get masks based on distance values
    np.less_equal(dest_array, min_dist, out = mask_leq_min_dist_array)
    np.greater_equal(dest_array, max_dist, out = mask_geq_max_dist_array)
    
    # Take the logical OR of the above masks to get the proper values that fall
    # between the min and max distances
    np.logical_or(
            mask_leq_min_dist_array, mask_geq_max_dist_array,
            out = dest_mask_array)
    
    dest_array[dest_mask_array] = out_nodata

    LOGGER.debug('mask the result back to nodata where originally nodata')
    dest_array[nodata_mask_array] = out_nodata
    
    LOGGER.debug('write to gdal object')
    out_band.WriteArray(dest_array)
    out_dataset.FlushCache()
    raster_utils.calculate_raster_stats(out_dataset)

    LOGGER.debug('deleting %s' % temp_dir)
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
        args[aoi] - an OGR datasource of type polygon that is projected in
            meters (required)
        args[biophysical_data] - an OGR datasource of type point
            from the output of the biophysical model run (required) 
        args[turbine_dict] - a dictionary that has the parameters
            for the type of turbine (required)
        args[grid_points] - an OGR datasource of type point, representing where
            the grid connections are (optional)
        args[land_points] - an OGR datasource of type point, representing where
            the land connections are (optional)
        args[land_polygon] - an OGR datasource of type polygon, to get the wind
            energy bin distances from if grid points and land points are not
            provided (required if grid_points and land_points are not provided)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required)
        args[suffix] - a string for the suffix to be appended to the output
            names (optional) 

        returns - Nothing """

    LOGGER.info('Entering core calculations for Valuation')

    workspace = args['workspace_dir']
    intermediate_dir = os.path.join(workspace, 'intermediate')
    output_dir = os.path.join(workspace, 'output')

    # Get constants from turbine_dict
    turbine_dict = args['turbine_dict']
    turbine_name = 'Siemens'
    # The length of infield cable in km
    infield_length = float(turbine_dict[turbine_name]['infield_length'])
    # The cost of infield cable in millions of dollars per km
    infield_cost = float(turbine_dict[turbine_name]['infield_cost'])
    # The cost of the foundation in millions of dollars 
    foundation_cost = float(turbine_dict[turbine_name]['foundation_cost'])
    # The cost of each turbine unit in millions of dollars
    unit_cost = float(turbine_dict[turbine_name]['unit_cost'])
    # The installation cost as a percentage of final capital costs converted to
    # a decimal
    install_cost = float(turbine_dict[turbine_name]['install_cost']) / 100.00
    # The miscellaneous costs as a percentage of CAPEX converted to a decimal
    misc_capex_cost = float(turbine_dict[turbine_name]['misc_capex']) / 100.00
    # The operations and maintenance costs as a percentage of CAPEX converted
    # to a decimal
    op_maint_cost = float(turbine_dict[turbine_name]['op_maint']) / 100.00
    # The distcount rate as a percentage converted to a decimal
    discount_rate = float(turbine_dict[turbine_name]['discount_rate']) / 100.00
    # The cost to decommission the farm as a percentage of CAPEX converted to a
    # decimal
    decom = float(turbine_dict[turbine_name]['decom']) / 100.00
    turbine_name = turbine_dict[turbine_name]['type']
    # The mega watt value for the turbines in MW
    mega_watt = float(turbine_dict[turbine_name]['mw'])
    # The average land cable distance in km
    avg_land_cable_dist = float(
            turbine_dict[turbine_name]['avg_land_cable_dist'])
    # The mean land distance to a grid connection point in km
    mean_land_dist = float(turbine_dict[turbine_name]['mean_land_dist'])
    time = int(turbine_dict[turbine_name]['time'])

    number_turbines = args['number_of_machines']
    total_mega_watt = mega_watt * number_turbines
    dollar_per_kwh = args['dollar_per_kWh']
    
    wind_energy_points = args['biophysical_data']
   
    try:
        # Try using the grid points to calculate distances
        grid_points_ds = args['grid_points']
        land_shape_ds = args['land_points']
    except KeyError:
        LOGGER.info('No grid points, calculating distances using land polygon')
        # Since the grid points were not provided use the land polygon to get
        # near shore distances
        land_shape_ds = args['land_polygon']
    
        # When using the land polygon to conduct distances there is a set
        # constant distance for land point to grid points. The following lines
        # add a new field to each point with that distance
        wind_energy_layer = wind_energy_points.GetLayer()
        feat_count = wind_energy_layer.GetFeatureCount()
        
        # Build up an array the same size as how many features (points) there
        # are. This is constructed so we can call the
        # 'add_field_to_shape_given_list' function. 
        grid_to_land_dist = np.ones(feat_count)
        
        # Set each value in the array to the constant distance for land to grid
        # points
        grid_to_land_dist = grid_to_land_dist * mean_land_dist
        
        wind_energy_layer = None     
    else:
        LOGGER.info('Calculating distances using grid points')
        # Get the shortest distances from each grid point to the land points
        grid_to_land_dist_local = point_to_polygon_distance(
                grid_points_ds, land_shape_ds)
         
        # Add the distances for land to grid points as a new field  onto the 
        # land points datasource
        LOGGER.info('Adding land to grid distances to land point datasource')
        land_to_grid_field = 'L2G'
        land_shape_ds = add_field_to_shape_given_list(
                land_shape_ds, grid_to_land_dist_local, land_to_grid_field)
  
        # In order to get the proper land to grid distances that each ocean
        # point corresponds to, we need to build up a KDTree from the land
        # points geometries and then iterate through each wind energy point
        # seeing which land point it is closest to. Knowing which land point is
        # closest allows us to add the proper land to grid distance to the wind
        # energy point ocean points.

        # Get the land points geometries
        land_geoms = get_points_geometries(land_shape_ds)
        
        # Build a dictionary from the land points datasource so that we can
        # have access to what land point has what land to grid distance
        land_dict = get_dictionary_from_shape(land_shape_ds)
        
        LOGGER.debug('land_dict : %s', land_dict)
        
        # Build up the KDTree for land points geometries
        kd_tree = spatial.KDTree(land_geoms)
        
        # Initialize a list to store all the proper grid to land distances to
        # add to the wind energy point datasource later
        grid_to_land_dist = []

        wind_energy_layer = wind_energy_points.GetLayer()
        for feat in wind_energy_layer:
            geom = feat.GetGeometryRef()
            x_loc = geom.GetX()
            y_loc = geom.GetY()
            
            # Create a point from the geometry
            point = np.array([x_loc, y_loc])
            
            # Get the shortest distance and closest index from the land points
            dist, closest_index = kd_tree.query(point)
            
            # Knowing the closest index we can look into the land geoms lists,
            # pull that lat/long key, and then use that to index into the
            # dictionary to get the proper distance
            L2G_dist = land_dict[tuple(land_geoms[closest_index])]['L2G'] 
            grid_to_land_dist.append(L2G_dist)

        wind_energy_layer.ResetReading()
        wind_energy_layer = None
    
    # Get the shortest distances from each ocean point to the land points
    land_to_ocean_dist = point_to_polygon_distance(
            land_shape_ds, wind_energy_points)
    
    # Add the ocean to land distance value for each point as a new field
    ocean_to_land_field = 'O2L'
    LOGGER.info('Adding ocean to land distances')
    wind_energy_points = add_field_to_shape_given_list(
            wind_energy_points, land_to_ocean_dist, ocean_to_land_field)
        
    # Add the grid to land distance value for each point as a new field
    land_to_grid_field = 'L2G'
    LOGGER.info('Adding land to grid distances')
    wind_energy_points = add_field_to_shape_given_list(
            wind_energy_points, grid_to_land_dist, land_to_grid_field)
   
    # Total infield cable cost
    infield_cable_cost = infield_length * infield_cost * number_turbines
    LOGGER.debug('infield_cable_cost : %s', infield_cable_cost)
    # Total foundation cost
    total_foundation_cost = (foundation_cost + unit_cost) * number_turbines
    LOGGER.debug('total_foundation_cost : %s', total_foundation_cost)
    # Nominal Capital Cost (CAP) minus the cost of cable which needs distances
    cap_less_dist = infield_cable_cost + total_foundation_cost
    LOGGER.debug('cap_less_dist : %s', cap_less_dist)
    # Discount rate plus one to get that constant
    disc_const = discount_rate + 1.0
    LOGGER.debug('discount_rate : %s', disc_const)
    # Discount constant raised to the total time, a constant found in the NPV
    # calculation (1+i)^T
    disc_time = disc_const**time
    LOGGER.debug('disc_time : %s', disc_time)
    
    # Create 3 new fields based on the 3 outputs
    wind_energy_layer = wind_energy_points.GetLayer()
    LOGGER.info('Creating new NPV, Levelized Cost and CO2 field')
    for new_field in ['NPV', 'LevCost', 'CO2']:
        field = ogr.FieldDefn(new_field, ogr.OFTReal)
        wind_energy_layer.CreateField(field)
    
    LOGGER.info('Calculating the NPV for each wind farm')
    # Iterate over each point calculating the NPV
    for feat in wind_energy_layer:
        npv_index = feat.GetFieldIndex('NPV')
        levelized_index = feat.GetFieldIndex('LevCost')
        co2_index = feat.GetFieldIndex('CO2')
        energy_index = feat.GetFieldIndex('HarvEnergy')
        O2L_index = feat.GetFieldIndex('O2L')
        L2G_index = feat.GetFieldIndex('L2G')
        
        # The energy value converted from Wh (Watt hours as output from CK's
        # biophysical model equations) to kWh
        energy_val = feat.GetField(energy_index) / 1000.0
        O2L_val = feat.GetField(O2L_index)
        L2G_val = feat.GetField(L2G_index)

        # Get the total cable distance
        total_cable_dist = O2L_val + L2G_val
        # Initialize cable cost variable
        cable_cost = 0

        # These constants are based on the literature from Rob's users guide on
        # valuation. The break at 60 indicates the difference in using AC and
        # DC current systems
        if total_cable_dist <= 60:
            cable_cost = (.81 * total_mega_watt) + (1.36 * total_cable_dist)
        else:
            cable_cost = (1.09 * total_mega_watt) + (.89 * total_cable_dist)
        
        # Compute the total CAP
        cap = cap_less_dist + cable_cost
        
        # Nominal total capital costs including installation and miscellaneous
        # costs (capex)
        capex = cap / (1.0 - install_cost - misc_capex_cost) 

        ongoing_capex = op_maint_cost * capex
        decommish_capex = decom * capex / disc_time
        npv = 0
        levelized_cost_num = 0
        levelized_cost_denom = 0
        # Calculate the total NPV summation over the lifespan of the wind farm
        for year in range(1, time + 1):
            # The revenue in the current time period
            rev = energy_val * dollar_per_kwh
            # Calcuate the first component of the NPV equation
            comp_one = (rev - ongoing_capex) / disc_const**year
            # Add this years NPV value to the running total
            npv = npv + (comp_one - decommish_capex - capex)
            # Calculate the numerator value for levelized cost of energy
            levelized_cost_num = levelized_cost_num + (
                    (ongoing_capex / disc_const**year) + 
                    decommish_capex + capex)
            # Calculate the denominator value for levelized cost of energy
            levelized_cost_denom = levelized_cost_denom + (energy_val /
                    disc_const**year) 
        
        # Calculate the levelized cost of energy
        levelized_cost = levelized_cost_num / levelized_cost_denom
        # The amount of CO2 not released into the atmosphere, with the constant
        # conversion factor provided in the users guide by Rob Griffin
        carbon_emissions = 6.8956e-4 * energy_val
        
        feat.SetField(npv_index, npv)
        feat.SetField(levelized_index, levelized_cost)
        feat.SetField(co2_index, carbon_emissions)
        
        wind_energy_layer.SetFeature(feat)

    wind_energy_layer.SyncToDisk()

    npv_uri = os.path.join(output_dir, 'npv.tif')
    levelized_uri = os.path.join(output_dir, 'levelized.tif')
    carbon_uri = os.path.join(output_dir, 'carbon_emissions.tif')
   
    uri_list = [npv_uri, levelized_uri, carbon_uri]
    field_list = ['NPV', 'LevCost', 'CO2']
    out_nodata = float(np.finfo(np.float).tiny)
    
    for uri, field in zip(uri_list, field_list):
        # Create a raster for the points to be vectorized to 
        LOGGER.info('Creating Output raster : %s', uri)
        output_ds = raster_utils.create_raster_from_vector_extents(
            30, 30, gdal.GDT_Float32, out_nodata, uri, wind_energy_points) 

        # Interpolate and vectorize the points field onto a gdal dataset
        LOGGER.info('Vectorizing the points from the %s field', field)
        raster_utils.vectorize_points(
                wind_energy_points, field, output_ds)
        
    LOGGER.info('Leaving Wind Energy Valuation Core')

def point_to_polygon_distance(poly_ds, point_ds):
    """Calculates the distances from points in a point geometry shapefile to the
        nearest polygon from a polygon shapefile. Both datasources must be
        projected in meters
    
        poly_ds - an OGR polygon geometry datasource projected in meters
        point_ds - an OGR point geometry datasource projected in meters

        returns - a list of the distances from each point"""

    LOGGER.info('Loading the polygons into Shapely')
    poly_layer = poly_ds.GetLayer()
    poly_list = []
    for poly_feat in poly_layer:
        poly_wkt = poly_feat.GetGeometryRef().ExportToWkt()
        shapely_polygon = shapely.wkt.loads(poly_wkt)
        poly_list.append(shapely_polygon.simplify(0.01, preserve_topology=False))

    LOGGER.info('Get the collection of polygon geometries by taking the union')
    polygon_collection = shapely.ops.unary_union(poly_list)

    LOGGER.info('Loading the points into shapely')
    point_layer = point_ds.GetLayer()
    point_list = []
    for point_feat in point_layer:
        point_wkt = point_feat.GetGeometryRef().ExportToWkt()
        shapely_point = shapely.wkt.loads(point_wkt)
        point_list.append(shapely_point)

    LOGGER.info('find distances')
    distances = []
    for point in point_list:
        # Get the distance in meters and convert to km
        point_dist = point.distance(polygon_collection) / 1000.0
        distances.append(point_dist)

    LOGGER.debug('Distance List Length : %s', len(distances))
    point_layer.ResetReading()
    poly_layer.ResetReading()

    return distances

def add_field_to_shape_given_list(shape_ds, value_list, field_name):
    """Addes a field and a value to a given shapefile from a list of values. The
        list of values must be the same size as the number of features in the 
        shape

        shape_ds - an OGR datasource 
        value_list - a list of values that is the same length as there are
            features in 'shape_ds'
        field_name - a String for the name of the new field

        returns - the datasource 'shape_ds' with a new field and values"""
    LOGGER.info('Entering add_field_to_shape_given_list')
    layer = shape_ds.GetLayer()

    LOGGER.info('Creating new field')
    new_field = ogr.FieldDefn(field_name, ogr.OFTReal)
    layer.CreateField(new_field)

    value_iterator = 0
    LOGGER.debug('Length of value_list : %s', len(value_list))
    LOGGER.debug('Feature Count : %s', layer.GetFeatureCount())
    LOGGER.info('Adding values to new field for each point')
    for feat in layer:
        field_index = feat.GetFieldIndex(field_name)
        feat.SetField(field_index, value_list[value_iterator])
        layer.SetFeature(feat)
        value_iterator = value_iterator + 1
    
    LOGGER.debug('value iterator : %s', value_iterator)
    layer.ResetReading()
    layer.SyncToDisk()
     
    return shape_ds

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
        points_list.append([float(val['long']), float(val['lati'])])

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

def get_dictionary_from_shape(shape):
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
    feat_dict = {}

    for feat in layer:    
        geom = feat.GetGeometryRef()
        x_location = geom.GetX()
        y_location = geom.GetY()
        feat_dict[(x_location, y_location)] = {}
        for field_index in range(feat.GetFieldCount()):
            field_defn = feat.GetFieldDefnRef(field_index)
            field_name = field_defn.GetNameRef()
            feat_dict[(x_location, y_location)][field_name] = feat.GetField(
                    field_index)

    return feat_dict 
