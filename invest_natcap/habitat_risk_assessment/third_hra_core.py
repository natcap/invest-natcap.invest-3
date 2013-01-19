'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import logging
import os
import numpy as np
 
from osgeo import gdal
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
            which would multiply E and C, and 'Exponential', which would use
            the equation sqrt((C-1)^2 + (E-1)^2).
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
            name, and stressors['habitatName']['DS'] points to the rasterized
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
            /output/html_plots/output.html- HTML page containing a matlab plot
                has cumulative exposure value for each habitat, as well as risk
                of each habitat plotted per stressor.
            /output/html_plots/plot_ecosys_risk.html- Plots the ecosystem risk
                value for each habitat.
            /output/html_plots/plot_risk.html- Risk value for each habitat
                plotted on a per-stressor graph.
            
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
    h_risk_list = make_cum_risk_raster(maps_dir, risk_dict)

    #Now, combine all of the habitat rasters unto one overall ecosystem
    #rasterusing the DS's from the previous function.
    make_ecosys_risk_raster(maps_dir, h_risk_list)

    #Recovery potential will use the 'Recovery' subdictionary from the
    #crit_lists and denoms dictionaries
    make_recov_potent_raster(maps_dir, crit_lists, denoms)

def make_recov_potent_raster(dir, crit_lists, denoms):
    '''This will do the same as the individual E/C calculations, but instead
    will be r/dq for each criteria.

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
    '''
    #This will give up two np lists where we have only the unique habs and
    #stress for the system.
    habitats = map((lambda pair: pair[0], risk_dict))
    habitats = np.array(habitats)
    habitats = np.unique(habitats)

    #First, going to try doing everything all at once. For every habitat,
    #concat the lists of 
    for h in habitats:

        def add_recov_pix(*pixels):

            value = 0.

            for p in pixels:
                value += p

            value = value / denoms['Recovery'][h]

        curr_list = crit_list['Recovery'][h]

        out_uri = os.path.join(dir, 'recov_potent_H[' + h + '].tif')

        raster_utils.vectorize_rasters(curr_list, add_recov_pixels, aoi = None,
                         raster_out_uri = out_uri, datatype=gdal.GDT_Float32,
                         nodata = 0)


def make_ecosys_risk_raster(dir, h_list):

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

def make_cum_risk_raster(dir, risk_dict):
    
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
    h_rasters = []

    #Run through all potential pairings, and make lists for the ones that
    #share the same habitat.
    for h in habitats:

        ds_list = []
        for s in stressors:
            
            ds_list.append(risk_dict[pair])

        #Once we have the complete list, we can pass it to vectorize.
        out_uri = os.path.join(dir, 'cum_risk_H[' + h + '].tif')

        h_rast = raster_utils.vectorize_rasters(ds_list, add_risk_pixels,
                                 aoi = None, raster_out_uri = out_uri,
                                 datatype=gdal.GDT_Float32, nodata = 0)

        h_rasters.append(h_rast)

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

        #For E/C, want to return a numpy array so that it's easier to work with
        #for risk calc.
        #E will only need to take in stressor subdictionary data
        E = calc_E_raster(e_out_uri, crit_lists['Risk']['s'][s],
                        denoms['Risk']['s'][s])
        #C will need to take in both habitat and hab-stress subdictionary data
        C = calc_C_raster(c_out_uri, crit_lists['Risk']['h-s'][pair], 
                        denoms['Risk']['h-s'][pair], crit_lists['Risk']['h'][h],
                        denoms['Risk']['h'][h])

        #Assume that there will be at least one raster.
        old_ds = crit_lists['Risk']['h-s'][pair][0]
        risk_uri = os.path.join(inter_dir, 'H[' + h + ']_S[' + s + ']_Risk.tif')
        new_ds = raster_utils.new_raster_from_base(old_ds, risk_uri, 'GTiff', 
                                    0, gdal.GDT_Float32)

        band, nodata = raster_utils.extract_band_and_nodata(new_ds)
        band.Fill(nodata)

        #Function that we call now will depend on what the risk calculation
        #equation desired is.

        #Want to get the relevant ds for this H-S pair
        base_ds = h_s[pair]['DS']
        base_array = base_ds.GetRasterBand(1).ReadAsArray()
        
        if risk_eq == 'Multiplicative':
            mod_array = make_risk_mult(base_array, E, C)
        elif risk_eq == 'Euclidean':
            mod_array = make_risk_euc(base_array, E, C)

        band.WriteArray(mod_array)

        risk_rasters[pair] = new_ds

    return risk_rasters

def make_risk_mult(base, e_array, c_array):

    risk_rast =  base* e_array * c_array

    return risk_rast

def make_risk_euc(base, e_array, c_array):

    #Want to make sure that the decay is applied to E first, then that product
    #is what is used as the new E
    e_array = e_array * base

    #Only want to perform these operation if there is data in the cell, else
    #we end up with false positive data when we subtract 1.
    e_array[e_array != 0 ] -= 1
    e_array = e_array * 2

    c_array[c_array != 0] -= 1
    c_array = c_array ** 2

    #Only want to add E and C if there was originally no data in that pixel.
    e_mask = np.make_mask(e_array)
    c_array = e_mask * c_array

    risk_array = c_array + e_array
    risk_array = risk_array ** .5

    return risk_array

def calc_E_raster(out_uri, s_list, s_denom):
    '''Should return a raster burned with an 'E' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns an 'E' raster that is the sum of all individual r/dq*w burned
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
    e_band = e_raster.GetRasterBand(1)
    e_array = e_band.ReadAsArray()

    return e_array

def calc_C_raster(out_uri, h_s_list, h_s_denom, h_list, h_denom):
    '''Should return a raster burned with an 'E' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns an 'E' raster that is the sum of all individual r/dq*w burned
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
    c_array = c_raster.GetRasterBand(1).ReadAsArray()

    return c_ratser

def pre_calc_denoms_and_criteria(dir, h_s, hab, stress):
    '''Want to return two dictionaries in the format of the following:
    (Note: the individual num raster comes from the crit_ratings
    subdictionary and should be pre-summed together to get the numerator
    for that particular raster. )

    crit_lists:
        #All risk burned rasters are r/dq*w
        {'Risk': {  'h-s': { (hab1, stressA): [indiv num raster, raster 1, ...],
                             (hab1, stressB): ...
                           },
                    'h':   { hab1: [indiv num raster, raster 1, ...],
                            ...
                           },
                    's':   { stressA: [indiv num raster, ...]
                           }
                 }
         #all recovery potential burned rasters are r/dq
         'Recovery': { hab1: [indiv num raster, ...],
                       hab2: ...
                     }
        }

    denoms:
        #All risk denoms are concatonated 1/dq*w
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
    '''
    pre_raster_dict = os.path.join(dir, 'Intermediate', 'Crit_Rasters')
    crit_lists = {'Risk': {'h_s': {}, 'h':{}, 's':{}},
                  'Recovery': {}
                 }
    denoms = {'Risk': {'h_s': {}, 'h':{}, 's':{}},
                  'Recovery': {}
                 }

    #Now will iterrate through the dictionaries one at a time, since each has
    #to be placed uniquely.

    for pair in h_s:
        h, s = pair

        crit_lists['Risk']['h_s'][pair] = []
        denoms['Risk']['h_s'][pair] = 0

        #The base dataset for all h_s overlap criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds = h_s[pair]['DS']
        base_band = base_ds.GetRasterBand(1)
        base_array = base_band.ReadAsArray() 
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

        for crit in (h_s[pair]['Crit_Ratings']):
                    
            r = crit['Rating']
            dq = crit['DQ']
            w = crit['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['h_s'][pair] += 1 / float(dq*w)

        single_crit_C_uri = os.path.join(pre_raster_dict, h + '_' + s + 
                                                        '_Indiv_C_Raster.tif')
        c_ds = raster_utils.new_raster_from_base(base_ds, single_crit_C_uri,
                                                 'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(c_ds)
        band.Fill(nodata)

        #This will not be spatially explicit, since we need to add the
        #others in first before multiplying against the decayed raster.
        #Instead, want to only have the crit_rate_numerator where data
        #exists, but don't want to multiply it.
        i_array = base_array
        i_array[i_array != nodata] = crit_rate_numerator
        band.WriteArray(i_array)

        #Add the burned ds containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['h_s'][pair].append(c_ds)
        
        #H-S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.
        for crit in h_s[pair]['Crit_Rasters']:
            crit_raster = crit['DS']
            crit_band = crit_raster.GetRasterBand(1)
            crit_array = crit_band.ReadAsArray()
            dq = crit['DQ']
            w = crit['Weight']
            denoms['Risk']['h_s'][pair] += 1/ float(dq * w)

            crit_C_uri = os.path.join(pre_raster_dict, pair + '_' + crit + \
                                                    '_' + 'C_Raster.tif')
            c_ds = raster_utils.new_raster_from_base(base_ds, crit_C_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(c_ds)
            band.Fill(nodata)

            edited_array = crit_array / float(dq * w)
            band.WriteArray(edited_array)
            crit_lists['Risk']['h_s'][pair].append(c_ds)
    
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
        base_array = base_band.ReadAsArray()

        rec_crit_rate_numerator = 0
        risk_crit_rate_numerator = 0

        for crit in (hab[h]['Crit_Ratings']):
                    
            r = crit['Rating']
            dq = crit['DQ']
            w = crit['Weight']

            #Explicitly want a float output so as not to lose precision.
            risk_crit_rate_numerator += r / float(dq*w)
            rec_crit_rate_numerator += r/dq
            denoms['Risk']['h'][h] += 1 / float(dq*w)
            denoms['Recovery'][h] += 1 / dq

        #First, burn the crit raster for risk
        single_crit_C_uri = os.path.join(pre_raster_dict, h + 
                                                        '_Indiv_C_Raster.tif')
        c_ds = raster_utils.new_raster_from_base(base_ds, single_crit_C_uri,
                                                 'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(c_ds)
        band.Fill(nodata)

        i_burned_array = base_array
        i_burned_array[i_burned_array != nodata] = risk_crit_rate_numerator
        band.WriteArray(i_burned_array)

        crit_lists['Risk']['h'][h].append(c_ds)

        #Now, burn the recovery potential raster, and add that.
        single_crit_C_uri = os.path.join(pre_raster_dict, h + 
                                                  '_Indiv_Recov_Raster.tif')
        c_ds = raster_utils.new_raster_from_base(base_ds, single_crit_C_uri,
                                                 'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(c_ds)
        band.Fill(nodata)

        i_burned_array[i_burned_array != nodata] = rec_crit_rate_numerator
        band.WriteArray(i_burned_array)
        band.WriteArray(i_burned_array)

        crit_lists['Recovery'][h].append(c_ds)
        
        #Raster Criteria: should output multiple rasters, each
        #of which is reburned with the old pixel value r as r/dq*w.
        for crit in h_s[pair]['Crit_Rasters']:
            dq = crit['DQ']
            w = crit['Weight']
            crit_ds = crit['DS']
            crit_band = crit_ds.GetRasterBand(1)
            crit_array = crit_band.ReadAsArray()

            denoms['Risk']['h'][h] += 1/ float(dq * w)
            denoms['Recovery'][h] += 1/ float(dq)

            #First the risk rasters
            crit_C_uri = os.path.join(pre_raster_dict, h + '_' + crit + \
                                                    '_' + 'C_Raster.tif')
            c_ds = raster_utils.new_raster_from_base(base_ds, crit_C_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(c_ds)
            band.Fill(nodata)

            edited_array = crit_array / float(dq * w)
            band.WriteArray(edited_array)
            crit_lists['Risk']['h'][h].append(c_ds)
            
            #Then the recovery rasters
            crit_recov_uri = os.path.join(pre_raster_dict, h + '_' + crit + \
                                                    '_' + 'Recov_Raster.tif')
            r_ds = raster_utils.new_raster_from_base(base_ds, crit_recov_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(r_ds)
            band.Fill(nodata)

            edited_array = crit_array / float(dq)
            band.WriteArray(edited_array)
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
        base_array = base_band.ReadAsArray() 
        #First, want to make a raster of added individual numerator criteria.
        #We will pre-sum all r / (dq*w), and then vectorize that with the 
        #spatially explicit criteria later. Should be okay, as long as we keep 
        #the denoms separate until after all raster crits are added.

        '''The following handle the cases for each dictionary for rasterizing
        the individual numerical criteria, and then the raster criteria.'''

        crit_rate_numerator = 0
        #single raster that equals to the sum of r/dq*w for all single number 
        #criteria in H-S
        for crit in (h_s[pair]['Crit_Ratings']):
                    
            r = crit['Rating']
            dq = crit['DQ']
            w = crit['Weight']

            #Explicitly want a float output so as not to lose precision.
            crit_rate_numerator += r / float(dq*w)
            denoms['Risk']['s'][s] += 1 / float(dq*w)

        single_crit_E_uri = os.path.join(pre_raster_dict, s + 
                                                     '_Indiv_E_Raster.tif')
        e_ds = raster_utils.new_raster_from_base(base_ds, single_crit_E_uri,
                                                 'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(e_ds)
        band.Fill(nodata)

        i_burned_array = base_array
        i_burned_array[i_burned_array != nodata] = crit_rate_numerator
        band.WriteArray(i_burned_array)

        #Add the burned ds containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['s'][s].append(e_ds)
        
        #H-S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.
        for crit in stress[s]['Crit_Rasters']:
            crit_ds = crit['DS']
            crit_band = crit_ds.GetRasterBand(1)
            crit_array = crit_band.ReadAsArray()
            dq = crit['DQ']
            w = crit['Weight']
            denoms['Risk']['s'][s] += 1/ float(dq * w)

            crit_E_uri = os.path.join(pre_raster_dict, pair + '_' + crit + \
                                                    '_' + 'E_Raster.tif')
            e_ds = raster_utils.new_raster_from_base(base_ds, crit_E_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(e_ds)
            band.Fill(nodata)

            edited_array = crit_array / float(dq * w)
            band.WriteArray(edited_array)
            crit_lists['Risk']['s'][s].append(e_ds)

    #This might help.
    return (crit_lists, denoms)
