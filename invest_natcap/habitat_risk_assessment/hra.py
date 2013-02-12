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
        hra_args['h-s']- A multi-level structure which holds numerical criteria
            ratings, as well as weights and data qualities for criteria rasters.
            h-s will hold only criteria that apply to habitat and stressor 
            overlaps. The structure's outermost keys are tuples of 
            (Habitat, Stressor) names. The overall structure will be as 
            pictured:

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
        args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            raster information. The outermost keys are habitat names.
        hra_args['stressors']- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            raster information. The outermost keys are stressor names.

   Output:
        hra_args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        hra_args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be subfolders of this one.
        hra_args['h-s']- The same as intermediate/'h-s', but with the addition
            of a 3rd key 'DS' to the outer dictionary layer. This will map to
            a dataset that shows the potentially buffered overlap between the 
            habitat and stressor. Additionally, any raster criteria will
            be placed in their criteria name subdictionary. The overall 
            structure will be as pictured:

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
        hra_args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile provided by the user.
        hra_args['stressors']- Similar to the h-s dictionary, a multi-level
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
    hra_args = {}
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    hra_args['workspace_dir'] = args['workspace_dir']

    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)
    
    #Since we need to use the h-s, stressor, and habitat dicts elsewhere, want
    #to use the pre-process module to unpack them and put them into the
    #hra_args dict. Then can modify that within the rest of the code.
    unpack_over_dict(args['csv_uri'], hra_args)

    #Where we will store the burned individual habitat and stressor rasters.
    hab_dir = os.path.join(inter_dir, 'Habitat_Rasters')
    stress_dir = os.path.join(inter_dir, 'Stressor_Rasters')
    overlap_dir = os.path.join(inter_dir, 'Overlap_Rasters')

    for folder in (hab_dir, stress_dir, overlap_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    #Habitats
    hab_list = []
    for ele in ('habitat_dir', 'species_dir'):
        if ele in args:
            hab_list.append(glob.glob(os.path.join(args[ele], '*.shp')))
    
    add_hab_rasters(hab_dir, hra_args['habitats'], hab_list, args['grid_size'])

    #Stressors
    add_stress_rasters(stress_dir, hra_args['stressors'], args['stressors_dir'],
                    hra_args['buffer_dict'], args['decay_eq'], args['grid_size'])

    make_add_overlap_rasters(overlap_dir, hra_args['habitats'], 
                    hra_args['stressors'], hra_args['h-s']) 


def add_stress_rasters(dir, stressors, stressors_dir, buffer_dict, decay_eq, 
                    grid_size):
    ''' Takes the stressor shapefiles, and burnes them to a raster buffered
    using the desired decay equation and individual distances.

    Input:
        dir- The directory into which completed rasterized stressor shapefiles
            shapefiles should be placed.
        stressors- A multi-level dictionary conatining stresor-specific
            criteria ratings and rasters.
        stressors_dir- A URI to the directory holding all stressor shapefiles.
        buffer_dict- A dictionary that holds desired buffer sizes for each
            stressors. The key is the name of the stressor, and the value is an
            int which correlates to desired buffer size.
        decay_eq- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence.

    Output:
        A modified version of stressors, into which have been placed a
            rasterized version of the stressor shaprefile. It will be placed
            at stressors[stressName]['DS'].
    '''
    stress_list = glob.glob(os.path.join(stressors_dir, '*.shp'))

    for shape in stress_list:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself
        name = os.path.splitext(os.path.split(shape)[1])[0]

        out_uri = os.path.join(dir, name + '.tif')
        
        datasource = ogr.Open(shape)
        layer = datasource.GetLayer()
        
        #Making the nodata value 0 so that it's easier to combine the 
        #layers later.

        ###Eventually, will use raster_utils.temporary_filename() here.###
        r_dataset = \
            raster_utils.create_raster_from_vector_extents(grid_size, grid_size,
                    gdal.GDT_Int32, 0, out_uri, datasource)

        band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
        band.Fill(nodata)

        gdal.RasterizeLayer(r_dataset, [1], layer, burn_values=[1], 
                                                options=['ALL_TOUCHED=TRUE'])
       
        #Now, want to take that raster, and make it into a buffered version of
        #itself.
        base_array = band.ReadAsArray()
        buff = buffer_dict[name]

        #Swaps 0's and 1's for use with the distance transform function.
        swp_array = (base_array + 1) % 2

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
        #Eventually, we will use the filename without buff, because it will
        #just be assumed to be buffered
        new_buff_uri = os.path.join(dir, name + '_buff.tif')
        
        new_dataset = raster_utils.new_raster_from_base(r_dataset, new_buff_uri,
                            'GTiff', 0, gdal.GDT_Float32)
        
        n_band, n_nodata = raster_utils.extract_band_and_nodata(new_dataset)
        n_band.Fill(n_nodata)
        
        n_band.WriteArray(decay_array)

        #Now, write the buffered version of the stressor to the stressors
        #dictionary
        stressors[name]['DS'] = new_dataset

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
    
def add_hab_rasters(dir, habitats, hab_list, grid_size):
    '''Want to get all shapefiles within any directories in hab_list, and burn
    them to a raster.
    
    Input:
        dir- Directory into which all completed habitat rasters should be 
            placed.
        habitats- A multi-level dictionary containing all habitat and 
            species-specific criteria ratings and rasters.
        hab_list- File URI's for all shapefile in habitats dir, species dir, or
            both.
        grid_size- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 

    Output:
        A modified version of habitats, into which we have placed a rasterized
            version of the habitat shapefile. It will be placed at
            habitats[habitatName]['DS'].
   ''' 
    for shape in hab_list:
        
        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself
        name = os.path.splitext(os.path.split(shape)[1])[0]

        out_uri = os.path.join(dir, name + '.tif')
        
        datasource = ogr.Open(shape)
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

        habitats[name]['DS'] = r_dataset

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
