'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''

import logging
import os
import matlib.pyplot

from osgeo import gdal, ogr
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
        hra_args['h_s_c']- The same as intermediate/'h-s', but with the addition
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
        hra_args['h_s_e']- Similar to the h_s_c dictionary, a multi-level
            dictionary containing habitat-stressor-specific criteria ratings and
            shapes. The same as intermediate/'h-s', but with the addition
            of a 3rd key 'DS' to the outer dictionary layer. This will map to
            a dataset URI that shows the potentially buffered overlap between the 
            habitat and stressor. Additionally, any raster criteria will
            be placed in their criteria name subdictionary. 
        args['risk_eq']- String which identifies the equation to be used
            for calculating risk.  The core module should check for 
            possibilities, and send to a different function when deciding R 
            dependent on this.
        args['max_risk']- The highest possible risk value for any given pairing
            of habitat and stressor.
        args['aoi_tables']- May or may not exist within this model run, but if it
            does, the user desires to have the average risk values by 
            stressor/habitat using E/C axes for each feature in the AOI layer
            specified by 'aoi_tables'. If the risk_eq is 'Euclidea', this will
            create risk plots, otherwise it will just create the standard HTML
            table for either 'Euclidean' or 'Multiplicative.'
        args['aoi_key']- The form of the word 'Name' that the aoi layer uses
            for this particular model run. 
    
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
    
    crit_lists, denoms = pre_calc_denoms_and_criteria(inter_dir, args['h_s_c'],
                                    args['habitats'], args['h_s_e'])

    #Need to have the h_s_c dict in there so that we can use the H-S pair DS to
    #multiply against the E/C rasters in the case of decay.
    risk_dict = make_risk_rasters(args['h_s_c'], inter_dir, crit_lists, denoms, 
                                    args['risk_eq'])

def make_risk_rasters(h_s, inter_dir, crit_lists, denoms, risk_eq):
    '''This will combine all of the intermediate criteria rasters that we
    pre-processed with their r/dq*w. At this juncture, we should be able to 
    straight add the E/C within themselves. The way in which the E/C rasters
    are combined depends on the risk equation desired.

    Input:
        h_s- Args dictionary containing much of the H-S overlap data in
            addition to the H-S base rasters. (In this function, we are only
            using it for the base h-s raster information.)
        inter_dir- Intermediate directory in which the H_S risk-burned rasters
            can be placed.
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h_s_c': { (hab1, stressA): ["indiv num raster URI", 
                                    "raster 1 URI", ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        'h_s_e': { (hab1, stressA): ["indiv num raster URI", ...]
                               }
                     }
             'Recovery': { hab1: ["indiv num raster URI", ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. 
            
            {'Risk': {  'h_s_c': { (hab1, stressA): 2.0, 
                                 (hab1, stressB): 1.3
                               },
                        'h':   { hab1: 3.2,
                                ...
                               },
                        'h_s_e': { (hab1, stressA): 1.2
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
            (Habitat, Stressor) to the URI for the risk raster created when the 
            various sub components (H/S/H_S) are combined.

            {('HabA', 'Stress1'): "A-1 Risk Raster URI",
            ('HabA', 'Stress2'): "A-2 Risk Raster URI",
            ...
            }
    '''
    
    #Create dictionary that we can pass back to execute to be passed along to
    #make_habitat_rasters
    risk_rasters = {}

    #We will use the h-s pairs as the way of iterrating through everything else.
    for pair in crit_lists['Risk']['h_s_c']:

        h, s = pair

        #Want to create an E and a C raster from the applicable 
        #pre-calc'd rasters. We should be able to use vec_ds to straight add 
        #the pixels and divide by the saved denoms total. These are the URIs to
        #which these parts of the risk equation will be burned. 
        c_out_uri = os.path.join(inter_dir, h + '_' + s + '_C_Risk_Raster.tif')
        e_out_uri = os.path.join(inter_dir, h + '_' + s + '_E_Risk_Raster.tif')

        #Each of the E/C calculations should take in all of the relevant 
        #subdictionary data, and return a raster to be used in risk calculation. 
        calc_E_raster(e_out_uri, crit_lists['Risk']['h_s_e'][pair],
                        denoms['h_s_e'][pair])

        calc_C_raster(c_out_uri, crit_lists['Risk']['h_s_c'][pair], 
                    denoms['Risk']['h_s_c'][pair], crit_lists['Risk']['h'][h],
                    denoms['Risk']['h'][h])

        
def calc_E_raster(out_uri, h_s_list, h_s_denom):
    '''Should return a raster burned with an 'E' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        out_uri- The location to which the E raster should be burned.
        h_s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that h, s pair.
        h_s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.
            criteria applicable for that s.

    Returns nothing.
    '''
    grid_size = raster_utils.get_cell_size_from_uri(h_s_list[0])

    def add_e_pix(*pixels):
        
        value = 0.
        
        for p in pixels:
            value += p
    
        return value / h_s_denom

    raster_utils.vectorize_datasets(h_s_list, add_e_pix, out_uri,
                        gdal.GDT_Float32, 0., grid_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)

def calc_C_raster(out_uri, h_s_list, h_s_denom, h_list, h_denom):
    '''Should return a raster burned with a 'C' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        out_uri- The location to which the calculated C raster should be burned.
        h_s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that h, s pair.
        h_s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns nothing.
    '''
    tot_crit_list = h_s_list + h_list
    tot_denom = h_s_denom + h_denom
    grid_size = raster_utils.get_cell_size_from_uri(tot_crit_list[0])

    def add_c_pix(*pixels):
        
        value = 0.
        
        for p in pixels:
            value += p
    
        return value / tot_denom

    raster_utils.vectorize_datasets(tot_crit_list, add_c_pix, out_uri, 
                        gdal.GDT_Float32, 0., grid_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)

def pre_calc_denoms_and_criteria(dir, h_s_c, hab, h_s_e):
    '''Want to return two dictionaries in the format of the following:
    (Note: the individual num raster comes from the crit_ratings
    subdictionary and should be pre-summed together to get the numerator
    for that particular raster. )

    Input:
        dir- Directory into which the rasterized criteria can be placed. This
            will need to have a subfolder added to it specifically to hold the
            rasterized criteria for now.
        h_s_c- A multi-level structure which holds all criteria ratings, 
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
                            {'DS': "CritName Raster URI", 'Weight': 1.0, 'DQ': 1.0}
                        },
                    'DS':  "A-1 Raster URI"
                    }
            }
        hab- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile URI provided by the user.
        h_s_e- Similar to the h_s_c dictionary, a multi-level
            dictionary containing habitat-stressor-specific criteria ratings and
            rasters. The outermost key is by (habitat, stressor) pair, but the
            criteria will be applied to the exposure portion of the risk calcs.
    
    Output:
        Creates a version of every criteria for every h-s paring that is
        burned with both a r/dq*w value for risk calculation, as well as a
        r/dq burned raster for recovery potential calculations.
    
    Returns:     
        crit_lists- A dictionary containing pre-burned criteria URI which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h_s_c': { (hab1, stressA): ["indiv num raster", "raster 1", ...],
                                   (hab1, stressB): ...
                                 },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        'h_s_e': { (hab1, stressA): ["indiv num raster URI", ...]
                                 }
                     }
             'Recovery': { hab1: ["indiv num raster URI", ...],
                           hab2: ...
                         }
            }
        denoms- Dictionary containing the combined denominator for a given
            H-S overlap. Once all of the rasters are combined, each H-S raster
            can be divided by this. This dictionary will be the same structure
            as crit_lists, but the innermost values will be floats instead of
            lists.
    '''
    pre_raster_dir = os.path.join(dir, 'ReBurned_Crit_Rasters')

    os.mkdir(pre_raster_dir)

    crit_lists = {'Risk': {'h_s_c': {}, 'h':{}, 'h_s_e':{}},
                  'Recovery': {}
                 }
    denoms = {'Risk': {'h_s_c': {}, 'h':{}, 'h_s_e':{}},
                  'Recovery': {}
                 }
    
    #Now will iterrate through the dictionaries one at a time, since each has
    #to be placed uniquely.

    #For Hab-Stress pairs that will be applied to the consequence portion of risk.
    for pair in h_s_c:
        h, s = pair

        crit_lists['Risk']['h_s_c'][pair] = []
        denoms['Risk']['h_s_c'][pair] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds_uri = h_s_c[pair]['DS']
        base_nodata = raster_utils.get_nodata_from_uri(base_ds_uri)
        base_pixel_size = raster_utils.get_cell_size_from_uri(base_ds_uri)

        #First, want to make a raster of added individual numerator criteria.
        #We will pre-sum all r / (dq*w), and then vectorize that with the 
        #spatially explicit criteria later. Should be okay, as long as we keep
        #the denoms separate until after all raster crits are added.

        '''The following handle the cases for each dictionary for rasterizing
        the individual numerical criteria, and then the raster criteria.'''

        crit_rate_numerator = 0
        
        #H-S-C dictionary, Numerical Criteria: should output a 
        #single raster that equals to the sum of r/dq*w for all single number 
        #criteria in H-S

        for crit_dict in (h_s_c[pair]['Crit_Ratings']).values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['h_s_c'][pair] += 1 / float(dq*w)
        
        #This will not be spatially explicit, since we need to add the
        #others in first before multiplying against the decayed raster.
        #Instead, want to only have the crit_rate_numerator where data
        #exists, but don't want to multiply it.
        
        single_crit_C_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + \
                                               s + ']' + '_Indiv_C_Raster.tif')
        #To save memory, want to use vectorize rasters instead of casting to an
        #array. Anywhere that we have nodata, leave alone. Otherwise, use
        #crit_rate_numerator as the burn value.
        def burn_numerator_single_hs(pixel):

            if pixel == base_nodata:
                return 0.
            else:
                return crit_rate_numerator

        raster_utils.vectorize_datasets([base_ds_uri], burn_numerator_single_hs,
                        single_crit_C_uri, gdal.GDT_Float32, 0., base_pixel_size,
                        "union", resample_method_list=None, 
                        dataset_to_align_index=None, aoi_uri=None)

        #Add the burned ds URI containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['h_s_c'][pair].append(single_crit_C_uri)
        
        #H-S-C dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.

        #.iteritems creates a key, value pair for each one.
        for crit, crit_dict in h_s_c[pair]['Crit_Rasters'].iteritems():

            crit_ds_uri = crit_dict['DS']
            crit_nodata = raster_utils.get_nodata_from_uri(crit_ds_uri)

            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['h_s_c'][pair] += 1/ float(dq * w)

            crit_C_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + s + \
                                        ']_' + crit + '_' + 'C_Raster.tif')

            def burn_numerator_hs(pixel):

                if pixel == crit_nodata:
                    return 0.

                else:
                    burn_rating = float(pixel) / (dq * w)
                    return burn_rating
            
            raster_utils.vectorize_datasets([crit_ds_uri], burn_numerator_hs,
                        crit_C_uri, gdal.GDT_Float32, 0., base_pixel_size,
                        "union", resample_method_list=None, 
                        dataset_to_align_index=None, aoi_uri=None)

            crit_lists['Risk']['h_s_c'][pair].append(crit_C_uri)

    #Habitats are a special case, since each raster needs to be burned twice-
    #once for risk (r/dq*w), and once for recovery potential (r/dq).
    for h in hab:

        crit_lists['Risk']['h'][h] = []
        crit_lists['Recovery'][h] = []
        denoms['Risk']['h'][h] = 0
        denoms['Recovery'][h] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds_uri = hab[h]['DS']
        base_nodata = raster_utils.get_nodata_from_uri(base_ds_uri)
        base_pixel_size = raster_utils.get_cell_size_from_uri(base_ds_uri)

        rec_crit_rate_numerator = 0
        risk_crit_rate_numerator = 0

        for crit_dict in hab[h]['Crit_Ratings'].values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            risk_crit_rate_numerator += r / float(dq*w)
            rec_crit_rate_numerator += r/ float(dq)
            denoms['Risk']['h'][h] += 1 / float(dq*w)
            denoms['Recovery'][h] += 1 / float(dq)

        #First, burn the crit raster for risk
        single_crit_C_uri = os.path.join(pre_raster_dir, h + 
                                                        '_Indiv_C_Raster.tif')
        def burn_numerator_risk_single(pixel):
            
            if pixel == base_nodata:
                return 0.

            else:
                return risk_crit_rate_numerator

        raster_utils.vectorize_datasets([base_ds_uri], burn_numerator_risk_single,
                            single_crit_C_uri, gdal.GDT_Float32, 0., 
                            base_pixel_size, "union", 
                            resample_method_list=None, 
                            dataset_to_align_index=None, aoi_uri=None)

        crit_lists['Risk']['h'][h].append(single_crit_C_uri)

        #Now, burn the recovery potential raster, and add that.
        single_crit_rec_uri = os.path.join(pre_raster_dir, h + 
                                                  '_Indiv_Recov_Raster.tif')

        def burn_numerator_rec_single(pixel):
            
            if pixel == base_nodata:
                return 0.

            else:
                return rec_crit_rate_numerator

        raster_utils.vectorize_datasets([base_ds_uri], burn_numerator_rec_single,
                            single_crit_rec_uri, gdal.GDT_Float32, 0., 
                            base_pixel_size, "union", 
                            resample_method_list=None, 
                            dataset_to_align_index=None, aoi_uri=None)

        crit_lists['Recovery'][h].append(single_crit_rec_uri)
        
        #Raster Criteria: should output multiple rasters, each
        #of which is reburned with the old pixel value r as r/dq*w, or r/dq.
        for crit, crit_dict in hab[h]['Crit_Rasters'].iteritems():
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            crit_ds_uri = crit_dict['DS']
            crit_nodata = raster_utils.get_nodata_from_uri(crit_ds_uri)

            denoms['Risk']['h'][h] += 1/ float(dq * w)
            denoms['Recovery'][h] += 1/ float(dq)

            #First the risk rasters
            crit_C_uri = os.path.join(pre_raster_dir, h + '_' + crit + \
                                                    '_' + 'C_Raster.tif')
            def burn_numerator_risk(pixel):
            
                if pixel == crit_nodata:
                    return 0.

                else:
                    burn_rating = float(pixel) / (w*dq)
                    return burn_rating

            raster_utils.vectorize_datasets([crit_ds_uri], burn_numerator_risk,
                                crit_C_uri, gdal.GDT_Float32, 0., base_pixel_size, 
                                "union", resample_method_list=None, 
                                dataset_to_align_index=None, aoi_uri=None)
            
            crit_lists['Risk']['h'][h].append(crit_C_uri)
            
            #Then the recovery rasters
            crit_recov_uri = os.path.join(pre_raster_dir, h + '_' + crit + \
                                                    '_' + 'Recov_Raster.tif')
            def burn_numerator_rec(pixel):
            
                if pixel == crit_nodata:
                    return 0.

                else:
                    burn_rating = float(pixel) / dq
                    return burn_rating

            raster_utils.vectorize_datasets([crit_ds_uri], burn_numerator_rec,
                                crit_recov_uri, gdal.GDT_Float32, 0., base_pixel_size, 
                                "union", resample_method_list=None, 
                                dataset_to_align_index=None, aoi_uri=None)
            
            crit_lists['Recovery'][h].append(crit_recov_uri)

    #Hab-Stress for Exposure
    for pair in h_s_e:
        h, s = pair

        crit_lists['Risk']['h_s_e'][pair] = []
        denoms['Risk']['h_s_e'][pair] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds_uri = h_s_e[pair]['DS']
        base_nodata = raster_utils.get_nodata_from_uri(base_ds_uri)
        base_pixel_size = raster_utils.get_cell_size_from_uri(base_ds_uri)
        
        #First, want to make a raster of added individual numerator criteria.
        #We will pre-sum all r / (dq*w), and then vectorize that with the 
        #spatially explicit criteria later. Should be okay, as long as we keep
        #the denoms separate until after all raster crits are added.

        '''The following handle the cases for each dictionary for rasterizing
        the individual numerical criteria, and then the raster criteria.'''

        crit_rate_numerator = 0
        
        #H-S-E dictionary, Numerical Criteria: should output a 
        #single raster that equals to the sum of r/dq*w for all single number 
        #criteria in H-S

        for crit_dict in (h_s_e[pair]['Crit_Ratings']).values():
                    
            r = crit_dict['Rating']
            dq = crit_dict['DQ']
            w = crit_dict['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['h_s_e'][pair] += 1 / float(dq*w)
        
        #This will not be spatially explicit, since we need to add the
        #others in first before multiplying against the decayed raster.
        #Instead, want to only have the crit_rate_numerator where data
        #exists, but don't want to multiply it.
        
        single_crit_E_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + \
                                               s + ']' + '_Indiv_E_Raster.tif')
        #To save memory, want to use vectorize rasters instead of casting to an
        #array. Anywhere that we have nodata, leave alone. Otherwise, use
        #crit_rate_numerator as the burn value.
        def burn_numerator_single_hs(pixel):

            if pixel == base_nodata:
                return 0.
            else:
                return crit_rate_numerator

        raster_utils.vectorize_datasets([base_ds_uri], burn_numerator_single_hs,
                        single_crit_C_uri, gdal.GDT_Float32, 0., base_pixel_size,
                        "union", resample_method_list=None, 
                        dataset_to_align_index=None, aoi_uri=None)

        #Add the burned ds URI containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['h_s_e'][pair].append(single_crit_E_uri)
        
        #H-S-E dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.

        #.iteritems creates a key, value pair for each one.
        for crit, crit_dict in h_s_e[pair]['Crit_Rasters'].iteritems():

            crit_ds_uri = crit_dict['DS']
            crit_nodata = raster_utils.get_nodata_from_uri(crit_ds_uri)

            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['h_s_e'][pair] += 1/ float(dq * w)

            crit_E_uri = os.path.join(pre_raster_dir, 'H[' + h + ']_S[' + s + \
                                        ']_' + crit + '_' + 'E_Raster.tif')

            def burn_numerator_hs(pixel):

                if pixel == crit_nodata:
                    return 0.

                else:
                    burn_rating = float(pixel) / (dq * w)
                    return burn_rating
            
            raster_utils.vectorize_datasets([crit_ds_uri], burn_numerator_hs,
                        crit_C_uri, gdal.GDT_Float32, 0., base_pixel_size,
                        "union", resample_method_list=None, 
                        dataset_to_align_index=None, aoi_uri=None)

            crit_lists['Risk']['h_s_e'][pair].append(crit_C_uri)
    
    #This might help.
    return (crit_lists, denoms)