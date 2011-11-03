import numpy as np
from osgeo import gdal
import osgeo.gdal
import osgeo.osr as osr
from osgeo import ogr
from dbfpy import dbf
import math
import invest_core

def biophysical(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.

        args - is a dictionary with at least the following entries:
        args['calculate_sequestration'] - a boolean, True if sequestration
            is to be calculated.
        args['calculate_hwp'] - a boolean, True if harvested wood product
            calcuation is to be done.  Also implies a sequestration 
            calculation.
        args['calc_uncertainty'] - a Boolean.  True if we wish to calculate 
            uncertainty in the carbon model.  Implies that carbon pools should
            have value ranges.
        args['uncertainty_percentile'] - a float indicating upper and lower
            percentiles of sequestration to output (required if calculating 
            uncertainty)
        args['lulc_cur'] - is a GDAL raster representing the current land 
            use/land cover map (required)
        args['lulc_fut'] - is a GDAL raster dataset representing the future 
            land use/land cover map (required if doing sequestration, HWP, or
            uncertainty calculations)
        args['carbon_pools'] - is a DBF dataset mapping carbon storage density
            to lulc classifications in input LULC rasters.  If 
            args['calc_uncertainty'] is True the columns should have additional
            information about min, avg, and max carbon pool measurements.
            (required if doing sequestration, HWP, or uncertainty)
        args['hwp_cur_shape'] - OAL shapefile representing harvest rates on 
            current lulc (required if calculating HWP)
        args['hwp_fut_shape'] - OAL shapefile representing harvest rates on 
            future lulc (required if calculating HWP)
        args['lulc_cur_year'] - an int represents the year of lulc_cur 
        args['lulc_fut_year'] - an int represents the year of lulc_fut
            (required if calculating HWP)
        args['tot_C_cur'] - an output GDAL raster dataset representing total 
            carbon stored on the current lulc, must be same dimensions as 
            lulc_cur (required)
        args['tot_C_fut'] - an output GDAL raster dataset representing total 
            carbon stored on the future lulc must be same dimensions as 
            lulc_cur (required, if doing sequestration, uncertainty, or HWP)
        args['sequest'] - an output GDAL raster dataset representing carbon 
            sequestration and emissions between current and future landscapes
            (required, if doing sequestration, uncertainty, or HWP)
        args['c_hwp_cur'] - an output GDAL raster dataset representing 
            carbon stored in harvested wood products for current land cover 
            (required if doing HWP)
        args['c_hwp_fut'] - an output GDAL raster dataset representing 
            carbon stored in harvested wood products for futureland cover 
            (required if doing HWP)
        args['bio_hwp_cur'] - an output GDAL raster dataset representing
            biomass of harvested wood products in current land cover
        args['vol_hwp_cur'] - an output GDAL raster dataset representing
            volume of harvested wood products in current land cover
        args['bio_hwp_fut'] - an output GDAL raster dataset representing
            biomass of harvested wood products in future land cover
        args['vol_hwp_fut'] - an output GDAL raster dataset representing
            volume of harvested wood products in future land cover
        args['uncertainty_percentile_map'] - an output GDAL raster highlighting
            the low and high percentile regions based on the value of 
            'uncertainty_percentile' from the 'sequest' output (required if
            calculating uncertainty)
            
        returns nothing"""

    #Calculate the per pixel carbon storage due to lulc pools
    cellArea = pixelArea(args['lulc_cur'])

    #Create carbon pool dictionary with appropriate values to handle
    #nodata in the input and nodata in the output
    inNoData = args['lulc_cur'].GetRasterBand(1).GetNoDataValue()
    outNoData = args['tot_C_cur'].GetRasterBand(1).GetNoDataValue()
    pools = build_pools_dict(args['carbon_pools'], cellArea, inNoData,
                             outNoData)


    #calculate carbon storage for the current landscape
    calculateCarbonStorage(pools, args['lulc_cur'].GetRasterBand(1),
                           args['tot_C_cur'].GetRasterBand(1))

    #Calculate HWP pools if a HWP shape is present
    if 'hwp_cur_shape' in args:
        calculateHWPStorageCur(args['hwp_cur_shape'], args['c_hwp_cur'],
                            args['bio_hwp_cur'], args['vol_hwp_cur'],
                            cellArea, args['lulc_cur_year'])
        #Add the current hwp carbon storage to tot_C_cur
        invest_core.rasterAdd(args['tot_C_cur'].GetRasterBand(1),
                              args['c_hwp_cur'].GetRasterBand(1),
                              args['tot_C_cur'].GetRasterBand(1))

    if 'lulc_fut' in args:
        #calculate carbon storage for the future landscape if it exists
        if 'lulc_fut' in args:
            calculateCarbonStorage(pools, args['lulc_fut'].GetRasterBand(1),
                                   args['tot_C_fut'].GetRasterBand(1))

        #Calculate a future HWP pool if a future landcover map is present, 
        #this means that a sequestration scenario is happening, so a current 
        #and/or future harvest map could add an additional pool to the future 
        #storage map
        harvestMaps = {}
        if 'hwp_cur_shape' in args:
            harvestMaps['cur'] = args['hwp_cur_shape']
        if 'hwp_fut_shape' in args:
            harvestMaps['fut'] = args['hwp_fut_shape']
        calculateHWPStorageFut(harvestMaps, args['c_hwp_fut'],
            args['bio_hwp_fut'], args['vol_hwp_fut'], cellArea,
            args['lulc_cur_year'], args['lulc_fut_year'])

    #if lulc_fut is present it means that sequestration needs to be calculated
    #calculate the future storage as well
    if 'lulc_fut' in args:
        #calculate storage for the future landscape
        calculateCarbonStorage(pools, args['lulc_fut'].GetRasterBand(1),
                               args['tot_C_fut'].GetRasterBand(1))

        #harvestProducts(args, ('cur', 'fut'))

    if 'lulc_fut' in args:
        #calculate seq. only after HWP has been added to the storage rasters
        invest_core.rasterDiff(args['tot_C_fut'].GetRasterBand(1),
                               args['tot_C_cur'].GetRasterBand(1),
                               args['sequest'].GetRasterBand(1))

def calculateHWPStorageFut(hwpShapes, c_hwp, bio_hwp, vol_hwp, pixelArea,
                           yr_cur, yr_fut):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due to 
        harvested wood products in parcels on current landscape.
        
        hwpShapes - a dictionary containing the current and/or future harvest
            maps (or nothing)
            hwpShapes['cur'] - oal shapefile indicating harvest map from the
                current landscape
            hwpShapes['fut'] - oal shapefile indicating harvest map from the
                future landscape
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        pixelArea - area of a pixel to calculate exact 
            carbon/volumePerPixel/biomassPerPixel amounts
        yr_cur - year of the current landcover map
        yr_fut - year of the current landcover map
        
        No return value"""
    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters

    #First fill output rasters with nodata
    for raster in [c_hwp, bio_hwp, vol_hwp]:
        raster.GetRasterBand(1).Fill(raster.GetRasterBand(1).GetNoDataValue())

    calculatedAttributeNames = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    if 'cur' in hwpShapes:
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwpShapes['cur'], '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayerByName('harv_samp_cur')

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for x in calculatedAttributeNames:
            field_def = ogr.FieldDefn(x, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, and 
        #volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            fieldArgs = getFields(feature)

            #If start date and/or the amount of carbon per cut is zero, it doesn't
            #make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if fieldArgs['Start_date'] != 0 and fieldArgs['Cut_cur'] != 0:

                timeSpan = (yr_fut + yr_cur) / 2.0 - fieldArgs['Start_date']
                startYears = yr_fut - fieldArgs['Start_date']

                #Calculate the carbon pool due to decaying HWP over the timeSpan
                featureCarbonStoragePerPixel = pixelArea * \
                    carbonPoolinHWPFromParcel(fieldArgs['C_den_cur'],
                                              timeSpan, startYears,
                                              fieldArgs['Freq_cur'],
                                              fieldArgs['Decay_cur'])

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(timeSpan / float(fieldArgs['Freq_cur']))
                biomassPerPixel = fieldArgs['Cut_cur'] * timeSpan * \
                    pixelArea / float(fieldArgs['C_den_cur'])
                volumePerPixel = biomassPerPixel / fieldArgs['BCEF_cur']

                #Copy biomassPerPixel and carbon pools to the temporary feature for
                #rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [featureCarbonStoragePerPixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, raster  in zip(calculatedAttributeNames,
                                          [c_hwp, bio_hwp, vol_hwp]):
            gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy,
                                    options=['ATTRIBUTE=' + attributeName])

    #handle the future term 
    if 'fut' in hwpShapes:
        hwp_shape_copy = \
            ogr.GetDriverByName('Memory').CopyDataSource(hwpShapes['fut'], '')
        hwp_shape_layer_copy = \
            hwp_shape_copy.GetLayerByName('harv_samp_fut')

        #Create fields in the layers to hold hardwood product pools, 
        #biomassPerPixel and volumePerPixel
        for x in calculatedAttributeNames:
            field_def = ogr.FieldDefn(x, ogr.OFTReal)
            hwp_shape_layer_copy.CreateField(field_def)

        #Visit each feature and calculate the carbon pool, biomassPerPixel, and 
        #volumePerPixel of that parcel
        for feature in hwp_shape_layer_copy:
            #This makes a helpful dictionary to access fields in the feature
            #later in the code
            fieldArgs = getFields(feature)

            #If start date and/or the amount of carbon per cut is zero, it doesn't
            #make sense to do any calculation on carbon pools or 
            #biomassPerPixel/volumePerPixel
            if fieldArgs['Cut_fut'] != 0:

                timeSpan = yr_fut - (yr_fut + yr_cur) / 2.0
                startYears = timeSpan

                #Calculate the carbon pool due to decaying HWP over the timeSpan
                featureCarbonStoragePerPixel = pixelArea * \
                    carbonPoolinHWPFromParcel(fieldArgs['C_den_fut'],
                                              timeSpan, startYears,
                                              fieldArgs['Freq_fut'],
                                              fieldArgs['Decay_fut'])

                #Claculate biomassPerPixel and volumePerPixel of harvested wood
                numberOfHarvests = \
                    math.ceil(timeSpan / float(fieldArgs['Freq_fut']))
                biomassPerPixel = fieldArgs['Cut_fut'] * timeSpan * \
                    pixelArea / float(fieldArgs['C_den_fut'])
                volumePerPixel = biomassPerPixel / fieldArgs['BCEF_fut']

                #Copy biomassPerPixel and carbon pools to the temporary feature for
                #rasterization of the entire layer later
                for field, value in zip(calculatedAttributeNames,
                                        [featureCarbonStoragePerPixel,
                                         biomassPerPixel, volumePerPixel]):
                    feature.SetField(feature.GetFieldIndex(field), value)

                #This saves the changes made to feature back to the shape layer
                hwp_shape_layer_copy.SetFeature(feature)

        #burn all the attribute values to a raster
        for attributeName, raster  in zip(calculatedAttributeNames,
                                          [c_hwp, bio_hwp, vol_hwp]):
            #we might have already written to the raster if we did a 'fut cur'
            #calculation, so rasterize to a temporary layer then add 'em
            tempRaster = invest_core.newRasterFromBase(raster, '', 'MEM',
                raster.GetRasterBand(1).GetNoDataValue(), gdal.GDT_Float32)
            tempRaster.GetRasterBand(1).Fill(tempRaster.GetRasterBand(1).\
                                             GetNoDataValue())
            gdal.RasterizeLayer(tempRaster, [1], hwp_shape_layer_copy,
                                    options=['ATTRIBUTE=' + attributeName])
            rasterAdd(tempRaster, raster, raster)

def calculateHWPStorageCur(hwp_shape, c_hwp, bio_hwp, vol_hwp, pixelArea,
                           yr_cur):
    """Calculates carbon storage, hwp biomassPerPixel and volumePerPixel due to 
        harvested wood products in parcels on current landscape.
        
        hwp_shape - oal shapefile indicating harvest map of interest
        c_hwp - an output GDAL rasterband representing  carbon stored in 
            harvested wood products for current calculation 
        bio_hwp - an output GDAL rasterband representing carbon stored in 
            harvested wood products for land cover under interest
        vol_hwp - an output GDAL rasterband representing carbon stored in
             harvested wood products for land cover under interest
        pixelArea - area of a pixel to calculate exact 
            carbon/volumePerPixel/biomassPerPixel amounts
        yr_cur - year of the current landcover map
        
        No return value"""

    #Create a temporary shapefile to hold values of per feature carbon pools
    #HWP biomassPerPixel and volumePerPixel, will be used later to rasterize 
    #those values to output rasters

    hwp_shape_copy = \
        ogr.GetDriverByName('Memory').CopyDataSource(hwp_shape, '')
    hwp_shape_layer_copy = \
        hwp_shape_copy.GetLayerByName('harv_samp_cur')

    #Create fields in the layers to hold hardwood product pools, 
    #biomassPerPixel and volumePerPixel
    calculatedAttributeNames = ['c_hwp_pool', 'bio_hwp', 'vol_hwp']
    for x in calculatedAttributeNames:
        field_def = ogr.FieldDefn(x, ogr.OFTReal)
        hwp_shape_layer_copy.CreateField(field_def)

    #Visit each feature and calculate the carbon pool, biomassPerPixel, and 
    #volumePerPixel of that parcel
    for feature in hwp_shape_layer_copy:
        #This makes a helpful dictionary to access fields in the feature
        #later in the code
        fieldArgs = getFields(feature)

        #If start date and/or the amount of carbon per cut is zero, it doesn't
        #make sense to do any calculation on carbon pools or 
        #biomassPerPixel/volumePerPixel
        if fieldArgs['Start_date'] != 0 and fieldArgs['Cut_cur'] != 0:

            timeSpan = yr_cur - fieldArgs['Start_date']
            startYears = timeSpan

            #Calculate the carbon pool due to decaying HWP over the timeSpan
            featureCarbonStoragePerPixel = pixelArea * \
                carbonPoolinHWPFromParcel(fieldArgs['C_den_cur'],
                                          timeSpan, startYears,
                                          fieldArgs['Freq_cur'],
                                          fieldArgs['Decay_cur'])

            #Next lines caculate biomassPerPixel and volumePerPixel of 
            #harvested wood
            numberOfHarvests = \
                math.ceil(timeSpan / float(fieldArgs['Freq_cur']))
            biomassPerPixel = fieldArgs['Cut_cur'] * timeSpan * \
                pixelArea / float(fieldArgs['C_den_cur'])
            volumePerPixel = biomassPerPixel / fieldArgs['BCEF_cur']

            #Copy biomassPerPixel and carbon pools to the temporary feature for
            #rasterization of the entire layer later
            for field, value in zip(calculatedAttributeNames,
                                    [featureCarbonStoragePerPixel,
                                     biomassPerPixel, volumePerPixel]):
                feature.SetField(feature.GetFieldIndex(field), value)

            #This saves the changes made to feature back to the shape layer
            hwp_shape_layer_copy.SetFeature(feature)

    #burn all the attribute values to a raster
    for attributeName, raster  in zip(calculatedAttributeNames,
                                      [c_hwp, bio_hwp, vol_hwp]):
        raster.GetRasterBand(1).Fill(raster.GetRasterBand(1).GetNoDataValue())
        gdal.RasterizeLayer(raster, [1], hwp_shape_layer_copy,
                                options=['ATTRIBUTE=' + attributeName])

#    avgYear = math.ceil((lulc_cur_year + lulc_fut_year) / 2.0)
#
#    #for each shape (if the shape is provided in args):
#    for harvestMap, layerName, timeframe in \
#        [(hwp_shape, 'harv_samp_cur', 'cur'),
#         (hwp_fut_shape, 'harv_samp_fut', 'fut')]:
#
#        #Make a copy of the appropriate shape in memory
#        copiedDS = ogr.GetDriverByName('Memory').CopyDataSource(harvestMap, '')
#
#        #open the copied file
#        copiedLayer = copiedDS.GetLayerByName(layerName)
#
#        #add a biomassPerPixel and volumePerPixel field to the shape
#        for fieldname in ('biomassPerPixel', 'volumePerPixel'):
#            field_def = ogr.FieldDefn(fieldname, ogr.OFTReal)
#            copiedLayer.CreateField(field_def)
#
#        #create a temporary mask raster for this shapefile
#        maskRaster = invest_core.newRasterFromBase(baseRaster, 'mask.tif',
#                                              'MEM', -1.0, gdal.GDT_CFloat32)
#        gdal.RasterizeLayer(maskRaster, [1], copiedLayer, burn_values=[1])
#
#        for feature in copiedLayer:
#            fieldArgs = getFields(feature)
#
#            #do the appropriate math based on the timeframe
#            if timeframe == 'cur':
#                timeSpan = math.ceil((avgYear - fieldArgs['Start_date'])
#                                       / fieldArgs['Freq_cur'])
#            else:
#                timeSpan = math.ceil((lulc_fut_year - avgYear)
#                                     / fieldArgs['Freq_fut'])
#
#            #calculate biomassPerPixel for this parcel (equation 10.8)
#            biomassPerPixel = fieldArgs['Cut_' + timeframe] * \
#                    timeSpan * (1.0 / fieldArgs['C_den_' + timeframe])
#
#            #calculate volumePerPixel for this parcel (equation 10.11)
#            volumePerPixel = biomassPerPixel * (1.0 / fieldArgs['BCEF_' + timeframe])
#
#            #set biomassPerPixel and volumePerPixel fields
#            for fieldName, value in (('biomassPerPixel', biomassPerPixel), ('volumePerPixel', volumePerPixel)):
#                index = feature.GetFieldIndex(fieldName)
#                feature.SetField(index, value)
#
#            #save the field modifications to the layer.
#            copiedLayer.SetFeature(feature)
#
#        #Burn values into temp raster, apply mask, save to args dict.
#        for fieldName in ('biomassPerPixel', 'volumePerPixel'):
#            tempRaster = invest_core.newRasterFromBase(baseRaster, '', 'MEM',
#                                                   - 1.0, gdal.GDT_CFloat32)
#            gdal.RasterizeLayer(tempRaster, [1], copiedLayer,
#                            options=['ATTRIBUTE=' + fieldName])
#            #Figure out how to do entire calculation here
#            #rasterMask(tempRaster, maskRaster, args[fieldName + '_' + timeframe])
    return

def carbonPoolinHWPFromParcel(carbonPerCut, startYears, timeSpan, harvestFreq,
                              decay):
    """This is the summation equation that appears in equations 1, 5, 6, and 7
        from the user's guide
        
        carbonPerCut - The amount of carbon removed from a parcel during a
            harvest period
        startYears - The number of years ago that the harvest first started
        timeSpan - The number of years to calculate the harvest over
        harvestFreq - How many years between harvests
        decay - the rate at which carbon is decaying from HWP harvested from
            parcels
        
        returns a float indicating the amount of carbon stored in HWP harvested
            from that parcel"""

    carbonSum = 0.0
    omega = math.log(2) / decay
    #Recall that xrange is nonexclusive on the upper bound, so it corresponds
    #to the -1 in the summation terms given in the user's manual
    for t in xrange(int(math.ceil(startYears / harvestFreq))):
        carbonSum += (1 - math.exp(-omega)) / (omega *
            math.exp((timeSpan - t * harvestFreq) * omega))
    return carbonSum * carbonPerCut

def harvestProducts(args, timespan):
    """Adds carbon due to harvested wood products in a future scenario
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset
        args['storage_cur'] - is a GDAL raster dataset
        args['storage_fut'] - in a GDAL raster dataset
        args['hwp_cur_shape'] - an open OGR object
        args['hwp_fut_shape'] - an open OGR object
        args['lulc_cur_year'] - an int
        args['lulc_fut_year'] - an int
        
        timespan - a list or array with the possible values 'cur' and 'fut'
        No return value."""

    for timeframe in timespan:
        #make a copy of the necessary shape
        src_dataset = args['hwp_' + timeframe + '_shape']
        dataset = ogr.GetDriverByName('Memory').CopyDataSource(src_dataset, '')
        layer = dataset.GetLayerByName('harv_samp_' + timeframe)

        #create a new field for HWP calculations
        hwp_def = ogr.FieldDefn("hwp_pool", ogr.OFTReal)
        layer.CreateField(hwp_def)

        #calculate hwp pools per feature for the timeframe
        if len(timespan) == 2:
            iterFeatures(layer, timeframe, args['lulc_cur_year'],
                          args['lulc_fut_year'])
        else:
            iterFeatures(layer, timeframe, args['lulc_cur_year'])

        #Make a new raster in memory for burning in the HWP values.
        hwp_ds = invest_core.newRasterFromBase(args['lulc_cur'], 'temp.tif',
                           'MEM', -1.0, gdal.GDT_Float32)

        #Now burn the current hwp pools into the HWP raster in memory.
        gdal.RasterizeLayer(hwp_ds, [1], layer,
                             options=['ATTRIBUTE=hwp_pool'])

        #Add the HWP raster to the storage raster, write the sum to the
        #storage raster.
        rasterAdd(args['storage_' + timeframe], hwp_ds, args['storage_' + timeframe])

        #clear the temp dataset.
        hwp_ds = None


def iterFeatures(layer, suffix, yrCur, yrFut=None):
    """Iterate over all features in the provided layer, calculate HWP.
    
        layer - an OGR layer
        suffix - a String, either 'cur' or 'fut'
        yrCur - an int
        yrFut - an int (required for future HWP contexts)
        
        no return value"""

    #calculate average for use in future contexts if a yrFut is given
    if yrFut != None:
        avg = math.floor((yrFut + yrCur) / 2.0)

    #calculate hwp pools per feature for the future scenario
    for feature in layer:
        fieldArgs = getFields(feature)

        #If 'cut_' is not specified, assume the parcel hasn't been harvested
        if fieldArgs['Cut_' + suffix] != 0:
            #Set a couple variables based on the input parameters
            if suffix == 'cur':
                #if no future scenario is provided, calc the sum on its own
                if yrFut == None:
                    limit = math.ceil(((yrCur - fieldArgs['Start_date'])\
                                    / fieldArgs['Freq_cur'])) - 1.0
                    endDate = yrCur
                #Calculate the sum of current HWP landscape in future context
                else:
                    limit = math.ceil(((avg - fieldArgs['Start_date'])\
                                    / fieldArgs['Freq_cur'])) - 1.0
                    endDate = yrFut

                decay = fieldArgs['Decay_cur']
                startDate = fieldArgs['Start_date']
                freq = fieldArgs['Freq_cur']

            #calcluate the sum of future HWP landscape in future context.
            else:
                limit = math.ceil(((yrFut - avg)\
                                    / fieldArgs['Freq_fut'])) - 1.0
                decay = fieldArgs['Decay_fut']
                startDate = avg
                endDate = yrFut
                freq = fieldArgs['Freq_fut']

            #calculate the feature's HWP carbon pool
            hwpsum = calcFeatureHWP(limit, decay, endDate, startDate, freq)
            hwpCarbonPool = fieldArgs['Cut_' + suffix] * hwpsum
        else:
            hwpCarbonPool = 0.0

        #set the HWP carbon pool for this feature.
        hwpIndex = feature.GetFieldIndex('hwp_pool')
        feature.SetField(hwpIndex, hwpCarbonPool)
        layer.SetFeature(feature)


def getFields(feature):
    """Return a dict with all fields in the given feature.
        
        feature - an OGR feature.
        
        Returns an assembled python dict with a mapping of 
        fieldname -> fieldvalue"""

    fields = {}
    for i in range(feature.GetFieldCount()):
        field_def = feature.GetFieldDefnRef(i)
        name = field_def.GetNameRef()
        value = feature.GetField(i)
        fields[name] = value

    return fields

def valuate(args):
    """Executes the economic valuation model.
        
        args is a dictionary with all of the options detailed in execute()
        
        No return value"""

    numYears = args['lulc_fut_year'] - args['lulc_cur_year']
    pools = build_pools(args['carbon_pools'], args['lulc_cur'], args['storage_cur'])
    rasterValue(args['seq_delta'], args['seq_value'], args['c_value'], args['discount'], args['rate_change'], numYears)

def rasterValue(inputRaster, outputRaster, carbonValue, discount, rateOfChange, numYears):
    """iterates through the rows in a raster and applies the carbon valuation model
        to all values.
        
        inputRaster - is a GDAL raster dataset
        outputRaster - is a GDAL raster dataset for outputing the value of carbon sequestered
        carbonValue - is a float representing the price of carbon per metric ton
        discount - is a float representing the market discount rate for Carbon
        rateOfChange - is a float representing the annual rate of change in the price of Carbon.
        numYears - an int representing the number of years between current and future land cover maps
        
        No return value."""

    nodataDict = build_nodata_dict(inputRaster, outputRaster)
    lulc = inputRaster.GetRasterBand(1)

    multiplier = 0.
#    for n in range(numYears-1): #Subtract 1 per the user's manual
    for n in range(numYears):    #This is incorrect, but it allows us to match the results of invest2
        multiplier += 1. / (((1. + rateOfChange) ** n) * (1. + discount) ** n)

    for i in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, i, lulc.XSize, 1)
        out_array = carbon_value(nodataDict, data, numYears, carbonValue, multiplier)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)

def calculateCarbonStorage(pools, lulcRasterBand, storageRasterBand):
    """Iterate through the rows in an LULC raster and map carbon storage values
        to the output raster.
        
        pools - a python dict mapping lulc indices to carbon storage/pixel
        lulcRasterBand - a GDAL raster dataset representing lulc 
        storageRasterBand - a GDAL raster dataset representing carbon storage
        
        No return value."""

    #Vectorize an operation that maps pixel values to carbon storage values
    def mapPool(x, dict):
        return dict[x]
    mapFun = np.vectorize(mapPool)

    #Iterate through lulc and map storage to the storage raster band
    for i in range(0, lulcRasterBand.YSize):
        data = lulcRasterBand.ReadAsArray(0, i, lulcRasterBand.XSize, 1)
        out_array = mapFun(data, pools)
        storageRasterBand.WriteArray(out_array, 0, i)

def rasterDiff(rasterBandA, rasterBandB, outputRasterBand):
    """Iterate through the rows in the two sequestration rasters and calculate 
        the difference in each pixel.  Maps the difference to the output 
        raster.
        
        rasterBandA - a GDAL raster band
        rasterBandB - a GDAL raster band
        outputRasterBand - a GDAL raster band with the elementwise value of 
            rasterBandA-rasterBandB
            
        returns nothing"""

    #Build an operation that does pixel difference unless one of the inputs
    #is a nodata value
    noDataA = rasterBandA.GetNoDataValue()
    noDataB = rasterBandB.GetNoDataValue()

    def noDataDiff(a, b):
        #a is nodata if and only if b is nodata
        if a == noDataA:
            return noDataB
        else:
            return a - b

    vectorizeOp(rasterBandA, rasterBandB, noDataDiff, outputRasterBand)

def vectorizeOp(rasterBandA, rasterBandB, op, outBand):
    """Applies the function 'op' over rasterBandA and rasterBandB
    
        rasterBandA - a GDAL raster
        rasterBandB - a GDAL raster of the same dimensions as rasterBandA
        op- a function that that takes 2 arguments and returns 1 value
        outBand - the result of vectorizing op over rasterbandA and 
            rasterBandB
            
        returns nothing"""

    vOp = np.vectorize(op)
    for i in range(0, rasterBandA.YSize):
        dataA = rasterBandA.ReadAsArray(0, i, rasterBandA.XSize, 1)
        dataB = rasterBandB.ReadAsArray(0, i, rasterBandB.XSize, 1)
        out_array = vOp(dataA, dataB)
        outBand.WriteArray(out_array, 0, i)

def rasterAdd(storage_cur, hwpRaster, outputRaster):
    """Iterate through the rows in the two sequestration rasters and calculate the 
        sum of each pixel.  Maps the sum to the output raster.
        
        storage_cur - a GDAL raster dataset
        hwpRaster - a GDAL raster dataset
        outputRaster - a GDAL raster dataset"""

    nodataDict = build_nodata_dict(storage_cur, outputRaster)
    storage_band = storage_cur.GetRasterBand(1)
    hwp_band = hwpRaster.GetRasterBand(1)
    for i in range(0, storage_band.YSize):
        cur_data = storage_band.ReadAsArray(0, i, storage_band.XSize, 1)
        fut_data = hwp_band.ReadAsArray(0, i, storage_band.XSize, 1)
        out_array = carbon_add(nodataDict, cur_data, fut_data)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)

def rasterMask(inputRaster, maskRaster, outputRaster):
    """Iterate through each pixel. Return the pixel of inputRaster if the mask
        is 1 at that pixel.  Return nodata if not.
        
        storage_cur - a GDAL raster dataset
        maskRaster - a GDAL raster dataset
        outputRaster - a GDAL raster dataset"""

    nodataDict = build_nodata_dict(inputRaster, outputRaster)
    input_band = inputRaster.GetRasterBand(1)
    mask_band = maskRaster.GetRasterBand(1)
    for i in range(0, input_band.YSize):
        in_data = input_band.ReadAsArray(0, i, input_band.XSize, 1)
        mask_data = mask_band.ReadAsArray(0, i, mask_band.XSize, 1)
        out_array = carbon_mask(nodataDict, in_data, mask_data)
        outputRaster.GetRasterBand(1).WriteArray(out_array, 0, i)

def pixelArea(dataset):
    """Calculates the pixel area of the given dataset.
    
        dataset - GDAL dataset
    
        returns area in Ha of each pixel in dataset"""

    srs = osr.SpatialReference()
    srs.SetProjection(dataset.GetProjection())
    linearUnits = srs.GetLinearUnits()
    geotransform = dataset.GetGeoTransform()
    #take absolute value since sometimes negative widths/heights
    areaMeters = abs(geotransform[1] * geotransform[5] * (linearUnits ** 2))
    return areaMeters / (10 ** 4) #convert m^2 to Ha

def build_nodata_dict(inputRaster, outputRaster):
    """Get the nodata values from the two input rasters, return them in a dict.
    
        inputRaster - a GDAL raster dataset
        outputRaster - a GDAL raster dataset
        
        returns a dict: {'input': number, 'output': number}
        """
    inNoData = inputRaster.GetRasterBand(1).GetNoDataValue()
    outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()

    nodata = {'input': inNoData, 'output': outNoData}
    return nodata

def build_pools(dbf, inputRaster, outputRaster):
    """Extract the nodata values from the input and output rasters and build
        the carbon pools dict.
        
        dbf - an open DBF dataset
        inputRaster - a GDAL dataset (representing an LULC)
        outputRaster - a GDAL dataset
        
        returns a dictionary calculating total carbon sequestered per lulc type.
        """
    area = pixelArea(inputRaster)
    lulc = inputRaster.GetRasterBand(1)

    inNoData = lulc.GetNoDataValue()
    outNoData = outputRaster.GetRasterBand(1).GetNoDataValue()

    return build_pools_dict(dbf, area, inNoData, outNoData)

def build_pools_dict(dbf, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
            sum += dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum * area
    return poolsDict

def carbon_add(nodata, firstArray, secondArray):
    """Creates a new array by returning the sum of the elements of the two input
        arrays.  If a nodata value is detected in firstArray, the proper nodata
        value for the new output array is returned.
    
        nodata - a dict: {'input': some number, 'output' : some number}
        firstArray - a numpy array
        secondarray - a numpy array
        
        return a new numpy array with the difference of the two input arrays
        """

    def mapSum(a, b):
        if a == nodata['input']:
            return nodata['output']
        else:
            return a + b

    if firstArray.size > 0:
        mapFun = np.vectorize(mapSum)
        return mapFun(firstArray, secondArray)

def carbon_value(nodata, data, numYears, carbonValue, multiplier):
    """iterate through the array and calculate the economic value of sequestered carbon.
        Map the values to the output array.
        
        nodata - a dict: {'input': some number, 'output' : some number}
        data - a numpy array
        numYears - an int: the number of years the simulation covers
        carbonValue - a float: the dollar value of carbon
        multiplier - a float"""

    def mapValue(x):
        if x == nodata['input']:
            return nodata['output']
        else:
            #calculate the pixel-specific value of carbon for this simulation
            return carbonValue * (x / numYears) * multiplier

    if data.size > 0:
        mapFun = np.vectorize(mapValue)
        return mapFun(data)
    else:
        return []

def carbon_mask(nodata, input, mask):
    """Iterate through inputArray and return its value only if the value of mask
        is 1.  Otherwise, return the nodata value of the output array.
        
        nodata - a dict: {'input': some number, 'output' : some number}
        input - a numpy array
        mask - a numpy array, with values of either 0 or 1"""

    def mapMask(x, y):
        if y == 0.0:
            return nodata['output']
        else:
            return x

    if input.size > 0:
        mapFun = np.vectorize(mapMask)
        return mapFun(input, mask)
    else:
        return []



def uncertainty(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with at least the following entries:
        args['lulc'] - is a GDAL raster dataset
        args['carbon_pools'] - is an uncertainty dictionary that maps LULC type
                               to Mg/Ha of carbon where the field names are
                               appended by 'L', 'A', or 'H', for low, average, 
                               and high measurements.
        args['output'] - a GDAL raster dataset for outputing the sequestered carbon
                         contains 3 bands for low, average, and high
        
        returns nothing"""

    area = carbon_core.pixelArea(args['lulc'])
    lulc = args['lulc'].GetRasterBand(1)
    inNoData = lulc.GetNoDataValue()
    outNoData = args['output'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to band numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}

    uncertaintyRank = None

    for poolType in poolTypes:
        pools[poolType] = build_uncertainty_pools_dict(args['carbon_pools'], poolType, area, inNoData, outNoData)
        maxValue, minValue = max(pools[poolType].values()), min(pools[poolType].values())
        if minValue == None:
            minValue = 0

        #create uncertainty dictionary with most recent dictionary as reference for keys
        if uncertaintyRank == None:
            uncertaintyRank = {}.fromkeys(pools[poolType].keys(), 0.0)

        #rank each pooltype
        for type, value in pools[poolType].iteritems():
            if maxValue != minValue and value != None:
                uncertaintyRank[type] += (value - minValue) / (maxValue - minValue) / len(poolTypes)

    #add the uncertainty pool so it gets iterated over on the map step
    poolTypes['uncertainty'] = 4
    pools['uncertainty'] = uncertaintyRank

    #map each row in the lulc raster
    for rowNumber in range(0, lulc.YSize):
        data = lulc.ReadAsArray(0, rowNumber, lulc.XSize, 1)
        #create a seq map for each pooltype 
        for poolType, index in poolTypes.iteritems():
            out_array = carbon_core.carbon_seq(data, pools[poolType])
            args['output'].GetRasterBand(index).WriteArray(out_array, 0, rowNumber)


def build_uncertainty_pools_dict(dbf, poolType, area, inNoData, outNoData):
    """Build a dict for the carbon pool data accessible for each lulc classification.
    
        dbf - the database file describing pools
        poolType - one of 'L', 'A', or 'H' indicating low average or high
                   pool data
        area - the area in Ha of each pixel
        inNoData - the no data value for the input map
        outNoData - the no data value for the output map
    
        returns a dictionary calculating total carbon sequestered per lulc type"""

    poolsDict = {int(inNoData): outNoData}
    for i in range(dbf.recordCount):
        sum = 0
        for field in [ x + '_' + poolType for x in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD')]:
            sum += dbf[i][field]
        poolsDict[dbf[i]['LULC']] = sum * area
    return poolsDict

def carbon_scenario_uncertainty(args):
    """Runs a scenario based uncertainty model for two LULC maps.  Output
        is a 4 output_seq raster for 3 bands indicating carbon sequestration
        change for low, average, and high measurements.  Fourth output_seq is
        the minimum percentage ranking of each pixel in each of the
        three scenarios.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset for current LULC
        args['lulc_fut'] - is a GDAL raster dataset for future LULC
        args['carbon_pools'] - is an uncertainty dictionary that maps LULC type
                               to Mg/Ha of carbon where the field names are
                               appended by 'L', 'A', or 'H', for low, average, 
                               and high measurements.
        args['percentile'] - cuts the output to be the top and bottom
                             percentile of sequestered carbon based on
                             the uncertainty scenarios
        args['output_seq'] - a GDAL raster dataset for outputting the conservative
                            amount of carbon sequestered.
        args['output_map'] - a colorized map indicating the regions of
                            output_seq that fall into the percentile
                            ranges given in args['percentile'].  Green
                            is carbon sequestered increase and red is a
                            decrease.
        
        returns nothing"""

    area = carbon_core.pixelArea(args['lulc_cur'])
    lulcCurrent = args['lulc_cur'].GetRasterBand(1)
    lulcFuture = args['lulc_fut'].GetRasterBand(1)
    inNoData = lulcCurrent.GetNoDataValue()
    outNoData = args['output_seq'].GetRasterBand(1).GetNoDataValue()

    #This maps pool types to output_seq numbers
    poolTypes = {'L':1, 'A':2, 'H':3}
    pools = {}

    uncertaintyRank = None

    for poolType in poolTypes:
        pools[poolType] = carbon_uncertainty.build_uncertainty_pools_dict(
            args['carbon_pools'], poolType, area, inNoData, outNoData)

    def singleSelector(a, b, c):
        if c == 0: return outNoData
        return min(a, b)

    vectorSelector = np.vectorize(singleSelector)

    maxMin = None
    output_seq = args['output_seq'].GetRasterBand(1)
    #map each row in the lulc raster
    for rowNumber in range(lulcCurrent.YSize):
        dataCurrent = lulcCurrent.ReadAsArray(0, rowNumber, lulcCurrent.XSize, 1)
        dataFuture = lulcFuture.ReadAsArray(0, rowNumber, lulcFuture.XSize, 1)
        #create a seqestration map for high-low, low-high, and average-average
        sequesteredChangeArray = []
        for poolTypeA, poolTypeB in [('L', 'H'), ('H', 'L'), ('A', 'A')]:
            sequesteredCurrent = carbon_core.carbon_seq(dataCurrent, pools[poolTypeA])
            sequesteredFuture = carbon_core.carbon_seq(dataFuture, pools[poolTypeB])
            sequesteredChange = sequesteredCurrent - sequesteredFuture

            if maxMin is None:
                maxMin = (np.max(sequesteredChange), np.min(sequesteredChange))
            else:
                maxMin = (max(np.max(sequesteredChange), maxMin[0]),
                      min(np.min(sequesteredChange), maxMin[1]))

            sequesteredChangeArray.append(sequesteredChange)

        #Output the min value of l-h or h-l if average is >=0 or max value if < 0
        output_seq.WriteArray(vectorSelector(sequesteredChangeArray[0],
                                              sequesteredChangeArray[1],
                                              sequesteredChangeArray[2]), 0, rowNumber)

    #create colorband
    (minSeq, maxSeq) = output_seq.ComputeRasterMinMax()

    steps = 31
    mid = steps / 2
    def mapIndexFun(x):
        if x == 0: return 255
        if x < 0:
            return int((minSeq - x) / minSeq * mid)
        return int(steps - (maxSeq - x) / maxSeq * mid)

    #Make a simple color table that ranges from red to green
    colorTable = gdal.ColorTable()
    negColor = (255, 0, 0)
    posColor = (100, 255, 0)
    for i in range(mid):
        frac = 1 - float(i) / mid
        colorTable.SetColorEntry(i, (int(negColor[0] * frac), int(negColor[1] * frac), int(negColor[2] * frac)))
        colorTable.SetColorEntry(steps - i, (int(posColor[0] * frac), int(posColor[1] * frac), int(posColor[2] * frac)))
    colorTable.SetColorEntry(mid, (0, 0, 0))
    args['output_map'].GetRasterBand(1).SetColorTable(colorTable)

    #Cutoff output_seq based on percentile cutoff
    def percentileCutoff(val, percentCutoff, max, min):
        if max == min: return val
        p = (val - min) / (max - min)
        if p < percentCutoff or p > 1 - percentCutoff:
            return val
        return outNoData
    percentileCutoffFun = np.vectorize(percentileCutoff)

    maxIndex = np.vectorize(mapIndexFun)
    for rowNumber in range(0, output_seq.YSize):
        seqRow = output_seq.ReadAsArray(0, rowNumber, output_seq.XSize, 1)
        #select only those elements which lie within the range percentile
        seqRow = percentileCutoffFun(seqRow, args['percentile'], maxMin[0], maxMin[1])
        #map them to colors
        args['output_map'].GetRasterBand(1).WriteArray(maxIndex(seqRow), 0, rowNumber)


def valuation(args):
    """Executes the basic carbon model that maps a carbon pool dataset to a
        LULC raster.
    
        args - is a dictionary with at least the following entries:
        args['lulc_cur'] - is a GDAL raster dataset
        args['lulc_fut'] - is a GDAL raster dataset
        args['carbon_pools'] - is a DBF dataset mapping carbon sequestration numbers to lulc classifications.
        args['storage_cur'] - a GDAL raster dataset for outputing the sequestered carbon
                          based on the current lulc
        args['storage_fut'] - a GDAL raster dataset for outputing the sequestered carbon
                          based on the future lulc
        args['seq_delta'] - a GDAL raster dataset for outputing the difference between
                            args['storage_cur'] and args['storage_fut']
        args['seq_value'] - a GDAL raster dataset for outputing the monetary gain or loss in
                            value of sequestered carbon.
        args['biomass_cur'] - a GDAL raster dataset for outputing the biomass 
            of harvested HWP parcels on the current landscape
        args['biomass_fut'] - a GDAL raster dataset for outputing the biomass 
            of harvested HWP parcels on the future landscape
        args['volume_cur'] - a GDAL raster dataset for outputing the volume of 
            HWP on the current landscape
        args['volume_fut'] - a GDAL raster dataset for outputing the volume of 
            HWP on the future landscape
        args['calc_value'] - is a Boolean.  True if we wish to perform valuation.
        args['lulc_cur_year'] - is an int.  Represents the year of lulc_cur
        args['lulc_fut_year'] - is an int.  Represents the year of lulc_fut
        args['c_value'] - a float.  Represents the price of carbon in US Dollars.
        args['discount'] - a float.  Represents the annual discount in the price of carbon
        args['rate_change'] - a float.  Represents the rate of change in the price of carbon
        
        returns nothing"""

    pass
