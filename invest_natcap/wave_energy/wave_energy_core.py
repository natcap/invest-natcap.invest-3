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
from bisect import bisect

from invest_natcap.dbfpy import dbf
from invest_natcap import raster_utils
from invest_natcap.invest_core import invest_core

LOGGER = logging.getLogger('wave_energy_core')

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
    args['wave_base_data'] - a dictionary of seastate bin data with the ranges
                             of period and height. The dictionary has the 
                             following structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }
    args['analysis_area'] - a point geometry shapefile representing the 
                            relevant WW3 points
    args['analysis_area_extract'] - a polygon geometry shapefile encompassing 
                                    the broader range of interest.
    args['machine_perf'] - a dictionary that holds the machine performance
                           information with the following keys and structure:
                           machine_perf['periods'] - [1,2,3,...]
                           machine_perf['heights'] - [.5,1,1.5,...]
                           machine_perf['bin_matrix'] - [[1,2],[5,6],...].
    args['machine_param'] - a dictionary which holds the machine 
                            parameter values.
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
    intermediate_dir = os.path.join(workspace_dir, 'Intermediate')
    #Output Directory path to store output rasters
    output_dir = os.path.join(workspace_dir, 'Output')
    #Path for clipped wave point shapefile holding wave attribute information
    clipped_wave_shape_path = \
        intermediate_dir + os.sep + 'WEM_InputOutput_Pts.shp'
    #Paths for wave energy and wave power raster
    wave_energy_unclipped_path = os.path.join(intermediate_dir, 
                                              'capwe_mwh_unclipped.tif')
    wave_power_unclipped_path = os.path.join(intermediate_dir,
                                             'wp_kw_unclipped.tif')
    wave_energy_path = os.path.join(output_dir, 'capwe_mwh.tif')
    wave_power_path = os.path.join(output_dir, 'wp_kw.tif')
    #Paths for wave energy and wave power percentile rasters
    wp_rc_path = os.path.join(output_dir, 'wp_rc.tif')
    capwe_rc_path = os.path.join(output_dir, 'capwe_rc.tif')
    global_dem = args['dem']
    #Set nodata value and datatype for new rasters
    nodata = 0
    datatype = gdal.GDT_Float32
    #Since the global dem is the finest resolution we get as an input,
    #use its pixel sizes as the sizes for the new rasters
    dem_gt = global_dem.GetGeoTransform()
    #Set the source projection for a coordinate transformation
    #to the input projection from the wave watch point shapefile
    analysis_area_sr = args['analysis_area'].GetLayer(0).GetSpatialRef()
    #Holds any temporary files we want to clean up at the end of the model run
    file_list = []
    #This if statement differentiates between having an AOI or doing a broad
    #run on all the wave watch points specified by args['analysis_area'].
    if 'aoi' in args:
        #There is an AOI, so we need to reproject WWIII points into that the
        #output can be in the same projection as the AOI.

        #Temporary shapefile path needed for an intermediate step when
        #changing the projection
        projected_wave_shape_path = \
            intermediate_dir + os.sep + 'projected_wave_data.shp'
        file_list.append(projected_wave_shape_path)
        #The polygon shapefile that specifies the area of interest
        aoi_shape = args['aoi']
        
        #Set the wave data shapefile to the same projection as the 
        #area of interest
        projected_wave_shape = change_shape_projection(args['analysis_area'], \
                                   aoi_shape.GetLayer(0).GetSpatialRef(), \
                                   projected_wave_shape_path)

        #Clip the wave data shape by the bounds provided from the 
        #area of interest
        clipped_wave_shape = clip_shape(projected_wave_shape, aoi_shape, \
                                        clipped_wave_shape_path)
        
        #Create a coordinate transformation from the given
        #WWIII point shapefile (args['analysis_area']), to the 
        #area of interest's projection (args['aoi'])
        aoi_sr = aoi_shape.GetLayer(0).GetSpatialRef()
        coord_trans, coord_trans_opposite = \
            get_coordinate_transformation(analysis_area_sr, aoi_sr)

        #Get the size of the pixels in meters, to be used for creating 
        #projected wave power and wave energy capacity rasters
        pixel_xsize, pixel_ysize = \
            pixel_size_helper(clipped_wave_shape, coord_trans, \
                              coord_trans_opposite, global_dem)
        
        #Close file as it is no longer used
        projected_wave_shape.Destroy()
        LOGGER.debug('X pixel size in meters : %f', pixel_xsize)
        LOGGER.debug('Y pixel size in meters : %f', pixel_ysize)

    else:
        #If no AOI, we can use the pixel size directly from the DEM, but this
        #is necessary to make the following while loop simpler.

        #The polygon shapefile that specifies the broader area of interest
        aoi_shape = args['analysis_area_extract']

        #Not sure if this is needed, as aoi_shape is already an outline 
        #of analysis_area
        clipped_wave_shape = clip_shape(args['analysis_area'], aoi_shape, \
                                        clipped_wave_shape_path)

        #Set the pixel size to that of DEM, to be used for creating rasters
        pixel_xsize, pixel_ysize = \
            float(dem_gt[1]), np.absolute(float(dem_gt[5]))

        #Create a coordinate transformation, because it is expected below
        aoi_sr = aoi_shape.GetLayer(0).GetSpatialRef()
        coord_trans, coord_trans_opposite = \
            get_coordinate_transformation(analysis_area_sr, aoi_sr)

    #We do all wave power calculations by manipulating the fields in
    #the wave data shapefile, thus we need to add proper depth values
    #from the raster DEM
    LOGGER.debug('Adding a depth field to the shapefile from the DEM raster')
    dem_matrix = global_dem.GetRasterBand(1).ReadAsArray()

    #Create a new field for the depth attribute
    field_defn = ogr.FieldDefn('DEPTH_M', ogr.OFTReal)

    clipped_wave_layer = clipped_wave_shape.GetLayer(0)
    clipped_wave_layer.ResetReading()
    clipped_wave_layer.CreateField(field_defn)
    feature = clipped_wave_layer.GetNextFeature()

    #For all the features (points) add the proper depth value from the DEM
    while feature is not None:
        depth_index = feature.GetFieldIndex('DEPTH_M')
        geom = feature.GetGeometryRef()
        geom_x, geom_y = geom.GetX(), geom.GetY()

        #Transform two points into meters
        point_decimal_degree = \
            coord_trans_opposite.TransformPoint(geom_x, geom_y)

        #To get proper depth value we must index into the dem matrix
        #by getting where the point is located in terms of the matrix
        i = int((point_decimal_degree[0] - dem_gt[0]) / dem_gt[1])
        j = int((point_decimal_degree[1] - dem_gt[3]) / dem_gt[5])
        depth = dem_matrix[j][i]
        feature.SetField(int(depth_index), float(depth))
        clipped_wave_layer.SetFeature(feature)
        feature.Destroy()
        feature = clipped_wave_layer.GetNextFeature()

    dem_matrix = None

    LOGGER.debug('Finished adding depth field to shapefile from DEM raster')

    #Generate an interpolate object for wave_energy_capacity
    LOGGER.debug('Interpolating machine performance table')

    energy_interp = wave_energy_interp(args['wave_base_data'], \
                                       args['machine_perf'])

    #Create a dictionary with the wave energy capacity sums from each location
    LOGGER.debug('Summing the wave energy capacity at each wave farm')
    LOGGER.info('Calculating Captured Wave Energy.')
    energy_cap = \
        compute_wave_energy_capacity(
        args['wave_base_data'], energy_interp, args['machine_param'])

    #Add the sum as a field to the shapefile for the corresponding points
    LOGGER.debug('Adding the wave energy sums to the WaveData shapefile')
    captured_wave_energy_to_shape(energy_cap, clipped_wave_shape)

    #Calculate wave power for each wave point and add it as a field 
    #to the shapefile
    LOGGER.debug('Calculating wave power for each farm site')
    LOGGER.info('Calculating Wave Power.')
    clipped_wave_shape = wave_power(clipped_wave_shape)

    #Reset the iterator head for the aoi_shape's layer so that it can properly
    #iterate over the features.  NOTE: A better solution to this issue would be
    #to handle shapefiles like Rich and I just did in
    #raster_utils.create_raster_from_vector_extents, where we solved this issue
    #by not iterating over the features but calling them specifically with their
    #index which we got from getting the feature count.
    aoi_layer = aoi_shape.GetLayer(0)
    aoi_layer.ResetReading()

    #Create blank rasters bounded by the shape file of analyis area
    wave_energy_raster = \
        raster_utils.create_raster_from_vector_extents(pixel_xsize, \
           pixel_ysize, datatype, nodata, wave_energy_unclipped_path, \
           aoi_shape)

    wave_power_raster = \
        raster_utils.create_raster_from_vector_extents(pixel_xsize, \
            pixel_ysize, datatype, nodata, wave_power_unclipped_path, \
            aoi_shape)

    #Interpolate wave energy and wave power from the shapefile over the rasters
    LOGGER.debug('Interpolate wave power and wave energy capacity onto rasters')
    raster_utils.vectorize_points(
            clipped_wave_shape, 'CAPWE_MWHY', wave_energy_raster)
    raster_utils.vectorize_points(
            clipped_wave_shape, 'WE_kWM', wave_power_raster)

    #Clip the wave energy and wave power rasters so that they are confined 
    #to the AOI
    clipped_wave_power_raster = clip_raster_from_polygon(aoi_shape, \
        wave_power_raster, wave_power_path)
    clipped_wave_energy_raster = clip_raster_from_polygon(aoi_shape, \
        wave_energy_raster, wave_energy_path)
    #Flush the cache to make sure all data has been saved to disk and nothing
    #is waiting in a buffer to be written
    clipped_wave_energy_raster.FlushCache()
    clipped_wave_power_raster.FlushCache()

    raster_utils.calculate_raster_stats(clipped_wave_power_raster)
    raster_utils.calculate_raster_stats(clipped_wave_energy_raster)

    #Create the percentile rasters for wave energy and wave power
    #These values are hard coded in because it's specified explicitly in  
    #the user's guide what the percentile ranges are and what the units will be.
    percentiles = [25, 50, 75, 90]
    capwe_units_short = ' (MWh/yr)'
    capwe_units_long = ' megawatt hours per year (MWh/yr)'
    wp_units_short = ' (kW/m)'
    wp_units_long = ' wave power per unit width of wave crest length (kW/m)'
    starting_percentile_range = '1'
    capwe_rc = \
       create_percentile_rasters(clipped_wave_energy_raster, capwe_rc_path, \
                                 capwe_units_short, capwe_units_long, \
                                 starting_percentile_range, percentiles, nodata)
    wp_rc_raster = \
        create_percentile_rasters(clipped_wave_power_raster, wp_rc_path, \
                                  wp_units_short, wp_units_long, \
                                  starting_percentile_range, percentiles, \
                                  nodata)

    #Clean up Shapefiles and Rasters
    clipped_wave_shape.Destroy()
    aoi_shape.Destroy()
    wave_energy_raster = None
    wave_power_raster = None
    clipped_wave_energy_raster = None
    clipped_wave_power_raster = None
    wp_rc_raster = None
    capwe_rc = None
    
    #Clean up any temporary files that the user does not need to know about
    file_cleanup_handler(file_list)

def file_cleanup_handler(file_list):
    """Handles removing any shape files and any necessary extensions
    
    file_list - A list of strings representing paths to shape files
    
    returns - nothing
    """
    LOGGER.debug('Cleaning up files : %s', file_list)
    for file_name in file_list:
        LOGGER.debug('Cleaning up file_name : %s', file_name)    
        #Clean up temporary files on disk
        #Creating a match pattern that finds the last directory seperator
        #in a path like '/home/blath/../name_of_shape.*' and focuses just on the
        #string after that separator and before the '.' extension.
        pattern = file_name[file_name.rfind(os.sep) + 1:len(file_name) - 4] + ".*"
        directory = file_name[0:file_name.rfind(os.sep) + 1]
        logging.debug('Regex file_name pattern : %s', pattern)
        for item in os.listdir(directory):
            if re.search(pattern, item):
                try:
                    os.remove(os.path.join(directory, item))
                except WindowsError:
                    LOGGER.warn("Warning, could not delete the file %s" % \
                                    os.path.join(directory, item))

def pixel_size_helper(shape, coord_trans, coord_trans_opposite, global_dem):
    """This function helps retrieve the pixel sizes of the global DEM 
    when given an area of interest that has a certain projection.
    
    shape - A point shapefile datasource indicating where in the world we
            are interested in
    coord_trans - A coordinate transformation
    coord_trans_opposite - A coordinate transformation that transforms in the
                           opposite direction of 'coord_trans'
    global_dem - The global DEM dataset to get the pixel size from
    
    returns - A tuple of the x and y pixel sizes of the global DEM 
              given in the units of what 'shape' is projected in
    """
    #Get a point in the clipped shape to determine output grid size
    feat = shape.GetLayer(0).GetNextFeature()
    geom = feat.GetGeometryRef()
    reference_point_x = geom.GetX()
    reference_point_y = geom.GetY()
    
    #Convert the point from meters to geom_x/long
    reference_point_latlng = \
        coord_trans_opposite.TransformPoint(reference_point_x, \
                                            reference_point_y)
        
    #Get the size of the pixels in meters, to be used for creating rasters
    pixel_size_tuple = \
        raster_utils.pixel_size_based_on_coordinate_transform(global_dem, coord_trans,
                                                reference_point_latlng)
    return pixel_size_tuple

def get_coordinate_transformation(source_sr, target_sr):
    """This function takes a source and target spatial reference and creates
    a coordinate transformation from source to target, and one from target 
    to source.
    
    source_sr - A spatial reference
    target_sr - A spatial reference
    
    return - A tuple, coord_trans (source to target) and coord_trans_opposite 
             (target to source)
    """
    coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
    coord_trans_opposite = osr.CoordinateTransformation(target_sr, source_sr)
    return (coord_trans, coord_trans_opposite)
    
def create_percentile_rasters(raster_dataset, output_path, units_short, \
                              units_long, start_value, percentile_list, nodata):
    """Creates a percentile (quartile) raster based on the raster_dataset. An 
    attribute table is also constructed for the raster_dataset that displays the
    ranges provided by taking the quartile of values.  
    The following inputs are required:
    
    raster_dataset - A gdal raster dataset with data of type integer
    output_path - A String for the destination of new raster
    units_short - A String that represents the shorthand for the units of the
                  raster values (ex: kW/m)
    units_long - A String that represents the description of the units of the
                 raster values (ex: wave power per unit width of 
                 wave crest length (kW/m))
    start_value - A String representing the first value that goes to the 
                  first percentile range (start_value - percentile_one)
                  
    return - The new gdal raster
    """
    #If the output_path is already a file, delete it
    if os.path.isfile(output_path):
        os.remove(output_path)
    #Create a blank raster from raster_dataset
    percentile_raster = \
        raster_utils.new_raster_from_base(raster_dataset, output_path, \
                                             'GTiff', 0, gdal.GDT_Int32)
    #Get raster bands
    percentile_band = percentile_raster.GetRasterBand(1)
    dataset_band = raster_dataset.GetRasterBand(1)
    def raster_percentile(band):
        """Operation to use in vectorize1ArgOp that takes
        the pixels of 'band' and groups them together based on 
        their percentile ranges.
        
        band - A gdal raster band
        
        returns - An integer that places each pixel into a group
        """
        return bisect(percentiles, band)

    #Read in the values of the raster we want to get percentiles from
    matrix = np.array(dataset_band.ReadAsArray())
    #Flatten the 2D numpy array into a 1D numpy array
    dataset_array = matrix.flatten()
    #Create a mask that makes all nodata values invalid.  Do this because
    #having a bunch of nodata values will muttle the results of getting the
    #percentiles
    dataset_mask = np.ma.masked_array(dataset_array, \
                                      mask=dataset_array == nodata)
    #Get all of the non-masked (non-nodata) data
    dataset_comp = np.ma.compressed(dataset_mask)
    #Get the percentile marks
    percentiles = get_percentiles(dataset_comp, percentile_list)
    LOGGER.debug('percentiles_list : %s', percentiles)
    #Get the percentile ranges
    percentile_ranges = create_percentile_ranges(percentiles, units_short, \
                                                units_long, start_value)
    #Add the start_value to the beginning of the percentiles so that any value
    #before the start value is set to nodata (zero)
    percentiles.insert(0, int(start_value))
    #Classify the pixels of raster_dataset into groups and write 
    #then to output band
    invest_core.vectorize1ArgOp(dataset_band, raster_percentile, \
                                percentile_band)
    #Initialize a list that will hold pixel counts for each group
    pixel_count = np.zeros(len(percentile_list) + 1)
    #Read in percentile raster so that we can get the count of each group
    perc_array = percentile_band.ReadAsArray()
    percentile_groups = np.arange(1, len(percentiles) + 1)
    for percentile_class in percentile_groups:
        #This line of code takes the numpy array 'perc_array', which holds 
        #the values from the percentile_band after being grouped, and checks 
        #to see where the values are equal to a certain a group. 
        #This check gives an array of indices where the case was true, 
        #so we take the size of that array to give us the number of pixels 
        #that fall in that group.
        pixel_count[percentile_class - 1] = \
            np.where(perc_array == percentile_class)[0].size

    logging.debug('number of pixels per group: : %s', pixel_count)
    #Generate the attribute table for the percentile raster
    create_attribute_table(output_path, percentile_ranges, pixel_count)

    #calculate min, max, std for visualization in arc
    raster_utils.calculate_raster_stats(percentile_raster)

    return percentile_raster

def get_percentiles(value_list, percentile_list):
    """Creates a list of integers of the percentile marks
    
    value_list - A list of numbers
    percentile_list - A list of ascending integers of the desired
                      percentiles
                      
    returns - A list of integers which are the percentile marks
    """
    pct_list = []
    for percentile in percentile_list:
        pct_list.append(int(stats.scoreatpercentile(value_list, percentile)))
    return pct_list

def create_percentile_ranges(percentiles, units_short, units_long, start_value):
    """Constructs the percentile ranges as Strings, with the first
    range starting at 1 and the last range being greater than the last
    percentile mark.  Each string range is stored in a list that gets returned
    
    percentiles - A list of the percentile marks in ascending order
    units_short - A String that represents the shorthand for the units of the
                  raster values (ex: kW/m)
    units_long - A String that represents the description of the units of the
                 raster values (ex: wave power per unit width of 
                wave crest length (kW/m))
    start_value - A String representing the first value that goes to the 
                 first percentile range (start_value - percentile_one)
                  
    returns - A list of Strings representing the ranges of the percentiles
    """
    length = len(percentiles)
    range_values = []
    #Add the first range with the starting value and long description of units
    #This function will fail and cause an error if the percentile list is empty
    range_first = start_value + ' - ' + str(percentiles[0]) + units_long
    range_values.append(range_first)
    for index in range(length - 1):
        range_values.append(str(percentiles[index]) + ' - ' + \
                            str(percentiles[index + 1]) + units_short)
    #Add the last range to the range of values list
    range_last = 'Greater than ' + str(percentiles[length - 1]) + units_short
    range_values.append(range_last)
    LOGGER.debug('range_values : %s', range_values)
    return range_values

def create_attribute_table(raster_uri, percentile_ranges, counter):
    """Creates an attribute table of type '.vat.dbf'.  The attribute table
    created is tied to the dataset of the raster_uri provided as input. 
    The table has 3 fields (VALUE, COUNT, VAL_RANGE) where VALUE acts as
    an ID, COUNT is the number of pixels, and VAL_RANGE is the corresponding
    percentile range
    
    raster_uri - A String of the raster file the table should be associated with
    percentile_ranges - A list of Strings representing the percentile ranges
    counter - A list of integers that represent the pixel count
    
    returns - nothing
    """
    #Create a new dbf file with the same name as the GTiff plus a .vat.dbf
    output_path = raster_uri + '.vat.dbf'
    #If the dbf file already exists, delete it
    if os.path.isfile(output_path):
        os.remove(output_path)
    #Create new table, making readOnly explicit
    dataset_attribute_table = dbf.Dbf(output_path, new = True, readOnly = False)
    #Set the defined fields for the table
    dataset_attribute_table.addField(
                 #integer field
                 ("VALUE", "N", 9),
                 #integer field
                 ("COUNT", "N", 9),
                 #character field, I think header names need to be short?
                 ("VAL_RANGE", "C", 254))
    #Add all the records
    for id_value in range(len(percentile_ranges)):
        logging.debug('id_value: %s', id_value)
        rec = dataset_attribute_table.newRecord()
        rec["VALUE"] = id_value + 1
        rec["COUNT"] = int(counter[id_value])
        rec["VAL_RANGE"] = percentile_ranges[id_value]
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
    field_defn = ogr.FieldDefn('WE_kWM', ogr.OFTReal)
    layer.CreateField(field_defn)
    layer.ResetReading()
    feat = layer.GetNextFeature()
    #For every feature (point) calculate the wave power and add the value
    #to itself in a new field
    while feat is not None:
        height_index = feat.GetFieldIndex('HSAVG_M')
        period_index = feat.GetFieldIndex('TPAVG_S')
        depth_index = feat.GetFieldIndex('DEPTH_M')
        wp_index = feat.GetFieldIndex('WE_kWM')
        height = feat.GetFieldAsDouble(height_index)
        period = feat.GetFieldAsDouble(period_index)
        depth = feat.GetFieldAsInteger(depth_index)

        depth = np.absolute(depth)
        #wave frequency calculation (used to calculate wave number k)
        tem = (2.0 * math.pi) / (period * alfa)
        #wave number calculation (expressed as a function of 
        #wave frequency and water depth)
        k = np.square(tem) / (grav * np.sqrt(np.tanh((np.square(tem)) * \
                                                     (depth / grav))))
        #Setting numpy overlow error to ignore because when np.sinh
        #gets a really large number it pushes a warning, but Rich
        #and Doug have agreed it's nothing we need to worry about.
        np.seterr(over='ignore')
        
        #wave group velocity calculation (expressed as a 
        #function of wave energy period and water depth)
        wave_group_velocity = \
            ((1 + ((2 * k * depth) / np.sinh(2 * k * depth))) * \
             np.sqrt((grav / k) * np.tanh(k * depth))) / 2
       
        #Reset the overflow error to print future warnings
        np.seterr(over='print')
       
        #wave power calculation
        wave_pow = (((swd * grav) / 16) * (np.square(height)) * \
                    wave_group_velocity) / 1000

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
        is not nodata, then pixel lies within polygon and the value 
        from 'raster' should be written out.
        
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
    invest_core.vectorize2ArgOp(raster.GetRasterBand(1), copy_band, \
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
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), in_layer.GetSpatialRef(), 
                                   in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the 
    #new shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd_def = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd_def.SetWidth(src_fd.GetWidth())
        fd_def.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd_def)
    LOGGER.debug('Binding Shapes Feature Count : %s', 
                 clip_layer.GetFeatureCount())
    LOGGER.debug('Shape to be Bounds Feature Count : %s', 
                 in_layer.GetFeatureCount())
    #Retrieve all the binding polygon features and save their cloned 
    #geometry references to a list
    clip_feat = clip_layer.GetNextFeature()
    clip_geom_list = []
    while clip_feat is not None:
        clip_geom = clip_feat.GetGeometryRef()
        #Get the spatial reference of the geometry to use in transforming
        source_sr = clip_geom.GetSpatialReference()
        #Retrieve the current point shapes feature and get it's 
        #geometry reference
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
        #Add geometry to list
        clip_geom_list.append(clip_geom.Clone())
        in_feat.Destroy()
        clip_feat.Destroy()
        clip_feat = clip_layer.GetNextFeature()

    in_layer.ResetReading()
    in_feat = in_layer.GetNextFeature()
    #For all the features in the current point shape (for all the points)
    #Check to see if they Intersect with any of the binding polygons geometry 
    #and if they do, copy that point and it's fields to the new shape
    while in_feat is not None:
        #Check to see if the point falls in any of the polygons
        for clip_geom in clip_geom_list:
            geom = in_feat.GetGeometryRef()
            #Intersection returns a new geometry if they intersect, null
            #otherwise.
            geom = geom.Intersection(clip_geom)
            if(geom.GetGeometryCount() + geom.GetPointCount()) != 0:
                #Create a new feature from the input feature and set 
                #its geometry
                out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
                out_feat.SetFrom(in_feat)
                out_feat.SetGeometryDirectly(geom)
                #For all the fields in the feature set the field values from 
                #the source field
                for fld_index2 in range(out_feat.GetFieldCount()):
                    src_field = in_feat.GetField(fld_index2)
                    out_feat.SetField(fld_index2, src_field)
    
                shp_layer.CreateFeature(out_feat)
                out_feat.Destroy()
                break
            
        in_feat.Destroy()
        in_feat = in_layer.GetNextFeature()

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
        reference_x = geom.GetX()
        reference_y = geom.GetY()
        points.append([reference_x, reference_y])
        geom = None
        shape_feat.Destroy()
        shape_feat = shape_layer.GetNextFeature()

    results = [points, values]
    return results

def wave_energy_interp(wave_data, machine_perf):
    """Generates a matrix representing the interpolation of the
    machine performance table using new ranges from wave watch data.
    
    wave_data - A dictionary holding the new x range (period) and 
                y range (height) values for the interpolation.  The
                dictionary has the following structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }
    machine_perf - a dictionary that holds the machine performance
                   information with the following keys and structure:
                   machine_perf['periods'] - [1,2,3,...]
                   machine_perf['heights'] - [.5,1,1.5,...]
                   machine_perf['bin_matrix'] - [[1,2,3,...],[5,6,7,...],...].
    
    returns - The interpolated matrix
    """
    #Get ranges and matrix for machine performance table
    x_range = np.array(machine_perf['periods'], dtype='f')
    y_range = np.array(machine_perf['heights'], dtype='f')
    z_matrix = np.array(machine_perf['bin_matrix'], dtype='f')
    #Get new ranges to interpolate to, from wave_data table
    new_x = wave_data['periods']
    new_y = wave_data['heights']
    #Interpolate machine performance table and return the interpolated matrix
    interp_z = raster_utils.interpolate_matrix(x_range, y_range, 
                                                    z_matrix, new_x, new_y)
    return interp_z

def compute_wave_energy_capacity(wave_data, interp_z, machine_param):
    """Computes the wave energy capacity for each point and
    generates a dictionary whos keys are the points (I,J) and whos value
    is the wave energy capacity.
    
    wave_data - A dictionary containing wave watch data with the following
                structure:
               {'periods': [1,2,3,4,...],
                'heights': [.5,1.0,1.5,...],
                'bin_matrix': { (i0,j0): [[2,5,3,2,...], [6,3,4,1,...],...],
                                (i1,j1): [[2,5,3,2,...], [6,3,4,1,...],...],
                                 ...
                                (in, jn): [[2,5,3,2,...], [6,3,4,1,...],...]
                              }
               }
    interp_z - A 2D array of the interpolated values for the machine
                performance table
    machine_param - A dictionary containing the restrictions for the machines
                    (CapMax, TpMax, HsMax)
                    
    returns - A dictionary representing the wave energy capacity at 
              each wave point
    """
    #It seems that the capacity max is already set to it's limit in
    #the machine performance table. However, if it needed to be
    #restricted the following line could be used:
    #interp_z = np.where(interp_z>cap_max, cap_max, interp_z)

    energy_cap = {}

    #Get the row,col headers (ranges) for the wave watch data
    #row is wave period label
    #col is wave height label
    wave_periods = wave_data['periods']
    wave_heights = wave_data['heights']

    #Get the machine parameter restriction values
    cap_max = float(machine_param['capmax'])
    period_max = float(machine_param['tpmax'])
    height_max = float(machine_param['hsmax'])

    #Set position variables to use as a check and as an end
    #point for rows/cols if restrictions limit the ranges
    period_max_index = -1
    height_max_index = -1

    #Using the restrictions find the max position (index) for period and height
    #in the wave_periods/wave_heights ranges

    for index_pos, value in enumerate(wave_periods):
        if (value > period_max):
            period_max_index = index_pos
            break

    for index_pos, value in enumerate(wave_heights):
        if (value > height_max):
            height_max_index = index_pos
            break

    LOGGER.debug('Position of max period : %f', period_max_index)
    LOGGER.debug('Position of max height : %f', height_max_index)

    #For all the wave watch points, multiply the occurence matrix by the 
    #interpolated machine performance matrix to get the captured wave energy
    for key, val in wave_data['bin_matrix'].iteritems():
        #Convert all values to type float
        temp_matrix = np.array(val, dtype='f')
        mult_matrix = np.multiply(temp_matrix, interp_z)
        #Set any value that is outside the restricting ranges provided by 
        #machine parameters to zero
        if period_max_index != -1:
            mult_matrix[:, period_max_index:] = 0
        if height_max_index != -1:
            mult_matrix[height_max_index:, :] = 0

        #Since we are doing a cubic interpolation there is a possibility we
        #will have negative values where they should be zero. So here
        #we drive any negative values to zero.
        mult_matrix[mult_matrix < 0] = 0
        #valid_array = np.where(mult_matrix < 0, 0, mult_matrix)

        #Sum all of the values from the matrix to get the total 
        #captured wave energy and convert into mega watts
        sum_we = (mult_matrix.sum() / 1000)
        #sum_we = (valid_array.sum() / 1000)
        energy_cap[key] = sum_we

    return energy_cap

def captured_wave_energy_to_shape(energy_cap, wave_shape):
    """Adds each captured wave energy value from the dictionary
    energy_cap to a field of the shapefile wave_shape. The values are
    set corresponding to the same I,J values which is the key of the
    dictionary and used as the unique identier of the shape.
    
    energy_cap - A dictionary with keys (I,J), representing the 
                 wave energy capacity values.
    wave_shape  - A point geometry shapefile to write the new field/values to
    
    returns - Nothing    
    """
    wave_layer = wave_shape.GetLayer(0)
    #Incase the layer has already been read through earlier in the program
    #reset it to start from the beginning
    wave_layer.ResetReading()
    #Create a new field for the shapefile
    field_def = ogr.FieldDefn('CAPWE_MWHY', ogr.OFTReal)
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

        index = feat.GetFieldIndex('CAPWE_MWHY')
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
    args['wave_data_shape'] - A file path to the shapefile generated from the 
                              biophysical run which holds various attributes 
                              of each wave farm.
    args['number_machines'] - An integer representing the number of machines 
                              to make up a farm.
    args['machine_econ'] - A dictionary holding the machine economic parameters.
    args['land_gridPts'] - A dictionary holidng the landing point and grid point
                           information and location.
    args['global_dem'] - A raster of the global DEM

    returns - Nothing
    """
    #Set variables for common output paths
    #Workspace Directory path
    workspace_dir = args['workspace_dir']
    #Output Directory path to store output rasters
    output_dir = workspace_dir + os.sep + 'Output'
    #Output path for landing point shapefile
    land_pt_path = output_dir + os.sep + 'LandPts_prj.shp'
    #Output path for grid point shapefile
    grid_pt_path = output_dir + os.sep + 'GridPts_prj.shp'
    #Output path for the projected net present value raster
    raster_projected_path = os.path.join(
            workspace_dir, 'Intermediate/npv_not_clipped.tif')
    #Path for the net present value percentile raster
    npv_rc_path = output_dir + os.sep + 'npv_rc.tif'
    #The datasource of the modified wave watch 3 shapefile from
    #the output of the biophysical run
    wave_data_shape = args['wave_data_shape']
    #Since the global_dem is the only input raster, we base the pixel
    #size of our output raster from the global_dem
    dem = args['global_dem']
    #Create a coordinate transformation for lat/long to meters
    srs_prj = osr.SpatialReference()
    #Using 'WGS84' as our well known lat/long projection
    srs_prj.SetWellKnownGeogCS("WGS84")
    wgs_84_sr = srs_prj
    wave_data_sr = wave_data_shape.GetLayer(0).GetSpatialRef()
    coord_trans, coord_trans_opposite = \
        get_coordinate_transformation(wgs_84_sr, wave_data_sr)
    #Get the size of the pixels in meters
    pixel_xsize, pixel_ysize = \
        pixel_size_helper(wave_data_shape, coord_trans, coord_trans_opposite, 
                          dem)

    LOGGER.debug('X pixel size of DEM : %f', pixel_xsize)
    LOGGER.debug('Y pixel size of DEM : %f', pixel_ysize)
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

    #Make a point shapefile for landing points.
    LOGGER.info('Creating Landing Points Shapefile.')
    landing_shape = build_point_shapefile('ESRI Shapefile', 'landpoints', \
                                          land_pt_path, land_pts, wave_data_sr, 
                                          coord_trans)
    #Make a point shapefile for grid points
    LOGGER.info('Creating Grid Points Shapefile.')
    grid_shape = build_point_shapefile('ESRI Shapefile', 'gridpoints', \
                                       grid_pt_path, grid_pts, wave_data_sr, 
                                       coord_trans)
    #Get the coordinates of points of wave_data_shape, landing_shape,
    #and grid_shape
    we_points = get_points_geometries(wave_data_shape)
    landing_points = get_points_geometries(landing_shape)
    grid_point = get_points_geometries(grid_shape)
    LOGGER.info('Calculating Distances.')
    #Calculate the distances between the relative point groups
    wave_to_land_dist, wave_to_land_id = calculate_distance(we_points, \
                                                            landing_points)
    land_to_grid_dist, land_to_grid_id = calculate_distance(landing_points, \
                                                            grid_point)
    wave_data_layer = wave_data_shape.GetLayer(0)
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
        
        annual_revenue - A numpy array of the annual revenue for the 
                         first 25 years
        annual_cost - A numpy array of the annual cost for the first 25 years
        
        returns - The Total NPV which is the sum of all 25 years
        """
        npv = []
        for i in range(len(time)):
            npv.append(rho ** i * (annual_revenue[i] - annual_cost[i]))
        return sum(npv)
    
    #Add Net Present Value field, Total Captured Wave Energy field, and
    #Units field to shapefile
    for field_name in ['NPV_25Y', 'CAPWE_ALL', 'UNITS']:
        field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)
        wave_data_layer.CreateField(field_defn)
    wave_data_layer.ResetReading()
    feat_npv = wave_data_layer.GetNextFeature()
    #For all the wave farm sites, calculate npv and write to shapefile
    LOGGER.info('Calculating the Net Present Value.')
    while feat_npv is not None:
        depth_index = feat_npv.GetFieldIndex('DEPTH_M')
        wave_to_land_index = feat_npv.GetFieldIndex('W2L_MDIST')
        land_to_grid_index = feat_npv.GetFieldIndex('L2G_MDIST')
        captured_wave_energy_index = feat_npv.GetFieldIndex('CAPWE_MWHY')
        npv_index = feat_npv.GetFieldIndex('NPV_25Y')
        capwe_all_index = feat_npv.GetFieldIndex('CAPWE_ALL')
        units_index = feat_npv.GetFieldIndex('UNITS')

        depth = feat_npv.GetFieldAsDouble(depth_index)
        wave_to_land = feat_npv.GetFieldAsDouble(wave_to_land_index)
        land_to_grid = feat_npv.GetFieldAsDouble(land_to_grid_index)
        captured_wave_energy = \
            feat_npv.GetFieldAsDouble(captured_wave_energy_index)
        capwe_all_result = captured_wave_energy * units
        #Create a numpy array of length 25, filled with the captured wave energy
        #in kW/h. Represents the lifetime of this wave farm.
        captured_we = np.ones(len(time)) * int(captured_wave_energy) * 1000.0
        #It is expected that there is no revenue from the first year
        captured_we[0] = 0
        #Compute values to determine NPV
        lenml = 3.0 * np.absolute(depth)
        install_cost = units * cap_max * capital_cost
        mooring_cost = smlpm * lenml * cml * units
        trans_cost = \
            (wave_to_land * cul / 1000.0) + (land_to_grid * col / 1000.0)
        initial_cost = install_cost + mooring_cost + trans_cost
        annual_revenue = price * units * captured_we
        annual_cost = omc * captured_we * units
        #The first year's costs are the initial start up costs
        annual_cost[0] = initial_cost

        npv_result = npv_wave(annual_revenue, annual_cost) / 1000.0
        feat_npv.SetField(npv_index, npv_result)
        feat_npv.SetField(capwe_all_index, capwe_all_result)
        feat_npv.SetField(units_index, units)

        wave_data_layer.SetFeature(feat_npv)
        feat_npv.Destroy()
        feat_npv = wave_data_layer.GetNextFeature()

    datatype = gdal.GDT_Float32
    nodata = -100000
    #Create a blank raster from the extents of the wave farm shapefile
    LOGGER.debug('Creating Raster From Vector Extents')
    raster_utils.create_raster_from_vector_extents(pixel_xsize, pixel_ysize,
                                                     datatype, nodata, 
                                                     raster_projected_path, 
                                                     wave_data_shape)
    LOGGER.debug('Completed Creating Raster From Vector Extents')
    npv_raster = gdal.Open(raster_projected_path, GA_Update)
    
    #Interpolate the NPV values based on the dimensions and 
    #corresponding points of the raster, then write the interpolated 
    #values to the raster
    LOGGER.info('Generating Net Present Value Raster.')
        
    raster_utils.vectorize_points(wave_data_shape, 'NPV_25Y', npv_raster)
   
    convex_uri = os.path.join(workspace_dir, 'Intermediate/convex_hull.shp')
    # Create a shapefile that is the convex hull of our points so that we can
    # use it for masking and clipping
    get_convex_hull(wave_data_shape, 'convex_hull', convex_uri)
    
    convex_hull = ogr.Open(convex_uri)

    npv_out_uri = os.path.join(workspace_dir, 'Output/npv_usd.tif')
    # Clip the raster to the convex hull polygon
    raster_utils.clip_dataset(npv_raster, convex_hull, npv_out_uri)
    
    npv_raster = None
    npv_raster = gdal.Open(npv_out_uri)

    #Create the percentile raster for net present value
    percentiles = [25, 50, 75, 90]
    npv_rc = create_percentile_rasters(npv_raster, npv_rc_path, ' (US$)',
                                       ' thousands of US dollars (US$)', '1',
                                        percentiles, nodata)
    npv_rc = None
    npv_raster = None
    wave_data_shape.Destroy()
    LOGGER.debug('End of wave_energy_core.valuation')

def get_convex_hull(point_datasource, layer_name, output_uri):
    """This function finds the convex hull of a point shapefile and creates a
        new polygon shapefile based on the convex hull.

        point_datasource - an OGR point geometry datasource
        layer_name - a string for the output polygon datasources layer name
        output_uri - a URI for the output polygon datasource

        returns - Nothing"""

    # Get the Layer and reset the pointer to make sure it is looking at the
    # first feature
    layer = point_datasource.GetLayer()
    layer.ResetReading()
    
    # Create a geometry collection from all the points, which we will then get
    # the convex hull from
    point_collection = ogr.Geometry(ogr.wkbGeometryCollection)
    # Iterate over all the points and build up the geometry collection
    for index in range(layer.GetFeatureCount()):
        feature = layer.GetFeature(index)
        geometry = feature.GetGeometryRef()
        point_collection.AddGeometry(geometry)

    # Get the convex hull geometry
    convex_hull = point_collection.ConvexHull()

    # If the output_uri exists delete it
    if os.path.isfile(output_uri):
        os.remove(output_uri)
    # Create a new datasource for the convex hull polygon
    output_driver = ogr.GetDriverByName('ESRI Shapefile')
    output_datasource = output_driver.CreateDataSource(output_uri)

    output_layer = output_datasource.CreateLayer(
            layer_name, layer.GetSpatialRef(), ogr.wkbPolygon)

    # Creating a field so that the datasource has at least one field
    output_field = ogr.FieldDefn('ID', ogr.OFTReal)   
    output_layer.CreateField(output_field)

    output_feature = ogr.Feature(output_layer.GetLayerDefn())
    output_layer.CreateFeature(output_feature)
    
    field_index = output_feature.GetFieldIndex('ID')
    output_feature.SetField(field_index, 1)

    # Set the geometry for the feature as the convex hull polygon
    output_feature.SetGeometryDirectly(convex_hull)
    output_layer.SetFeature(output_feature)
    output_feature = None
    output_datasource = None

def build_point_shapefile(driver_name, layer_name, path, data, prj, 
                          coord_trans):
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
    #If the shapefile exists, remove it.
    if os.path.isfile(path):
        os.remove(path)
    #Make a point shapefile for landing points.
    driver = ogr.GetDriverByName(driver_name)
    data_source = driver.CreateDataSource(path)
    layer = data_source.CreateLayer(layer_name, prj, ogr.wkbPoint)
    field_defn = ogr.FieldDefn('Id', ogr.OFTInteger)
    layer.CreateField(field_defn)
    #For all of the landing points create a point feature on the layer
    for key, value in data.iteritems():
        latitude = value[0]
        longitude = value[1]
        geom = ogr.Geometry(ogr.wkbPoint)
        geom.AddPoint_2D(float(longitude), float(latitude))
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
    a numpy array as a point [x_location,y_location], which is returned 
    when all the features have been iterated through.
    
    shape - An OGR shapefile datasource
    
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

def change_shape_projection(shape_to_reproject, target_sr, output_path):
    """Changes the projection of a shapefile by creating a new shapefile 
    based on the projection passed in.  The new shapefile then copies all the 
    features and fields of the shapefile to reproject as its own. 
    The reprojected shapefile is written to 'outputpath' and is returned.
    
    shape_to_reproject - A shapefile to be copied and reprojected.
    target_sr - The desired projection as a SpatialReference from a WKT string.
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
    #Create a new shapefile with similar properties of the current 
    #point geometry shape
    shp_driver = ogr.GetDriverByName('ESRI Shapefile')
    shp_ds = shp_driver.CreateDataSource(shape_source)
    #Create the new layer for the shapefile using same name and geometry
    #type from shape_to_reproject, but different projection
    shp_layer = shp_ds.CreateLayer(in_defn.GetName(), target_sr, \
                                   in_defn.GetGeomType())
    #Get the number of fields in the current point shapefile
    in_field_count = in_defn.GetFieldCount()
    #For every field, create a duplicate field and add it to the new 
    #shapefiles layer
    for fld_index in range(in_field_count):
        src_fd = in_defn.GetFieldDefn(fld_index)
        fd_def = ogr.FieldDefn(src_fd.GetName(), src_fd.GetType())
        fd_def.SetWidth(src_fd.GetWidth())
        fd_def.SetPrecision(src_fd.GetPrecision())
        shp_layer.CreateField(fd_def)

    in_layer.ResetReading()
    #Get the spatial reference of the source layer to use in transforming
    source_sr = in_layer.GetSpatialRef()
    #Create a coordinate transformation
    coord_trans = osr.CoordinateTransformation(source_sr, target_sr)
    #Get the first feature from the shapefile
    in_feat = in_layer.GetNextFeature()
    #Copy all of the features in shape_to_reproject to the new shapefile
    while in_feat is not None:
        geom = in_feat.GetGeometryRef()
        #Transform the geometry into a format desired for the new projection
        geom.Transform(coord_trans)
        #Copy shape_to_reproject's feature and set as new shapes feature
        out_feat = ogr.Feature(feature_def=shp_layer.GetLayerDefn())
        out_feat.SetFrom(in_feat)
        out_feat.SetGeometry(geom)
        #For all the fields in the feature set the field values from the 
        #source field
        for fld_index2 in range(out_feat.GetFieldCount()):
            src_field = in_feat.GetField(fld_index2)
            out_feat.SetField(fld_index2, src_field)

        shp_layer.CreateFeature(out_feat)
        out_feat.Destroy()

        in_feat.Destroy()
        in_feat = in_layer.GetNextFeature()

    return shp_ds
