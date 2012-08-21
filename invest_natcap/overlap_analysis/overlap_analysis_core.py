'''inVEST core module to handle all actual processing of overlap analysis data.'''
import os
import math
import logging
import operator
import datetime

from osgeo import ogr
from osgeo import gdal

from invest_natcap import raster_utils

LOGGER = logging.getLogger('overlap_analysis_core')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')
ogr.UseExceptions()
gdal.UseExceptions()

def execute(args):
    '''This function will take the properly formatted arguments passed to it by
    overlap_analysis.py in the args dictionary, and perform calculations using
    these data to determine the optimal areas for activities.

    Input:
        args['workspace_dir'] - The directory in which all output and intermediate
            files should be placed.
        args['zone_layer_file'] - This is the shapefile representing our area of
            interest. We will rasterize this using cells of 'grid_size' by 
            'grid_size'.
        args['grid_size'] - This is the size of 1 side of each of the square polygons
            present on 'zone_layer_file'. This can be used to set the size of the
            pixels for the intermediate rasters.
        args['overlap_files'] - A dictionary which maps the name of the shapefile
            (excluding the .shp extension) to the open datasource itself. This can
            be used directly.
        args['over_layer_dict'] - A dictionary which contains the weights of each
            of the various shapefiles included in the 'overlap_files' dictionary.
            The dictionary key is the string name of the shapefile it represents,
            minus the .shp extension. This ID maps to a double representing that
            layer's inter-activity weight.
        args['intra_name']- A string which corresponds to a field within the
           layers being passed in within overlap analysis directory. This is
           the intra-activity importance for each activity.
            weighting is desired. This tells us if the overlap table exists.
        args['do_intra']- Boolean which indicates whether or not intra-activity
            weighting is desired. This will will pull attributes from shapefiles
            passed in in 'zone_layer_file'.

    Intermediate:
        A set of rasterized shapefiles of the form 
        args['workspace_dir']/Intermediate/<filename>. For each shapefile that we
        passed in args['overlap_files'] we create a raster with the shape
        burned onto a band of the same size as our AOI.

        (Optional) A set of weighted rasterized shapefiles of the form
        args['wprkspace_dir']/Intermediate/Weighted/<filename>. For each 
        shapefile, if intra-activity weighting is also desired, we will create 
        a rasterized file where the burn value is the args['intra_name']
        attribute of that particular polygon.

    Output:
        A raster file named ['workspace_dir']/Output/hu_freq.tif. This depicts the 
            unweighted frequency of activity within a gridded area or management
            zone.
        (Optional) A raster file named ['workspace_dir']/Ouput/hu_impscore.tif. 
        This depicts the importance scores for each grid cell in the area of 
        interest. This combines the desired inter or intra activity weighting
        into one raster.

        A textfile created every time the model is run listing all variable
        parameters used during that run. This is created within the 
        make_param_file function. It will be of the form ['workspace_dir]/Output/*. 

    Returns nothing.'''
    
    output_dir = os.path.join(args['workspace_dir'], 'Output')
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')

    create_unweighted_raster(args)

    #Need to set up dummy var for when inter or intra are available without the other so
    #that all parameters can be filled in.
    if (args['do_inter'] or args['do_intra']):
        
        layer_dict = args['over_layer_dict'] if args['do_inter'] else None
        intra_name = args['intra_name'] if args['do_intra'] else None
        
        #Want some place to put weighted rasters so we aren't blasting over the
        #unweighted rasters
        weighted_dir = os.path.join(inter_dir, 'Weighted')
        
        if not (os.path.exists(weighted_dir)):
            os.makedirs(weighted_dir)
        
        #Now we want to create a second raster that includes all of the weighting information
        create_weighted_raster(output_dir, weighted_dir, aoi_raster, layer_dict, 
                               args['overlap_files'], intra_name, 
                               args['do_inter'], args['do_intra'], raster_files, raster_names)

def create_unweighted_raster(args):

    output_dir = os.path.join(args['workspace_dir'], 'Output')
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')

    aoi_shp_layer = args['zone_layer_file'].GetLayer()
    aoi_rast_file = os.path.join(inter_dir, 'AOI_Raster.tif')
    
    #Need to figure out what to do with management zones
    aoi_raster = raster_utils.create_raster_from_vector_extents(int(args['grid_size']), 
                                    int(args['grid_size']), gdal.GDT_Int32, -1, aoi_rast_file,
                                    args['zone_layer_file'])
    aoi_band, aoi_nodata = raster_utils.extract_band_and_nodata(aoi_raster)
    aoi_band.Fill(aoi_nodata)
    
    gdal.RasterizeLayer(aoi_raster, [1], aoi_shp_layer, burn_values=[1])
    
    #Want to get each interest layer, and rasterize them, then combine them all at
    #the end. Could do a list of the filenames that we are creating within the
    #intermediate directory, so that we can access later. Want to pass in the
    #inter_dir, as well as the list of shapefiles, and the AOI raster to get info from
    raster_files, raster_names = make_indiv_rasters(inter_dir, args['overlap_files'], aoi_raster)
    
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
        
    raster_utils.vectorize_rasters(raster_files, get_raster_sum, aoi = None,
                                   raster_out_uri = activities_uri, 
                                   datatype = gdal.GDT_Int32, nodata = aoi_nodata)

def create_weighted_raster(out_dir, inter_dir, aoi_raster, inter_weights_dict, 
                           layers_dict, intra_name, do_inter, do_intra, raster_files, raster_names):
    '''This function will create an output raster that takes into account both inter-
    activity weighting and intra-activity weighting. This will produce a map that looks
    both at where activities are occurring, and how much people value those activities
    and areas.
    
    Input:
        out_dir- This is the directory into which our completed raster file should be placed
            when completed.
        inter_dir- The directory in which the weighted raster files can be stored.
        inter_weights_dict- The dictionary that holds the mappings from layer names to
            the inter-activity weights passed in by CSV. The dictionary key is the string
            name of each shapefile, minus the .shp extension. This ID maps to a list 
            containing the two values, with the form being as follows:
                ({ID: [inter-activity weight, buffer], ...})
       layers_dict- This dictionary contains all the activity layers that are included
           in the particular model run. This maps the name of the shapefile (excluding 
           the .shp extension) to the open datasource itself.
        intra_name- A string which represents the desired field name in our shapefiles.
            This field should contain the intra-activity weight for that particular shape.
        do_inter- A boolean that indicates whether inter-activity weighting is desired.
        do_intra- A boolean that indicates whether intra-activity weighting is desired.
        aoi_raster- The dataset for our Area Of Interest. This will be the base map for
            all following datasets.
    raster_files- A list of open unweighted raster files created my make_indiv_rasters
        that begins with the AOI raster. This will be used when intra-activity
        weighting is not desired.
    raster_names- A list of file names that goes along with the unweighted raster files.
        These strings can be used as keys to the other ID-based dictionaries, and will
        be in the same order as the 'raster_files' list.
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
                        Y{j} = inter-activity weight of an activity
                        Y{max} = max inter-activity weight of an activity weight for all
                            activities.
                Else:
                    I{j} = 1
    '''

    #Want to set up vars that will be universal across all pixels first.
    #n should NOT include the AOI, since it is not an interest layer
    n = len(layers_dict)
    outgoing_uri = os.path.join(out_dir, 'hu_impscore.tif') 
    aoi_band, aoi_nodata = raster_utils.extract_band_and_nodata(aoi_raster)

    #If intra-activity weighting is desired, we need to create a whole new set of values,
    #where the burn value of each pixel is the attribute value of the polygon that it
    #resides within. This means that we need the AOI raster, and need to rebuild based on
    #that, then move on from there. I'm abstracting this to a different file for ease of
    #reading. It will return a tuple of two lists- the first will be the list of 
    #rasterized aoi/layers, and the second will be a list of the original file names in
    #the same order as the layers so that the dictionaries with other weights can be
    #cross referenced. 
    weighted_raster_files, weighted_raster_names = \
        make_indiv_weight_rasters(inter_dir, aoi_raster, layers_dict, 
                                  intra_name)
      
    #Need to get the X{max} now, so iterate through the features on a layer, and make a
    #dictionary that maps the name of the layer to the max potential 
    #intra-activity weight
    max_intra_weights = {}
    
    for layer_name in layers_dict:
        
        datasource = layers_dict[layer_name]
        layer = datasource.GetLayer()
        
        for feature in layer:
            
            attribute = feature.items()[intra_name]
            
            try:
                max_intra_weights[layer_name] = \
                    max(attribute, max_intra_weights[layer_name])
            except KeyError:
                max_intra_weights[layer_name] = attribute

    #We also need to know the maximum of the inter-activity value weights, but only
    #if inter-activity weighting is desired at all. If it is not, we don't need this
    #value, so we can just set it to a None type.
    max_inter_weight = None
    if do_inter:
        max_inter_weight = max(inter_weights_dict.values())
    
    #Assuming that inter-activity valuation is desired, whereas intra-activity is not,
    #we should use the original rasterized layers as the pixels to combine. If, on the
    #other hand, inter is not wanted, then we should just use 1 in our equation
    
    def combine_weighted_pixels(*pixel_parameter_list):
        
        aoi_pixel = pixel_parameter_list[0]
        
        curr_pix_sum = 0

        if aoi_pixel == aoi_nodata:
            return aoi_nodata

        for i in range(1, n+1):
            #This will either be a 0 or 1, since the burn value for the unweighted
            #raster files was a 1.
            U =  pixel_parameter_list[i]
            I = None
            if do_inter:
                layer_name = raster_names[i]
                Y = inter_weights_dict[layer_name]
                I = Y / max_inter_weights
            else:
                I = 1

            #This is coming from the documentation, refer to additional info in the
            #docstring. n gets cast to a float so that it can be used in division.
            curr_pix_sum += ((1/float(n)) * U * I)
        return curr_pix_sum    

    def combine_weighted_pixels_intra(*pixel_parameter_list):
    
        aoi_pixel = pixel_parameter_list[0]

        curr_pix_sum = 0.0

        if aoi_pixel == aoi_nodata:
            return aoi_nodata

        for i in range(1, n+1):

            #Can assume that if we have gotten here, that intra-activity weighting
            #is desired. Compute U for that weighting, assuming the raster pixels
            #are the intra weights.
            layer_name = weighted_raster_names[i]
            X = pixel_parameter_list[i]
            X_max = max_intra_weights[layer_name]    

            U = X / X_max
            I = None

            if do_inter:
                layer_name = raster_names[i]
                Y = inter_weights_dict[layer_name]
                I = Y / max_inter_weight
            else:
                I = 1

            #This is coming from the documentation, refer to additional info in the
            #docstring.
            #n is getting cast to a float so that we can use non-integer division in
            #the calculations.  
            curr_pix_sum += ((1/float(n)) * U * I)
        return curr_pix_sum

    if do_intra:
        raster_utils.vectorize_rasters(weighted_raster_files, combine_weighted_pixels_intra,
                   aoi = None, raster_out_uri = outgoing_uri, 
                                   datatype = gdal.GDT_Float32, nodata = aoi_nodata)
    else:
        raster_utils.vectorize_rasters(raster_files, combine_weighted_pixels,
                   aoi = None, raster_out_uri = outgoing_uri,
                   datatype = gdal.GDT_Float32, nodata = aoi_nodata)
  
def make_indiv_weight_rasters(dir, aoi_raster, layers_dict, intra_name):
    ''' This is a helper function for create_weighted_raster, which abstracts some of the
    work for getting the intra-activity weights per pixel to a separate function. This
    function will take in a list of the activities layers, and using the aoi_raster as a
    base for the tranformation, will rasterize the shapefile layers into rasters where the
    burn value is based on a per-pixel intra-activity weight (specified in each polygon on
    the layer). This function will return a tuple of two lists- the first is a list of the
    rasterized shapefiles, starting with the aoi. The second is a list of the shapefile
    names (minus the extension) in the same order as they were added to the first list.
    This will be used to reference the dictionaries containing the rest of the weighting
    information for the final weighted raster calculation.
    
    Input:
        dir: The directory into which the weighted rasters should be placed.
        aoi_raster: The razterized version of the area of interest. This will be used as a
            basis for all following rasterizations.
        layers_dict: A dictionary of all shapefiles to be rasterized. The key is the name
            of the original file, minus the file extension. The value is an open shapefile
            datasource.
        intra_name: The string corresponding to the value we wish to pull out of the
            shapefile layer. This is an attribute of all polygons corresponding to
            the intra-activity weight of a given shape.
            
    RETURNS is output?

    Output:
        weighted_raster_files: A list of raster versions of the original activity
            shapefiles. The first file will ALWAYS be the AOI, followed by the rasterized
            layers.
        weighted_names: A list of the filenames minus extensions, of the rasterized files
            in weighted_raster_files. These can be used to reference properties of the 
            raster files that are located in other dictionaries.
    '''
       
    #aoi_raster has to be the first so that we can easily pull it out later when we go
    #to combine them. Will need the aoi_nodata for later as well.
    weighted_raster_files = [aoi_raster]
    #Inserting 'aoi' as a placeholder so that when I go through the list, I can reference
    #other indicies without having to convert for the missing first element in names.
    weighted_names = ['aoi']
    
    for element in layers_dict:
        
        datasource = layers_dict[element]
        layer = datasource.GetLayer()
        
        outgoing_uri = os.path.join(dir, element + ".tif")

        #Setting nodata value to 0 so that the nodata pixels can be used directly in
        #calculations without messing up the weighted total equations for the second
        #output file.
        dataset = raster_utils.new_raster_from_base(aoi_raster, outgoing_uri, 'GTiff',
                                0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        
        band.Fill(nodata)
        
        gdal.RasterizeLayer(dataset, [1], layer, options = ["ATTRIBUTE=%s" %intra_name])
        #this should do something about flushing the buffer
        dataset.FlushCache()
       
        weighted_raster_files.append(dataset)
        weighted_names.append(element)
   
    return weighted_raster_files, weighted_names
        
def make_indiv_rasters(dir, overlap_files, aoi_raster):
    '''This will pluck each of the files out of the dictionary and create a new raster
    file out of them. The new file will be named the same as the original shapefile,
    but with a .tif extension, and will be placed in the intermediate directory that
    is being passed in as a parameter.
    
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
    #aoi_raster has to be the first so that we can use it as an easy "weed out" for
    #pixel summary later
    raster_files = [aoi_raster]
    raster_names = ['aoi']
    
    #Remember, this defaults to element being the keys of the dictionary
    for element, datasource in overlap_files.iteritems():

        datasource = overlap_files[element]
        layer = datasource.GetLayer()       

        outgoing_uri = os.path.join(dir, element + ".tif")        
        
        dataset = raster_utils.new_raster_from_base(aoi_raster, outgoing_uri, 'GTiff',
                                -1, gdal.GDT_Int32)
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        
        band.Fill(nodata)
        
        overlap_burn_value = 1
        gdal.RasterizeLayer(dataset, [1], layer, burn_values=[1], 
                                        options=['ALL_TOUCHED=TRUE'])
        #this should do something about flushing the buffer
        dataset.FlushCache()
        
        raster_files.append(dataset)
        raster_names.append(element)
    
    return raster_files, raster_names
