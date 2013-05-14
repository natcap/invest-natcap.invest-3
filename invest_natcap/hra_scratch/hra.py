'''This will be the preperatory module for HRA. It will take all unprocessed
and pre-processed data from the UI and pass it to the hra_core module.'''

import os
import shutil
import logging
import fnmatch
import numpy as np
import math

from osgeo import gdal, ogr, osr
from scipy import ndimage
from invest_natcap.habitat_risk_assessment import hra_core
from invest_natcap.habitat_risk_assessment import hra_preprocessor
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

class ImproperCriteriaAttributeName(Exception):
    '''An excepion to pass in hra non core if the criteria provided by the user
    for use in spatially explicit rating do not contain the proper attribute 
    name. The attribute should be named 'RATING', and must exist for every shape 
    in every layer provided.'''
    pass

class ImproperAOIAttributeName(Exception):
    '''An exception to pass in hra non core if the AOIzone files do not
    contain the proper attribute name for individual indentification. The
    attribute should be named 'name', and must exist for every shape in the
    AOI layer.'''
    pass

class DQWeightNotFound(Exception):
    '''An exception to be passed if there is a shapefile within the spatial
    criteria directory, but no corresponing data quality and weight to support
    it. This would likely indicate that the user is try to run HRA without
    having added the criteria name into hra_preprocessor properly.'''
    pass

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
            in calculating risk scores for each H-S overlap cell. This will be
            either 'Euclidean' or 'Multiplicative'.
        args['decay_eq']- A string identifying the equation that should be used
            in calculating the decay of stressor buffer influence. This can be
            'None', 'Linear', or 'Exponential'.
        args['max_rating']- An int representing the highest potential value that
            should be represented in rating, data quality, or weight in the
            CSV table.
        args['aoi_tables']- A shapefile containing one or more planning regions
            for a given model. This will be used to get the average risk value
            over a larger area. Each potential region MUST contain the
            attribute "name" as a way of identifying each individual shape.

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
        hra_args['habitats']- Similar to the h-s dictionary, a multi-level
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
        hra_args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
    
    Returns nothing.
    '''

    hra_args = {}
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    hra_args['workspace_dir'] = args['workspace_dir']

    hra_args['risk_eq'] = args['risk_eq']
    
    #Depending on the risk calculation equatioa, this should return the highest
    #possible value of risk for any given habitat-stressor pairing. The highest
    #risk for a habitat would just be this risk value * the number of stressor
    #pairs that apply to it.
    max_r = calc_max_rating(args['risk_eq'], args['max_rating'])
    hra_args['max_risk'] = max_r
    
    #Create intermediate and output folders. Delete old ones, if they exist.
    for folder in (inter_dir, output_dir):
        if (os.path.exists(folder)):
            shutil.rmtree(folder) 

        os.makedirs(folder)
   
    #If using aoi zones are desired, pass the AOI layer directly to core to be
    #dealt with there.
    if 'aoi_tables' in args:

        #Need to check that this shapefile contains the correct attribute name.
        #Later, this is where the uppercase/lowercase dictionary can be
        #implimented.
        shape = ogr.Open(args['aoi_tables'])
        layer = shape.GetLayer()
    
        lower_attrib = None
        for feature in layer:
            
            if lower_attrib == None:
                lower_attrib = dict(zip(map(lambda x: x.lower(), feature.items().keys()), 
                            feature.items().keys()))
            
            if 'name' not in lower_attrib:
                raise ImproperAOIAttributeName("Risk table layer attributes must \
                    contain the attribute \"Name\" in order to be properly used \
                    within the HRA model run.")

        #By this point, we know that the AOI layer contains the 'name' attribute,
        #in some form. Pass that on to the core so that the name can be easily
        #pulled from the layers.
        hra_args['aoi_key'] = lower_attrib['name']        
        hra_args['aoi_tables'] = args['aoi_tables']

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

    #Criteria, if they exist.
    if 'criteria_dir' in hra_args:
        c_shape_dict = hra_preprocessor.make_crit_shape_dict(hra_args['criteria_dir'])
        add_crit_rasters(crit_dir, c_shape_dict, hra_args['habitats'], 
                    hra_args['stressors'], hra_args['h-s'], args['grid_size'])

    #Habitats
    hab_list = []
    for ele in ('habitats_dir', 'species_dir'):
        if ele in hra_args:
            hab_names = listdir(hra_args[ele])
            hab_list += fnmatch.filter(hab_names, '*.shp')
    
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

    #No reason to hold the directory paths in memory since all info is now
    #within dictionaries. Can remove them here before passing to core.
    for name in ('habitats_dir', 'species_dir', 'stressors_dir', 'criteria_dir'):
        if name in hra_args:
            del hra_args[name]

    hra_core.execute(hra_args)

def listdir(path):
    '''A replacement for the standar os.listdir which, instead of returning
    only the filename, will include the entire path. This will use os as a
    base, then just lambda transform the whole list.

    Input:
        path- The location container from which we want to gather all files.

    Returns:
        A list of full URIs contained within 'path'.
    '''
    file_names = os.listdir(path)
    uris = map(lambda x: os.path.join(path, x), file_names)

    return uris

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
        
        An appended version of habitats, stressors, and h-s which will include
        entries for criteria rasters at 'Rating' in the appropriate dictionary.
        'Rating' will map to the URI of the corresponding criteria dataset.

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

            #Since all features will contain the same set of attributes,
            #and if it passes this loop, will definitely contain a 'rating', we
            #can just use the last feature queried to figure out how 'rating' 
            #was used.
            lower_attrib = None

            for feature in layer:
                
                if lower_attrib == None:
                    lower_attrib = dict(zip(map(lambda x: x.lower(), feature.items().keys()), 
                                feature.items().keys()))

                if 'rating' not in lower_attrib:
                    raise ImproperCriteriaAttributeName("Criteria layer must \
                        contain the attribute \"Rating\" in order to be properly used \
                        within the HRA model run.")
                
            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)


            #lower_attrib['rating'] should give us what rating is called within
            #this set of features.
            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=' + lower_attrib['rating'],'ALL_TOUCHED=TRUE'])
             
            if c_name in h_s[pair]['Crit_Rasters']:
                h_s[pair]['Crit_Rasters'][c_name]['DS'] = out_uri
            else:
                raise DQWeightNotFound("All spatial criteria desired within the \
                    model run require corresponding Data Quality and Weight \
                    information. Please run HRA Preprocessor again to include all\
                    relavant criteria data.")

    #Habs
    for h in crit_dict['h']:
        
        for c_name, c_path in crit_dict['h'][h].iteritems():

            #The path coming in from the criteria should be of the form
            #dir/h_critname.shp.
            filename =  os.path.splitext(os.path.split(c_path)[1])[0]
            shape = ogr.Open(c_path)
            layer = shape.GetLayer()

            #Since all features will contain the same set of attributes,
            #and if it passes this loop, will definitely contain a 'rating', we
            #can just use the last feature queried to figure out how 'rating' 
            #was used.
            lower_attrib = None

            for feature in layer:
                
                if lower_attrib == None:
                    lower_attrib = dict(zip(map(lambda x: x.lower(), feature.items().keys()), 
                                feature.items().keys()))

                if 'rating' not in lower_attrib:
                    raise ImproperCriteriaAttributeName("Criteria layer must \
                        contain the attribute \"Rating\" in order to be properly used \
                        within the HRA model run.")
            
            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)

            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=' + lower_attrib['rating'],'ALL_TOUCHED=TRUE'])
            
            if c_name in habitats[h]['Crit_Rasters']:  
                habitats[h]['Crit_Rasters'][c_name]['DS'] = out_uri
            else:
                raise DQWeightNotFound("All spatial criteria desired within the \
                    model run require corresponding Data Quality and Weight \
                    information. Please run HRA Preprocessor again to include all\
                    relavant criteria data.")

    #Stressors
    for s in crit_dict['s']:
        
        for c_name, c_path in crit_dict['s'][s].iteritems():

            #The path coming in from the criteria should be of the form
            #dir/s_critname.shp.
            filename =  os.path.splitext(os.path.split(c_path)[1])[0]
            shape = ogr.Open(c_path)
            layer = shape.GetLayer()

            #Since all features will contain the same set of attributes,
            #and if it passes this loop, will definitely contain a 'rating', we
            #can just use the last feature queried to figure out how 'rating' 
            #was used.
            lower_attrib = None
            
            for feature in layer:
                
                if lower_attrib == None:
                    lower_attrib = dict(zip(map(lambda x: x.lower(), feature.items().keys()), 
                                feature.items().keys()))

                if 'rating' not in lower_attrib:
                    raise ImproperCriteriaAttributeName("Criteria layer must \
                        contain the attribute \"Rating\" in order to be properly used \
                        within the HRA model run.")
            
            out_uri = os.path.join(dir, filename + '.tif')

            r_dataset = \
                raster_utils.create_raster_from_vector_extents(grid_size, 
                        grid_size, gdal.GDT_Int32, 0, out_uri, shape)


            band, nodata = raster_utils.extract_band_and_nodata(r_dataset)
            band.Fill(nodata)

            gdal.RasterizeLayer(r_dataset, [1], layer, 
                            options=['ATTRIBUTE=' + lower_attrib['rating'],'ALL_TOUCHED=TRUE'])
             
            if c_name in stressors[s]['Crit_Rasters']:
                stressors[s]['Crit_Rasters'][c_name]['DS'] = out_uri
            else:
                raise DQWeightNotFound("All spatial criteria desired within the \
                    model run require corresponding Data Quality and Weight \
                    information. Please run HRA Preprocessor again to include all\
                    relavant criteria data.")


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
        h_nodata = raster_utils.get_nodata_from_uri(habitats[h]['DS'])
 
        files = [habitats[h]['DS'], stressors[s]['DS']]

        def add_h_s_pixels(h_pix, s_pix):
            '''Since the stressor is buffered, we actually want to make sure to
            preserve that value. If there is an overlap, return s value.'''

            if h_pix != h_nodata:
                return s_pix
            else:
                return 0.
        
        out_uri = os.path.join(dir, 'H[' + h + ']_S[' + s + '].tif')

        raster_utils.vectorize_datasets(files, add_h_s_pixels, out_uri, 
                        gdal.GDT_Float32, 0, grid_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)
        
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
    s_names = listdir(stressors_dir)
    stress_list = fnmatch.filter(s_names, '*.shp')

    for shape in stress_list:

        #The return of os.path.split is a tuple where everything after the final
        #slash is returned as the 'tail' in the second element of the tuple
        #path.splitext returns a tuple such that the first element is what comes
        #before the file extension, and the second is the extension itself
        name = os.path.splitext(os.path.split(shape)[1])[0]

        out_uri = os.path.join(dir, name + '.tif')
        
        datasource = ogr.Open(shape)
        layer = datasource.GetLayer()
        
        buff = buffer_dict[name]
       
        #Want to set this specifically to make later overlap easier.
        nodata = 0.

        #Need to create a larger base than the envelope that would normally
        #surround the raster, since we know that we can be expanding by at
        #least buffer size more. For reference, look to "~/workspace/Examples/expand_raster.py"
        shp_extent = layer.GetExtent()

        #These have to be expanded by 2 * buffer to account for both sides
        width = abs(shp_extent[1] - shp_extent[0]) + 2*buff
        height = abs(shp_extent[3] - shp_extent[2]) + 2*buff 
        p_width = int(np.ceil(width / grid_size))
        p_height = int(np.ceil(height /grid_size))
         
        driver = gdal.GetDriverByName('GTiff')
        raster = driver.Create(out_uri, p_width, p_height, 1, gdal.GDT_Float32) 

        #increase everything by buffer size
        transform = [shp_extent[0]-buff, grid_size, 0.0, shp_extent[3]+buff, 0.0, -grid_size]
        raster.SetGeoTransform(transform)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(layer.GetSpatialRef().__str__())
        raster.SetProjection(srs.ExportToWkt())

        band = raster.GetRasterBand(1)
        band.Fill(nodata)
        band.FlushCache()

        gdal.RasterizeLayer(raster, [1], layer, burn_values=[1], 
                                                options=['ALL_TOUCHED=TRUE'])
       
        #Now, want to take that raster, and make it into a buffered version of
        #itself.
        base_array = band.ReadAsArray()
        
        #Swaps 0's and 1's for use with the distance transform function.
        swp_array = (base_array + 1) % 2

        #The array with each value being the distance from its own cell to land
        dist_array = ndimage.distance_transform_edt(swp_array, 
                                                    sampling=grid_size)

        #Need to have a special case for 0's, to avoid divide by 0 errors
        if buff == 0:
            decay_array = make_zero_buff_decay_array(dist_array, nodata)
        elif decay_eq == 'None':
            decay_array = make_no_decay_array(dist_array, buff, nodata)
        elif decay_eq == 'Exponential':
            decay_array = make_exp_decay_array(dist_array, buff, nodata)
        elif decay_eq == 'Linear':
            decay_array = make_lin_decay_array(dist_array, buff, nodata)

        #Create a new file to which we should write our buffered rasters.
        #Eventually, we will use the filename without buff, because it will
        #just be assumed to be buffered
        new_buff_uri = os.path.join(dir, name + '_buff.tif')
        
        new_dataset = raster_utils.new_raster_from_base(raster, new_buff_uri,
                            'GTiff', 0, gdal.GDT_Float32)
        
        n_band, n_nodata = raster_utils.extract_band_and_nodata(new_dataset)
        n_band.Fill(n_nodata)
        
        n_band.WriteArray(decay_array)

        #Now, write the buffered version of the stressor to the stressors
        #dictionary
        stressors[name]['DS'] = new_buff_uri

def make_zero_buff_decay_array(dist_array, nodata):
    '''Creates an array in the case of a zero buffer width, where we should
    have is land and nodata values.

    Input:
        dist_array- A numpy array where each pixel value represents the
            distance to the closest piece of land.
        nodata- The value which should be placed into anything that is not land.
    Returns:
        A numpy array reprsenting land with 1's, and everything else with nodata.
    '''

    #Since we know anything that is land is currently represented as 0's, want
    #to turn that back into 1's.
    dist_array[dist_array == 0] = 1

    #everything else will just be nodata
    dist_array[dist_array > 1] = nodata

    return dist_array

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
                    gdal.GDT_Float32, 0., out_uri, datasource)

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

    for dict_name in dicts:
        args[dict_name] = dicts[dict_name]