"""InVEST Carbon biophysical module at the "uri" level"""

import sys
import os
import math
import json
import logging
import shutil

from osgeo import gdal
from osgeo import ogr
import numpy

from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('carbon_biophysical')

def execute(args):
    execute_30(**args)

def execute_30(**args):
    """This function invokes the carbon model given URI inputs of files.
        It will do filehandling and open/create appropriate objects to 
        pass to the core carbon biophysical processing function.  It may write
        log, warning, or error messages to stdout.
        
        args - a python dictionary with at the following possible entries:
        args['workspace_dir'] - a uri to the directory that will write output
            and other temporary files during calculation. (required)
        args['suffix'] - a string to append to any output file name (optional)
        args['lulc_cur_uri'] - is a uri to a GDAL raster dataset (required)
        args['carbon_pools_uri'] - is a uri to a DBF dataset mapping carbon 
            storage density to the lulc classifications specified in the
            lulc rasters. (required if 'use_uncertainty' is false)
        args['carbon_pools_uncertain_uri'] - as above, but has probability distribution
            data for each lulc type rather than point estimates.
            (required if 'use_uncertainty' is true)
        args['use_uncertainty'] - a boolean that indicates whether we should do
            uncertainty analysis. Defaults to False if not present.
        args['lulc_fut_uri'] - is a uri to a GDAL raster dataset (optional
         if calculating sequestration)
        args['lulc_cur_year'] - An integer representing the year of lulc_cur 
            used in HWP calculation (required if args contains a 
            'hwp_cur_shape_uri', or 'hwp_fut_shape_uri' key)
        args['lulc_fut_year'] - An integer representing the year of  lulc_fut
            used in HWP calculation (required if args contains a 
            'hwp_fut_shape_uri' key)
        args['hwp_cur_shape_uri'] - Current shapefile uri for harvested wood 
            calculation (optional, include if calculating current lulc hwp) 
        args['hwp_fut_shape_uri'] - Future shapefile uri for harvested wood 
            calculation (optional, include if calculating future lulc hwp)
        
        returns nothing."""

    try:
        file_suffix = args['suffix']
        if not file_suffix.startswith('_'):
            file_suffix = '_' + file_suffix
    except KeyError:
        file_suffix = ''

    output_dir = os.path.join(args['workspace_dir'], 'output')
    intermediate_dir = os.path.join(args['workspace_dir'], 'intermediate')
    for directory in [output_dir, intermediate_dir]:
        if not os.path.exists(directory):
            LOGGER.info('creating directory %s', directory)
            os.makedirs(directory)

    #1) load carbon pools into dictionary indexed by LULC
    LOGGER.debug("building carbon pools")
    use_uncertainty = args.get('use_uncertainty', False)
    if use_uncertainty:
        pools = raster_utils.get_lookup_from_table(args['carbon_pools_uncertain_uri'], 'LULC')
    else:
        pools = raster_utils.get_lookup_from_table(args['carbon_pools_uri'], 'LULC')

    #2) map lulc_cur and _fut (if availble) to total carbon
    out_file_names = {}
    for lulc_uri in ['lulc_cur_uri', 'lulc_fut_uri']:
        if lulc_uri in args:
            scenario_type = lulc_uri.split('_')[-2] #get the 'cur' or 'fut'
            cell_area_ha = (
                raster_utils.get_cell_area_from_uri(args[lulc_uri]) /
                10000.0)

            for lulc_id, lookup_dict in pools.iteritems():
                pool_estimate_types = ['c_above', 'c_below', 'c_soil', 'c_dead']

                if use_uncertainty:
                    # Use the mean estimate of the distribution to compute the carbon output.
                    pool_estimate_sds = list(pool_estimate_types) # Make a copy for std deviations
                    for i in range(len(pool_estimate_types)):
                        pool_estimate_types[i] += '_mean' # Data for the mean
                        pool_estimate_sds[i] += '_sd'  # Data for the standard deviation

                    # Compute the total variance per pixel for each lulc type.
                    # We have a normal distribution for each pool; we assume each is independent,
                    # so the variance of the sum is equal to the sum of the variances.
                    # Note that we scale by the area squared.
                    pools[lulc_id]['variance_%s' % lulc_uri] = (cell_area_ha ** 2) * sum(
                        [pools[lulc_id][pool_type_sd] ** 2 for pool_type_sd in pool_estimate_sds])
                    
                # Compute the total carbon per pixel for each lulc type
                pools[lulc_id]['total_%s' % lulc_uri] = cell_area_ha * sum(
                    [pools[lulc_id][pool_type] for pool_type in pool_estimate_types])

            nodata = raster_utils.get_nodata_from_uri(args[lulc_uri])
            nodata_out = -5.0
            def map_carbon_pool(lulc):
                if lulc == nodata:
                    return nodata_out
                return pools[lulc]['total_%s' % lulc_uri]
            dataset_out_uri = os.path.join(
                output_dir, 'tot_C_%s%s.tif' % (scenario_type, file_suffix))
            out_file_names['tot_C_%s' % scenario_type] = dataset_out_uri

            pixel_size_out = raster_utils.get_cell_size_from_uri(args[lulc_uri])
            # Create a raster that models total carbon storage per pixel.
            raster_utils.vectorize_datasets(
                [args[lulc_uri]], map_carbon_pool, dataset_out_uri,
                gdal.GDT_Float32, nodata_out, pixel_size_out,
                "intersection", dataset_to_align_index=0)

            if use_uncertainty:
                def map_carbon_pool_variance(lulc):
                    if lulc == nodata:
                        return nodata_out
                    return pools[lulc]['variance_%s' % lulc_uri]
                variance_out_uri = os.path.join(
                    intermediate_dir, 'variance_C_%s%s.tif' % (scenario_type, file_suffix))
                out_file_names['variance_C_%s' % scenario_type] = dataset_out_uri
                
                # Create a raster that models variance in carbon storage per pixel.
                raster_utils.vectorize_datasets(
                    [args[lulc_uri]], map_carbon_pool_variance, variance_out_uri,
                    gdal.GDT_Float32, nodata_out, pixel_size_out,
                    "intersection", dataset_to_align_index=0)

            #Add calculate the hwp storage, if it is passed as an input argument
            hwp_key = 'hwp_%s_shape_uri' % scenario_type
            if hwp_key in args:
                c_hwp_uri = os.path.join(intermediate_dir, 'c_hwp_%s%s.tif' % (scenario_type, file_suffix))
                bio_hwp_uri = os.path.join(intermediate_dir, 'bio_hwp_%s%s.tif' % (scenario_type, file_suffix))
                vol_hwp_uri = os.path.join(intermediate_dir, 'vol_hwp_%s%s.tif' % (scenario_type, file_suffix))

                if scenario_type == 'cur':
                    calculate_hwp_storage_cur(
                        args[hwp_key], args[lulc_uri], c_hwp_uri, bio_hwp_uri,
                        vol_hwp_uri, args['lulc_%s_year' % scenario_type])
                    #TODO add to tot_C_cur
                    temp_c_cur_uri = raster_utils.temporary_filename()
                    LOGGER.debug(out_file_names)
                    shutil.copyfile(out_file_names['tot_C_cur'], temp_c_cur_uri)
                    
                    hwp_cur_nodata = raster_utils.get_nodata_from_uri(c_hwp_uri)
                    def add_op(tmp_c_cur, hwp_cur):
                        if hwp_cur == hwp_cur_nodata:
                            return tmp_c_cur
                        return tmp_c_cur + hwp_cur

                    raster_utils.vectorize_datasets(
                        [temp_c_cur_uri, c_hwp_uri], add_op, out_file_names['tot_C_cur'], gdal.GDT_Float32, nodata_out,
                        pixel_size_out, "intersection", dataset_to_align_index=0)

                elif scenario_type == 'fut':
                    hwp_shapes = {}

                    if 'hwp_cur_shape_uri' in args:
                        hwp_shapes['cur'] = args['hwp_cur_shape_uri']
                    if 'hwp_fut_shape_uri' in args:
                        hwp_shapes['fut'] = args['hwp_fut_shape_uri']

                    calculate_hwp_storage_fut(
                        hwp_shapes, args[lulc_uri], c_hwp_uri, bio_hwp_uri,
                        vol_hwp_uri, args['lulc_cur_year'], args['lulc_fut_year'])

                    #TODO add to tot_C_cur
                    temp_c_fut_uri = raster_utils.temporary_filename()
                    LOGGER.debug(out_file_names)
                    shutil.copyfile(out_file_names['tot_C_fut'], temp_c_fut_uri)
                    
                    hwp_fut_nodata = raster_utils.get_nodata_from_uri(c_hwp_uri)
                    def add_op(tmp_c_fut, hwp_fut):
                        if hwp_fut == hwp_fut_nodata:
                            return tmp_c_fut
                        return tmp_c_fut + hwp_fut

                    raster_utils.vectorize_datasets(
                        [temp_c_fut_uri, c_hwp_uri], add_op, out_file_names['tot_C_fut'], gdal.GDT_Float32, nodata_out,
                        pixel_size_out, "intersection", dataset_to_align_index=0)


    #TODO: sequestration
    if 'lulc_cur_uri' in args and 'lulc_fut_uri' in args:
        def sub_op(c_cur, c_fut):
            if nodata_out in [c_cur, c_fut]:
                return nodata_out
            return c_fut - c_cur

        pixel_size_out = raster_utils.get_cell_size_from_uri(args['lulc_cur_uri'])
        out_file_names['sequest'] = os.path.join(output_dir, 'sequest%s.tif' % file_suffix)
        raster_utils.vectorize_datasets(
            [out_file_names['tot_C_cur'], out_file_names['tot_C_fut']], sub_op, out_file_names['sequest'], gdal.GDT_Float32, nodata_out,
            pixel_size_out, "intersection", dataset_to_align_index=0)

    _calculate_summary(out_file_names)



def calculate_hwp_storage_cur(
    hwp_shape_uri, base_dataset_uri, c_hwp_uri, bio_hwp_uri, vol_hwp_uri,
    yr_cur):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due 
        to harvested wood products in parcels on current landscape.
        
        hwp_shape - oal shapefile indicating harvest map of interest
        base_dataset_uri - a gdal dataset to create the output rasters from
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        yr_cur - year of the current landcover map
        
        No return value"""

    ############### Start
    pixel_area = raster_utils.get_cell_size_from_uri(base_dataset_uri) ** 2 / 10000.0 #convert to Ha
    hwp_shape = ogr.Open(hwp_shape_uri)
    base_dataset = gdal.Open(base_dataset_uri)
    nodata = -5.0

    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters
    hwp_shape_copy = ogr.GetDriverByName('Memory').CopyDataSource(hwp_shape, '')
    hwp_shape_layer_copy = hwp_shape_copy.GetLayer()

    #Create fields in the layers to hold hardwood product pools, 
    #biomassPerPixel and volumePerPixel
    calculated_attribute_names = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    for x in calculated_attribute_names:
        field_def = ogr.FieldDefn(x, ogr.OFTReal)
        hwp_shape_layer_copy.CreateField(field_def)

    #Visit each feature and calculate the carbon pool, biomassPerPixel, and 
    #volumePerPixel of that parcel
    for feature in hwp_shape_layer_copy:
        #This makes a helpful dictionary to access fields in the feature
        #later in the code
        field_args = _get_fields(feature)

        #If start date and/or the amount of carbon per cut is zero, it doesn't
        #make sense to do any calculation on carbon pools or 
        #biomassPerPixel/volumePerPixel
        if field_args['start_date'] != 0 and field_args['cut_cur'] != 0:

            time_span = yr_cur - field_args['start_date']
            start_years = time_span

            #Calculate the carbon pool due to decaying HWP over the time_span
            feature_carbon_storage_per_pixel = (
                pixel_area * _carbon_pool_in_hwp_from_parcel(
                    field_args['cut_cur'], time_span, start_years,
                    field_args['freq_cur'], field_args['decay_cur']))

            #Next lines caculate biomassPerPixel and volumePerPixel of 
            #harvested wood
            number_of_harvests = \
                math.ceil(time_span / float(field_args['freq_cur']))

            biomass_in_feature = field_args['cut_cur'] * number_of_harvests / \
                float(field_args['c_den_cur'])

            biomass_per_pixel = biomass_in_feature * pixel_area

            volume_per_pixel = biomass_per_pixel / field_args['bcef_cur']

            #Copy biomass_per_pixel and carbon pools to the temporary feature 
            #for rasterization of the entire layer later
            for field, value in zip(calculated_attribute_names,
                                    [feature_carbon_storage_per_pixel,
                                     biomass_per_pixel, volume_per_pixel]):
                feature.SetField(feature.GetFieldIndex(field), value)

            #This saves the changes made to feature back to the shape layer
            hwp_shape_layer_copy.SetFeature(feature)

    #burn all the attribute values to a raster
    for attribute_name, raster_uri in zip(
        calculated_attribute_names, [c_hwp_uri, bio_hwp_uri, vol_hwp_uri]):
        
        raster = raster_utils.new_raster_from_base(
            base_dataset, raster_uri, 'GTiff', nodata, gdal.GDT_Float32,
            fill_value=nodata)
        gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy,
                            options=['ATTRIBUTE=' + attribute_name])
        raster.FlushCache()
        raster = None


def calculate_hwp_storage_fut(
    hwp_shapes, base_dataset_uri, c_hwp_uri, bio_hwp_uri, vol_hwp_uri,
    yr_cur, yr_fut):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due to 
        harvested wood products in parcels on current landscape.
        
        hwp_shapes - a dictionary containing the current and/or future harvest
            maps (or nothing)
            hwp_shapes['cur'] - oal shapefile indicating harvest map from the
                current landscape
            hwp_shapes['fut'] - oal shapefile indicating harvest map from the
                future landscape
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        yr_cur - year of the current landcover map
        yr_fut - year of the current landcover map
        
        No return value"""

    ############### Start
    pixel_area = raster_utils.get_cell_size_from_uri(base_dataset_uri) ** 2 / 10000.0 #convert to Ha
    nodata = -5.0

    c_hwp_cur_uri = raster_utils.temporary_filename()
    bio_hwp_cur_uri = raster_utils.temporary_filename()
    vol_hwp_cur_uri = raster_utils.temporary_filename()

    raster_utils.new_raster_from_base_uri(base_dataset_uri, c_hwp_uri, 'GTiff', nodata, gdal.GDT_Float32, fill_value=nodata)
    raster_utils.new_raster_from_base_uri(base_dataset_uri, bio_hwp_uri, 'GTiff', nodata, gdal.GDT_Float32, fill_value=nodata)
    raster_utils.new_raster_from_base_uri(base_dataset_uri, vol_hwp_uri, 'GTiff', nodata, gdal.GDT_Float32, fill_value=nodata)

    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters

    calculatedAttributeNames = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    if 'cur' in hwp_shapes:
        hwp_shape = ogr.Open(hwp_shapes['cur'])
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwp_shape, '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayer()

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for fieldName in calculatedAttributeNames:
            field_def = ogr.FieldDefn(fieldName, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, 
        #and volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            field_args = _get_fields(feature)

            #If start date and/or the amount of carbon per cut is zero, it 
            #doesn't make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if field_args['start_date'] != 0 and field_args['cut_cur'] != 0:

                time_span = (yr_fut + yr_cur) / 2.0 - field_args['start_date']
                start_years = yr_fut - field_args['start_date']

                #Calculate the carbon pool due to decaying HWP over the 
                #time_span
                feature_carbon_storage_per_pixel = (
                    pixel_area * _carbon_pool_in_hwp_from_parcel(
                        field_args['cut_cur'], time_span, start_years,
                        field_args['freq_cur'], field_args['decay_cur']))

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(time_span / float(field_args['freq_cur']))
                #The measure of biomass is in terms of Mg/ha
                biomassInFeaturePerArea = field_args['cut_cur'] * \
                    numberOfHarvests / float(field_args['c_den_cur'])


                biomassPerPixel = biomassInFeaturePerArea * pixel_area
                volumePerPixel = biomassPerPixel / field_args['bcef_cur']

                #Copy biomassPerPixel and carbon pools to the temporary 
                #feature for rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [feature_carbon_storage_per_pixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, raster_uri in zip(calculatedAttributeNames,
                                          [c_hwp_cur_uri, bio_hwp_cur_uri, vol_hwp_cur_uri]):
            nodata = -1.0
            raster_utils.new_raster_from_base_uri(base_dataset_uri, raster_uri, 'GTiff', nodata, gdal.GDT_Float32, fill_value=nodata)
            raster = gdal.Open(raster_uri, gdal.GA_Update)
            gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy, options=['ATTRIBUTE=' + attributeName])
            raster.FlushCache()
            raster = None

    #handle the future term 
    if 'fut' in hwp_shapes:
        hwp_shape = ogr.Open(hwp_shapes['fut'])
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwp_shape, '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayer()

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for fieldName in calculatedAttributeNames:
            field_def = ogr.FieldDefn(fieldName, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, 
        #and volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            field_args = _get_fields(feature)

            #If start date and/or the amount of carbon per cut is zero, it 
            #doesn't make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if field_args['cut_fut'] != 0:

                time_span = yr_fut - (yr_fut + yr_cur) / 2.0
                start_years = time_span

                #Calculate the carbon pool due to decaying HWP over the 
                #time_span
                feature_carbon_storage_per_pixel = pixel_area * \
                    _carbon_pool_in_hwp_from_parcel(
                    field_args['cut_fut'], time_span, start_years,
                    field_args['freq_fut'], field_args['decay_fut'])

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(time_span / float(field_args['freq_fut']))

                biomassInFeaturePerArea = field_args['cut_fut'] * \
                    numberOfHarvests / float(field_args['c_den_fut'])

                biomassPerPixel = biomassInFeaturePerArea * pixel_area

                volumePerPixel = biomassPerPixel / field_args['bcef_fut']

                #Copy biomassPerPixel and carbon pools to the temporary 
                #feature for rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [feature_carbon_storage_per_pixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, (raster_uri, cur_raster_uri) in zip(
            calculatedAttributeNames, [(c_hwp_uri, c_hwp_cur_uri), (bio_hwp_uri, bio_hwp_cur_uri), (vol_hwp_uri, vol_hwp_cur_uri)]):

            temp_filename = raster_utils.temporary_filename()
            raster_utils.new_raster_from_base_uri(
                base_dataset_uri, temp_filename, 'GTiff',
                nodata, gdal.GDT_Float32, fill_value=nodata)
            temp_raster = gdal.Open(temp_filename, gdal.GA_Update)
            gdal.RasterizeLayer(temp_raster, [1], hwp_shape_layer_copy,
                                options=['ATTRIBUTE=' + attributeName])
            temp_raster.FlushCache()
            temp_raster = None
            cur_raster = None

            #add temp_raster and raster cur raster into the output raster
            nodata = -1.0
            base_nodata = raster_utils.get_nodata_from_uri(raster_uri)
            cur_nodata = raster_utils.get_nodata_from_uri(cur_raster_uri)
            def add_op(base, current):
                if base == base_nodata or current == cur_nodata:
                    return nodata
                return base + current

            pixel_size_out = raster_utils.get_cell_size_from_uri(raster_uri)
            raster_utils.vectorize_datasets(
                [cur_raster_uri, temp_filename], add_op, raster_uri, gdal.GDT_Float32, nodata,
                pixel_size_out, "intersection", dataset_to_align_index=0)


def _get_fields(feature):
    """Return a dict with all fields in the given feature.

        feature - an OGR feature.

        Returns an assembled python dict with a mapping of 
        fieldname -> fieldvalue"""

    fields = {}
    for i in xrange(feature.GetFieldCount()):
        field_def = feature.GetFieldDefnRef(i)
        name = field_def.GetName().lower()
        value = feature.GetField(i)
        fields[name] = value

    return fields


def _carbon_pool_in_hwp_from_parcel(carbonPerCut, start_years, timeSpan, harvestFreq,
                              decay):
    """This is the summation equation that appears in equations 1, 5, 6, and 7
        from the user's guide

        carbonPerCut - The amount of carbon removed from a parcel during a
            harvest period
        start_years - The number of years ago that the harvest first started
        timeSpan - The number of years to calculate the harvest over
        harvestFreq - How many years between harvests
        decay - the rate at which carbon is decaying from HWP harvested from
            parcels

        returns a float indicating the amount of carbon stored from HWP
            harvested in units of Mg/ha"""

    carbonSum = 0.0
    omega = math.log(2) / decay
    #Recall that xrange is nonexclusive on the upper bound, so it corresponds
    #to the -1 in the summation terms given in the user's manual
    for t in xrange(int(math.ceil(start_years / harvestFreq))):
        carbonSum += (1 - math.exp(-omega)) / (omega *
            math.exp((timeSpan - t * harvestFreq) * omega))
    return carbonSum * carbonPerCut

def _calculate_summary(args):
    """Dumps information about total carbon summaries from the past run
        in the form

        Total current carbon: xxx Mg
        Total scenario carbon: yyy Mg
        Total sequestered carbon: zzz Mg

        args - a dictionary of arguments defined as follows:

        args['tot_C_cur'] - a gdal dataset uri that contains pixels with
            total Mg of carbon per cell on current landscape (required)
        args['tot_C_fut'] - a gdal dataset uri that contains pixels with
            total Mg of carbon per cell on future landscape (optional)
        args['sequest'] - a gdal dataset uri that contains pixels with
            total Mg of carbon sequestered per cell (optional)

        returns nothing
        """
    LOGGER.debug('calculate summary')
    raster_key_messages = [('tot_C_cur', 'Total current carbon: '),
                           ('tot_C_fut', 'Total scenario carbon: '),
                           ('sequest', 'Total sequestered carbon: ')]

    for raster_key, message in raster_key_messages:
        #Make sure we passed in the dictionary, and gracefully continue
        #if we didn't.
        if raster_key not in args:
            continue
        dataset = gdal.Open(args[raster_key])
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        total_sum = 0.0
        #Loop over each row in out_band
        for row_index in range(band.YSize):
            row_array = band.ReadAsArray(0, row_index, band.XSize, 1)
            total_sum += numpy.sum(row_array[row_array != nodata])
        LOGGER.info("%s %s Mg" % (message, total_sum))
