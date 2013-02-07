'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import re
import shutil
import logging
import glob
import numpy as np
import math

from osgeo import gdal, ogr
from scipy import ndimage
from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra_preprocessor
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
        args['csv_uri']- The location of the directory containing the CSV files
            of habitat, stressor, and overlap ratings.         
        args['habitat_dir']- The string describing a directory location of all
            habitat shapefiles. These will be parsed though and rasterized to 
            be passed to hra_core module.
        args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.'
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['risk_eq']- A string identifying the equation that should be used
            in calculating risk scores for each H-S overlap cell.
        args['decay_eq']- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence.
        args['max_rating']- An int representing the highest potential value that
            should be represented in rating, data quality, or weight in the
            CSV table.
        args['crit_uri']- The location of the shapefile criteria that we will
            use in our model. These will be rasterized and added to their
            approipriate dictionaries.

    Intermediate:
        hra_args['buffer_dict']- A dictionary that links the string name of each
            stressor shapefile to the desired buffering for that shape when
            rasterized.  This will get unpacked by the hra_preprocessor module.

            {'Stressor 1': 50,
             'Stressor 2': ...,
            }
    Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        hra_args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be supfolders of this one.
        hra_args['h-s']- A multi-level structure which holds all criteria ratings, 
            both numerical and raster that apply to habitat and stressor 
            overlaps. The structure, whose keys are tuples of 
            (Habitat, Stressor) names and map to an inner dictionary will have
            3 outer keys containing numeric-only criteria, raster-based
            criteria, and a dataset that shows the potentially buffered overlap
            between the habitat and stressor. The overall structure will be as
            pictured:

            {(Habitat A, Stressor 1): 
                    {'Crit_Ratings': 
                        {'CritName': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': 
                        {'CritName':
                            {'DS': <CritName Raster>, 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile provided by the user.
        args['stressors']- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            name, and stressors['stressorName']['DS'] points to the rasterized
            stressor shapefile provided by the user that will be buffered by
            the indicated amount in buffer_dict['stressorName'].
        hra_args['risk_eq']- String which identifies the equation to be used
            for calculating risk.  The core module should check for 
            possibilities, and send to a different function when deciding R 
            dependent on this.
        args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
    Returns nothing.
    '''
    #Since we need to use the h-s, stressor, and habitat dicts elsewhere, want
    #to use the pre-process module to unpack them.
    unpack_over_dict(args['csv_uri'], args)
    LOGGER.debug(args)
    hra_args = {}

    #Want to parse through the file structure and return a dictionary of all of
    #the open shapefiles. These will be rasterized later and added to their
    #respective criteria dictionaries. This function can also be called by
    #hra_preprocessor in order to determine how to fill in the CSVs.
    c_shape_dict = make_crit_shape_dict(args['crit_uri'])

    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    hra_args['workspace_dir'] = args['workspace_dir']
    
    hra_args['risk_eq'] = args['risk_eq']
    
    #Depending on the risk calculation equation, this should return the highest
    #possible value of risk for any given habitat-stressor pairing. The highest
    #risk for a habitat would just be this risk value * the number of stressor
    #pairs that apply to it.
    max_r = calc_max_rating(args['risk_eq'], args['max_rating'])
    hra_args['max_risk'] = max_r

    #Take all shapefiles in both the habitats and the stressors folders and
    #make them into rasters of grid_size by grid_size resolution.
    
    #Glob.glob gets all of the files that fall into the form .shp, and makes
    #them into a list.
    file_names = glob.glob(os.path.join(args['habitat_dir'], '*.shp'))
    h_rast = os.path.join(inter_dir, 'Habitat_Rasters')
    
    #Make folders in which to store the habitat rasters.
    if (os.path.exists(h_rast)):
        shutil.rmtree(h_rast) 

    os.makedirs(h_rast)

    make_rasters(file_names, h_rast, args['grid_size'])
    mod_habitats = add_rast_to_dict(h_rast, args['habitats'])
    hra_args['habitats'] = mod_habitats

    file_names = glob.glob(os.path.join(args['stressors_dir'], '*.shp'))
    s_rast = os.path.join(inter_dir, 'Stressor_Rasters')

    #Make folder for the stressors.
    if (os.path.exists(s_rast)):
        shutil.rmtree(s_rast) 

    os.makedirs(s_rast)

    #Make rasters based on the stressor shapefiles
    make_rasters(file_names, s_rast, args['grid_size'])

    #Checks the stressor buffer, and makes a new "buffered" raster. If the
    #buffer is 0, this will be identical to the original rasterized shapefile.
    buffer_s_rasters(s_rast, args['buffer_dict'], args['grid_size'], 
                    args['decay_eq'])

    hra_args['stressors'] = args['stressors']

    #Now, want to make all potential combinations of the rasters, and add it to
    #the structure containg data about the H-S combination.
    ratings_with_rast = combine_hs_rasters(inter_dir, h_rast, s_rast, 
                                            args['h-s'])

    hra_args['h-s'] = ratings_with_rast

    hra_core.execute(hra_args)

def make_crit_shape_dict(crit_uri):

    '''This will take in the location of the file structure, and will return
    a dictionary containing all the shapefiles that we find. Hypothetically, we
    should be able to parse easily through the files, since it should be
    EXACTLY of the specs that we laid out.
    
    Input:
        crit_uri- Location of the file structure containing all of the shapefile
            criteria.

    Returns:
        A dictionary containing open shapefiles, indexed by their criteria name,
        in addition to which dictionaries and h-s pairs they apply to. The
        sturcture will be as follows:
        
        {'h-s':
            {('HabA', 'Stress1'):
                {'CriteriaName': <Open Shapefile Datasource>, ...}, ...
            },
         'h':
            {'HabA':
                {'CriteriaName: <Open Shapefile DS>, ...}, ...
            },
         's':
            {'Stress1':
                {'CriteriaName: <Open Shapefile DS>, ...}, ...
                   
            }
        }
    '''
    c_shape_dict = {'h-s':{}, 'h': {}, 's':{}}

    #First, want to get the things that are either habitat specific or 
    #species specific. These should all be in the 'Resiliance' subfolder
    #of raster_criteria.
    res_shps = glob.glob(os.path.join(crit_uri, 'Resiliance', '*.shp'))
   
    #Now we have a list of all habitat specific shapefile criteria. Now we need
    #to parse them out.
    for path in res_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the second part to all be one piece
        parts = filename.split('_', 1)
        hab_name = parts[0]
        crit_name = parts[1].replace('_', ' ')

        if hab_name not in c_shape_dict['h']:
            c_shape_dict['h'][hab_name] = {}
        
        c_shape_dict['h'][hab_name][crit_name] = ogr.Open(path)
    
    #Now, want to move on to stressor-centric criteria, but will do much the
    #same thing. 
    exps_shps = glob.glob(os.path.join(crit_uri, 'Exposure', '*.shp'))
   
    #Now we have a list of all stressor specific shapefile criteria. 
    #Now we need to parse them out.
    for path in exp_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the second part to all be one piece
        parts = filename.split('_', 1)
        stress_name = parts[0]
        crit_name = parts[1].replace('_', ' ')

        if stress_name not in c_shape_dict['s']:
            c_shape_dict['s'][stress_name] = {}
        
        c_shape_dict['s'][stress_name][crit_name] = ogr.Open(path)



def calc_max_rating(risk_eq, max_rating):
    ''' Should take in the max possible risk, and return the highest possible
    per pixel risk that would be seen on a H-S raster pixel.

    Input:
        risk_eq- The equation that will be used to determine risk.
        max_rating- The highest possible value that could be given as a
            criteria rating, data quality, or weight.
    
    Returns:
        An int representing the highest possible risk value for any given h-s
        overlap raster.
    '''
    
    #The max_rating ends up being the simplified result of each of the E and
    #C equations when the same value is used in R/DQ/W. Thus for E and C, their
    #max value is equivalent to the max_rating.
    
    if risk_eq == 'Multiplicative':
        max_r = max_rating * max_rating

    elif risk_eq == 'Euclidean':
        under_rt = (max_rating - 1)**2 + (max_rating - 1)**2
        max_r = math.sqrt(under_rt)

    return max_r
    
def unpack_over_dict(csv_uri, args):
    '''This throws the dictionary coming from the pre-processor into the
    equivalent dictionaries in args so that they can be processed before being
    passed into the core module.
    
    Input:
        csv_uri- Reference to the folder location of the CSV tables containing
            all habitat and stressor rating information.
        args- The dictionary into which the individual ratings dictionaries
            should be placed.
    Output:
        A modified args dictionary containing dictionary versions of the CSV
        tables located in csv_uri. The dictionaries should be of the forms as
        follows.
           
        h-s- A multi-level structure which will hold all criteria ratings, 
            both numerical and raster that apply to habitat and stressor 
            overlaps. The structure, whose keys are tuples of 
            (Habitat, Stressor) names and map to an inner dictionary will have
            2 outer keys containing numeric-only criteria, and raster-based
            criteria. At this time, we should only have two entries in a
            criteria raster entry, since we have yet to add the rasterized
            versions of the criteria.

            {(Habitat A, Stressor 1): 
                    {'Crit_Ratings': 
                        {'CritName': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'Crit_Rasters': 
                        {'CritName':
                            {'Weight': 1.0, 'DQ': 1.0}
                        },
                    }
            }
        habitats- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            weights and data quality for the rasters.         
        stressors- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            weights and data quality for the rasters.w
    Returns nothing.
    '''
    dicts = hra_preprocessor.parse_hra_tables(csv_uri)
    LOGGER.debug(csv_uri)
    LOGGER.debug("DICTIONARIES:")
    LOGGER.debug(dicts)


    for dict_name in dicts:
        args[dict_name] = dicts[dict_name]

def add_rast_to_dict(direct, dictionary):
    '''Allows us to add an open dataset to the already existing dictionary.

    Input:
        direct- The directory from which we will be getting our .tif raster
            files.
        dictionary- The structure into which the completed open raster datasets
            should be placed. In this case, we want to put them within
            dictionary[name]['DS'] for retrieval later.

    Returns:
        A modified dictionary containing a reference to an open dataset. This
            dataset is accessable by the key 'DS' within the outer
            dictionary[name] value.
    '''

    #Glob.glob gets all of the files that fall into the form .tif, and makes
    #them into a list.
    file_names = glob.glob(os.path.join(direct, '*.tif'))
    LOGGER.debug("DICTIONARY:")
    LOGGER.debug(dictionary.keys())
    for r_file in file_names:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(r_file)[1])[0]

        dictionary[name]['DS'] = gdal.Open(r_file)

    return dictionary

def buffer_s_rasters(r_dir, buffer_dict, grid_size, decay_eq):
    '''If there is buffering desired, this will take each file and buffer the
    given raster shape by the distance of the buffer from the landmass.

    Input:
        r_dir- The directory in which the current raster files reside, and into
            which the re-rasterized files should be placed.
        buffer_dict- Dictionary which maps the name of the stressor to the
            desired buffer distance. This is separate from the h-s
            dictionary to avoid having to pass it to core. The key will be a
            string, and the value a double.
        grid_size- The current size of the raster cells.
        decay_eq- String representing the equation that shuld be used to decay
            the stressor importance from the original points.

    Output:
        Re-buffered rasters of the same name as those contained within 'r_dir'
            which have the size of the original rasterized shapefile plus a
            buffer distance given in 'buffer_dict'

    Returns nothing.
    '''
    #This will get the names of all rasters in the rasterized stressor
    #dictionary. We will pull the names themselves in order to compare them
    #against those in the buffer dictionary.
    file_names = glob.glob(os.path.join(r_dir, '*.tif'))

    for r_file in file_names:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        name = os.path.splitext(os.path.split(r_file)[1])[0]
        buff = buffer_dict[name]
       
        #This allows us to read/write to the dataset.
        raster = gdal.Open(r_file, gdal.GA_Update)
        band, nodata = raster_utils.extract_band_and_nodata(raster)
        
        array = band.ReadAsArray()
        
        #Swaps 0's and 1's for use with the distance transform function.
        swp_array = (array + 1) % 2

        #The array with each value being the distance from its own cell to land
        dist_array = ndimage.distance_transform_edt(swp_array, 
                                                    sampling=grid_size)
        
        if decay_eq == 'None':
            decay_array = make_no_decay_array(dist_array, buff, nodata)
        elif decay_eq == 'Exponential':
            decay_array = make_exp_decay_array(dist_array, buff, nodata)
        elif decay_eq == 'Linear':
            decay_array = make_lin_decay_array(dist_array, buff, nodata)

        #Create a new file to which we should write our buffered rasters.
        new_buff_uri = os.path.join(r_dir, name + '_buff.tif')
        new_dataset = raster_utils.new_raster_from_base(raster, new_buff_uri,
                            'GTiff', 0, gdal.GDT_Float32)
        n_band, n_nodata = raster_utils.extract_band_and_nodata(new_dataset)
        n_band.Fill(n_nodata)
        
        n_band.WriteArray(decay_array)

def make_lin_decay_array(dist_array, buff, nodata):
    '''Should create an array where the area around land is a function of 
    linear decay from the values representing the land.

    Input:
        dist_array- A numpy array where each pixel value represents the
            distance to the closest piece of land.
        buff- The distance surrounding the land that the user desires to buffer
            with linearly decaying values.
        nodata- The value which should be placed into anything not land or
            buffer area.
    Returns:
        A numpy array reprsenting land with 1's, and everything within the buffer
        zone as linearly decayed values from 1.
    '''

    #The decay rate should be approximately -1/distance we want 0 to be at.
    #We add one to have a proper y-intercept.
    lin_decay_array = -dist_array/buff + 1.0
    lin_decay_array[lin_decay_array < 0] = nodata

    return lin_decay_array

def make_exp_decay_array(dist_array, buff, nodata):
    '''Should create an array where the area around the land is a function of
    exponential decay from the land values.

    Input:
        dist_array- Numpy array where each pixel value represents the distance
            to the closest piece of land.
        buff- The distance surrounding the land that the user desires to buffer
            with exponentially decaying values.
        nodata- The value which should be placed into anything not land or
            buffer area.
    Returns:
        A numpy array representing land with 1's and eveything withing the buffer
        zone as exponentially decayed values from 1.
    '''

    #Want a cutoff for the decay amount after which we will say things are
    #equivalent to nodata, since we don't want to have values outside the buffer
    #zone.
    cutoff = 0.01

    #Need to have a value representing the decay rate for the exponential decay
    rate = -math.log(cutoff)/ buff

    exp_decay_array = np.exp(-rate * dist_array)
    exp_decay_array[exp_decay_array < cutoff] = nodata

    return exp_decay_array

def make_no_decay_array(dist_array, buff, nodata):
    '''Should create an array where the buffer zone surrounding the land is
    buffered with the same values as the land, essentially creating an equally
    weighted larger landmass.

    Input:
        dist_array- Numpy array where each pixel value represents the distance
            to the closest piece of land.
        buff- The distance surrounding the land that the user desires to buffer
            with land data values.
        nodata- The value which should be placed into anything not land or
            buffer area.
    Returns:
        A numpy array representing both land and buffer zone with 1's, and \
        everything outside that with nodata values.
    '''

    #Setting anything within the buffer zone to 1, and anything outside
    #that distance to nodata.
    inner_zone_index = dist_array <= buff
    dist_array[inner_zone_index] = 1
    dist_array[~inner_zone_index] = nodata  
    
    return dist_array 

def combine_hs_rasters(out_dir, h_rast, s_rast, h_s):
    '''Takes in a habitat and a stressor, and combines the two raster files,
    then places that in the corresponding entry within the h-s dictionary.

    Input:
        out_dir- The directory into which the completed raster files should be placed.
        h_rast- The folder holding all habitat raster files.
        s_rast- The folder holding all stressor raster files. We want to look
            for the "buffered" files, since those have already taken into
            account any where there are 0 buffer sizes.
        h_s- A dictionary which comes from the IUI which contains all
            ratings and weightings of each Habitat-Stressor pair.

    Output:
        out_uri- A raster file which shows the overlap between the given
            habitat and stressor. There will be number of habitat x number of
            stressor versions of this file, all individualled named according
            to their corresponding parts.
    
    Returns an edited version of 'h-s' that contains an open raster
    dataset correspondoing to the appropriate H-S key for the dictionary.
    This dataset should be placed in 'h-s' as 
        h-s[(HabName, StressName)]['DS'] = <Open Raster Dataset>
    '''
    #They will be output with the form 'H[habitat_name]_S[stressor_name].tif'
    h_rast_files = glob.glob(os.path.join(h_rast, '*.tif'))
    #We only want to get the "buffered" version of the files.
    s_rast_files = glob.glob(os.path.join(s_rast, '*_buff.tif'))


    for h in h_rast_files:
        for s in s_rast_files:
            
            #The return of os.path.split is a tuple where everything after the 
            #final slash is returned as the 'tail' in the second element of the
            #tuple path.splitext returns a tuple such that the first element is 
            #what comes before the file extension, and the second is the 
            #extension itself 
            h_name = os.path.splitext(os.path.split(h)[1])[0]
            s_name_buff = os.path.splitext(os.path.split(s)[1])[0]
            #We know the file will be the buffered version, so when creating the
            #new filename, need to pull out the 'buffered' portion of it.
            s_name = re.split('\_buff', s_name_buff)[0]

            out_uri = os.path.join(out_dir, 'H[' + h_name + ']_S[' + s_name + \
                        '].tif')
            
            h_dataset = gdal.Open(h)
            s_dataset = gdal.Open(s)

            #python doesn't let us edit out of scope vars, so we're creating a
            #dictionary to modify instead, because that apparently works.
            #Need a pixel count to get a spatial overlap percentage.
            #Need to have called var since vectorize_raster calls +1 times.
            variables = {'all_pix_ct': 0., 'overlap_pix_ct': 0., 'called': False}
            
            #Create vectorize_raster's function to call when combining the 
            #h-s rasters
            def combine_hs_pixels(pixel_h, pixel_s):
                '''Returns a pixel combination of the given habitat raster and 
                stressor raster. If both exist, the value returned is the 
                stressor pixel value, since it is potentially decayed.'''

                if not variables['called']:
                    variables['called'] = True
                    return 0.0
                #Want to keep track of total pixels checked against one another
                variables['all_pix_ct'] += 1

                #Return the int value of whether or not both are non-zero
                overlap = int(bool(pixel_h * pixel_s))
                variables['overlap_pix_ct'] += overlap 
                return pixel_s * overlap
            
            LOGGER.info("combine_hs_rasters")
            raster_utils.vectorize_rasters([h_dataset, s_dataset], 
                            combine_hs_pixels, raster_out_uri = out_uri,
                            datatype = gdal.GDT_Float32, nodata=0)
            
            #Now place the datasource into the corresponding dictionary entry
            #in 'h-s'. We will make the open datasource the third item in
            #the tuple. The first two are the exposure and consequence ratings 
            #that were gleaned from the IUI.
            h_s[(h_name, s_name)]['DS'] = gdal.Open(out_uri)

    return h_s

def make_rasters(file_names, dir_path, grid_size):

    '''Takes a shapefile and make s rasterized version which will be used to
    make the combined H-S rasters afterwards.

    Input:
        dir_path- The directory into which the finished raster files should be placed.
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
        name = os.path.splitext(os.path.split(file_uri)[1])[0]

        out_uri = os.path.join(dir_path, name + '.tif')
        
        datasource = ogr.Open(file_uri)
        layer = datasource.GetLayer()
        
        #Making the nodata value 0 so that it's easier to combine the 
        #layers later.
        r_dataset = \
            raster_utils.create_raster_from_vector_extents(grid_size, grid_size,
                    gdal.GDT_Int32, 0, out_uri, datasource)

        band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
        band.Fill(nodata)

        gdal.RasterizeLayer(r_dataset, [1], layer, burn_values=[1], 
                                                options=['ALL_TOUCHED=TRUE'])

