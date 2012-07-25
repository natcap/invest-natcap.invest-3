'''inVEST core module to handle all actual processing of overlap analysis data.'''
import os
import math
import logging

from osgeo import ogr
from osgeo import gdal
from invest_natcap import raster_utils

LOGGER = logging.getLogger('overlap_analysis_core')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This function will take the properly formatted arguments passed to it by
    overlap_analysis.py in the args dictionary, and perform calculations using
    these data to determine the optimal areas for activities.
    
    Input:
        args['workspace_dir'] - The directory in which all output and intermediate
            files should be placed.
        args['zone_layer_file'] - This is the shapefile representing our area of
            interest. If 'do_grid' is true, this will be a series of square polygons
            of size 'grid_size' that span the entire bounding envelope of the AOI.
            If 'do_grid' is false, then this is a file with management zones instead
            of identical grids. 
        args['do_grid'] - This tells us whether the area of interest file that was
            being passed in was a management zone divided shapefile, or was
            pre-gridded into identical squares.
        args['grid_size'] - This is the size of 1 side of each of the square polygons
            present on 'zone_layer_file'. This can be used to set the size of the
            pixels for the intermediate rasters.
        args['overlap_files'] - A dictionary which maps the name of the shapefile
            (excluding the .shp extension) to the open datasource itself. This can
            be used directly.
        args['over_layer_dict'] - A dictionary which contains the weights of each
            of the various shapefiles included in the 'overlap_files' dictionary.
            The dictionary key is the string name of each shapefile, minus the .shp
            extension. This ID maps to a list containing the two values, with 
            the form being as follows:
                ({ID: [inter-activity weight, buffer], ...})    
        args['import_field']- A string which corresponds to a field within the
           layers being passed in within overlap analysis directory. This is
           the intra-activity importance for each activity.
        args['hum_use_hubs_loc']- An open shapefile of major hubs of human 
            activity. This would allow you to degrade the weight of activity
            zones as they get farther away from these locations.
        args['decay']- float between 0 and 1, representing the decay of interest
           in areas as you get farther away from human hubs.
        args['do-inter']-Boolean that indicates whether or not inter-activity
            weighting is desired. This tells us if the overlap table exists.
        args['do_intra']- Boolean which indicates whether or not intra-activity
            weighting is desired. This will will pull attributes from shapefiles
            passed in in 'zone_layer_file'.
    
    Intermediate:
        Rasterized Shapefiles- For each shapefile that we passed in 'overlap_files'
            we are creating a raster with the shape burned onto a band of the same
            size as our AOI. 
        <Some Other Things>
    
    Output:
        activities_uri- This is a raster output which depicts the
            unweighted frequency of activity within a gridded area or management
            zone.
        <Insert Raster Name Here>- This is a raster depicting the importance scores
            for each grid or management zone in the area of interest.
        Parameters Text File- A file created every time the model is run listing
            all variable parameters used during that run.
            
    Returns nothing.
    '''
    output_dir = os.path.join(args['workspace_dir'], 'Output')
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    
    #LOGGER.debug(args['zone_layer_file'])
    aoi_shp_layer = args['zone_layer_file'].GetLayer()
    aoi_rast_file = os.path.join(inter_dir, 'AOI_Raster.tif')
    #Need to figure out what to do with management zones
    aoi_raster = raster_utils.create_raster_from_vector_extents(args['grid_size'], 
                                    args['grid_size'], gdal.GDT_Int32, -1, aoi_rast_file,
                                    args['zone_layer_file'])
    aoi_band, aoi_nodata = raster_utils.extract_band_and_nodata(aoi_raster)
    aoi_band.Fill(aoi_nodata)
    
    gdal.RasterizeLayer(aoi_raster, [1], aoi_shp_layer, burn_values=[1])
    
    #Want to get each interest layer, and rasterize them, then combine them all at
    #the end. Could do a list of the filenames that we are creating within the
    #intermediate directory, so that we can access later. Want to pass in the
    #inter_dir, as well as the list of shapefiles, and the AOI raster to get info from
    raster_files = make_indiv_rasters(inter_dir, args['overlap_files'], aoi_raster)
    
    #When we go to actually burn, should have a "0" where there is AOI, not same as nodata
    activities_uri = os.path.join(output_dir, 'hu_freq.tif')
    
    #By putting it within execute, we are able to use execute's own variables, so we can
    #just use aoi_nodata without having to pass it somehow
    def get_raster_sum(*activity_pixels):
        '''For any given pixel, if the AOI covers the pixel, we want to ignore nodata 
        value activities, and sum all other activities happening on that pixel.
        
        Input:
            *activity_pixels- This expands into a dynamic list of single variables. The 
                first will always be the AOI pixels. Those following will be a pixel
                from the overlap rasters that we are looking to combine.
                
        Returns:
            sum_pixel- This is either the aoi_nodata value if the AOI is not turned on
                in that area, or, if the AOI does cover this pixel, this is the sum of 
                all activities that are taking place in that area.
        '''
        #We have pre-decided that nodata for the activity pixel will produce a different
        #result from the "no activities within that AOI area" result of 0.
        
        aoi_pixel = activity_pixels[0]
        
        if aoi_pixel == aoi_nodata:
            return aoi_nodata
        
        sum_pixel = 0
        
        for activ in activity_pixels[1::]:

            if activ == 1:
                
                sum_pixel += 1
         
        return sum_pixel   
        
    LOGGER.debug(raster_files)
    raster_utils.vectorize_rasters(raster_files, get_raster_sum, aoi = None,
                                   raster_out_uri = activities_uri, 
                                   datatype = gdal.GDT_Int32, nodata = aoi_nodata)
    
    #Now we want to create a second raster that includes all of the weighting information
    create_weighted_raster(output_dir, args['over_layer_dict'], args['overlap_files'],
                            args['import_field'], args['do_inter'], args['do_intra'],
                            raster_files, raster_dict)
    
def create_weighted_raster(dir, inter_weights_dict, layers_dict, field_name,
                           do_inter, do_intra, raster_files, raster_dict):
    '''This function will create an output raster that takes into account both inter-
    activity weighting and intra-activity weighting. This will produce a map that looks
    both at where activities are occurring, and how much people value those activities
    and areas.
    
    Input:
        dir- This is the directory into which our completed raster file should be placed
            when completed.
        inter_weights_dict- The dictionary that holds the mappings from layer names to
            the inter-activity weights passed in by CSV. The dictionary key is the string
            name of each shapefile, minus the .shp extension. This ID maps to a list 
            containing the two values, with the form being as follows:
                ({ID: [inter-activity weight, buffer], ...})
       layers_dict- This dictionary contains all the activity layers that are included
           in the particular model run. This maps the name of the shapefile (excluding 
           the .shp extension) to the open datasource itself.
        field_name- A string which represents the desired field name in our shapefiles.
            This field should contain the intra-activity weight for that particular shape.
        do_inter- A boolean that indicates whether inter-activity weighting is desired.
        do_intra- A boolean that indicates whether intra-activity weighting is desired.
        
    Output:
        weighted_raster- A raster file output that takes into account both inter-activity
            weights and intra-activity weights.
            
    Returns nothing.
    '''
    ''' The equation that we are given to work with is:
            IS = (1/n) * SUM (U{i,j}*I{j}
        Where:
            IS = Importance Score
            n = Number of human use activities included
            U{i,j}:
                If do_intra:
                    U{i,j} = X{i,j} / X{max}
                        X {i,j} = intra-activity weight of activity j in grid cell i
                        X{max} = The max potential intra-activity weight for all cells
                            where activity j occurs.
                Else:
                    U{i,j} = 1 if activity exists, or 0 if it doesn't.
            I{j}:
                If do_inter:
                    I{j} = Y{j} / Y{max}
                        Y{j} = inter-activity weight of an activuty
                        Y{max} = max inter-activity weight of an activity weight for all
                            activities.
                Else:
                    I{j} = 1    
    '''
    #Want to set up vars that will be universal across all pixels first.
    #n should NOT include the AOI, since it is not an interest layer
    n = len(layers_dict)
    
    #Need to 
    
    
    
def make_indiv_rasters(dir, overlap_files, aoi_raster):
    '''This will pluck each of the files out of the dictionary and create a new raster
    file out of them. The new file will be named the same as the original shapefile,
    but with a .tif extension, and will be placed in the intermediate directory that
    is being passed in as a parameter
    
    Input:
        dir- This is the directory into which our completed raster files should be
            placed when completed.
        overlap_files- This is a dictionary containing all of the open shapefiles which
            need to be rasterized. The key for this dictionary is the name of the 
            file itself, minus the .shp extension. This key maps to the open shapefile
            of that name.
        aoi_raster- The dataset for our Area Of Interest. This will be the base map for
            all following datasets.
            
    Returns:
        raster_files- This is a list of the datasets that we want to sum. The first will
            ALWAYS be the AOI dataset, and the rest will be the variable number of other
            datasets that we want to sum.
    '''
    #Want to switch directories so that we can easily write our files
    
    #aoi_raster has to be the first so that we can use it as an easy "weed out" for
    #pixel summary later
    raster_files = [aoi_raster]
    
    raster_files_dict = {}
    
    print overlap_files
    
    #Remember, this defaults to element being the keys of the dictionary
    for element in overlap_files:

        datasource = overlap_files[element]
        layer = datasource.GetLayer()       

        outgoing_uri = dir + os.sep + element + ".tif"        
        
        dataset = raster_utils.new_raster_from_base(aoi_raster, outgoing_uri, 'GTiff',
                                -1, gdal.GDT_Int32)
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        
        #Do we want to specify -1, or just fill with generic nodata (which in this case
        #should actually be -1)
        band.Fill(nodata)
        
        overlap_burn_value = 1
        gdal.RasterizeLayer(dataset, [1], layer, burn_values=[1])
        #this should do something about flushing the buffer
        dataset.FlushCache()
        
        raster_files.append(dataset)
        raster_files_dict[element] = dataset
        
    return raster_files