'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import glob
import numpy as np
import math

from osgeo import gdal, ogr
from scipy import ndimage
from invest_natcap.habitat_risk_assessment import hra_core
#from invest_natcap.habitat_risk_assessment import hra_preprocessor
import hra_preprocessor
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
            of habitat, stressor, and overlap ratings. Will also contain a .txt
            JSON file that has directory locations (potentially) for habitats,
            species, stressors, and criteria.
        args['grid_size']- Int representing the desired pixel dimensions of
            both intermediate and ouput rasters. 
        args['risk_eq']- A string identifying the equation that should be used
            in calculating risk scores for each H-S overlap cell.
        args['decay_eq']- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence.
        args['max_rating']- An int representing the highest potential value that
            should be represented in rating, data quality, or weight in the
            CSV table.
        args['plot_aoi']- A shapefile containing one or more planning regions
            for a given model. This will be used to get the average risk value
            over a larger area. Each potential region MUST contain the
            attribute "NAME" as a way of identifying each individual shape.

    Intermediate:
        hra_args['habitats_dir']- The directory location of all habitat 
            shapefiles. These will be parsed though and rasterized to be passed
            to hra_core module. This may not exist if 'species_dir' exists.
        hra_args['species_dir']- The directory location of all species
            shapefiles. These will be parsed though and rasterized to be passed
            to hra_core module. This may not exist if 'habitats_dir' exists.
        hra_args['stressors_dir']- The string describing a directory location of
            all stressor shapefiles. Will be parsed through and rasterized
            to be passed on to hra_core.
        hra_args['criteria_dir']- The directory which holds the criteria 
            shapefiles. May not exist if the user does not desire criteria 
            shapefiles. This will be in a VERY specific format, which shall be
            described in the user's guide.
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
            a dataset URI that shows the potentially buffered overlap between the 
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
                            {'DS': "CritName Raster URI", 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  "A-1 Dataset URI"
                    }
            }
        hra_args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile URI provided by the user.
        hra_args['stressors']- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            name, and stressors['stressorName']['DS'] points to the rasterized
            stressor shapefile URI provided by the user that will be buffered by
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
    #We will also return a dictionary conatining directory locations for all
    #of the necessary shapefiles. This will be used instead of having users
    #re-enter the locations within args.
    unpack_over_dict(args['csv_uri'], hra_args)

    #Where we will store the burned individual habitat and stressor rasters.
    crit_dir = os.path.join(inter_dir, 'Criteria_Rasters')
    hab_dir = os.path.join(inter_dir, 'Habitat_Rasters')
    stress_dir = os.path.join(inter_dir, 'Stressor_Rasters')
    overlap_dir = os.path.join(inter_dir, 'Overlap_Rasters')

    for folder in (crit_dir, hab_dir, stress_dir, overlap_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)

    #Criteria
    c_shape_dict = make_crit_shape_dict(hra_args['criteria_dir'])
    add_crit_rasters(crit_dir, c_shape_dict, hra_args['habitats'], 
                hra_args['stressors'], hra_args['h-s'], args['grid_size'])

    #Habitats
    hab_list = []
    for ele in ('habitats_dir', 'species_dir'):
        if ele in hra_args:
            hab_list.append(glob.glob(os.path.join(args[ele], '*.shp')))
    
    add_hab_rasters(hab_dir, hra_args['habitats'], hab_list, args['grid_size'])

    #Stressors
    #OHGODNAMES. stress_dir is the local variable that points to where the
    #stress rasters should be placed. 'stressors' is the stressors dictionary,
    #'stressors_dir' is the directory containing the stressors shapefiles.
    add_stress_rasters(stress_dir, hra_args['stressors'], 
                hra_args['stressors_dir'], hra_args['buffer_dict'], 
                args['decay_eq'], args['grid_size'])

    #H-S Overlap
    make_add_overlap_rasters(overlap_dir, hra_args['habitats'], 
                    hra_args['stressors'], hra_args['h-s'], args['grid_size']) 

    hra_core.execute(hra_args)
    
def add_crit_rasters(dir, crit_dict, habitats, stressors, h_s, grid_size):
    '''This will take in the dictionary of criteria shapefiles, rasterize them,
    and add the URI of that raster to the proper subdictionary within h/s/h-s.

    Input:
        dir- Directory into which the raserized criteria shapefiles should be
            placed.
        crit_dict- A multi-level dictionary of criteria shapefiles. The 
            outermost keys refer to the dictionary they belong with. The
            structure will be as follows:
            
            {'h-s':
                {('HabA', 'Stress1'):
                    {'CriteriaName': "Shapefile Datasource URI", ...}, ...
                },
             'h':
                {'HabA':
                    {'CriteriaName: "Shapefile Datasource URI"...}, ...
                },
             's':
                {'Stress1':
                    {'CriteriaName: "Shapefile Datasource URI", ...}, ...
                }
            }
        h_s- A multi-level structure which holds numerical criteria
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
        habitats- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            raster information. The outermost keys are habitat names.
        stressors- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            raster information. The outermost keys are stressor names.
        grid_size- An int representing the desired pixel size for the criteria
            rasters. 
    Output:
        A set of rasterized criteria files. The criteria shapefiles will be
            burned based on their 'Rating' attribute. These will be placed in
            the 'dir' folder.

    Returns nothing.
    '''
    #H-S
    for pair in crit_dict['h-s']:
        
        for c_name, c_path in crit_dict['h-s'][pair].iteritems():

            #The path coming in from the criteria should be of the form
            #dir/h_s_critname.shp.
            filename =  os.path.splitext(os.path.split(c_path)[1])[0]
            shape = ogr.Open(c_path)
            layer = shape.GetLayer()

            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)

            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=Rating','ALL_TOUCHED=TRUE'])
             
            h_s['Crit_Rasters'][c_name]['Rating'] = out_uri
    
    #Habs
    for h in crit_dict['h']:
        
        for c_name, c_path in crit_dict['h'][h].iteritems():

            #The path coming in from the criteria should be of the form
            #dir/h_critname.shp.
            filename =  os.path.splitext(os.path.split(c_path)[1])[0]
            shape = ogr.Open(c_path)
            layer = shape.GetLayer()

            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)

            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=Rating','ALL_TOUCHED=TRUE'])
             
            habitats['Crit_Rasters'][c_name]['Rating'] = out_uri

    #Stressors
    for s in crit_dict['s']:
        
        for c_name, c_path in crit_dict['s'][s].iteritems():

            #The path coming in from the criteria should be of the form
            #dir/s_critname.shp.
            filename =  os.path.splitext(os.path.split(c_path)[1])[0]
            shape = ogr.Open(c_path)
            layer = shape.GetLayer()

            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)

            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=Rating','ALL_TOUCHED=TRUE'])
             
            stressors['Crit_Rasters'][c_name]['Rating'] = out_uri
def make_crit_shape_dict(crit_uri):
    '''This will take in the location of the file structure, and will return
    a dictionary containing all the shapefiles that we find. Hypothetically, we
    should be able to parse easily through the files, since it should be
    EXACTLY of the specs that we laid out.
    
    Input:
        crit_uri- Location of the file structure containing all of the shapefile
            criteria.

    Returns:
        A dictionary containing shapefile URI's, indexed by their criteria name,
        in addition to which dictionaries and h-s pairs they apply to. The
        structure will be as follows:
        
        {'h-s':
            {('HabA', 'Stress1'):
                {'CriteriaName': "Shapefile Datasource URI", ...}, ...
            },
         'h':
            {'HabA':
                {'CriteriaName: "Shapefile Datasource URI"...}, ...
            },
         's':
            {'Stress1':
                {'CriteriaName: "Shapefile Datasource URI", ...}, ...
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
        crit_name = parts[1].replace('_', ' ').lower()

        if hab_name not in c_shape_dict['h']:
            c_shape_dict['h'][hab_name] = {}
        
        c_shape_dict['h'][hab_name][crit_name] = path
                   
    
    #Now, want to move on to stressor-centric criteria, but will do much the
    #same thing. 
    exps_shps = glob.glob(os.path.join(crit_uri, 'Exposure', '*.shp'))
   
    #Now we have a list of all stressor specific shapefile criteria. 
    #Now we need to parse them out.
    for path in exps_shps:

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
        
        c_shape_dict['s'][stress_name][crit_name] = path
    
    #Finally, want to get all of our pair-centric shape criteria. 
    sens_shps = glob.glob(os.path.join(crit_uri, 'Sensitivity', '*.shp'))
   
    #Now we have a list of all pair specific shapefile criteria. 
    #Now we need to parse them out.
    for path in sens_shps:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself 
        filename =  os.path.splitext(os.path.split(path)[1])[0]

        #want the first and second part to be separate, since they are the
        #habitatName and the stressorName, but want the criteria name to be
        #self contained.
        parts = filename.split('_', 2)
        hab_name = parts[0]
        stress_name = parts[1]
        crit_name = parts[2].replace('_', ' ')

        if (hab_name, stress_name) not in c_shape_dict['h-s']:
            c_shape_dict['h-s'][(hab_name, stress_name)] = {}
        
        c_shape_dict['h-s'][(hab_name, stress_name)][crit_name] = path

    #Et, voila! C'est parfait.
    return c_shape_dict

def make_add_overlap_rasters(dir, habitats, stressors, h_s, grid_size):
    '''For every pair in h_s, want to get the corresponding habitat and
    stressor raster, and return the overlap of the two. Should add that as the
    'DS' entry within each (h, s) pair key in h_s.

    Input:
        dir- Directory into which all completed h-s overlap files shoudl be
            placed.
        habitats- A multi-level dictionary containing all habitat-specific 
            criteria ratings and rasters. In this case, however, the outermost
            key is by habitat name, and habitats['habitatName']['DS'] points to
            the URI of the rasterized habitat shapefile provided by the user.
        stressors- A multi-level dictionary containing all stressor-specific 
            criteria ratings and name, and stressors['stressorName']['DS'] 
            points to the URI of the rasterized and buffered stressor shapefile.
        h_s- A multi level dictionary similar to habitats and stressors, but
            which does not yet contain the 'DS' entry for a h-s raster.
    Output:
        A modified version of h_s which contains a 'DS' entry within each
            (Habitat, Stressor) subdictionary. 

    Returns nothing.
    ''' 
    
    for pair in h_s:

        h, s = pair

        _, s_nodata = raster_utils.extract_band_and_nodata(gdal.Open(stressors[s]['DS']))
        _, h_nodata = raster_utils.extract_band_and_nodata(gdal.Open(habitats[h]['DS']))
 
        files = [habitats[h]['DS'], stressors[s]['DS']]

        def add_h_s_pixels(h_pix, s_pix):
            '''Since the stressor is buffered, we actually want to make sure to
            preserve that value. If there is an overlap, return s value.'''

            if not h_pix == h_nodata and not s_pix == s_nodata:
                
                return s_pix
            else:
                return 0

        
        out_uri = os.path.join(dir, 'H[' + h + ']_S[' + s + '].tif')

        #For the h-s overlap, want to do intersection, since we will never need
        #anything outside that bounding box.
        raster_utils.vectorize_datasets(files, add_h_s_pixels, gdal.GDT_Float32,
                        grid_size, "intersection", resample_method_list=None, 
                        dataset_to_align_index=None, aoi_uri=None)

        h_s[pair]['DS'] = out_uri

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
        A modified version of stressors, into which have been placed the URI of
            rasterized version of the stressor shapefile. It will be placed
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
        stressors[name]['DS'] = new_buff_uri

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
        A modified version of habitats, into which we have placed the URI to the
            rasterized version of the habitat shapefile. It will be placed at
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

        habitats[name]['DS'] = out_uri

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
