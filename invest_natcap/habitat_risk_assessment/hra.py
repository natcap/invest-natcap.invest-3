'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import glob

from osgeo import gdal, ogr
from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This function will prepare files passed from the UI to be sent on to the
    hra_core module.

    Input:
        args- A python dictionary created by the UI for use in the HRA model. It
            will contain the following data.
        args['workspace_dir']- String which points to the directory into which
            intermediate and output files should be placed.
        args['habitat_dir']- The string describing a directory location of all
            habitat shapefiles. These will be parsed though and rasterized to 
            be passed to hra_core module.
        args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.'
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['ratings']- A structure which holds all exposure and consequence
            rating for each combination of habitat and stressor. The inner
            structure is a dictionary whose key is a tuple which points to a
            tuple of lists which contain tuples.

            {(Habitat A, Stressor 1): ([(E1Rating, E1DataQuality, E1Weight), ...],
                                       [(C1Rating, C1DataQuality, C1Weight), ...])
                                       .
                                       .
                                       . }
    Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        hra_args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be supfolders of this one.
        hra_args['ratings']- Dictionary with a similar structure to the above,
            but with an additional item in the value tuple containing an open
            raster dataset of the overlap of key H-S.

    Returns nothing.
    '''
    hra_args = {}

    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    hra_args['workspace_dir'] = args['workspace_dir']

    #Take all shapefiles in both the habitats and the stressors folders and
    #make them into rasters of grid_size by grid_size resolution.
    
    #Glob.glob gets all of the files that fall into the form .shp, and makes
    #them into a list.
    file_names = glob.glob(os.path.join(args['habitat_dir'], '*.shp'))
    h_rast = os.path.join(inter_dir, 'Habitat_Rasters')

    make_rasters(file_names, h_rast, args['grid_size'])
    
    file_names = glob.glob(os.path.join(args['stressors_dir'], '*.shp'))
    s_rast = os.path.join(inter_dir, 'Stressor_Rasters')

    make_rasters(file_names, s_rast, args['grid_size'])

    #INSERT WAY OF BUFFERING STRESSORS HERE
    
    #Now, want to make all potential combinations of the rasters, and add it to
    #the structure containg data about the H-S combination.
    ratings_with_rast = combine_hs_rasters(inter_dir, h_rast, s_rast, args['ratings'])

    hra_args['ratings'] = ratings_with_rast

    hra_core.execute(hra_args)

def combine_hs_rasters(dir, h_rast, s_rast, ratings):
    '''Takes in a habitat and a stressor, and combines the two raster files,
    then places that in the corresponding entry within the ratings dictionary.

    Input:
        dir- The directory into which the completed raster files should be placed.
        h_rast- The folder holding all habitat raster files.
        s_rast- The folder holding all stressor raster files.
        ratings- A dictionary which comes from the IUI which contains all
            ratings and weightings of each Habitat-Stressor pair.

     Output:
        out_uri- A raster file which shows the overlap between the given
            habitat and stressor. There will be number of habitat x number of
            stressor versions of this file, all individualled named according
            to their corresponding parts.
    
    Returns an edited version of 'ratings' that contains an open raster
    datasource correspondoing to the appropriate H-S key for the dictionary.
    '''

    #They will be output with the form 'H[habitat_name]_S[stressor_name].tif'
    h_rast_files = glob.glob(os.path.join(h_rast, '*.tif'))
    s_rast_files = glob.glob(os.path.join(s_rast, '*.tif'))
 
    #Create vectorize_raster's function to call when combining the h-s rasters
    def combine_hs_pixels(pixel_h, pixel_s):
        
        #For all pixels in the two rasters, return this new pixel value
        pix_sum = pixel_h + pixel_s
        
        return pix_sum
        
    for h in h_rast_files:
        for s in s_rast_files:
            
            #The return of os.path.split is a tuple where everything after the final
            #slash is returned as the 'tail' in the second element of the tuple
            #path.splitext returns a tuple such that the first element is what comes
            #before the file extension, and the second is the extension itself 
            h_name = os.path.splitext(os.path.split(h)[1])[0]
            s_name = os.path.splitext(os.path.split(s)[1])[0]
            out_uri = os.path.join(dir, 'H[' + h_name + ']_S[' + s_name + \
                        '].tif')
            
            h_dataset = gdal.Open(h)
            s_dataset = gdal.Open(s)
    
            raster_utils.vectorize_rasters([h_dataset, s_dataset], 
                            combine_hs_pixels, raster_out_uri = out_uri,
                            datatype = gdal.GDT_Int32, nodata=[0])
            
            #Now place the datasource into the corresponding dictionary entry
            #in 'ratings'. We will make the open datasource the third item in
            #the tuple. The first two are the exposure and consequence ratings
            #that were gleaned from the IUI.
            ratings[(h_name, s_name)][2] = gdal.Open(out_uri)

    return ratings

def make_rasters(dir, file_names, grid_size):
    '''Takes a shapefile and make s rasterized version which will be used to
    make the combined H-S rasters afterwards.

    Input:
        dir- The directory into which the finished raster files should be placed.
        file_names- A list containing the filepaths to all shapefiles that
            need to be rasterized.
        grid_size- The desired raster pixel resolution

    Output:
        out_uri- The filepath of the newly created raster file based on the
            incoming file name located within file_names.

    Returns nothing.
    '''

    for file_uri in file_names:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(file)[1])[0]
        out_uri = os.path.join(dir, name, '.tif')

        datasource = ogr.Open(file_uri)
        layer = datasource.GetLayer()
        
        #Making the nodata value 0 so that it's easier to combine the layers later.
        r_dataset = \
            raster_utils.create_raster_from_vector_extents(grid_size, grid_size,
                    gdal.GDT_Int32, 0, out_uri, datasource)

        band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
        band.Fill(nodata)

        gdal.RasterizeLayer(r_dataset, [1], burn_values=[1])

