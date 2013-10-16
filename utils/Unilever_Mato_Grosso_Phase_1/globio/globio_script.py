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

import gdal
import numpy
import scipy.ndimage
import scipy
import scipy.stats
import os
import errno
import time
from multiprocessing import Process, Pool
import collections
import signal

import numpy as np
from numpy import copy
import scipy
import scipy.ndimage.filters
import matplotlib.pyplot as plt
from invest_natcap import raster_utils


def expand_lu_type(
    base_array, nodata, expansion_id, converting_id_list, current_step, 
    pixels_per_step, land_cover_start_fractions=None,
    land_cover_end_fractions=None, end_step=None):
    """Given a base array, and a number of pixels to expand
        from, buffer out a conversion of that number of pixels
        
        base_array - a 2D array of integers that represent
            land cover IDs
        nodata - value in base_array to ignore
        expansion_id - the ID type to expand
        converting_id_list - a list of land cover types that the simulation will
            calculate distances from
        expansion_pixel_count - convert this number of pixels
        land_cover_start_percentages/land_cover_end_percentages -
            optional, if defined is a dictionary of land cover types
            that are used for conversion during the start step
        end_expansion_pixel_count - defined if land_cover_*_percentages are defined.  use to know what % of total conversion has been reached
        
        returns the new expanded array, the number of pixels per type that were converted to expansion_id
        """
        
    def step_percent(lu_code):
        total_pixels = 0
        for step_id in range(current_step):
            current_percent = float(step_id) / (end_step - 1)
            #print current_percent, pixels_per_step
            total_pixels += pixels_per_step * (
                land_cover_start_fractions[lu_code] * (1-current_percent) + 
                land_cover_end_fractions[lu_code] * current_percent)
        return total_pixels
            
    expansion_pixel_count = pixels_per_step * current_step
    
    #Calculate the expansion distance
    expansion_existance = base_array != nodata
    for converting_id in converting_id_list:
        expansion_existance = (base_array != converting_id) & expansion_existance
    edge_distance = scipy.ndimage.morphology.distance_transform_edt(
        expansion_existance)
        
    zero_distance_mask = edge_distance == 0
    edge_distance = scipy.ndimage.filters.gaussian_filter(edge_distance, 2.0)
    edge_distance[zero_distance_mask] = numpy.inf
    
    result_array = base_array.copy()
    pixels_converted_so_far = 0
    pixel_count = collections.defaultdict(int)
    for lu_code in land_cover_start_fractions:
        lu_edge_distance = edge_distance.copy()
        lu_edge_distance[base_array != lu_code] = numpy.inf
        increasing_distances = numpy.argsort(lu_edge_distance.flat)
        lu_pixels_to_convert = int(round(step_percent(lu_code)))
        result_array.flat[increasing_distances[0:lu_pixels_to_convert]] = expansion_id
        pixels_converted_so_far += int(lu_pixels_to_convert)
        pixel_count[lu_code] += int(lu_pixels_to_convert)
    edge_distance[result_array == expansion_id] = numpy.inf
    increasing_distances = numpy.argsort(edge_distance.flat)
    #print expansion_pixel_count - pixels_converted_so_far
    
    remaining_pixels = result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]]
    for lu_code in numpy.unique(remaining_pixels):
        pixel_count[lu_code] += numpy.count_nonzero(remaining_pixels == lu_code)
    result_array.flat[increasing_distances[0:(expansion_pixel_count - pixels_converted_so_far)]] = expansion_id
        
    return result_array, pixel_count


def lowpriority():
    """ Set the priority of the process to below-normal."""

    import sys
    try:
        sys.getwindowsversion()
    except:
        isWindows = False
    else:
        isWindows = True

    if isWindows:
        # Based on:
        #   "Recipe 496767: Set Process Priority In Windows" on ActiveState
        #   http://code.activestate.com/recipes/496767/
        import win32api,win32process,win32con

        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        win32process.SetPriorityClass(handle, win32process.IDLE_PRIORITY_CLASS)
    else:
        import os

        os.nice(1)

def create_globio_infrastructure(args):
    """Takes publicly available data and converts to a raster of infrastructure
    that is ready to be  inputted into calc_msa_i"""
    print 'Creating GLOBIO Infrastructure.'
    
    infrastructure = np.zeros(args['roads_array'].shape)
    infrastructure = np.where((args['roads_array'] >= 1.0) & (args['roads_array'] <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((args['highways_array'] >= 1.0) & (args['highways_array'] <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((args['transmission_lines_array'] >= 1.0) & (args['transmission_lines_array'] <= 2000.0), 1.0,infrastructure)
    infrastructure = np.where((args['canals_array'] >= 1.0) & (args['canals_array'] <= 2000.0), 1.0,infrastructure)

    #export_array_as_geotiff(infrastructure, args['export_folder']+'infrastructure_binary'+str(time.time()).split(",")[0]+'.tif', args["input_lulc_uri"])

    not_infrastructure = (infrastructure - 1)*(-1) #flip 0 and 1
    distance_to_infrastructure = scipy.ndimage.morphology.distance_transform_edt(not_infrastructure) * 500 #500 meter cell size
    #export_array_as_geotiff(distance_to_infrastructure, args['export_folder']+'distance_to_infrastructure'+str(time.time()).split(",")[0]+'.tif', args["input_lulc_uri"])

    return distance_to_infrastructure, infrastructure
    
    
def create_globio_lulc(args, scenario_lulc_array=None):
    """Converts MODIS based LULC map into GLOBIO compatible LULC.
    
    normally gets lulc data from args['input_lulc_uri'] but ignores that
    if scenario_lulc_array is defined. scenario_lulc_array should be the same
    shape as args['input_lulc_array']"""    
    
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
    
    
    
    #sum_yieldgap = np.zeros(args["input_lulc_array"].shape)
    uris_to_align = [args['input_lulc_uri'], args['potential_vegetation_uri'], args['pasture_uri']] + [
        os.path.join(args['yield_gap_data_folder'],
        crop_filename) for crop_filename in os.listdir(args['yield_gap_data_folder'])]

    #stack lulc and yield gap rasters so they all align
    aligned_uris = [raster_utils.temporary_filename() for _ in uris_to_align] 
    print 'aligning yield gap uris %s' % (str(uris_to_align))
    
    out_pixel_size = raster_utils.get_cell_size_from_uri(args["input_lulc_uri"])
    
    raster_utils.align_dataset_list(
        uris_to_align, aligned_uris, ['nearest'] * len(aligned_uris),
        out_pixel_size, "dataset", dataset_to_align_index=0,
        dataset_to_bound_index=0, assert_datasets_projected=False)
    
    sum_yieldgap = None
    for crop_yieldgap_uri in aligned_uris[3::]:
        print "Adding " + crop_yieldgap_uri + " to sum_yieldgap."
        if sum_yieldgap is None:
            sum_yieldgap = geotiff_to_array(crop_yieldgap_uri)
        else:
            crop_yieldgap_array = geotiff_to_array(crop_yieldgap_uri)
            sum_yieldgap += crop_yieldgap_array   
    print 'total sum is %s' % numpy.sum(sum_yieldgap)
    #Step 1.2b: Assign high/low according to threshold based on yieldgap.    
    high_low_intensity_agriculture = np.zeros(args["input_lulc_array"].shape)
    #high_low_intensity_agriculture_uri = args["export_folder"]+"high_low_intensity_agriculture_"+args['run_id']+".tif"
    high_intensity_agriculture_threshold = 1 #hardcode for now until UI is determined. Eventually this is a user input. Do I bring it into the ARGS dict?
    print "Splitting agriculture into high/low intensity."
    high_low_intensity_agriculture = np.where(sum_yieldgap < float(args['yieldgap_threshold']*high_intensity_agriculture_threshold), 9.0, 8.0) #45. = average yieldgap on global cells with nonzero yieldgap.


    #Step 1.2c: Stamp ag_split classes onto input LULC
    broad_lulc_ag_split = np.where(broad_lulc_array==132.0, high_low_intensity_agriculture, broad_lulc_array)

    #Step 1.3a: Split Scrublands and grasslands into pristine vegetations, 
    #livestock grazing areas, and man-made pastures. 
    three_types_of_scrubland = np.zeros(args['input_lulc_array'].shape)
    print 'Splitting shrub/grassland into human-made pasture, grazing and pristine.'
    potential_vegetation_array = geotiff_to_array(aligned_uris[1])
    three_types_of_scrubland = np.where((potential_vegetation_array <= 8) & (broad_lulc_ag_split== 131), 6.0, 5.0) # < 8 min potential veg means should have been forest, 131 in broad  is grass, so 1.0 implies man made pasture
    pasture_array = geotiff_to_array(aligned_uris[2])
    three_types_of_scrubland = np.where((three_types_of_scrubland == 5.0) & (pasture_array < args['pasture_threshold']), 1.0, three_types_of_scrubland) 

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
    for temp_uri in aligned_uris:
        os.remove(temp_uri)
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
    
def calc_msa_i(distance_to_infrastructure, input_lulc, iteration_number):
    print "Calculating MSA(Infrastructure)"
   
    
    #Calculate msa_i effects for each relevant LULC. This is based on table 6 from UNEP 2009.
    msa_i_tropical_forest = np.zeros(input_lulc.shape)
    msa_i_tropical_forest = np.where((distance_to_infrastructure > 4000.0) & (distance_to_infrastructure <= 14000.0), 0.9, 1.0)
    msa_i_tropical_forest = np.where((distance_to_infrastructure > 1000.0) & (distance_to_infrastructure <= 4000.0), 0.8, msa_i_tropical_forest)
    msa_i_tropical_forest = np.where( (distance_to_infrastructure <= 1000.0), 0.4, msa_i_tropical_forest)
    
    msa_i_temperate_and_boreal_forest = np.zeros(input_lulc.shape)
    print msa_i_temperate_and_boreal_forest.shape
    msa_i_temperate_and_boreal_forest = np.where((distance_to_infrastructure > 1200.0) & (distance_to_infrastructure <= 4200.0), 0.9, 1.0)
    print msa_i_temperate_and_boreal_forest.shape
    msa_i_temperate_and_boreal_forest = np.where((distance_to_infrastructure > 300.0) & (distance_to_infrastructure <= 1200.0), 0.8, msa_i_temperate_and_boreal_forest)
    print msa_i_temperate_and_boreal_forest.shape
    msa_i_temperate_and_boreal_forest = np.where( (distance_to_infrastructure <= 300.0), 0.4, msa_i_temperate_and_boreal_forest)
    print msa_i_temperate_and_boreal_forest.shape

    msa_i_cropland_and_grassland = np.zeros(input_lulc.shape)
    msa_i_cropland_and_grassland = np.where((distance_to_infrastructure > 2000.0) & (distance_to_infrastructure <= 7000.0), 0.9, 1.0)
    msa_i_cropland_and_grassland = np.where((distance_to_infrastructure > 500.0) & (distance_to_infrastructure <= 2000.0), 0.8, msa_i_cropland_and_grassland)
    msa_i_cropland_and_grassland = np.where( (distance_to_infrastructure <= 500.0), 0.4, msa_i_cropland_and_grassland)

    msa_i = np.zeros(input_lulc.shape)
    print msa_i.shape, input_lulc.shape, msa_i_temperate_and_boreal_forest.shape
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
    lowpriority()
    scenario_name = 'forest_edge_expansion'
    print '\nStarting GLOBIO', scenario_name,'scenario.\n'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

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
        'Percent Soy Expansion in Forest Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

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
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['aoi_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['aoi_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['aoi_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['aoi_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
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

    lowpriority()
    scenario_name = "globio_forest_core_expansion"
    print '\nStarting',scenario_name,'scenario\n.'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

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
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

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
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['aoi_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['aoi_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['aoi_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['aoi_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)

        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
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

    lowpriority()
    scenario_name = "globio_forest_core_fragmentation"
    print '\nStarting',scenario_name,'scenario.\n'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

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
        'Percent Soy Expansion in Forest Core Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    deepest_edge_index = 0

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent

        if percent > 0:         
            deepest_edge_index = args['pixels_to_convert_per_step']
            
            scenario_edge_distance = calculate_forest_edge_distance(
                scenario_lulc_array, args['forest_lucodes'], cell_size)        
            decreasing_distances = numpy.argsort(scenario_edge_distance.flat)[::-1]

            scenario_lulc_array.flat[
                decreasing_distances[0:deepest_edge_index]] = (
                    args['converting_crop'])
        #Calcualte the effect on MSA using calc_msa_lu function
        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['aoi_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['aoi_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['aoi_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['aoi_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
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
    lowpriority()
    scenario_name = 'lu_edge_expansion'
    print '\nStarting GLOBIO', scenario_name,'scenario.\n'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

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
        'Percent Soy Expansion in LU Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    #This index will keep track of the number of forest pixels converted.
    pixels_converted = 0
    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating change in MSA for expansion step %s' % percent

        if percent > 0:
            landcover_mask = numpy.where(
                scenario_lulc_array.flat == args['conversion_lucode'])
            scenario_lulc_array.flat[landcover_mask[0][
                0:args['pixels_to_convert_per_step']]] = args['converting_crop']

        globio_lulc = create_globio_lulc(args, scenario_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['aoi_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, scenario_lulc_array, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['aoi_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, scenario_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['aoi_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['aoi_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()
 
def analyze_composite_globio_change(args):
    """This function loads scenarios from disk and calculates the carbon stocks
        on them.

        args['base_biomass_filename'] - a raster that contains carbon densities
            per Ha.
        args['base_landcover_filename'] - a raster of same dimensions as
            'base_biomass_filename' that contains lucodes for the landscape
            regression analysis
        args['carbon_pool_table_filename'] - a CSV file containing carbon
            biomass values for given lucodes.  Must contain at least the
            columns 'LULC' and 'C_ABOVE_MEAN'
        args['forest_lucodes'] - a list of lucodes that are used to determine
            forest landcover types
        args['regression_lucodes'] - a list of lucodes that will use the
            linear regression to determine forest biomass given edge
            distance
        args['biomass_from_table_lucodes'] - a list of lucodes that will use
            the carbon pool csv table to determine biomass
        args['output_table_filename'] - this is the filename of the CSV
            output table.
        args['scenario_conversion_steps'] - the number of steps to run in
            the simulation
        args['scenario_path'] - the path to the directory that holds the
            scenarios
        args['converting_crop'] - when a pixel is converted to crop, it uses
            this lucode.
        args['pixels_to_convert_per_step'] - each step of the simulation
            converts this many pixels
        args['land_cover_start_fractions'] - a dictionary of landcover
            types to conversion fractions per step for the first step
            of land cover conversion.  The fractional amounts should
            add up to less than or equal to 1.  If less than 1
            land cover nearest to agriculture will be converted.
        args['land_cover_end_fractions'] - a dictionary of landcover
            types to conversion fractions per step for the last step
            of land cover conversion.  Percent of landcover will be
            linearly interpolated between 'start' and 'end' fractions.
        args['output_pixel_count_filename'] - a report of the number of pixel
            types changed per step
        """

    lowpriority()
    scenario_name = 'analyze_composite_globio_change'
    print '\nStarting GLOBIO', scenario_name,'scenario.\n'

    #create static maps that only need to be calculated once.   
    distance_to_infrastructure, infrastructure = create_globio_infrastructure(args)

    #Load the base landcover map that we use in the scenarios
    scenario_lulc_dataset = gdal.Open(args['input_lulc_uri'])
    cell_size = scenario_lulc_dataset.GetGeoTransform()[1]
    scenario_lulc_array = copy(args['input_lulc_array'])
    scenario_nodata = scenario_lulc_dataset.GetRasterBand(1).GetNoDataValue()
    scenario_lulc_dataset=None

    #Open a .csv file to dump the grassland expansion scenario
    output_table = open(args['output_table_filename'], 'wb')
    output_table.write(
        'Percent Soy Expansion in LU Expansion Scenario,Average MSA,Average MSA(LU),Average MSA(Infrastructure),Average MSA(Fragmentation)\n')

    output_count_table = open(args['output_pixel_count_filename'], 'wb')
    unique_lucodes = sorted(numpy.unique(scenario_lulc_array))
    output_count_table.write(','.join(map(str,unique_lucodes)) + '\n')

    for percent in range(args['scenario_conversion_steps'] + 1):
        print 'calculating carbon stocks for composite expansion step %s' % percent
        try:
            expanded_lulc_array, pixel_count = expand_lu_type(
                scenario_lulc_array, scenario_nodata, args['converting_crop'], 
                args['converting_id_list'], percent, args['pixels_to_convert_per_step'], 
                args['land_cover_start_fractions'], 
                args['land_cover_end_fractions'], 
                args['scenario_conversion_steps'])
        except Exception as e:
            print e
            return
        for lu_code in unique_lucodes:
            output_count_table.write('%s,' % pixel_count[lu_code])
        output_count_table.write('\n')
        output_count_table.flush()
        #Calculate the carbon stocks based on the regression functions, lookup
        #tables, and land cover raster.
        
        globio_lulc = create_globio_lulc(args, expanded_lulc_array) 
        
        msa_lu = calc_msa_lu(globio_lulc, args, percent)
        avg_msa_lu = str(float(np.mean(msa_lu[np.where(args['aoi_array'] == 1)])))
        
        msa_i = calc_msa_i(distance_to_infrastructure, expanded_lulc_array, percent)
        avg_msa_i = str(float(np.mean(msa_i[np.where(args['aoi_array'] == 1)])))
        
        msa_f = calc_msa_f(infrastructure, expanded_lulc_array, args, percent)
        avg_msa_f = str(float(np.mean(msa_f[np.where(args['aoi_array'] == 1)])))

        
        msa = msa_f * msa_lu * msa_i
        avg_msa = str(float(np.mean(msa[np.where(args['aoi_array'] == 1)])))
        print "results for",scenario_name,percent,avg_msa, np.sum(msa), np.sum(msa_f), np.sum(msa_lu), np.sum(msa_i)
        
        output_table.write('%s,%s,%s,%s,%s\n' % (percent,avg_msa,avg_msa_lu,avg_msa_i,avg_msa_f))
        output_table.flush()

 
def run_globio_mgds(number_of_steps, pool):
    output_folder = './globio_mgds_output'
    try:
        os.makedirs(output_folder)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
    #This set of args are shared by all of the LULC-generating-scenarios
    args = {
        #define which lu  codes count as forest when calculating distance to forest edge.
        'forest_lucodes' : [1,2,3,4,5],
        #number of iterations to run.
        'scenario_conversion_steps': number_of_steps, 
        #how many pixels should be converted to crop in each iteration step
        'pixels_to_convert_per_step': 932,
        #identify a new lu code for newly-created crop that we add via the simulation
        'converting_crop': 17,
        'converting_id_list': [12, 17, 120],
        #a unique string based on unix-timestamp that i postpend to each filename to avoid accidental overwriting.
        'run_id': str(time.time()).split(".")[0],
        #a table that indicates which of the input lu codes should be mapped to which intermediate lu codes (see documentation). First row reserved for labels.
        'lulc_conversion_table_uri': './inputs_mg_globio/lulc_conversion_table.csv',
        #export location
        'export_folder': output_folder,    
        #if all-crop yield data have already been calculated for your region, fill this in with the URI to the data. If this doesn't yet exist, make this variable None
        'yield_gap_data_folder': './inputs_mgds_globio/crop_specific_yieldgap_data/', #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. Will automatically sum this folder and save as sum_yieldgap.tif if sum_yieldgap.tif does not exist in the data location.
        #uri to geotiff  of potential vegetation
        'potential_vegetation_uri': './inputs_mgds_globio/potential_vegetation_proj.tif',  
        #uri to geotiff of proportion in pasture
        'pasture_uri': './inputs_mgds_globio/pasture.tif',
        #uri to geotiff that defines the zone of interest. Can be  constructed from any shapefile of any region, defined as 1 = within region, 0 = not in region.  If data need to be buffered, ensure that the extent of this map is not at the border, but rather at the extent of the buffered border.
        'aoi_uri': './inputs_mgds_globio/mgds_proj.shp',
        #uri to geotiff of lulc data. the values in this map must correspond to the values in lulc_conversion_table_uri 
        'input_lulc_uri': './inputs_mgds_globio/lulc_2008.tif',
        #the next 4 lines define the 4 elements that I used to construct a map of infrastructure. These were drawn from Digital Chart of the World and the EMBRAPA dataset from the Brazilian government. The globio script sums up these 4 sources to createa binary defined map of 1=is_infrastructure, 0=not_infrastructure and then applies the globio method to that.
        'roads_uri': './brazil_infrastructure/roads_prj.shp',
        'highways_uri': './brazil_infrastructure/highways_prj.shp',
        'transmission_lines_uri': './brazil_infrastructure/transmission_lines_prj.shp',
        'canals_uri': './brazil_infrastructure/canals_prj.shp',
        #Default of .5. pasture data is from Ramankutty  2008 and is defined as a proportion, (0,1). The threshold defined in this variable declares that any land less than the threshold is pristine vegetation, else it is defined as livestock grazing.
        'pasture_threshold': .5,   
        #areas with yieldgaps greater than this threshold are defined as low intensity (because they have not used intensification methods to reach their achievable yield) Defined in terms of tons not produed per 5min grid cell. 45.6 is the default value, representing 50% of the global average yieldgap.
        'yieldgap_threshold': 45.6804906897,
        #areas with FFQI > primary threshold are defined as primary forest
        'primary_threshold':.66,
        #areas < primary but > secondary threshold are defined as secondary forest while < secondary threshold is defined as forest-plantation
        'secondary_threshold':.33,
    }

    #This set of args store arrays for each of the inputted URIs. This method of processing is faster in my program, but could present problems if very large input data are considered. In which case, I will need to do case-specific blocking of the matrices in the analysis.
    args['input_lulc_array']= geotiff_to_array(args['input_lulc_uri'])
    aoi_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], aoi_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        aoi_raster_uri, args['aoi_uri'], burn_values=[1])
    args['aoi_array']= geotiff_to_array(aoi_raster_uri) #1 = in MG, 0 = notprintin MG
    
    roads_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], roads_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        roads_raster_uri, args['roads_uri'], burn_values=[1])
    args['roads_array']= geotiff_to_array(roads_raster_uri)
    
    highways_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], highways_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        highways_raster_uri, args['highways_uri'], burn_values=[1])
    args['highways_array']= geotiff_to_array(highways_raster_uri)
    
    transmission_lines_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], transmission_lines_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        transmission_lines_raster_uri, args['transmission_lines_uri'], burn_values=[1])
    args['transmission_lines_array']= geotiff_to_array(transmission_lines_raster_uri)
    
    canals_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], canals_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        canals_raster_uri, args['canals_uri'], burn_values=[1])
    args['canals_array']= geotiff_to_array(canals_raster_uri)
    
    
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mgds_composite_change_20_80.csv'))
    args['output_pixel_count_filename'] = (
        os.path.join(output_folder, 'globio_mgds_composite_change_20_80_mg.csv'))
    args['land_cover_start_fractions'] = {
        2: .2,
        9: .8
        }
    args['land_cover_end_fractions'] = {
        2: .8,
        9: .2
        }
    pool.apply_async(analyze_composite_globio_change, args=[args.copy()])
    
    #Set up args for the forest core expansion scenario
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mgds_forest_core_expansion_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_core_expansion, args=[args.copy()])
    
     #Set up args for the savanna scenario (via lu_expansion function)
    args['output_table_filename'] = (
       os.path.join(output_folder, 'globio_mgds_lu_expansion_msa_change_'+args['run_id']+'.csv'))
    #currently,  this code only calculates on scenario based on the globio_analyze_lu_expansion() function for savannah (with lu_code of 9). Rich defined additional scenarios but I have not been updated on these, so I have omitted them for now.
    args['conversion_lucode'] = 9
    pool.apply_async(globio_analyze_lu_expansion, args=[args.copy()])
    
    #Set up args for the forest (edge) expansion scenario
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mgds_forest_expansion_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_expansion, args=[args.copy()])
    
    args['output_table_filename'] = (
        os.path.join(output_folder,'globio_mgds_forest_core_fragmentation_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_core_fragmentation, args=[args.copy()])
 
 
def run_globio_mg(number_of_steps, pool):
    output_folder = './globio_mg_output'
    try:
        os.makedirs(output_folder)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            
    #This set of args are shared by all of the LULC-generating-scenarios
    args = {
        #define which lu  codes count as forest when calculating distance to forest edge.
        'forest_lucodes' : [1,2,3,4,5],
        #number of iterations to run.
        'scenario_conversion_steps': number_of_steps, 
        #how many pixels should be converted to crop in each iteration step
        'pixels_to_convert_per_step': 932,
        #identify a new lu code for newly-created crop that we add via the simulation
        'converting_crop': 17,
        'converting_id_list': [12, 17, 120],
        #a unique string based on unix-timestamp that i postpend to each filename to avoid accidental overwriting.
        'run_id': str(time.time()).split(".")[0],
        #a table that indicates which of the input lu codes should be mapped to which intermediate lu codes (see documentation). First row reserved for labels.
        'lulc_conversion_table_uri': './inputs_mg_globio/lulc_conversion_table.csv',
        #export location
        'export_folder': output_folder,    
        #if all-crop yield data have already been calculated for your region, fill this in with the URI to the data. If this doesn't yet exist, make this variable None
        'yield_gap_data_folder': './inputs_mg_globio/crop_specific_yieldgap_data/', #this is here because EarthStat does not provided summed yield-gap data. Thus, I created it by placing the relevant layers into this folder, ready for summation. Will automatically sum this folder and save as sum_yieldgap.tif if sum_yieldgap.tif does not exist in the data location.
        #uri to geotiff  of potential vegetation
        'potential_vegetation_uri': './inputs_mg_globio/potential_vegetation.tif',  
        #uri to geotiff of proportion in pasture
        'pasture_uri': './inputs_mg_globio/pasture.tif',
        #uri to geotiff that defines the zone of interest. Can be  constructed from any shapefile of any region, defined as 1 = within region, 0 = not in region.  If data need to be buffered, ensure that the extent of this map is not at the border, but rather at the extent of the buffered border.
        'aoi_uri': './inputs_mg_globio/mg_proj.shp',
        #uri to geotiff of lulc data. the values in this map must correspond to the values in lulc_conversion_table_uri 
        'input_lulc_uri': './inputs_mg_globio/lulc_2008.tif',
        #the next 4 lines define the 4 elements that I used to construct a map of infrastructure. These were drawn from Digital Chart of the World and the EMBRAPA dataset from the Brazilian government. The globio script sums up these 4 sources to createa binary defined map of 1=is_infrastructure, 0=not_infrastructure and then applies the globio method to that.
        'roads_uri': './brazil_infrastructure/roads_prj.shp',
        'highways_uri': './brazil_infrastructure/highways_prj.shp',
        'transmission_lines_uri': './brazil_infrastructure/transmission_lines_prj.shp',
        'canals_uri': './brazil_infrastructure/canals_prj.shp',
        #Default of .5. pasture data is from Ramankutty  2008 and is defined as a proportion, (0,1). The threshold defined in this variable declares that any land less than the threshold is pristine vegetation, else it is defined as livestock grazing.
        'pasture_threshold': .5,   
        #areas with yieldgaps greater than this threshold are defined as low intensity (because they have not used intensification methods to reach their achievable yield) Defined in terms of tons not produed per 5min grid cell. 45.6 is the default value, representing 50% of the global average yieldgap.
        'yieldgap_threshold': 45.6804906897,
        #areas with FFQI > primary threshold are defined as primary forest
        'primary_threshold':.66,
        #areas < primary but > secondary threshold are defined as secondary forest while < secondary threshold is defined as forest-plantation
        'secondary_threshold':.33,
    }
    
    #This set of args store arrays for each of the inputted URIs. This method of processing is faster in my program, but could present problems if very large input data are considered. In which case, I will need to do case-specific blocking of the matrices in the analysis.
    args['input_lulc_array']= geotiff_to_array(args['input_lulc_uri'])
    aoi_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], aoi_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        aoi_raster_uri, args['aoi_uri'], burn_values=[1])
    args['aoi_array']= geotiff_to_array(aoi_raster_uri) #1 = in MG, 0 = notprintin MG
    
    roads_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], roads_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        roads_raster_uri, args['roads_uri'], burn_values=[1])
    args['roads_array']= geotiff_to_array(roads_raster_uri)
    
    highways_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], highways_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        highways_raster_uri, args['highways_uri'], burn_values=[1])
    args['highways_array']= geotiff_to_array(highways_raster_uri)
    
    transmission_lines_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], transmission_lines_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        transmission_lines_raster_uri, args['transmission_lines_uri'], burn_values=[1])
    args['transmission_lines_array']= geotiff_to_array(transmission_lines_raster_uri)
    
    canals_raster_uri = raster_utils.temporary_filename()
    raster_utils.new_raster_from_base_uri(args['input_lulc_uri'], canals_raster_uri, 'GTiff', 255, gdal.GDT_Byte, fill_value=0)
    raster_utils.rasterize_layer_uri(
        canals_raster_uri, args['canals_uri'], burn_values=[1])
    args['canals_array']= geotiff_to_array(canals_raster_uri)
    
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mg_composite_change_20_80.csv'))
    args['output_pixel_count_filename'] = (
        os.path.join(output_folder, 'globio_mg_composite_20_80_pixel_count.csv'))
    args['land_cover_start_fractions'] = {
        2: .2,
        9: .8
        }
    args['land_cover_end_fractions'] = {
        2: .8,
        9: .2
        }
        
    pool.apply_async(analyze_composite_globio_change, [args.copy()])
        
    #Set up args for the forest core expansion scenario
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mg_forest_core_expansion_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_core_expansion, [args.copy()])
    
    #Set up args for the savanna scenario (via lu_expansion function)
    args['output_table_filename'] = (
       os.path.join(output_folder, 'globio_mg_lu_expansion_msa_change_'+args['run_id']+'.csv'))
    #currently,  this code only calculates on scenario based on the globio_analyze_lu_expansion() function for savannah (with lu_code of 9). Rich defined additional scenarios but I have not been updated on these, so I have omitted them for now.
    args['conversion_lucode'] = 9
    pool.apply_async(globio_analyze_lu_expansion, [args.copy()])
       
    #Set up args for the forest (edge) expansion scenario
    args['output_table_filename'] = (
        os.path.join(output_folder, 'globio_mg_forest_expansion_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_expansion, [args.copy()])
    
    args['output_table_filename'] = (
        os.path.join(output_folder,'globio_mg_forest_core_fragmentation_msa_change_'+args['run_id']+'.csv'))
    pool.apply_async(globio_analyze_forest_core_fragmentation, [args.copy()])

def main():
    NUMBER_OF_STEPS = 2
    
    pool = Pool(2)
    run_globio_mgds(NUMBER_OF_STEPS, pool)
    print 'MGDS closing pool and joining'
    pool.close()
    pool.join()

    pool = Pool(2)
    run_globio_mg(NUMBER_OF_STEPS, pool)
    print 'MG closing pool and joining'
    pool.close()
    pool.join()


if __name__ == '__main__':
    main()