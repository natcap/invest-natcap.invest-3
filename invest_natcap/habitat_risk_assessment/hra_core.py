'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import logging
import os
import numpy as np
import collections 
import math

from osgeo import gdal, ogr, osr
from invest_natcap import raster_utils
 
LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
   %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''This provides the main calculation functionaility of the HRA model. This
    will call all parts necessary for calculation of final outputs.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be subfolders of this one.
        args['risk_eq']-  A string representing the equation to be used for
            risk calculation. Possible risk equations are 'Multiplicative',
            which would multiply E and C, and 'Euclidean', which would use
            the equation sqrt((C-1)^2 + (E-1)^2).
        args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
        args['h-s']- A multi-level structure which holds all criteria ratings, 
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
            rasters. In this case, however, the outermost key is by stressor
            name, and stressors['stressorName']['DS'] points to the rasterized
            stressor shapefile provided by the user.

    Outputs:
        --Intermediate--
            These should be the temp risk and criteria files needed for the 
            final output calcs.
        --Output--
            /output/maps/recov_potent_H[habitatname].tif- Raster layer depicting
                the recovery potential of each individual habitat. 
            /output/maps/cum_risk_H[habitatname]- Raster layer depicting the
                cumulative risk for all stressors in a cell for the given 
                habitat.
            /output/maps/ecosys_risk- Raster layer that depicts the sum of all 
                cumulative risk scores of all habitats for that cell.
            /output/maps/[habitatname]_HIGH_RISK- A raster-shaped shapefile
                containing only the "high risk" areas of each habitat, defined
                as being above a certain risk threshold. 

    Returns nothing.
    '''
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    crit_lists, denoms = pre_calc_denoms_and_criteria(inter_dir, args['h-s'],
                                    args['habitats'], args['stressors'])

    #Need to have h-s in there so that we can use the DS for each H-S pair to
    #multiply against the E/C rasters in the case of decay.
    risk_dict = make_risk_rasters(args['h-s'], inter_dir, crit_lists, denoms, 
                                    args['risk_eq'])

    #Know at this point that the non-core has re-created the ouput directory
    #So we can go ahead and make the maps directory without worrying that
    #it will throw an 'already exists.'
    maps_dir = os.path.join(output_dir, 'maps')
    os.mkdir(maps_dir)

    #We will combine all of the h-s rasters of the same habitat into
    #cumulative habitat risk rastersma db return a list of the DS's of each,
    #so that it can be read into the ecosystem risk raster's vectorize.
    h_risk_dict = make_hab_risk_raster(maps_dir, risk_dict)

    #Also want to output a polygonized version of high risk areas in each
    #habitat. Will polygonize everything that falls above a certain percentage
    #of the total raster risk.
    make_risk_shapes(maps_dir, crit_lists, h_risk_dict, args['max_risk'])

    #Now, combine all of the habitat rasters unto one overall ecosystem
    #rasterusing the DS's from the previous function.
    make_ecosys_risk_raster(maps_dir, h_risk_dict)

    #Recovery potential will use the 'Recovery' subdictionary from the
    #crit_lists and denoms dictionaries
    make_recov_potent_raster(maps_dir, crit_lists, denoms)

def make_risk_shapes(dir, crit_lists, h_dict, max_risk):
    '''This function will take in the current rasterized risk files for each
    habitat, and output a shapefile where the areas that are "HIGH RISK" (high
    percentage of risk over potential risk) are the only existing polygonized
    areas.
    
    Since the raster_utils function can only take in ints, want to predetermine
    what areas are or are not going to be shapefile, and pass in a raster that
    is only 1 or nodata.
    
    Input:
        dir- Directory in which the completed shapefiles should be placed.
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): [indiv num raster, raster 1, ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: [indiv num raster, raster 1, ...],
                                ...
                               },
                        's':   { stressA: [indiv num raster, ...]
                               }
                     }
             'Recovery': { hab1: [indiv num raster, ...],
                           hab2: ...
                         }
            }
        h_dict- A dictionary that contains open raster datasets corresponding
            to each of the habitats in the model. The key in this dictionary is
            the name of the habiat, and it maps to the open dataset.
        max_risk- Double representing the highest potential value for a single
            h-s raster. The amount of risk for a given Habitat raster would be
            SUM(s) for a given h.

     Output:
        Returns a shapefile for every habitat, showing features only for the
        areas that are "high risk" within that habitat.        
     '''
    #For each h, want  to know how many stressors are associated with it. This
    #allows us to not have to think about whether or not a h-s pair was zero'd
    #out by weighting or DQ.
    num_stress = collections.Counter()
    for pair in crit_lists['Risk']['h-s']:
        h, s = pair
        
        if h in num_stress:
            num_stress[h] += 1
        else:
            num_stress[h] = 1
    
    curr_top_risk = None

    def high_risk_raster(pixel):

        percent = float(pixel)/ curr_top_risk

        #Will need to be specified what percentage the cutoff for 'HIGH RISK'
        #areas are.
        if percent > 50.0:
            return 1
        else:
            return 0

    for h in h_dict:
        #Want to know the number of stressors for the current habitat        
        curr_top_risk = num_stress[h] * max_risk
        old_ds = h_dict[h]

        out_uri_r = os.path.join(dir, h + '_HIGH_RISK.tif') 
        out_uri = os.path.join(dir, h + '_HIGH_RISK.shp')
        new_ds = raster_utils.vectorize_rasters(old_ds, high_risk_raster,
                        aoi = None, raster_out_uri = out_uri_r, 
                        datatype=gdal.GDT_Float32, nodata = 0)

        #Use gdal.Polygonize to take the raster, which should have only
        #data where there are high percentage risk values, and turn it into
        #a shapefile. 
        raster_to_polygon(new_ds, out_uri, h, 'VALUE')

def raster_to_polygon(raster, out_uri, layer_name, field_name):
    '''This will take in a raster file, and output a shapefile of the same
    area and shape.

    Input:
        raster- The raster that needs to be turned into a shapefile. This is
            only an open raster, not the band. 
        out_uri- The desired URI for the new shapefile.
        layer_name- The name of the layer going into the new shapefile.
        field-name- The name of the field that will contain the raster pixel
            value.
    
    Output:
        This will be a shapefile in the shape of the raster. The raster being
        passed in will be solely "high risk" areas that conatin data, and
        nodata values for everything else.

    Returns nothing.
    '''
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.CreateDataSource(out_uri)
                
    spat_ref = osr.SpatialReference()
    spat_ref.ImportFromWkt(raster.GetProjection())
                                
    layer = ds.CreateLayer(layer_name, spat_ref, ogr.wkbPolygon)

    field_defn = ogr.FieldDefn(field_name, ogr.OFTReal)

    layer.CreateField(field_defn)

    band = raster.GetRasterBand(1)
    mask = band.GetMaskBand()

    gdal.Polygonize(band, mask, layer, 0)

    layer = None

    ds.SyncToDisk()

def make_recov_potent_raster(dir, crit_lists, denoms):
    '''This will do the same h-s calculation as used for the individual E/C 
    calculations, but instead will use r/dq as the equation for each criteria.
    The full equation will be:

        SUM HAB CRITS( r/dq )
        ---------------------
        SUM HAB CRITS( 1/dq )

    Input:
        dir- Directory in which the completed raster files should be placed.
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): [indiv num raster, raster 1, ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: [indiv num raster, raster 1, ...],
                                ...
                               },
                        's':   { stressA: [indiv num raster, ...]
                               }
                     }
             'Recovery': { hab1: [indiv num raster, ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. This dictionary will be the same structure
            as crit_lists, but the innermost values will be floats instead of
            lists.
    Output:
        A raster file for each of the habitats included in the model displaying
            the recovery potential within each potential grid cell.

    Returns nothing.
    '''
    #Want all of the unique habitat names
    habitats = denoms['Recovery'].keys()
    
    #First, going to try doing everything all at once. For every habitat,
    #concat the lists of criteria rasters.
    for h in habitats:

        def add_recov_pix(*pixels):

            value = 0.

            for p in pixels:
                value += p

            value = value / denoms['Recovery'][h]

        curr_list = crit_lists['Recovery'][h]

        out_uri = os.path.join(dir, 'recov_potent_H[' + h + '].tif')

        raster_utils.vectorize_rasters(curr_list, add_recov_pix, aoi = None,
                         raster_out_uri = out_uri, datatype=gdal.GDT_Float32,
                         nodata = 0)


def make_ecosys_risk_raster(dir, h_dict):
    '''This will make the compiled raster for all habitats within the ecosystem.
    The ecosystem raster will be a direct sum of each of the included habitat
    rasters.

    Input:
        dir- The directory in which all completed should be placed.
        h_dict- A dictionary of open raster datasets which can be combined to 
            create an overall ecosystem raster. The key is the habitat name, 
            and the value is the open dataset.
    Output:
        ecosys_risk.tif- An overall risk raster for the ecosystem. It will
            be placed in the dir folder.

    Returns nothing.
    '''
    #Need a straight list of the values from h_dict
    h_list = map((lambda key: h_dict[key], h_dict.keys()))

    out_uri = os.path.join(dir, 'ecosys_risk.tif')

    def add_e_pixels(*pixels):
        '''Sum all habitat pixels for ecosystem raster.'''
 
        pixel_sum = 0.0
        
        for p in pixels:
 
            pixel_sum += p
 
        return pixel_sum
     
    raster_utils.vectorize_rasters(h_list, add_e_pixels, aoi = None,
                     raster_out_uri = out_uri, datatype=gdal.GDT_Float32,
                     nodata = 0)

def make_hab_risk_raster(dir, risk_dict):
    '''This will create a combined raster for all habitat-stressor pairings
    within one habitat. It should return a list of open rasters that correspond
    to all habitats within the model.

    Input:
        dir- The directory in which all completed habitat rasters should be 
            placed.
        risk_dict- A dictionary containing the risk rasters for each pairing of
            habitat and stressor. The key is the tuple of (habitat, stressor),
            and the value is the open raster dataset corresponding to that
            combination.
    Output:
        A cumulative risk raster for every habitat included within the model.
    
    Returns:
        h_rasters- A dictionary containing habitat names mapped directly to
            open datasets corresponding to all habitats being observed within 
            the model.
    '''
    def add_risk_pixels(*pixels):
        '''Sum all risk pixels to make a single habitat raster out of all the 
        h-s overlap rasters.'''
        pixel_sum = 0.0

        for p in pixels:
            pixel_sum += p

        return pixel_sum


    #This will give up two np lists where we have only the unique habs and
    #stress for the system.
    habitats = map((lambda pair: pair[0], risk_dict))
    habitats = np.array(habitats)
    habitats = np.unique(habitats)

    stressors = map(lambda pair: pair[1], risk_dict)
    stressors = np.array(stressors)
    stressors = np.unique(stressors)

    #List to store the completed h rasters in. Will be passed on to the
    #ecosystem raster function to be used in vectorize_raster.
    h_rasters = {} 

    #Run through all potential pairings, and make lists for the ones that
    #share the same habitat.
    for h in habitats:

        ds_list = []
        for s in stressors:
            pair = (h, s)

            ds_list.append(risk_dict[pair])

        #Once we have the complete list, we can pass it to vectorize.
        out_uri = os.path.join(dir, 'cum_risk_H[' + h + '].tif')

        h_rast = raster_utils.vectorize_rasters(ds_list, add_risk_pixels,
                                 aoi = None, raster_out_uri = out_uri,
                                 datatype=gdal.GDT_Float32, nodata = 0)

        h_rasters[h] = h_rast

    return h_rasters

def make_risk_rasters(h_s, inter_dir, crit_lists, denoms, risk_eq):
    '''This will combine all of the intermediate criteria rasters that we
    pre-processed with their r/dq*w. At this juncture, we should be able to 
    straight add the E/C within themselven. The way in which the E/C rasters
    are combined depends on the risk equation desired.

    Input:
        h_s- Args dictionary containing much of the H-S overlap data in
            addition to the H-S base rasters.
        inter_dir- Intermediate directory in which the H_S risk-burned rasters
            can be placed.
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): [indiv num raster, raster 1, ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: [indiv num raster, raster 1, ...],
                                ...
                               },
                        's':   { stressA: [indiv num raster, ...]
                               }
                     }
             'Recovery': { hab1: [indiv num raster, ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. 
            
            {'Risk': {  'h-s': { (hab1, stressA): 2.0, 
                                 (hab1, stressB): 1.3
                               },
                        'h':   { hab1: 3.2,
                                ...
                               },
                        's':   { stressA: 1.2
                               }
                     }
             'Recovery': { hab1: 1.6,
                           hab2: ...
                         }
            }
        risk_eq- A string description of the desired equation to use when
            preforming risk calculation. 
    Output:
        A new raster file for each overlapping of habitat and stressor. This
        file will be the overall risk for that pairing from all H/S/H-S 
        subdictionaries.
    Returns:
        risk_rasters- A simple dictionary that maps a tuple of 
            (Habitat, Stressor) to the risk raster created when the various
            sub components (H/S/H_S) are combined.
    '''    
    #Create dictionary that we can pass back to execute to be passed along to
    #make_habitat_rasters
    risk_rasters = {}

    #We will use the h-s pairs as the way of iterrating through everything else.
    for pair in crit_lists['Risk']['h-s']:

        h, s = pair

        #Want to get E and C from the applicable subdictionaries
        #E and C should be rasters of their own that are calc'd using
        #vectorize raster to straight add the pixels and divide by denoms
        c_out_uri = os.path.join(inter_dir, h + '_' + s + 'C_Risk_Raster.tif')
        e_out_uri = os.path.join(inter_dir, h + '_' + s + 'E_Risk_Raster.tif')

        #E/C should take in all of the subdictionary data, and return a raster
        #to be used in risk calculation. 
        #E will only need to take in stressor subdictionary data
        #C will take in both h-s and habitat subdictionary data
        E = calc_E_raster(e_out_uri, crit_lists['Risk']['s'][s],
                        denoms['Risk']['s'][s])
        #C will need to take in both habitat and hab-stress subdictionary data
        C = calc_C_raster(c_out_uri, crit_lists['Risk']['h-s'][pair], 
                        denoms['Risk']['h-s'][pair], crit_lists['Risk']['h'][h],
                        denoms['Risk']['h'][h])

        #Function that we call now will depend on what the risk calculation
        #equation desired is.
        risk_uri = os.path.join(inter_dir, 'H[' + h + ']_S[' + s + ']_Risk.tif')

        #Want to get the relevant ds for this H-S pair
        base_ds = h_s[pair]['DS']
        
        if risk_eq == 'Multiplicative':
            mod_raster = make_risk_mult(base_ds, E, C, risk_uri)
        
        elif risk_eq == 'Euclidean':
            mod_raster = make_risk_euc(base_ds, E, C, risk_uri)

        risk_rasters[pair] = mod_raster

    return risk_rasters

def make_risk_mult(base, e_rast, c_rast, risk_uri):
    '''Combines the E and C rasters according to the multiplicative combination
    equation.

    Input:
        base- The h-s overlap raster, including potentially decayed values from
            the stressor layer.
        e_rast- The r/dq*w burned raster for all stressor-specific criteria
            in this model run. 
        c_rast- The r/dq*w burned raster for all habitat-specific and
            habitat-stressor-specific criteria in this model run. 
        risk_uri- The file path to which we should be burning our new raster.
            
    Returns a raster representing the multiplied E raster, C raster, and 
    the base raster.
    '''
    #Since we aren't necessarily sure what base nodata is coming in as, just
    #want to be sure that this will output 0.
    base_nodata = base.GetNoDataValue()

    def combine_risk_mult(*pixels):

        #since the E and C are created within this module, we are very sure
        #that their nodata will be 0. Just need to check base, which we know
        #was the first ds passed.
        b_pixel = pixels[0]
        if b_pixel == base_nodata:
            return 0       

        #Otherwise, straight multiply all of the pixel values. We assume that
        #base could potentially be decayed.
        value = 1.
 
        for p in pixels:
            value = value * p

        return value

    mod_raster = raster_utils.vectorize_rasters([base, e_rast, c_rast], 
                            combine_risk_mult, aoi = None, 
                            raster_out_uri = risk_uri, datatype=gdal.GDT_Float32,
                            nodata = 0)

    return mod_raster

def make_risk_euc(base, e_rast, c_rast, risk_uri):
    '''Combines the E and C rasters according to the euclidean combination
    equation.

    Input:
        base- The h-s overlap raster, including potentially decayed values from
            the stressor layer.
        e_rast- The r/dq*w burned raster for all stressor-specific criteria
            in this model run.         
        c_rast- The r/dq*w burned raster for all habitat-specific and
            habitat-stressor-specific criteria in this model run.
        risk_uri- The file path to which we should be burning our new raster.

    Returns a raster representing the euclidean calculated E raster, C raster, 
    and the base raster. The equation will be sqrt((C-1)^2 + (E-1)^2)
    '''
    base_nodata = base.GetNoDataValue()
    e_nodata = e_rast.GetNoDataValue()

    #we need to know very explicitly which rasters are being passed in which
    #order. However, since it's all within the make_risk_euc function, should
    #be safe.
    def combine_risk_euc(b_pix, e_pix, c_pix):

        #Want to make sure we return nodata if there is no base, or no exposure
        if b_pix == base_nodata or e_pix == e_nodata:
            return 0.
        
        #Want to make sure that the decay is applied to E first, then that product
        #is what is used as the new E
        e_val = b_pix * e_pix

        #Only want to perform these operation if there is data in the cell, else
        #we end up with false positive data when we subtract 1. If we have
        #gotten here, we know that e_pix != 0. Just need to check for c_pix.
        if not c_pix == 0:
            c_val = c_pix - 1
        else:
            c_val = 0

        e_val -= 1

        #Now square both.
        c_val = c_val ** 2
        e_val = e_val ** 2
        
        #Combine, and take the sqrt
        value = math.sqrt(e_val + c_val)

    mod_raster = raster_utils.vectorize_rasters([base, e_rast, c_rast], 
                            combine_risk_mult, aoi = None, 
                            raster_out_uri = risk_uri, datatype=gdal.GDT_Float32,
                            nodata = 0)
    return mod_raster

def calc_E_raster(out_uri, s_list, s_denom):
    '''Should return a raster burned with an 'E' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns:
        An 'E' raster that is the sum of all individual r/dq*w burned
        criteria rasters divided by the summed denominator.
    '''
    
    def add_e_pix(*pixels):
        
        value = 0.
        
        for p in pixels:
            value += p
    
        return value / s_denom

    e_raster = raster_utils.vectorize_rasters(s_list, add_e_pix, aoi = None,
                            raster_out_uri = out_uri, datatype=gdal.GDT_Float32,
                            nodata = 0)
    
    LOGGER.debug('\nE Raster X Size, E Raster Y Size')
    LOGGER.debug(str(e_band.XSize) + ', ' + str(e_band.YSize))
    
    return e_raster

def calc_C_raster(out_uri, h_s_list, h_s_denom, h_list, h_denom):
    '''Should return a raster burned with a 'C' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns:
        A 'C' raster that is the sum of all individual r/dq*w burned
        criteria rasters divided by the summed denominator.
    '''
    tot_crit_list = h_s_list + h_list
    tot_denom = h_s_denom + h_denom

    def add_c_pix(*pixels):
        
        value = 0.
        
        for p in pixels:
            value += p
    
        return value / tot_denom

    c_raster = raster_utils.vectorize_rasters(tot_crit_list, add_c_pix, 
                            aoi = None, raster_out_uri = out_uri, 
                            datatype=gdal.GDT_Float32, nodata = 0)

    LOGGER.debug(tot_crit_list)
    for ds in tot_crit_list:
        r = ds.GetRasterBand(1)
        LOGGER.debug('\nC Raster X Size, C Raster Y Size')
        LOGGER.debug(str(r.XSize) + ', ' + str(r.YSize))
    return c_raster

def pre_calc_denoms_and_criteria(dir, h_s, hab, stress):
    '''Want to return two dictionaries in the format of the following:
    (Note: the individual num raster comes from the crit_ratings
    subdictionary and should be pre-summed together to get the numerator
    for that particular raster. )

    Input:
        dir- Directory into which the rasterized criteria can be placed. This
            will need to have a subfolder added to it specifically to hold the
            rasterized criteria for now.
        h_s- A multi-level structure which holds all criteria ratings, 
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
        hab- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile provided by the user.
        stress- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            rasters. In this case, however, the outermost key is by stressor
            name, and stressors['habitatName']['DS'] points to the rasterized
            stressor shapefile provided by the user.
    
    Output:
        Creates a version of every criteria for every h-s paring that is
        burned with both a r/dq*w value for risk calculation, as well as a
        r/dq burned raster for recovery potential calculations.
    
    Returns:     
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): [indiv num raster, raster 1, ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: [indiv num raster, raster 1, ...],
                                ...
                               },
                        's':   { stressA: [indiv num raster, ...]
                               }
                     }
             'Recovery': { hab1: [indiv num raster, ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. This dictionary will be the same structure
            as crit_lists, but the innermost values will be floats instead of
            lists.
    '''
    pre_raster_dir = os.path.join(dir, 'Crit_Rasters')

    os.mkdir(pre_raster_dir)

    crit_lists = {'Risk': {'h-s': {}, 'h':{}, 's':{}},
                  'Recovery': {}
                 }
    denoms = {'Risk': {'h-s': {}, 'h':{}, 's':{}},
                  'Recovery': {}
                 }

    #Now will iterrate through the dictionaries one at a time, since each has
    #to be placed uniquely.

    for pair in h_s:
        h, s = pair

        crit_lists['Risk']['h-s'][pair] = []
        denoms['Risk']['h-s'][pair] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds = h_s[pair]['DS']
        base_band = base_ds.GetRasterBand(1)
        base_nodata = base_band.GetNoDataValue()
        
        #First, want to make a raster of added individual numerator criteria.
        #We will pre-sum all r / (dq*w), and then vectorize that with the 
        #spatially explicit criteria later. Should be okay, as long as we keep
        #the denoms separate until after all raster crits are added.

        '''The following handle the cases for each dictionary for rasterizing
        the individual numerical criteria, and then the raster criteria.'''

        crit_rate_numerator = 0
        #H-S dictionary, Numerical Criteria: should output a 
        #single raster that equals to the sum of r/dq*w for all single number 
        #criteria in H-S

        for crit_dict in (h_s[pair]['Crit_Ratings']).values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['h-s'][pair] += 1 / float(dq*w)

        #This will not be spatially explicit, since we need to add the
        #others in first before multiplying against the decayed raster.
        #Instead, want to only have the crit_rate_numerator where data
        #exists, but don't want to multiply it.
        
        single_crit_C_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + \
                                               s + ']' + '_Indiv_C_Raster.tif')
        #To save memory, want to use vectorize rasters instead of casting to an
        #array. Anywhere that we have nodata, leave alone. Otherwise, use
        #crit_rate_numerator as the burn value.
        def burn_numerator(pixel):

            if pixel == base_nodata:
                return 0
            else:
                return crit_rate_numerator

        c_ds = raster_utils.vectorize_rasters(base_ds, burn_numerator,
                                    raster_out_uri = single_crit_C_uri,
                                    datatype = gdal.GDT_Float32, nodata = [0])

        #Add the burned ds containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['h-s'][pair].append(c_ds)
        
        #H-S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.

        #.iteritems creates a key, value pair for each one.
        for crit, crit_dict in h_s[pair]['Crit_Rasters'].iteritems():

            crit_ds = crit_dict['DS']
            crit_band = crit_ds.GetRasterBand(1)
            crit_nodata = crit_band.GetNoDataValue()
            
            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['h-s'][pair] += 1/ float(dq * w)

            crit_C_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + s + \
                                        ']_' + crit + '_' + 'C_Raster.tif')

            def burn_numerator(pixel):

                if pixel = crit_nodata:
                    return 0

                else:
                    burn_rating = float(pixel) / (dq * w)
                    return burn_rating
            
            c_ds = raster_utils.vectorize_rasters(crit_ds, burn_numerator,
                                    raster_out_uri = crit_C_uri,
                                    datatype = gdal.GDT_Float32, nodata = [0])

            crit_lists['Risk']['h-s'][pair].append(c_ds)
   
    #Habitats are a special case, since each raster needs to be burned twice-
    #once for risk (r/dq*w), and once for recovery potential (r/dq).
    for h in hab:

        crit_lists['Risk']['h'][h] = []
        crit_lists['Recovery'][h] = []
        denoms['Risk']['h'][h] = 0
        denoms['Recovery'][h] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds = hab[h]['DS']
        base_band = base_ds.GetRasterBand(1)
        base_nodata = base_band.GetNoDataValue()

        rec_crit_rate_numerator = 0
        risk_crit_rate_numerator = 0

        for crit_dict in hab[h]['Crit_Ratings'].values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            risk_crit_rate_numerator += r / float(dq*w)
            rec_crit_rate_numerator += r/dq
            denoms['Risk']['h'][h] += 1 / float(dq*w)
            denoms['Recovery'][h] += 1 / dq

        #First, burn the crit raster for risk
        single_crit_C_uri = os.path.join(pre_raster_dir, h + 
                                                        '_Indiv_C_Raster.tif')
        def burn_numerator_risk(pixel):
            
            if pixel == base_nodata:
                return 0

            else:
                return risk_crit_rate_numerator

        c_ds = raster_utils.vectorize_rasters(base_ds, burn_numerator_risk,
                                raster_out_uri = single_crit_C_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])

        crit_lists['Risk']['h'][h].append(c_ds)

        #Now, burn the recovery potential raster, and add that.
        single_crit_C_uri = os.path.join(pre_raster_dir, h + 
                                                  '_Indiv_Recov_Raster.tif')

        def burn_numerator_rec(pixel):
            
            if pixel == base_nodata:
                return 0

            else:
                return rec_crit_rate_numerator

        c_ds = raster_utils.vectorize_rasters(base_ds, burn_numerator_risk,
                                raster_out_uri = single_crit_C_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])

        crit_lists['Recovery'][h].append(c_ds)
        
        #Raster Criteria: should output multiple rasters, each
        #of which is reburned with the old pixel value r as r/dq*w, or r/dq.
        for crit, crit_dict in hab[h]['Crit_Rasters'].iteritems():
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            crit_ds = crit_dict['DS']
            crit_band = crit_ds.GetRasterBand(1)
            crit_nodata = crit_band.GetNoDataValue()

            denoms['Risk']['h'][h] += 1/ float(dq * w)
            denoms['Recovery'][h] += 1/ float(dq)

            #First the risk rasters
            crit_C_uri = os.path.join(pre_raster_dir, h + '_' + crit + \
                                                    '_' + 'C_Raster.tif')
            def burn_numerator_risk(pixel):
            
                if pixel == crit_nodata:
                    return 0

                else:
                    burn_rating = float(pixel) / (w*dq)
                    return burn_rating

            c_ds = raster_utils.vectorize_rasters(crit_ds, burn_numerator_risk,
                                raster_out_uri = crit_C_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])
            crit_lists['Risk']['h'][h].append(c_ds)
            
            #Then the recovery rasters
            crit_recov_uri = os.path.join(pre_raster_dir, h + '_' + crit + \
                                                    '_' + 'Recov_Raster.tif')
            def burn_numerator_rec(pixel):
            
                if pixel == crit_nodata:
                    return 0

                else:
                    burn_rating = float(pixel) / dq
                    return burn_rating

            r_ds = raster_utils.vectorize_rasters(crit_ds, burn_numerator_rec,
                                raster_out_uri = crit_recov_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])
            crit_lists['Recovery'][h].append(r_ds)

    #And now, loading in all of the stressors. Will just be the standard
    #risk equation (r/dq*w)
    for s in stress:

        crit_lists['Risk']['s'][s] = []
        denoms['Risk']['s'][s] = 0

        #The base dataset for all s criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds = stress[s]['DS']
        base_band = base_ds.GetRasterBand(1)
        base_nodata = base_band.GetNoDataValue() 
        #First, want to make a raster of added individual numerator criteria.
        #We will pre-sum all r / (dq*w), and then vectorize that with the 
        #spatially explicit criteria later. Should be okay, as long as we keep 
        #the denoms separate until after all raster crits are added.

        '''The following handle the cases for each dictionary for rasterizing
        the individual numerical criteria, and then the raster criteria.'''

        crit_rate_numerator = 0
        #single raster that equals to the sum of r/dq*w for all single number 
        #criteria in S
        for crit_dict in stress[s]['Crit_Ratings'].values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['s'][s] += 1 / float(dq*w)

        single_crit_E_uri = os.path.join(pre_raster_dir, s + 
                                                     '_Indiv_E_Raster.tif')
        def burn_numerator(pixel):
            
            if pixel == base_nodata:
                return 0

            else:
                return crit_rate_numerator

        e_ds = raster_utils.vectorize_rasters(base_ds, burn_numerator,
                                raster_out_uri = single_crit_E_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])

        #Add the burned ds containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['s'][s].append(e_ds)
        
        #S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.
        for crit, crit_dict in stress[s]['Crit_Rasters'].iteritems():
            crit_ds = crit_dict['DS']
            crit_band = crit_ds.GetRasterBand(1)
            crit_nodata = crit_band.GetNoDataValue()
            
            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['s'][s] += 1/ float(dq * w)

            crit_E_uri = os.path.join(pre_raster_dir, s + '_' + crit + \
                                                    '_' + 'E_Raster.tif')
            def burn_numerator(pixel):
            
                if pixel == crit_nodata:
                    return 0

                else:
                    burn_rating = float(pixel) / (dq*w)
                    return burn_rating

            e_ds = raster_utils.vectorize_rasters(crit_ds, burn_numerator,
                                raster_out_uri = crit_E_uri,
                                datatype = gdal.GDT_Float32, nodata = [0])
            crit_lists['Risk']['s'][s].append(e_ds)

    #This might help.
    return (crit_lists, denoms)
