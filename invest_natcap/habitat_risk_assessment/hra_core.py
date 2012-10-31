'''This is #the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import math
import datetime
import logging
import os
import numpy as np
import shutil

from osgeo import gdal, ogr
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

#gdal.UseExceptions()

def execute(args):
    '''This provides the main functionaility of the hra_core program. This
    will call all parts necessary for calculation of final outputs.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be subfolders of this one.
        args['risk_eq']-  A string representing the equation to be used for
            risk calculation. We should check for possibilities, and send to a 
            different function when deciding R dependent on this.
        args['h-s']- A structure which holds all exposure and consequence
            ratings that are applicable to habitat and stressor overlaps. The
            outermost key is a tuple of two strings, the habitat and the
            stressor. This points to a dictionary whose keys include 'E' for
            exposure criteria, 'C' for consequence criteria, and 'DS', which
            will point directly to an open raster depicting the overlap between
            the habitat and the stressor. E/C will each point to a dictionary
            where the keys are strings names of the criteria, and the values
            are dictionaries. These dictionaries will have keys of 'Rating',
            'DQ' for data quality, and 'Weight', and will point to double
            values which correspond to those qualities of the criteria. The
            structure will be as pictured below:

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        args['habitats']- A structure which will hold exposure and consequence
            criteria data for criteria which are habitat specific. The
            dictionary will contain an open raster dataset to the rasterized
            versions of the habitats.
        args['stressors'] A structure which will hold exposure and consequence
            criteria data for criteria which are stressor specific. The
            dictionary will not contain an open raster dataset, but will
            otherwise be the same structure as the args['h-s'] dictionary.

    Outputs:
        --Intermediate--
            These should be the temp risk add files for the final output calcs.
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

    #NEED TO FIND A WAY OF CALCULATING SPATIAL OVERLAP AUTOMAGICALLY AND THEN
    #INSERT IT INTO THE PROPER H-S DICTIONARY ENTRY. THIS MAY BE BETER OFF IN
    #THE NON-CORE FUNCTION, SO THAT IT ALREADY EXISTS BY THIS POINT, SINCE WE
    #ARE ONLY SEEING H-S BY NOW INSTEAD OF EACH SEPARATE RASTER.

    make_risk_rasters(inter_dir, args['h-s'], args['habitats'], 
                args['stressors'], args['risk_eq'])

    #We know at this point that the non-core module has already recreated the
    #output directory. So we can go ahead and create the maps directory without
    #worrying about it already existing.
    maps_dir = os.path.join(output_dir, 'maps')
    os.mkdir(maps_dir)

    #We will combine all h-s rasters of the same habitat into a cumulative
    #habitat risk raster, and return a list of the datasets of each so that it
    #can be passed on to the ecosystem raster's vectorize_raster
    h_risk_list = make_cum_risk_raster(maps_dir, args['h-s'])

    #Will now combine all habitat rasters insto one overall ecosystem raster
    #using the datasources that we collected from the previous function.
    make_ecosys_risk_raster(maps_dir, h_risk_list)
    
    #Since recovery potential is only related to habitats specifically, we
    #don't need to pass the whole h-s dictionary.
    make_recov_potent_raster(maps_dir, args['habitats'])

def make_recov_potent_raster(direct, habitats):
    '''This will take the scores from the habitat-specific criteria and combine
    them into a recovery potential raster using the following equation.

    (r_NM/ dq_NM) + (r_RR /dq_RR) + (r_RT/ dq_RT) + (r_CR/ dq_CR) 
                _______________________________________
           (1/ dq_NM) + (1 /dq_RR) + (1/ dq_RT) + (1/ dq_CR) 
   
        r = rating score
        dq = data quality score
        NM = Natural Mortality Rate
        RR = Recruitment Rate
        RT = Recovery Time
        CR = Connectivity Rate

        Input:
            direct- The folder into which the recovery potential rasters should
                be placed.
            habitats- A multi-level dictionary structure which holds all scores
                for habitat-specific criteria. This will be used to generate
                the rasters for recovery potential. The form of the structure
                is as follows:
                
                {'Habitat Name': 
                        {'E': 
                            {E's Criteria Dictionaries}, 
                        'C': {'Natural Mortality':
                                {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}                         
                            }
                        }
                }
        Output:
            Raster files which represent each habitat's recovery potential.
                These filenames will be of the form 
                'direct'/recov_potent_H[habitatname].tif.
        
        Returns nothing.
    '''
    for h in habitats:
        
        sum_top = 0.0
        sum_bottom = 0.0

        #Depending on how the criteria are entered, we may need to change the
        #strings to retrieve their data within this fuction.
        NM = habitats[h]['C']['Natural Mortality']
        RR = habitats[h]['C']['Recruitment Rate']
        RT = habitats[h]['C']['Recovery Time']
        CR = habitats[h]['C']['Connectivity Rate']
 
        sum_top += NM['Rating'] / NM['DQ']
        sum_bottom += 1 / NM['DQ']

        sum_top += RR['Rating'] / RR['DQ']
        sum_bottom += 1 / RR['DQ']

        sum_top += RT['Rating'] / RT['DQ']
        sum_bottom += 1 / RT['DQ']

        sum_top += CR['Rating'] / CR['DQ']
        sum_bottom += 1 / CR['DQ']

        r_potent = sum_top / sum_bottom

        orig_dataset = habitats[h]['DS']
        orig_band = orig_dataset.GetRasterBand(1)
        #Create new raster based on the original habitat rasters, then extract
        #the array from the band, and multiply everything by the recovery
        #potential output
        new_uri = os.path.join(direct, 'recov_potent_H[' + h + '].tif')

        new_dataset = raster_utils.new_raster_from_base(orig_dataset, new_uri,
                            'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(new_dataset)
        band.Fill(nodata)

        #Multiply the whole thing by r_potent. Nodata is 0, so should continue
        #to asct as nodata
        orig_array = orig_band.ReadAsArray()
        new_array = orig_array * r_potent

        band.WriteArray(new_array)
        new_dataset.FlushCache()

def make_ecosys_risk_raster(direct, h_ds):
    '''This function will combine all habitat rasters into one overarching
    ecosystem risk raster.
    
    Input:
        direct- The folder into which the completed files should be placed.
        h_ds- Open raster datasources of the completed habitat risk rasters.
            We will combine all of these into one larger ecosystem raster.

    Output:
        A raster file of the form 'direct'/ecosys_risk.tif which displays the
            risk score by pixel for all habitats within the ecosystem.

    Returns nothing.
    '''
    out_uri = os.path.join(direct, 'ecosys_risk.tif')

    def add_e_pixels(*pixels):

        pixel_sum = 0.0

        for p in pixels:

            pixel_sum += p

        return pixel_sum

    LOGGER.info("make_ecosys_raster")
    raster_utils.vectorize_rasters(h_ds, add_e_pixels, aoi = None,
                    raster_out_uri = out_uri, datatype=gdal.GDT_Float32, nodata = 0)

def make_cum_risk_raster(direct, h_s):
    '''This will take all h-s rasters of a given habitat, and combine them to
    visualize a cumulative risk raster for each habitat.

    Input:
        direct- The directory into which the completed habitat risk rasters
            should be placed.
        h_s- A structure which holds all ratings, weights, and data quality
            numbers for each habitat-stressor overlap. Additionally, each h-s
            tuple key points to a dictionary containing a raster dataset of the
            risk scores for all h-s pixels. The structure resembles the
            following:

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }

    Output:
        A set of raster files representing the cumulative risk scores for each
            habitat. These files will combine all habitat-stressor risk rasters,
            and will be of the form 'direct'/cum_risk_H[habitatname].tif.

    Returns:
        h_rasters- A list of open raster datasets corresponding to the completed
            cumulative raster files for each habitat.
    '''
    #THIS WILL BE THE COMBINE FUNCTION
    def add_risk_pixels(*pixels):

        pixel_sum = 0.0

        for p in pixels:
            pixel_sum += p

        return pixel_sum

    #This will give us two np lists where we have only the unique habitats and
    #stressors for the system. 
    habitats = map(lambda pair: pair[0], h_s)   
    habitats = np.array(habitats)
    habitats = np.unique(habitats)

    stressors = map(lambda pair: pair[1], h_s)
    stressors = np.array(stressors)
    stressors = np.unique(stressors)
    
    #Need somewhere to hold the finished cumulative rasters. This will be used
    #to calculate overall ecosystem risk
    h_rasters = []

    #Now we can run through all potential pairings and make lists for the ones
    #that have the same habitat.
    for h in habitats:

        ds_list = []
        for s in stressors:
            #Datasource can be retrieved by indexing into the value dictionary
            #using 'DS'
            ds_list.append(h_s[(h,s)]['DS'])

        #When we have a complete list of the stressors, let's pass the habitat
        #name and our list off to another function and have it create and
        #combine the file.
        out_uri = os.path.join(direct, 'cum_risk_H[' + h + '].tif')
        LOGGER.info("make_cum_risk_raster")    
        h_rast = raster_utils.vectorize_rasters(ds_list, add_risk_pixels, aoi = None,
                    raster_out_uri = out_uri, datatype=gdal.GDT_Float32, nodata = 0)

        h_rasters.append(h_rast)

    return h_rasters

def make_risk_rasters(direct, h_s, habitats, stressors, risk_eq):
    '''This will re-burn the intermediate files of the H-S intersection with
    the risk value for that given layer. This will be calculated based on the
    three ratings dictionaries.

    Input:
        direct- The directory into which the completed raster files should be 
            placed.
        risk_eq- This is a string description of the desired equation to use
            when performing risk calculation.
        h_s- A multi-level structure which contains E/C ratings for each of
            the criteria applicable to the given H-S overlap. It also contains
            the open dataset that shows the raster overlap between the habitat
            and the stressor. The ratings structue is laid out as follows:

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },
                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                    }
            }
        habitats- A multi level dictionary with the same structure as h_s, but
            which only contaings ratings applicable to habitats.
        stressors- A multi-level dictionary with the same structure as h_s, but
            which only contains reatings applicable to stressors. 

    Returns:
        A dictionary which maps h,s pairs to an open raster dataset depicting
            the risk values for that layer.
    '''
    #We will call one of the risk creation equations based on the string
    #passed in by 'risk_eq'. This will return a dataset, and we will then
    #write that out to a file within 'direct'

    #Create dictionary that we can pass back to the execute call and pass on to
    #create habitat rasters
    risk_rasters = {}

    #We are going to us the h_s dictionary as our way of running through all H-S
    #possibilities, and then run through individual criteria from H/S separately.
    for pair in h_s:
        
        #need to identify which is which to be used as a key to the other two
        #dictionaries
        h = pair[0]
        s = pair[1]

        #We will have calc_score_value take in three things- one
        #sub dictionary based on that pair from h_s, one sub dictionary from
        #habitats based on that particular habitat, and one sub dictionary
        #from stressors based on that particular stressor.
        E = calc_score_value(h_s[pair]['E'], habitats[h]['E'], stressors[s]['E'])

        C = calc_score_value(h_s[pair]['C'], habitats[h]['C'], stressors[s]['C'])

        #Need to remember that E should be applied to the decayed raster values,
        #then the decayed value per pixel can be used for the risk value. These
        #functions should return a modified array which can be burned back to
        #the raster band.
        
        #We know, in this case, that there is only one band.
        r_ds = h_s[pair]['DS']
        r_band = r_ds.GetRasterBand(1)
        r_array = r_band.ReadAsArray()
        
        if risk_eq == 'Euclidean':
            mod_array = make_risk_euc(r_array, E, C) 

        elif risk_eq == 'Multiplicative':
            mod_array = make_risk_mult(r_array, E, C)

        risk_uri = os.path.join(direct, "H[" + h + "]_S[" + s + "]_Risk.tif")

        new_dataset = raster_utils.new_raster_from_base(r_ds, risk_uri,
                            'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(new_dataset)
        band.Fill(nodata)

        #Now want to take this dataset and write it back to a new raster file
        #containing the H-S overlap. We will also add it to the dictionary so
        #that it can be saved for later.
        band.WriteArray(mod_array)
        
        risk_rasters[(h, s)] = new_dataset

    return risk_rasters

def calc_score_value(h_s_sub, hab_sub, stress_sub):
    '''This will take in 3 sub-dictionaries and use the criteria that they
    contain to calculate an overall score based on the following equation.
    
    Value = SUM{i=1, N} (r{i}/(d{i}*w{i}) / SUM{i=1, N} 1/(d{i}*w{i})
        
        i = The current criteria that we are evaluating.
        r = Rating value for criteria i.
        N = Total number of criteria being evaluated for the combination of
            habitat and stressor.
        d = Data quality rating for criteria i.
        w = The importance weighting for that criteria relative to other
            criteria being evaluated.
    Inputs:
        Three sub-dictionaries, each of which will have the following form:
            
            {'Criteria Name 1' : {'Rating': 2.0, 'Weight': 1.0, 'DQ': 2.0},
             'Criteria Name 2' : { . . .}
            }
   
    Returns:
        A score value that represents E or C based on the above equation.
    '''
    
    #Want to make into a tuple so I can easily iterate through them and apply
    #the 'no divide by zero' rule to everything at once.
    crit_dicts = (h_s_sub, hab_sub, stress_sub)

    sum_top = 0.0
    sum_bottom = 0.0

    for dictionary in crit_dicts:

        for criteria in dictionary:
           
            r = dictionary[criteria]['Rating']
            d = dictionary[criteria]['DQ']
            w = dictionary[criteria]['Weight']

            if d == 0 or w == 0:
                sum_top += 0
                sum_bottom += 0
            else:
                sum_top += (r / d * w)
                sum_bottom += (1 / d * w)

    S = sum_top / sum_bottom
        
    return S

def make_risk_mult(array, E, C):
    '''This will create a risk raster array using a multiplicative function to
    calculate a risk value for each given pixel.

    Input:
        array- A numpy array containing pixel values for every pixel in the
            raster dataset of a given habitat-stressor overlap.
        E- The calculated overall exposure value for the given h-s criteria.
        C- The calculated overall consequence value for the given h-s criteria. 

    Returns:
        A numpy array of risk values for the given habitat-stressor overlap 
            based on a multiplicative risk function.
    '''
    
    R = array * E * C
    
    return R

def make_risk_euc(array, E, C):
    '''This will create a risk raster array using a euclidean distance function
    to calculate a risk value for every h-s pixel. It should be noted that
    with this equation, the potentially decayed array being passed in will first
    have E applied to it, then then new decayed E's can be used for final
    risk calcs.

    Input:
        array- A numpy array containing pixel values for every pixel in the
            raster dataset of a given habitat-stressor overlap.
        E- The calculated overall exposure value for the given h-s criteria.
        C- The calculated overall consequence value for the given h-s criteria. 

    Returns:
        A numpy array of risk values for the gievn habitat-stressor overlap
            based on a euclidean risk function.
    '''
   
    #Want to get an array that has potential decay applied to E, so that the E
    #could be different for any pixel in the risk array.
    e_array = array * E

    sub_e = (e_array - 1) ** 2
    sub_c = (C - 1) ** 2

    under_sq = sub_e + sub_c

    #Raising to the 1/2 is the same as taking the sqrt
    R = under_sq ** .5

    return R
