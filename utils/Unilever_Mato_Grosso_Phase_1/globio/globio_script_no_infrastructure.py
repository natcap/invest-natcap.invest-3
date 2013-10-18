"""This script calculates the effect on biodiversity loss, measured
   by Mean Species Abundance (MSA) for two drivers: Land Use Change, 
   and Fragmentation. The GLOBIO methodology (2009, from UNEP) 
   is used to calculate MSA. The script can analyze scenarios of several types,
   including (identical to the scenario set used in the Carbon assessment):

   1) predefined scenarios as LULC GIS rasters
   2) forest erosion from edges inward
   3) grassland expansion, then forest erosion

   The program writes to several output files, including:    
   pre_calculated_scenarios_biodiversity_change.csv, 
   forest_degredation_biodiversity_change.csv and 
   grassland_expansion_biodiversity_change.csv that contains two columns, the
   first the soybean expansion percent and the second, the amount of carbon
   stocks on the landscape for each of the three scenarios above"""

SAVE_MAPS = 0 #0 = none, 1 only first and last, 2 = everything 

import gdal
import numpy
import scipy.ndimage
import scipy
import scipy.stats
import os
import errno
import time

import numpy as np
from numpy import copy
import scipy
import scipy.ndimage.filters
import matplotlib.pyplot as plt

def create_globio_lulc(args, scenario_lulc_array=None):
    """Converts MODIS based LULC map into GLOBIO compatible LULC."""    
    
    #Step 1: Calculate MSA(LU). This requires converting input LULC map to 
    #GLOBIO-compatible LULC classes and multiplying these classes by their MSA 
    #effect values from the 2009 article.
    #Step 1.1: Convert MODIS to GLOBIO_Broad (a temporary map used only as an 
    #intermediate step)
    
    if scenario_lulc_array == None: scenario_lulc_array = copy(args['input_lulc_array'])
    broad_lulc_array = assign_values_by_csv(scenario_lulc_array, args['lulc_conversion_table_uri'])

    #Step 1.2: Split Agriculture (from broad lulc) into high and low intensity 
    #agriculture. We do this by defining high intensity agriculture as 
    #grid-cells that have a yieldgap (difference between actual and max 
    #potential yield) at least above USER_INPUTTED_THRESHOLD*Avg_Yield_Gap

    #Step 1.2a: If there does not exist a pre-created sum_yieldgap or
    #Sum together EarthStat data on crop-specific yield gaps to get 
    #sum_yieldgap. Here, these 8 crops represent the only crops present in Mato 
    #Grosso. 
    
    if not os.path.exists(args["sum_yieldgap_uri"]): #if the sum_yieldgap_uri does not point to a geotiff, the program will recreate it.
        sum_yieldgap = np.zeros(args["input_lulc_array"].shape)
        crops_to_sum = os.listdir(args['yield_gap_data_folder'])
        #crops_to_sum = ["cassava_yieldgap","groundnut_yieldgap","maize_yieldgap","rapeseed_yieldgap","rice_yieldgap","sorghum_yieldgap","soybean_yieldgap","sugarcane_yieldgap",]
        for i in crops_to_sum:  
            crop_yieldgap_uri = os.path.join(args["yield_gap_data_folder"],i)
            print "Adding " + crop_yieldgap_uri + " to sum_yieldgap."
            to_add = geotiff_to_array(crop_yieldgap_uri)
            to_add_sized = np.zeros(sum_yieldgap.shape)
            to_add_sized = to_add  #this line is a bad hack because my yieldgap data had 2 extra rows on the top and 1 on the bottom. I bet Rich has a much better solution to this in raster_utils, but I didn't have time to implement.
            sum_yieldgap += to_add_sized
        export_array_as_geotiff(sum_yieldgap,args["sum_yieldgap_uri"],args["input_lulc_uri"],0)     
        args['sum_yieldgap_array'] = sum_yieldgap
    else: 
        args['sum_yieldgap_array']= geotiff_to_array(args['sum_yieldgap_uri'])
    #Step 1.2b: Assign high/low according to threshold based on yieldgap.    
    high_low_intensity_agriculture = np.zeros(args["input_lulc_array"].shape)
    #high_low_intensity_agriculture_uri = args["export_folder"]+"high_low_intensity_agriculture_"+args['run_id']+".tif"
    high_intensity_agriculture_threshold = 1 #hardcode for now until UI is determined. Eventually this is a user input. Do I bring it into the ARGS dict?
    print "Splitting agriculture into high/low intensity."
    high_low_intensity_agriculture = np.where(args['sum_yieldgap_array'] < float(args['yieldgap_threshold']*high_intensity_agriculture_threshold), 9.0, 8.0) #45. = average yieldgap on global cells with nonzero yieldgap.


    #Step 1.2c: Stamp ag_split classes onto input LULC
    broad_lulc_ag_split = np.where(broad_lulc_array==132.0, high_low_intensity_agriculture, broad_lulc_array)

    #Step 1.3a: Split Scrublands and grasslands into pristine vegetations, 
    #livestock grazing areas, and man-made pastures. 
    three_types_of_scrubland = np.zeros(args['input_lulc_array'].shape)
    print 'Splitting shrub/grassland into human-made pasture, grazing and pristine.'
    three_types_of_scrubland = np.where((args['potential_vegetation_array'] <= 8) & (broad_lulc_ag_split== 131), 6.0, 5.0) # < 8 min potential veg means should have been forest, 131 in broad  is grass, so 1.0 implies man made pasture
    three_types_of_scrubland = np.where((three_types_of_scrubland == 5.0) & (args['pasture_array'] < args['pasture_threshold']), 1.0, three_types_of_scrubland) 

    #Step 1.3b: Stamp ag_split classes onto input LULC
    broad_lulc_shrub_split = np.where(broad_lulc_ag_split==131, three_types_of_scrubland, broad_lulc_ag_split)

    #Step 1.4a: Split Forests into Primary, Secondary, Lightly Used and Plantation. 
    four_types_of_forest = np.zeros(args['input_lulc_array'].shape)
    print 'Splitting Forest into Primary, Secondary, Lightly Used and Plantation.'    
    sigma = 9
    primary_threshold = args['primary_threshold']
    secondary_threshold = args['secondary_threshold']
    is_natural = np.zeros(args['input_lulc_array'].shape) 
    is_natural = np.where((broad_lulc_shrub_split == 130) | (broad_lulc_shrub_split == 1),1.0,0.0)
    blurred = scipy.ndimage.filters.gaussian_filter(is_natural, sigma, mode='constant', cval=0.0)
    ffqi = np.where(is_natural == 1,blurred,0)
    four_types_of_forest = np.where((ffqi >= primary_threshold),1.0,four_types_of_forest)
    four_types_of_forest = np.where((ffqi < primary_threshold) & (ffqi >= secondary_threshold),3.0,four_types_of_forest)
    four_types_of_forest = np.where((ffqi < secondary_threshold),4.0,four_types_of_forest)    

    #Step 1.4b: Stamp ag_split classes onto input LULC
    globio_lulc = np.where(broad_lulc_shrub_split == 130 ,four_types_of_forest, broad_lulc_shrub_split) #stamp primary vegetation

    #export_array_as_geotiff(globio_lulc,args["export_folder"]+"globio_lulc_"+args['run_id']+".tif",args['input_lulc_uri'],0)    
    #make_map(globio_lulc)
    return globio_lulc 

    
def calc_msa_f(input_lulc, args, iteration_number):
    print "Calculating MSA(Fragmentation)"
    
    is_natural = np.where((input_lulc <= 10.0) | (input_lulc == 16),1.0,0.0)
    is_natural_buffered = is_natural
    sigma = 3
    ffqi = np.zeros(input_lulc.shape) 
    blurred = scipy.ndimage.filters.gaussian_filter(is_natural_buffered, sigma, mode='constant', cval=0.0)
    ffqi = np.where(is_natural == 1,blurred,0)

    #now write the MSA(F) per FFQI using the values in table 6.
    msa_f = np.zeros(ffqi.shape)
    msa_f = np.where((ffqi>.9825) & (ffqi <= .9984),0.95,1.0)
    msa_f = np.where((ffqi>.89771) & (ffqi <= .9825),0.90,msa_f)
    msa_f = np.where((ffqi>.578512) & (ffqi <= .89771),0.7,msa_f)
    msa_f = np.where((ffqi>.42877) & (ffqi <= .578512),0.6,msa_f)
    msa_f = np.where((ffqi <= .42877),0.3,msa_f)
     
    return msa_f


def calc_msa_lu(input_array, args, iteration_number):
    globio_lulc = input_array
    print "Calculating MSA(lu) from globio_lulc"
    #TODO: make this input  more elegant, as part of the input CSV
    msa_lu = np.zeros(globio_lulc.shape)
    msa_lu = np.where(globio_lulc == 1.0, 1.0, msa_lu)
    msa_lu = np.where(globio_lulc == 2.0, 0.7, msa_lu)
    msa_lu = np.where(globio_lulc == 3.0, 0.5, msa_lu)
    msa_lu = np.where(globio_lulc == 4.0, 0.2, msa_lu)
    msa_lu = np.where(globio_lulc == 5.0, 0.7, msa_lu)
    msa_lu = np.where(globio_lulc == 6.0, 0.1, msa_lu)
    msa_lu = np.where(globio_lulc == 7.0, 0.5, msa_lu)
    msa_lu = np.where(globio_lulc == 8.0, 0.3, msa_lu)
    msa_lu = np.where(globio_lulc == 9.0, 0.1, msa_lu)
    msa_lu = np.where(globio_lulc == 10.0, 0.05, msa_lu)
 
    return msa_lu

def assign_values_by_csv(input_array, correspondenceURI): #If input_array is not set, it loads a raster. if outRaster = None, only returns an array, else outputs a geotiff
    array_out = copy(input_array)
    table = {} 
    fileList = []
    with open(correspondenceURI, "rU") as f:
        for line in f:
            line = line.replace("\n","")
            line = line.replace("\\","/")
            fileList.append(line)
    for key, rowString in enumerate(fileList): 
        row = rowString.split(",")
        if key != 0 and row[0] != "":
            toAddKey = float(row[0])
            toAddValue = float(row[1])
            table.update({toAddKey:toAddValue})
    for k, v in table.iteritems(): 
        #print "Replacing",k,"with",v
        array_out[input_array==k] = v 
    return array_out


def calculate_forest_edge_distance(lulc_array, forest_lucodes, cell_size):
    """Generates an array that contains the distance from the edge of
        a forest inside the forest.

        lulc_array - an array of land cover codes
        forest_lucodes - a list of lucodes that are forest types
        cell_size - the size of a cell

        returns an array of same shape as lulc_array that contains the distance
            from a forest pixel to its edge."""

    forest_existance = numpy.zeros(lulc_array.shape)
    for landcover_type in forest_lucodes:
        forest_existance = forest_existance + (lulc_array == landcover_type)

    #This calculates an edge distance for the clusters of forest
    edge_distance = scipy.ndimage.morphology.distance_transform_edt(
        forest_existance) * cell_size

    return edge_distance

def export_array_as_geotiff(arrayToExport, exportFileURI, rasterURIToBeLike, noDataValue=None):
    ds = gdal.Open(rasterURIToBeLike)
    band = ds.GetRasterBand(1)
    geotransform = ds.GetGeoTransform() 
    projection = ds.GetProjection()
    if noDataValue == None: noDataValue = band.GetNoDataValue()
    datatype = band.DataType
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    
    output_raster = gdal.GetDriverByName('GTiff').Create(exportFileURI, cols, rows, 1 ,datatype)  # Open the file
    output_raster.SetGeoTransform(geotransform)
    output_raster.SetProjection(projection)   # Exports the coordinate system to the file    
    output_raster.GetRasterBand(1).SetNoDataValue(noDataValue)
    output_raster.GetRasterBand(1).WriteArray(arrayToExport)

    ds = None
    band = None

def geotiff_to_array(filepath): 
    global geotransform
    ds = gdal.Open(filepath)
    band = ds.GetRasterBand(1)
    raster = band.ReadAsArray(0, 0, ds.RasterXSize, ds.RasterYSize).astype(np.float32)
    #self.geotransform = ds.GetGeoTransform() 
    ds = None
    band = None
    return raster
    
def make_graph(x_plot, y_plot, graph_args=None):
    plt.plot(x_plot, y_plot, 'go-', label='Label', linewidth=2)
    #plt.axis([0, 15, 24, 30])
    plt.legend()
    plt.show()  

def make_map(array):
        plt.imshow(array)
        plt.gray()
        plt.colorbar()
        plt.show()
        
def globio_analyze_premade_lulc_scenarios(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges and calculates MSA for each percent
        cropland expansion.

        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.            
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_path'] - the path to the directory that holds the
            scenarios
        args['scenario_file_pattern'] - the filename pattern to load the
            scenarios, a string of the form xxxxx%nxxxx, where %n is the
            simulation step integer.            
            
        """

    scenario_name = "premade_lulc_scenarios"
    print 'Starting',scenario_name,'scenario. Note that this scenario will only work if the data in the input folder are the right shape. If you get a broadcasting shape error, it is because your inputs are not the same shape as the other GLOBIO files.'

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Fragmentation)\n')

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent

        scenario_filename = os.path.join(
            args['scenario_path'],
            args['scenario_file_pattern'].replace('%n', str(percent)))
        
        scenario_dataset = gdal.Open(scenario_filename)
        scenario_lulc_array = scenario_dataset.GetRasterBand(1).ReadAsArray()


        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_f))
        output_table.flush()
        
        
def globio_analyze_forest_expansion(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges.

        args['forest_lucodes'] - a list of lucodes that are used to determine
            forest landcover types
        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.

        """
    scenario_name = 'forest_edge_expansion'
    print '\nStarting GLOBIO', scenario_name,'scenario.\n'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_dataset=None
    scenario_lulc_array = copy(args['input_lulc_array'])
    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        

        if percent > 0:
            deepest_edge_index += args['pixels_to_convert_per_step']
            scenario_lulc_array.flat[
                increasing_distances[0:deepest_edge_index]] = (
                    args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        msa = msa_f * msa_lu
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_f))
        output_table.flush()


def globio_analyze_forest_core_expansion(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges and calculates MSA for each percent
        cropland expansion.

        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.            
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        """

    scenario_name = "globio_forest_core_expansion"
    print '\nStarting',scenario_name,'scenario\n.'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_dataset=None
    scenario_lulc_array = copy(args['input_lulc_array'])
    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in decreasing distance order starting
    #from the core pixel in.
    decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        if percent > 0:
            deepest_edge_index += args['pixels_to_convert_per_step']
            scenario_lulc_array.flat[
                decreasing_distances[0:deepest_edge_index]] = (
                    args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))

        msa_f = calc_msa_f(scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)

        output_table.write('%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_f))
        output_table.flush()

        
def globio_analyze_forest_core_fragmentation(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges and calculates MSA for each percent
        cropland expansion.

        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.            
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        """

    scenario_name = "globio_forest_core_fragmentation"
    print '\nStarting',scenario_name,'scenario.\n'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_dataset=None
    scenario_lulc_array = copy(args['input_lulc_array'])
    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent

        if percent > 0:         
            deepest_edge_index += args['pixels_to_convert_per_step']
            
            scenario_edge_distance = calculate_forest_edge_distance(
                scenario_lulc_array, args['forest_lucodes'], cell_size)        
            decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]
    
            
            
            scenario_lulc_array.flat[
                decreasing_distances[0:deepest_edge_index]] = (
                    args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))
        
        msa = msa_f * msa_lu
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)

        
        output_table.write('%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_f))
        output_table.flush()

        
def globio_analyze_lu_expansion(args):
    """This function does a simulation of cropland expansion by
        expanding into the forest edges.

        args['forest_lucodes'] - a list of lucodes that are used to determine
            forest landcover types
        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['output_table_filename'] - this is the filename of the CSV
            output table. 
        args['conversion_lucode'] - Which LU we will be changing.
        """
    scenario_name = 'lu_edge_expansion'
    print '\nStarting GLOBIO', scenario_name,'scenario.\n'

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_dataset=None
    scenario_lulc_array = copy(args['input_lulc_array'])
    total_converting_pixels = numpy.count_nonzero(
        scenario_lulc_array == args['conversion_lucode'])

    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in increasing distance order starting
    #from the fist pixel in.  Set the pixels outside to at a distance of
    #infinity so that we visit the inner edge forest pixels first
    scenario_edge_distance[scenario_edge_distance == 0] = numpy.inf
    increasing_distances = numpy.argsort(scenario_edge_distance.flat)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in LU Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    pixels_converted = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        
#        deepest_edge_index += args['pixels_to_convert_per_step']
#        scenario_lulc_array.flat[
#            increasing_distances[0:deepest_edge_index]] = (
#                args['converting_crop'])
#        #Calcualte the effect on MSA using calc_msa_lu function
    #Convert lulc for the next iteration
        #This section converts grassland
        if percent > 0:
            landcover_mask = numpy.where(
                scenario_lulc_array.flat == args['conversion_lucode'])
            scenario_lulc_array.flat[landcover_mask[0][
                0:args['pixels_to_convert_per_step']]] = args['converting_crop']

        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))
        
        msa = msa_f * msa_lu
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
 
 
if __name__ == '__main__':
    try:
        os.makedirs('./export')
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
    #This set of ARGS are shared by all of the LULC-generating-scenarios
    ARGS = {
        #define which lu  codes count as forest when calculating distance to forest edge.
        'forest_lucodes' : [1,2,3,4,5],
        #number of iterations to run.
        'scenario_conversion_steps': 2, 
        #how many pixels should be converted to crop in each iteration step
        'pixels_to_convert_per_step': 2608,
        #identify a new lu code for newly-created crop that we add via the simulation
        'converting_crop': 120,
        #a unique string based on unix-timestamp that i postpend to each filename to avoid accidental overwriting.
        'run_id': str(time.time()).split(".")[0],  
        #location where all data not specified below are stored 
        'data_location': './',
        #a table that indicates which of the input lu codes should be mapped to which intermediate lu codes (see documentation). First row reserved for labels.
        'lulc_conversion_table_uri': './lulc_conversion_table.csv',
        #export location
        'export_folder': './export/',    
        #if all-crop yield data have already been calculated for your region, fill this in with the URI to the data. If this doesn't yet exist, make this variable None
        'sum_yieldgap_uri': './sum_yieldgap.tif', #TODO: fix so that this smartly chooses to load premade or folder-based calculation  
        #if sum_yieldgap_uri is None, this variable indicates where crop-specific yieldgap maps (available at earthstat.org, see documentation) are placed. The script then aggregates them to creat sum_yieldgap.tif
        'yield_gap_data_folder': './crop_specific_yieldgap_data/', #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. Will automatically sum this folder and save as sum_yieldgap.tif if sum_yieldgap.tif does not exist in the data location.
        #uri to geotiff  of potential vegetation
        'potential_vegetation_uri': './potential_vegetation.tif',  
        #uri to geotiff of proportion in pasture
        'pasture_uri': './pasture.tif',
        #uri to geotiff that defines the zone of interest. Can be  constructed from any shapefile of any region, defined as 1 = within region, 0 = not in region.  If data need to be buffered, ensure that the extent of this map is not at the border, but rather at the extent of the buffered border.
        'mg_definition_uri': './mg_definition.tif',
        #uri to geotiff of lulc data. the values in this map must correspond to the values in lulc_conversion_table_uri 
        'input_lulc_uri': './lulc_2008.tif',
        #Default of .5. pasture data is from Ramankutty  2008 and is defined as a proportion, (0,1). The threshold defined in this variable declares that any land less than the threshold is pristine vegetation, else it is defined as livestock grazing.
        'pasture_threshold': .5,   
        #areas with yieldgaps greater than this threshold are defined as low intensity (because they have not used intensification methods to reach their achievable yield) Defined in terms of tons not produed per 5min grid cell. 45.6 is the default value, representing 50% of the global average yieldgap.
        'yieldgap_threshold': 45.6804906897,
        #areas with FFQI > primary threshold are defined as primary forest
        'primary_threshold':.66,
        #areas < primary but > secondary threshold are defined as secondary forest while < secondary threshold is defined as forest-plantation
        'secondary_threshold':.33,
  }            

    #This set of ARGS store arrays for each of the inputted URIs. This method of processing is faster in my program, but could present problems if very large input data are considered. In which case, I will need to do case-specific blocking of the matrices in the analysis.
    ARGS['input_lulc_array']= geotiff_to_array(ARGS['input_lulc_uri'])
    ARGS['potential_vegetation_array']= geotiff_to_array(ARGS['potential_vegetation_uri'])
    ARGS['pasture_array']= geotiff_to_array(ARGS['pasture_uri'])
    ARGS['mg_definition_array']= geotiff_to_array(ARGS['mg_definition_uri']) #1 = in MG, 0 = notprintin MG

    #Set up the ARGS for the disk based scenario
    ARGS['scenario_path'] = './data/MG_Soy_Exp_07122013/'
    ARGS['scenario_file_pattern'] = 'mg_lulc%n'
    ARGS['output_table_filename'] = ('./export/globio_premade_lulc_scenarios_msa_change_'+ARGS['run_id']+'.csv')
    #globio_analyze_premade_lulc_scenarios(ARGS) 

    #Set up ARGS for the forest core expansion scenario
    ARGS['output_table_filename'] = (
        './export/globio_forest_core_expansion_msa_change_'+ARGS['run_id']+'.csv')
    globio_analyze_forest_core_expansion(ARGS)
    
     #Set up ARGS for the savanna scenario (via lu_expansion function)
    ARGS['output_table_filename'] = (
       './export/globio_lu_expansion_msa_change_'+ARGS['run_id']+'.csv')
    #currently,  this code only calculates on scenario based on the globio_analyze_lu_expansion() function for savannah (with lu_code of 9). Rich defined additional scenarios but I have not been updated on these, so I have omitted them for now.
    ARGS['conversion_lucode'] = 9
    globio_analyze_lu_expansion(ARGS)
       
    #Set up ARGS for the forest (edge) expansion scenario
    ARGS['output_table_filename'] = (
        './export/globio_forest_expansion_msa_change_'+ARGS['run_id']+'.csv')
    globio_analyze_forest_expansion(ARGS)

    ARGS['output_table_filename'] = (
        './export/globio_forest_core_fragmentation_msa_change_'+ARGS['run_id']+'.csv')
    globio_analyze_forest_core_fragmentation(ARGS)