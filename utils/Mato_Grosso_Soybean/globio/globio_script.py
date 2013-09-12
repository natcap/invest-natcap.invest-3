"""This script calculates the effect on biodiversity loss, measured
   by Mean Species Abundance (MSA) for three drivers: Land Use Change, 
   Infrastructure and Fragmentation. The GLOBIO methodology (2009, from UNEP) 
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

def create_globio_infrastructure(args):
    """Takes publicly available data and converts to a raster of infrastructure
    that is ready to be  inputted into calc_msa_i"""
    print 'Creating GLOBIO Infrastructure.'
    roads = geotiff_to_array(args['data_location']+"roads.tif")[0:2528:1,0:2695:1]
    highways = geotiff_to_array(args['data_location']+"highways.tif")[0:2528:1,0:2695:1]
    transmission_lines = geotiff_to_array(args['data_location']+"transmission_lines.tif")[0:2528:1,0:2695:1]
    canals = geotiff_to_array(args['data_location']+"canals.tif")[0:2528:1,0:2695:1]
    
    infrastructure = np.zeros(roads.shape)
    infrastructure = np.where((roads >= 1.0) & (roads <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((highways >= 1.0) & (highways <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((transmission_lines >= 1.0) & (transmission_lines <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((canals >= 1.0) & (canals <= 2000.0), 1.0,infrastructure)

    #export_array_as_geotiff(infrastructure, args['export_folder']+'infrastructure_binary'+str(time.time()).split(",")[0]+'.tif', args["input_lulc_uri"])

    not_infrastructure = (infrastructure - 1)*(-1) #flip 0 and 1
    distance_to_infrastructure = scipy.ndimage.morphology.distance_transform_edt(not_infrastructure) * 500 #500 meter cell size
    #export_array_as_geotiff(distance_to_infrastructure, args['export_folder']+'distance_to_infrastructure'+str(time.time()).split(",")[0]+'.tif', args["input_lulc_uri"])

    return distance_to_infrastructure, infrastructure
    
    
def create_globio_lulc(args, scenario_lulc_array=None):
    """Converts MODIS based LULC map into GLOBIO compatible LULC."""    
    
    #Step 1: Calculate MSA(LU). This requires converting input LULC map to 
    #GLOBIO-compatible LULC classes and multiplying these classes by their MSA 
    #effect values from the 2009 article.
    #Step 1.1: Convert MODIS to GLOBIO_Broad (a temporary map used only as an 
    #intermediate step)
    
    if scenario_lulc_array == None: scenario_lulc_array = args['input_lulc_array']
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
        crops_to_sum = ["cassava_yieldgap","groundnut_yieldgap","maize_yieldgap","rapeseed_yieldgap","rice_yieldgap","sorghum_yieldgap","soybean_yieldgap","sugarcane_yieldgap",]
        for i in crops_to_sum:  
            crop_yieldgap_uri = args["yield_gap_data_folder"]+i+".tif"
            print "Adding " + crop_yieldgap_uri + " to sum_yieldgap."
            to_add = geotiff_to_array(crop_yieldgap_uri)[0:2528:1,0:2695:1]
            to_add_sized = np.zeros(sum_yieldgap.shape)
            to_add_sized = to_add  #this line is a bad hack because my yieldgap data had 2 extra rows on the top and 1 on the bottom. I bet Rich has a much better solution to this in raster_utils, but I didn't have time to implement.
            sum_yieldgap += to_add_sized
        export_array_as_geotiff(sum_yieldgap,args["sum_yieldgap_uri"],args["input_lulc_array"],0)     
        
    #Step 1.2b: Assign high/low according to threshold based on yieldgap.    
    high_low_intensity_agriculture = np.zeros(args["input_lulc_array"].shape)
    #high_low_intensity_agriculture_uri = args["export_folder"]+"high_low_intensity_agriculture_"+args['run_id']+".tif"
    high_intensity_agriculture_threshold = 1 #hardcode for now until UI is determined. Eventually this is a user input. Do I bring it into the ARGS dict?
    print "Splitting agriculture into high/low intensity."
    high_low_intensity_agriculture = np.where(args['sum_yieldgap_array'] < float(45.6804906897*high_intensity_agriculture_threshold), 9.0, 8.0) #45. = average yieldgap on global cells with nonzero yieldgap.


    #Step 1.2c: Stamp ag_split classes onto input LULC
    broad_lulc_ag_split = np.where(broad_lulc_array==132.0, high_low_intensity_agriculture, broad_lulc_array)

    #Step 1.3a: Split Scrublands and grasslands into pristine vegetations, 
    #livestock grazing areas, and man-made pastures. 
    three_types_of_scrubland = np.zeros(args['input_lulc_array'].shape)
    print 'Splitting shrub/grassland into human-made pasture, grazing and pristine.'
    three_types_of_scrubland = np.where((args['potential_vegetation_array'] <= 8) & (broad_lulc_ag_split== 131), 6.0, 5.0) # < 8 min potential veg means should have been forest, 131 in broad  is grass, so 1.0 implies man made pasture
    three_types_of_scrubland = np.where((three_types_of_scrubland == 5.0) & (args['pasture_array'] < .5), 1.0, three_types_of_scrubland) #TODO also hardcoded this .5. #pasture is from Ramankutty  2008 and is (0,1). Thus, if a random float is less than, assign it as  LiveStock Grazing" else pristine veg"

    #Step 1.3b: Stamp ag_split classes onto input LULC
    broad_lulc_shrub_split = np.where(broad_lulc_ag_split==131, three_types_of_scrubland, broad_lulc_ag_split)

    #Step 1.4a: Split Forests into Primary, Secondary, Lightly Used and Plantation. 
    four_types_of_forest = np.zeros(args['input_lulc_array'].shape)
    print 'Splitting Forest into Primary, Secondary, Lightly Used and Plantation.'    
    sigma = 9
    primary_threshold = .66
    secondary_threshold = .33
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

    
def calc_msa_f(infrastructure, input_lulc, args, iteration_number):
    print "Calculating MSA(Fragmentation)"
    not_infrastructure = (infrastructure - 1)*(-1)
    not_infrastructure_buffered = np.where((scipy.ndimage.morphology.distance_transform_edt(not_infrastructure) * 500) < 1000,1.0,0.0)   #500 meter cell size, 3.1622 = 10^.5
    infrastructure_buffered = (not_infrastructure_buffered-1)*(-1)
    
    is_natural = np.where((input_lulc <= 10.0) | (input_lulc == 16),1.0,0.0)
    is_natural_buffered = np.where(infrastructure_buffered == 0.0,0.0,is_natural)
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
    
def calc_msa_i(distance_to_infrastructure, input_lulc, args, iteration_number):
    print "Calculating MSA(Infrastructure)"
   
    
    #Calculate msa_i effects for each relevant LULC. This is based on table 6 from UNEP 2009.
    msa_i_tropical_forest = np.zeros(input_lulc.shape)
    msa_i_tropical_forest = np.where((distance_to_infrastructure > 4000.0) & (distance_to_infrastructure <= 14000.0), 0.9, 1.0)
    msa_i_tropical_forest = np.where((distance_to_infrastructure > 1000.0) & (distance_to_infrastructure <= 4000.0), 0.8, msa_i_tropical_forest)
    msa_i_tropical_forest = np.where( (distance_to_infrastructure <= 1000.0), 0.4, msa_i_tropical_forest)
    
    msa_i_temperate_and_boreal_forest = np.zeros(input_lulc.shape)
    msa_i_temperate_and_boreal_forest = np.where((distance_to_infrastructure > 1200.0) & (distance_to_infrastructure <= 4200.0), 0.9, 1.0)
    msa_i_temperate_and_boreal_forest = np.where((distance_to_infrastructure > 300.0) & (distance_to_infrastructure <= 1200.0), 0.8, msa_i_temperate_and_boreal_forest)
    msa_i_temperate_and_boreal_forest = np.where( (distance_to_infrastructure <= 300.0), 0.4, msa_i_temperate_and_boreal_forest)

    msa_i_cropland_and_grassland = np.zeros(input_lulc.shape)
    msa_i_cropland_and_grassland = np.where((distance_to_infrastructure > 2000.0) & (distance_to_infrastructure <= 7000.0), 0.9, 1.0)
    msa_i_cropland_and_grassland = np.where((distance_to_infrastructure > 500.0) & (distance_to_infrastructure <= 2000.0), 0.8, msa_i_cropland_and_grassland)
    msa_i_cropland_and_grassland = np.where( (distance_to_infrastructure <= 500.0), 0.4, msa_i_cropland_and_grassland)

    msa_i = np.zeros(input_lulc.shape)
    msa_i = np.where((input_lulc >= 1) & (input_lulc <= 5), msa_i_temperate_and_boreal_forest,1.0)
    msa_i = np.where((input_lulc >= 6) & (input_lulc <= 12), msa_i_cropland_and_grassland,msa_i)
    
    return msa_i


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
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        args['scenario_path'] - the path to the directory that holds the
            scenarios
        args['scenario_file_pattern'] - the filename pattern to load the
            scenarios, a string of the form xxxxx%nxxxx, where %n is the
            simulation step integer.            
            
        """

    scenario_name = "premade_lulc_scenarios"
    print 'Starting',scenario_name,'scenario.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent

        scenario_filename = os.path.join(
            args['scenario_path'],
            args['scenario_file_pattern'].replace('%n', str(percent)))
        
        scenario_dataset = gdal.Open(scenario_filename)
        scenario_lulc_array = scenario_dataset.GetRasterBand(1).ReadAsArray()[0:2528:1,0:2695:1]
        print scenario_lulc_array.shape

        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, args, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
        if SAVE_MAPS >= 1 and (percent == 0 or percent == args['scenario_conversion_steps'] + 1) or SAVE_MAPS == 2:
            export_array_as_geotiff(scenario_lulc_array,args['export_folder']+scenario_name+"_scenario_lulc_array_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(globio_lulc,args['export_folder']+scenario_name+"_globio_lulc_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_lu,args['export_folder']+scenario_name+"_msa_lu_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_i,args['export_folder']+scenario_name+"_msa_i_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_f,args['export_folder']+scenario_name+"_msa_f_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
            export_array_as_geotiff(msa,args['export_folder']+scenario_name+"_msa_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
    if SAVE_MAPS >= 1:
        export_array_as_geotiff(distance_to_infrastructure,args['export_folder']+scenario_name+"_distance_to_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
        export_array_as_geotiff(infrastructure,args['export_folder']+scenario_name+"_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
        
        
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
    print 'Starting GLOBIO', scenario_name,'scenario.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = args['input_lulc_array']
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
        'Percent Soy Expansion in Forest Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        
        deepest_edge_index += args['pixels_to_convert_per_step']
        scenario_lulc_array.flat[
            increasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, args, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
        if SAVE_MAPS >= 1 and (percent == 0 or percent == args['scenario_conversion_steps'] + 1) or SAVE_MAPS == 2:
            export_array_as_geotiff(scenario_lulc_array,args['export_folder']+scenario_name+"_scenario_lulc_array_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(globio_lulc,args['export_folder']+scenario_name+"_globio_lulc_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_lu,args['export_folder']+scenario_name+"_msa_lu_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_i,args['export_folder']+scenario_name+"_msa_i_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_f,args['export_folder']+scenario_name+"_msa_f_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
            export_array_as_geotiff(msa,args['export_folder']+scenario_name+"_msa_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
    if SAVE_MAPS >= 1:
        export_array_as_geotiff(distance_to_infrastructure,args['export_folder']+scenario_name+"_distance_to_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
        export_array_as_geotiff(infrastructure,args['export_folder']+scenario_name+"_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])


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
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """

    scenario_name = "globio_forest_core_expansion"
    print 'Starting',scenario_name,'scenario.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = args['input_lulc_array']
    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #We want to visit the edge pixels in decreasing distance order starting
    #from the core pixel in.
    decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        
        deepest_edge_index += args['pixels_to_convert_per_step']
        scenario_lulc_array.flat[
            decreasing_distances[0:deepest_edge_index]] = (
                args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, args, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
        if SAVE_MAPS >= 1 and (percent == 0 or percent == args['scenario_conversion_steps'] + 1) or SAVE_MAPS == 2:
            export_array_as_geotiff(scenario_lulc_array,args['export_folder']+scenario_name+"_scenario_lulc_array_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(globio_lulc,args['export_folder']+scenario_name+"_globio_lulc_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_lu,args['export_folder']+scenario_name+"_msa_lu_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_i,args['export_folder']+scenario_name+"_msa_i_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_f,args['export_folder']+scenario_name+"_msa_f_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
            export_array_as_geotiff(msa,args['export_folder']+scenario_name+"_msa_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
    if SAVE_MAPS >= 1:
        export_array_as_geotiff(distance_to_infrastructure,args['export_folder']+scenario_name+"_distance_to_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
        export_array_as_geotiff(infrastructure,args['export_folder']+scenario_name+"_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])

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
        args['scenario_lulc_base_map_filename'] - the base LULC map used for
            the scenario runs
        """

    scenario_name = "globio_forest_core_fragmentation"
    print 'Starting',scenario_name,'scenario.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = args['input_lulc_array']
    scenario_edge_distance = calculate_forest_edge_distance(
        scenario_lulc_array, args['forest_lucodes'], cell_size)

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent
        
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
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, args, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
        if SAVE_MAPS >= 1 and (percent == 0 or percent == args['scenario_conversion_steps'] + 1) or SAVE_MAPS == 2:
            export_array_as_geotiff(scenario_lulc_array,args['export_folder']+scenario_name+"_scenario_lulc_array_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(globio_lulc,args['export_folder']+scenario_name+"_globio_lulc_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_lu,args['export_folder']+scenario_name+"_msa_lu_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_i,args['export_folder']+scenario_name+"_msa_i_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_f,args['export_folder']+scenario_name+"_msa_f_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
            export_array_as_geotiff(msa,args['export_folder']+scenario_name+"_msa_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
    if SAVE_MAPS >= 1:
        export_array_as_geotiff(distance_to_infrastructure,args['export_folder']+scenario_name+"_distance_to_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
 
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
    print 'Starting GLOBIO', scenario_name,'scenario.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = args['input_lulc_array']
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
        'Percent Soy Expansion in LU Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

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
        landcover_mask = numpy.where(
            scenario_lulc_array.flat == args['conversion_lucode'])
        scenario_lulc_array.flat[landcover_mask[0][
            0:args['pixels_to_convert_per_step']]] = args['converting_crop']

        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['mg_definition_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, args, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['mg_definition_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['mg_definition_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['mg_definition_array'] == 1)])))
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
        if SAVE_MAPS >= 1 and (percent == 0 or percent == args['scenario_conversion_steps'] + 1) or SAVE_MAPS == 2:
            export_array_as_geotiff(scenario_lulc_array,args['export_folder']+scenario_name+"_scenario_lulc_array_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(globio_lulc,args['export_folder']+scenario_name+"_globio_lulc_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_lu,args['export_folder']+scenario_name+"_msa_lu_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_i,args['export_folder']+scenario_name+"_msa_i_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
            export_array_as_geotiff(msa_f,args['export_folder']+scenario_name+"_msa_f_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
            export_array_as_geotiff(msa,args['export_folder']+scenario_name+"_msa_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri']) 
    if SAVE_MAPS >= 1:
        export_array_as_geotiff(distance_to_infrastructure,args['export_folder']+scenario_name+"_distance_to_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])
        export_array_as_geotiff(infrastructure,args['export_folder']+scenario_name+"_infrastructure_"+str(args['run_id'])+"_"+str(percent)+".tif",args['input_lulc_uri'])

 
 
if __name__ == '__main__':
    try:
        os.makedirs('./data/export')
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise    

    #sets up forest expansion scenario
    args = {}
    args['forest_lucodes'] = [1,2,3,4,5]
    args['scenario_conversion_steps'] = 2
    args['run_id'] = str(time.time()).split(".")[0]
    args['input_lulc_uri'] = './data/lulc_2008.tif'
    args['input_lulc_array'] = geotiff_to_array(args['input_lulc_uri'])[0:2528:1,0:2695:1] #TODO: This was a bad hack I had to do because I accidentally made my data wrong sizes by 1 pixel but didn't  have time to fix.
    args['pixels_to_convert_per_step'] = 2608*4 #default 2608. 
    args['converting_crop'] = 120,
    args['data_location'] = './data/'
    args['output_table_filename'] = (
        './data/export/globio_forest_expansion_msa_change_'+args['run_id']+'.csv')
    args['lulc_conversion_table_uri'] = './lulc_conversion_table.csv'
    args['export_folder'] = './data/export/'
    args['sum_yieldgap_uri'] = './data/sum_yieldgap.tif' 
    args['sum_yieldgap_array'] = geotiff_to_array(args['sum_yieldgap_uri'])[0:2528:1,0:2695:1]
    args['yield_gap_data_folder'] = './data/' #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. 
    args['potential_vegetation_uri'] = './data/potential_vegetation.tif'
    args['potential_vegetation_array'] = geotiff_to_array(args['potential_vegetation_uri'])[0:2528:1,0:2695:1]
    args['pasture_uri'] = './data/pasture.tif'
    args['pasture_array'] = geotiff_to_array(args['pasture_uri'])[0:2528:1,0:2695:1]
    args['mg_definition_uri'] = './data/mg_definition.tif'
    args['mg_definition_array'] = geotiff_to_array(args['mg_definition_uri'])[0:2528:1,0:2695:1] #1 = in MG, 0 = not in MG
    globio_analyze_forest_expansion(args)

    #set up args for forest core expansion scenario using GLOBIO
    args = {}
    args['forest_lucodes'] = [1,2,3,4,5]
    args['scenario_conversion_steps'] = 2
    args['run_id'] = str(time.time()).split(".")[0]
    args['input_lulc_uri'] = './data/lulc_2008.tif'
    args['input_lulc_array'] = geotiff_to_array(args['input_lulc_uri'])[0:2528:1,0:2695:1] #TODO: This was a bad hack I had to do because I accidentally made my data wrong sizes by 1 pixel but didn't  have time to fix.
    args['pixels_to_convert_per_step'] = 2608*4 #default 2608. 
    args['converting_crop'] = 120,
    args['data_location'] = './data/'
    args['output_table_filename'] = (
        './data/export/globio_forest_core_expansion_msa_change_'+args['run_id']+'.csv')
    args['lulc_conversion_table_uri'] = './lulc_conversion_table.csv'
    args['export_folder'] = './data/export/'
    args['sum_yieldgap_uri'] = './data/sum_yieldgap.tif' 
    args['sum_yieldgap_array'] = geotiff_to_array(args['sum_yieldgap_uri'])[0:2528:1,0:2695:1]
    args['yield_gap_data_folder'] = './data/' #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. 
    args['potential_vegetation_uri'] = './data/potential_vegetation.tif'
    args['potential_vegetation_array'] = geotiff_to_array(args['potential_vegetation_uri'])[0:2528:1,0:2695:1]
    args['pasture_uri'] = './data/pasture.tif'
    args['pasture_array'] = geotiff_to_array(args['pasture_uri'])[0:2528:1,0:2695:1]
    args['mg_definition_uri'] = './data/mg_definition.tif'
    args['mg_definition_array'] = geotiff_to_array(args['mg_definition_uri'])[0:2528:1,0:2695:1] #1 = in MG, 0 = not in MG
    globio_analyze_forest_core_expansion(args)

    #set up args for forest core fragmentation scenario using GLOBIO
    args = {}
    args['forest_lucodes'] = [1,2,3,4,5]
    args['scenario_conversion_steps'] = 2
    args['run_id'] = str(time.time()).split(".")[0]
    args['input_lulc_uri'] = './data/lulc_2008.tif'
    args['input_lulc_array'] = geotiff_to_array(args['input_lulc_uri'])[0:2528:1,0:2695:1] #TODO: This was a bad hack I had to do because I accidentally made my data wrong sizes by 1 pixel but didn't  have time to fix.
    args['pixels_to_convert_per_step'] = 2608*4 #default 2608. 
    args['converting_crop'] = 120,
    args['data_location'] = './data/'
    args['output_table_filename'] = (
        './data/export/globio_forest_core_fragmentation_msa_change_'+args['run_id']+'.csv')
    args['lulc_conversion_table_uri'] = './lulc_conversion_table.csv'
    args['export_folder'] = './data/export/'
    args['sum_yieldgap_uri'] = './data/sum_yieldgap.tif' 
    args['sum_yieldgap_array'] = geotiff_to_array(args['sum_yieldgap_uri'])[0:2528:1,0:2695:1]
    args['yield_gap_data_folder'] = './data/' #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. 
    args['potential_vegetation_uri'] = './data/potential_vegetation.tif'
    args['potential_vegetation_array'] = geotiff_to_array(args['potential_vegetation_uri'])[0:2528:1,0:2695:1]
    args['pasture_uri'] = './data/pasture.tif'
    args['pasture_array'] = geotiff_to_array(args['pasture_uri'])[0:2528:1,0:2695:1]
    args['mg_definition_uri'] = './data/mg_definition.tif'
    args['mg_definition_array'] = geotiff_to_array(args['mg_definition_uri'])[0:2528:1,0:2695:1] #1 = in MG, 0 = not in MG
    globio_analyze_forest_core_fragmentation(args)

    #set up args for forest lu expansion scenario using GLOBIO
    args = {}
    args['forest_lucodes'] = [1,2,3,4,5]
    args['scenario_conversion_steps'] = 2
    args['run_id'] = str(time.time()).split(".")[0]
    args['input_lulc_uri'] = './data/lulc_2008.tif'
    args['input_lulc_array'] = geotiff_to_array(args['input_lulc_uri'])[0:2528:1,0:2695:1] #TODO: This was a bad hack I had to do because I accidentally made my data wrong sizes by 1 pixel but didn't  have time to fix.
    args['pixels_to_convert_per_step'] = 2608*4 #default 2608. 
    args['converting_crop'] = 120,
    args['data_location'] = './data/'
    args['output_table_filename'] = (
        './data/export/globio_lu_expansion_msa_change_'+args['run_id']+'.csv')
    args['lulc_conversion_table_uri'] = './lulc_conversion_table.csv'
    args['export_folder'] = './data/export/'
    args['sum_yieldgap_uri'] = './data/sum_yieldgap.tif' 
    args['sum_yieldgap_array'] = geotiff_to_array(args['sum_yieldgap_uri'])[0:2528:1,0:2695:1]
    args['yield_gap_data_folder'] = './data/' #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. 
    args['potential_vegetation_uri'] = './data/potential_vegetation.tif'
    args['potential_vegetation_array'] = geotiff_to_array(args['potential_vegetation_uri'])[0:2528:1,0:2695:1]
    args['pasture_uri'] = './data/pasture.tif'
    args['pasture_array'] = geotiff_to_array(args['pasture_uri'])[0:2528:1,0:2695:1]
    args['mg_definition_uri'] = './data/mg_definition.tif'
    args['mg_definition_array'] = geotiff_to_array(args['mg_definition_uri'])[0:2528:1,0:2695:1] #1 = in MG, 0 = not in MG
    args['conversion_lucode'] = 9
    globio_analyze_lu_expansion(args)
    
    #set up args for premade lulc scenario using GLOBIO
    args = {}
    args['forest_lucodes'] = [1,2,3,4,5]
    args['scenario_conversion_steps'] = 2
    args['run_id'] = str(time.time()).split(".")[0]
    args['input_lulc_uri'] = './data/lulc_2008.tif'
    args['input_lulc_array'] = geotiff_to_array(args['input_lulc_uri'])[0:2528:1,0:2695:1] #TODO: This was a bad hack I had to do because I accidentally made my data wrong sizes by 1 pixel but didn't  have time to fix.
    args['pixels_to_convert_per_step'] = 2608*4 #default 2608. 
    args['converting_crop'] = 120,
    args['data_location'] = './data/'
    args['output_table_filename'] = (
        './data/export/globio_premade_lulc_scenarios_msa_change_'+args['run_id']+'.csv')
    args['lulc_conversion_table_uri'] = './lulc_conversion_table.csv'
    args['export_folder'] = './data/export/'
    args['sum_yieldgap_uri'] = './data/sum_yieldgap.tif' 
    args['sum_yieldgap_array'] = geotiff_to_array(args['sum_yieldgap_uri'])[0:2528:1,0:2695:1]
    args['yield_gap_data_folder'] = './data/' #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. 
    args['potential_vegetation_uri'] = './data/potential_vegetation.tif'
    args['potential_vegetation_array'] = geotiff_to_array(args['potential_vegetation_uri'])[0:2528:1,0:2695:1]
    args['pasture_uri'] = './data/pasture.tif'
    args['pasture_array'] = geotiff_to_array(args['pasture_uri'])[0:2528:1,0:2695:1]
    args['mg_definition_uri'] = './data/mg_definition.tif'
    args['mg_definition_array'] = geotiff_to_array(args['mg_definition_uri'])[0:2528:1,0:2695:1] #1 = in MG, 0 = not in MG
    args['scenario_path'] = './data/MG_Soy_Exp_07122013/'
    args['scenario_file_pattern'] = 'mg_lulc%n'
    #globio_analyze_premade_lulc_scenarios(args) #Currently, this does not work with the projection Brad used ( I couldn't figure out which it was), so I just randomly crop the image to be the right size. This  makes the results here inaccurate, but if the user were to supply a set of maps with known projections, it would  be accurate.