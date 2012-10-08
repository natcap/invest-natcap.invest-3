'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import math
import datetime
import logging
import os
import numpy as np

from osgeo import gdal, ogr
from invest_natcap import raster_utils

LOGGER = logging.getLogger('HRA_CORE')
logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

def execute(args):
    '''The overarching function that will call all parts of the HRA model.

    Inputs:
        args- Dictionary containing everything that hra_core will need to
            complete the rest of the model run. It will contain the following.
        args['workspace_dir']- Directory in which all data resides. Output
            and intermediate folders will be supfolders of this one.
        args['ratings']- A structure which holds all exposure and consequence
            rating for each combination of habitat and stressor. The inner
            structure is a dictionary whose key is a tuple which points to a
            dictionary where the keys are string descriptions of the values,
            and the values are two lists and a open raster dataset.

            {(Habitat A, Stressor 1): 
                    {'E': 
                        {'Spatital Overlap': 
                            {'Rating': 2.0, 'DQ': 1.0, 'Weight': 1.0}
                        },

                    'C': {C's Criteria Dictionaries},
                    'DS':  <Open A-1 Raster Dataset>
                                       .
                                       .
                                       . 
                    }
            }

    Outputs:
        --Intermediate--
            These should be the temp risk add files for the final output calcs.
        --Output--
            /output/maps/recov_potent.tif- Raster layer depicting the recovery
                potential of the predominant habitat for a given cell.
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
            
            /output/Parameters_[TIME].txt- Lists the parameters that the model
                was run with.
    Returns nothing.
    '''
    
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    #This will pre-calculate the risk value for each of the stressor layers
    #and re-burn the raster. Should be noted that the H-S overlap raster for
    #each pair already exists within the inter_dir file, but can be accessed
    #by using the ratings structure, since there is an open version of the
    #raster dataset there.
    burn_risk_values(args['ratings'])

    #this will take the new raster datasets that are still conatined within the
    #ratings structure, and combine them for all rasters whose first key is the
    #same habitat.
    maps_dir = os.path.join(output_dir, 'maps')
    h_risk_list = make_cum_risk_raster(maps_dir, args['ratings'])

    #In this case, may be easier to get the files that were already rasterized
    #to disk, and combine them that way, rather than trying to select the
    #correct combination of open datasets
    make_ecosys_risk_raster(maps_dir, h_risk_list)

def make_ecosys_risk_raster(dir, h_risks):
    '''This function will output a raster which combines all of the habitat
    risk rasters.

    Input:
        dir- The folder into which the completed file should be placed.
        h_risks- A list containing the open raster datasets of cumulative
            habitat risk.

    Output:
        A file of the form '/dir/ecosys_risk.tif' that is a combined grid of
            risks across all habitats being viewed within this model. Each
            grid cell will be the sum of the habitat risks contained within
            that cell.

    Returns nothing.
    '''
    out_uri = os.path.join(dir, 'ecosys_risk.tif')

    def add_e_pixels(*pixels):

        pixel_sum = 0.0

        for p in pixels:

            pixel_sum += p

        return pixel_sum

    raster_utils.vectorize_rasters(h_risks, add_e_pixels, aoi = None,
                    raster_out_uri = out_uri, datatype=gdal.GDT_Float32, nodata = 0)


def make_cum_risk_raster(dir, ratings):
    '''This will create the outputs for the cumulative habitat risk of the
    given habitat.

    Input:
        dir- The dirctory into which the completed raster files should be
            placed. Note: they should be of the form 
            /dir/cum_risk_H[habitatname].tif
        ratings- A multi-level structure which contains E/C ratings for each of
            the criteria applicable to the given H-S overlap. It also contains
            the open dataset that shows the raster overlap between the habitat
            and the stressor with the risk value for that H-S combination as
            the burn value. The ratings structue is laid out as follows:
            
            {(Habitat A, Stressor 1): 'E': [(E1Rating, E1DataQuality, E1Weight), ...],
                                      'C': [(C1Rating, C1DataQuality, C1Weight), ...],
                                      'DS':  <Open A-1 Raster Dataset>
                                       .
                                       .
                                       . }
    Output:
        /dir/cum_risk_H[habitatname].tif- A raster file that represents the
            cumulative risk of all stressors within the gievn habitat across
            all shown pixels.

    Returns a list containing the open cumulative habitat raster datasets so
        they can be passed along to the overall ecosystem risk.
    '''
    #THIS WILL BE THE COMBINE FUNCTION
    def add_risk_pixels(*pixels):

        pixel_sum = 0.0

        for p in pixels:
            pixel_sum += p

        return pixel_sum

    #This will give us two np lists where we have only the unique habitats and
    #stressors for the system. 
    habitats = map(lambda pair: pair[0], ratings)   
    habitats = np.array(habitats)
    habitats = np.unique(habitats)

    stressors = maps(lambda pair: pair[1], ratings)
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
            ds_list.append(ratings[(h,s)]['DS'])

        #When we have a complete list of the stressors, let's pass the habitat
        #name and our list off to another function and have it create and
        #combine the file.
        out_uri = os.path.join(dir, 'cum_risk_H[' + h + '].tif')
        
        h_rast = raster_utils.vectorize_rasters(ds_list, add_risk_pixels, aoi = None,
                    raster_out_uri = out_uri, datatype=gdal.GDT_Float32, nodata = 0)

        h_rasters.append(h_raster)

    return cum_rasters
def burn_risk_values(ratings):
    '''This will re-burn the intermediate files of the H-S intersection with
    the risk value for that given layer. This will be calculated based on the
    ratings withing the 'ratings' structure.

    Input:
        ratings- A multi-level structure which contains E/C ratings for each of
            the criteria applicable to the given H-S overlap. It also contains
            the open dataset that shows the raster overlap between the habitat
            and the stressor. The ratings structue is laid out as follows:

            {(Habitat A, Stressor 1): 'E': [(E1Rating, E1DataQuality, E1Weight), ...],
                                      'C': [(C1Rating, C1DataQuality, C1Weight), ...],
                                      'DS':  <Open A-1 Raster Dataset>
                                       .
                                       .
                                       . }

    Output:
        Updated versions of the H-S datasets with the risk value burned to the
            overlap area of the given habitat and stressor.

    Returns nothing.
    '''
    
    #Want to run this for each of the H-S layers
    for pair in ratings:

        #Want the 'E' value within the ratings[pair] entry of the ratings
        #dictionary. This is a list of the exposure ratings.
        E = calculate_exposure_value(ratings[pair]['E'])
        
        #The 'C' makes to a list of the consequence values.
        C = calculate_consequence_value(pair[1])

        R = calculate_risk_value(E, C)

        dataset = pair[2]
        gdal.RasterizeLayer(dataset, [1], burn_values=[R]) 

def calculate_exposure_value(iterable):
    '''This is the weighted average exposure value for all criteria for a given
    H-S combination as determined on a run by run basis. The equation is 
    as follows:

    E = SUM{i=1, N} (e{i}/(d{i}*w{i}) / SUM{i=1, N} 1/(d{i}*w{i})
        
        i = The current criteria that we are evaluating.
        e = Exposure value for criteria i.
        N = Total number of criteria being evaluated for the combination of
            habitat and stressor.
        d = Data quality rating for criteria i.
        w = The importance weighting for that criteria relative to other
            criteria being evaluated.
    '''
    sum_top, sum_bottom = 0.0

    for criteria in iterable:
        
        #For this imaginary data structure, imagine that each criteria maps
        #to a tuple of (value, data quality, weight)
        e_i, d_i, w_i = iterable[criteria]
        
        sum_top += e_i / (d_i * w_i)
        sum_bottom += 1 / (d_i * w_i)

    E = sum_top / sum_bottom

    return E

def calculate_consequence_value(iterable):
    '''Structure of this equation will be the same as the exposure values.
    However, the iterable passed in should contain criteria specific to the
    consequences of that particular H-S interraction.'''

    sum_top, sum_bottom = 0.0

    for criteria in iterable:
        
        #For this imaginary data structure, imagine that each criteria maps
        #to a tuple of (value, data quality, weight)
        c_i, d_i, w_i = iterable[criteria]
        
        sum_top += c_i / (d_i * w_i)
        sum_bottom += 1 / (d_i * w_i)

    C = sum_top / sum_bottom

    return C

#For this, I am assuming that something is running the risk values as a loop,
#and passing in the E and C values that it wants us to use.
def calculate_risk_value(exposure, consequence):
    '''Takes an individual exposure value and consequence value (we assume they are
    from the same H-S space, and finds their euclidean distance from the origin of
    the exposure-consequence space.

        Input:
            exposure- Avg. of exposure values within a H-S space.
            consequence- Avg. of consequence values within a H-S space.

        Returns:
            R - The risk value for the given E and C.
    '''

    R = math.sqrt((exposure - 1)**2 + (consequence - 1)**2)

    return R

