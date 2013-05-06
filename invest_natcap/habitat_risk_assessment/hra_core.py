'''This is the core module for HRA functionality. This will perform all HRA
calcs, and return the appropriate outputs.
'''
import logging
import os
import collections 
import math
import datetime
import matplotlib.pyplot

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
        args['h-s']- The same as intermediate/'h-s', but with the addition
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
        args['habitats']- Similar to the h-s dictionary, a multi-level
            dictionary containing all habitat-specific criteria ratings and
            rasters. In this case, however, the outermost key is by habitat
            name, and habitats['habitatName']['DS'] points to the rasterized
            habitat shapefile URI provided by the user.
        args['stressors']- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            name, and stressors['stressorName']['DS'] points to the rasterized
            stressor shapefile URI provided by the user that will be buffered by
            the indicated amount in buffer_dict['stressorName'].
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

    crit_lists, denoms = pre_calc_denoms_and_criteria(inter_dir, args['h-s'],
                                    args['habitats'], args['stressors'])

    #Need to have h-s in there so that we can use the DS for each H-S pair to
    #multiply against the E/C rasters in the case of decay.
    risk_dict = make_risk_rasters(args['h-s'], inter_dir, crit_lists, denoms, 
                                    args['risk_eq'])

    #Know at this point that the non-core has re-created the ouput directory
    #So we can go ahead and make the maps directory without worrying that
    #it will throw an 'already exists.'
    maps_dir = os.path.join(output_dir, 'Maps')
    os.mkdir(maps_dir)

    #We will combine all of the h-s rasters of the same habitat into
    #cumulative habitat risk rastersma db return a list of the DS's of each,
    #so that it can be read into the ecosystem risk raster's vectorize.
    h_risk_dict = make_hab_risk_raster(maps_dir, risk_dict)
    
    #Also want to output a polygonized version of high risk areas in each
    #habitat. Will polygonize everything that falls above a certain percentage
    #of the total raster risk.
    num_stress = make_risk_shapes(maps_dir, crit_lists, h_risk_dict, args['max_risk'])
    
    #Now, combine all of the habitat rasters unto one overall ecosystem
    #rasterusing the DS's from the previous function.
    make_ecosys_risk_raster(maps_dir, h_risk_dict)

    #Recovery potential will use the 'Recovery' subdictionary from the
    #crit_lists and denoms dictionaries
    make_recov_potent_raster(maps_dir, crit_lists, denoms)

    if 'aoi_tables' in args:

        #Let's pre-calc stuff so we don't have to worry about it in the middle of
        #the file creation.
        avgs_dict, aoi_names = pre_calc_avgs(inter_dir, risk_dict, args['aoi_tables'], args['aoi_key'])
        aoi_pairs = rewrite_avgs_dict(avgs_dict, aoi_names)
        
        tables_dir = os.path.join(output_dir, 'HTML_Plots')
        os.mkdir(tables_dir)
        
        make_aoi_tables(tables_dir, aoi_pairs, args['max_risk'])

        if args['risk_eq'] == 'Euclidean':
            make_risk_plots(tables_dir, aoi_pairs, args['max_risk'], num_stress, len(h_risk_dict))

def rewrite_avgs_dict(avgs_dict, aoi_names):
    '''Aftermarket rejigger of the avgs_dict setup so that everything is AOI
    centric instead. Should produce something like the following:
    
    {'AOIName':
        [(HName, SName, E, C, Risk), ...],
        ....
    }
    '''
    pair_dict = {}

    for aoi_name in aoi_names:
        pair_dict[aoi_name] = []

        for h_name, h_dict in avgs_dict.items():
            for s_name, s_list in h_dict.items():
                        
                for aoi_dict in s_list:
                    if aoi_dict['Name'] == aoi_name:
                        pair_dict[aoi_name].append((h_name, s_name, aoi_dict['E'], aoi_dict['C'], aoi_dict['Risk']))

    return pair_dict

def make_risk_plots(out_dir, aoi_pairs, max_h_s_risk, num_stress, num_habs):
    '''This function will produce risk plots when the risk equation is
    euclidean.

    Input:
        out_dir- The directory into which the completed risk plots should be
            placed.
        
        aoi_pairs-

            {'AOIName':
                [(HName, SName, E, C, Risk), ...],
                ....
            }

        num_stress- A dictionary that simply associates every habaitat with the
            number of stressors associated with it. This will help us determine
            the max E/C we shoudl be expecting in our overarching ecosystem plot.
    Output:
        A set of .png images containing the matplotlib plots for every H-S
        combination. Within that, each AOI will be displayed as plotted by
        (E,C) values.

        A single png that is the "ecosystem plot" where the E's for each AOI
        are the summed 


    '''
    def plot_background_circle(max_value):
        circle_stuff = [(5, '#C44539'), (4.75, '#CF5B46'), (4.5, '#D66E54'), (4.25, '#E08865'),
                        (4, '#E89D74'), (3.75, '#F0B686'), (3.5, '#F5CC98'), (3.25, '#FAE5AC'),
                        (3, '#FFFFBF'), (2.75, '#EAEBC3'), (2.5, '#CFD1C5'), (2.25, '#B9BEC9'),
                        (2, '#9FA7C9'), (1.75, '#8793CC'), (1.5, '#6D83CF'), (1.25, '#5372CF'),
                        (1, '#305FCF')]
        index = 0
        for radius, color in circle_stuff:
            index += 1
            linestyle = 'solid' if index % 2 == 0 else 'dashed'
            cir = matplotlib.pyplot.Circle((0, 0), edgecolor='.25', linestyle=linestyle, 
                        radius=radius * max_value/ 3.5, fc=color)
            matplotlib.pyplot.gca().add_patch(cir)

    
    #Create plots for each combination of AOI, Hab
    plot_index = 0

    for aoi_name, aoi_list in aoi_pairs.iteritems():

        matplotlib.pyplot.figure(plot_index)
        plot_index += 1
        matplotlib.pyplot.suptitle(aoi_name)

        hab_index = 0
        curr_hab_name = aoi_list[0][0]

        #Elements look like: (HabName, StressName, E, C, Risk)
        for element in aoi_list:
            if element == aoi_list[0]:

                max_risk = max_h_s_risk * num_stress[curr_hab_name]

                #Want to have two across, and make sure there are enough spaces
                #going down for each of the subplots 
                matplotlib.pyplot.subplot(int(math.ceil(num_habs/2.0)), 2, hab_index)
                plot_background_circle(max_risk)
                matplotlib.pyplot.title(curr_hab_name)
                matplotlib.pyplot.xlim([0.5, max_risk])
                matplotlib.pyplot.ylim([0.5, max_risk])
                matplotlib.pyplot.xlabel("Exposure")
                matplotlib.pyplot.ylabel("Consequence")

            hab_name = element[0]
            if curr_hab_name == hab_name:

                matplotlib.pyplot.plot(element[2], element[3], 'k^', 
                        markerfacecolor='black', markersize=8)
                matplotlib.pyplot.annotate(element[1], xy=(element[2], 
                        element[3]), xytext=(element[2], element[3]+0.07))
                continue    
            
            #We get here once we get to the next habitat
            hab_index += 1
            matplotlib.pyplot.subplot(int(math.ceil(num_habs/2.0)), 2, hab_index)
            plot_background_circle(max_risk)
        
            curr_hab_name = hab_name

            max_risk = max_h_s_risk * num_stress[curr_hab_name]
            
            matplotlib.pyplot.title(curr_hab_name)
            matplotlib.pyplot.xlim([0.5, max_risk])
            matplotlib.pyplot.ylim([0.5, max_risk])
            matplotlib.pyplot.xlabel("Exposure")
            matplotlib.pyplot.ylabel("Consequence")

        out_uri = os.path.join(out_dir, 'risk_plot_' + 'AOI[' + aoi_name+ '].png')

        matplotlib.pyplot.savefig(out_uri, format='png')

    #Create one ecosystem megaplot that plots the points as summed E,C from
    #a given habitat, AOI pairing. So each dot would be (HabitatName, AOI1)
    #for all habitats in the ecosystem.
    plot_index += 1
    max_tot_risk = max_h_s_risk * max(num_stress.values()) * num_habs 
    
    matplotlib.pyplot.figure(plot_index)
    matplotlib.pyplot.suptitle("Ecosystem Risk")
    
    plot_background_circle(max_tot_risk)
    
    points_dict = {}
    
    for aoi_name, aoi_list in aoi_pairs.items():

        for element in aoi_list:
        
            if aoi_name in points_dict:
                points_dict[aoi_name]['E'] += element[2]
                points_dict[aoi_name]['C'] += element[3]
            else:
                points_dict[aoi_name] = {}
                points_dict[aoi_name]['E'] = 0
                points_dict[aoi_name]['C'] = 0

    for aoi_name, p_dict in points_dict.items():
        #Create the points which are summed AOI's across all Habitats.    
        matplotlib.pyplot.plot(p_dict['E'], p_dict['C'], 'k^', 
                    markerfacecolor='black', markersize=8)
        matplotlib.pyplot.annotate(aoi_name,
                    xy=(p_dict['E'], p_dict['C']), 
                    xytext=(p_dict['E'], p_dict['C']+0.07))
                        
    matplotlib.pyplot.xlim([0.5, max_tot_risk])
    matplotlib.pyplot.ylim([0.5, max_tot_risk])
    matplotlib.pyplot.xlabel("Exposure (Cumulative)")
    matplotlib.pyplot.ylabel("Consequence (Cumulative)")

    out_uri = os.path.join(out_dir, 'ecosystem_risk_plot.png')
    matplotlib.pyplot.savefig(out_uri, format='png')

def make_aoi_tables(out_dir, aoi_pairs, max_risk):
    '''This function will take in an shapefile containing multiple AOIs, and
    output a table containing values averaged over those areas.

    Input:
        out_dir- The directory into which the completed HTML tables should be
            placed.
        aoi_pairs- Replacement for avgs_dict, holds all the averaged values on
            a H, S basis.

            {'AOIName':
                [(HName, SName, E, C, Risk), ...],
                ....
            }
     Output:
        A set of HTML tables which will contain averaged values of E, C, and
        risk for each H, S pair within each AOI. Additionally, the tables will
        contain a column for risk %, which is the averaged risk value in that
        area divided by the total potential risk for a given pixel in the map.

     Returns nothing.
    '''

    filename = os.path.join(out_dir, 'Sub_Region_Averaged_Results_[%s].html' \
                   % datetime.datetime.now().strftime("%Y-%m-%d_%H_%M"))

    file = open(filename, "w")

    file.write("<html>")
    file.write("<title>" + "InVEST HRA" + "</title>")
    file.write("<CENTER><H1>" + "Habitat Risk Assessment Model" + "</H1></CENTER>")
    file.write("<br>")
    file.write("This page contains results from running the InVEST Habitat Risk \
    Assessment model." + "<p>" + "Each table displays values on a per-habitat \
    basis. For each overlapping stressor within the model, the averages for the \
    desired sub-regions are presented. C, E, and Risk values are calculated as \
    an average across a given subregion. Risk Percentage is calculated as a \
    function of total potential risk within that area.")
    file.write("<br><br>")
    file.write("<HR>")


    #Now, all of the actual calculations within the table. We want to make one
    #table for each AOi used on the subregions shapefile.
    for aoi_name, aoi_list in aoi_pairs.items():
        
        file.write("<H2>" + aoi_name + "</H2>")
        file.write('<table border="1", cellpadding="5">')

        #Headers row
        file.write("<tr><b><td>Habitat Name</td><td>Stressor Name</td><td>E</td>" + \
            "<td>C</td><td>Risk</td><td>Risk %</td></b></tr>")

        #Element looks like (HabName, StressName, E, C, Risk)
        for element in aoi_list:

            file.write("<tr>")
            file.write("<td>" + element[0]+ "</td>")
            file.write("<td>" + element[1] + "</td>")
            file.write("<td>" + str(round(element[2], 2)) + "</td>")
            file.write("<td>" + str(round(element[3], 2)) + "</td>")
            file.write("<td>" + str(round(element[4], 2)) + "</td>")
            file.write("<td>" + str(round(element[4] * 100 / max_risk, 2)) + "</td>")
            file.write("</tr>")
            
        #End of the AOI-specific table
        file.write("</table>")

    #End of the page.
    file.write("</html>")
    file.close()


def pre_calc_avgs(inter_dir, risk_dict, aoi_uri, aoi_key):
    '''This funtion is a helper to make_aoi_tables, and will just handle
    pre-calculation of the average values for each aoi zone.

    Input:
        inter_dir- The directory which contains the individual E and C rasters.
            We can use these to get the avg. E and C values per area. Since we
            don't really have these in any sort of dictionary, will probably
            just need to explicitly call each individual file based on the
            names that we pull from the risk_dict keys.
        risk_dict- A simple dictionary that maps a tuple of 
            (Habitat, Stressor) to the URI for the risk raster created when the 
            various sub components (H/S/H_S) are combined.

            {('HabA', 'Stress1'): "A-1 Risk Raster URI",
            ('HabA', 'Stress2'): "A-2 Risk Raster URI",
            ...
            }
        aoi_uri- The location of the AOI zone files. Each feature within this
            file (identified by a 'name' attribute) will be used to average 
            an area of E/C/Risk values.

    Returns:
        avgs_dict- A multi level dictionary to hold the average values that
            will be placed into the HTML table.

            {'HabitatName':
                {'StressorName':
                    [{'Name': AOIName, 'E': 4.6, 'C': 2.8, 'Risk': 4.2},
                        {...},
                    ...
                    ]
                },
                ....
            }
       aoi_names- Quick and dirty way of getting the AOI keys.
    '''
    #Since we know that the AOI will be consistent across all of the rasters,
    #want to create the new int field, and the name mapping dictionary upfront
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    aoi = ogr.Open(aoi_uri)
    cp_aoi_uri = os.path.join(inter_dir, 'temp_aoi_copy.shp')
    cp_aoi = driver.CopyDataSource(aoi, cp_aoi_uri)
    layer = cp_aoi.GetLayer()

    field_defn = ogr.FieldDefn('BURN_ID', ogr.OFTInteger)
    layer.CreateField(field_defn)

    name_map = {}
    count = 0
    ids = []

    for feature in layer:

        ids.append(count)
        name = feature.items()[aoi_key]
        feature.SetField('BURN_ID', count)
        name_map[count] = name
        count += 1

        layer.SetFeature(feature)
        
    layer.ResetReading()

    #Now we will loop through all of the various pairings to deal with all their
    #component parts across our AOI. Want to make sure to use our new field as
    #the index.
    avgs_dict = {}

    for pair in risk_dict:
        h, s = pair

        if h not in avgs_dict:
            avgs_dict[h] = {}
        if s not in avgs_dict[h]:
            avgs_dict[h][s] = []

        #The way that aggregate_raster_values is written, it does not include an
        #entry for any AOI feature that does not overlap a valid pixel.
        #Thus, we want to initialize ALL to 0, then just update if there is any
        #change.
        r_agg_dict = dict.fromkeys(ids, 0)
        e_agg_dict = dict.fromkeys(ids, 0)
        c_agg_dict = dict.fromkeys(ids, 0)

        #GETTING MEANS OF THE RISK RASTERS HERE

        r_raster_uri = risk_dict[pair]

        #We explicitly placed the 'BURN_ID' feature on each layer. Since we know
        #currently there is a 0 value for all means, can just update each entry
        #if there is a real mean found.
        r_agg_dict.update(raster_utils.aggregate_raster_values_uri(r_raster_uri, cp_aoi_uri, 'BURN_ID',
                        'mean'))

        #GETTING MEANS OF THE E RASTERS HERE

        #Just going to have to pull explicitly. Too late to go back and
        #rejigger now.
        e_rast_uri = os.path.join(inter_dir, h + '_' + s + '_E_Risk_Raster.tif')

        e_agg_dict.update(raster_utils.aggregate_raster_values_uri(e_rast_uri, cp_aoi_uri, 'BURN_ID',
                        'mean'))

        #GETTING MEANS OF THE C RASTER HERE

        c_rast_uri = os.path.join(inter_dir, h + '_' + s + '_C_Risk_Raster.tif')

        c_agg_dict.update(raster_utils.aggregate_raster_values_uri(c_rast_uri, cp_aoi_uri, 'BURN_ID',
                        'mean'))

        #Now, want to place all values into the dictionary. Since we know that
        #the names of the attributes will be the same for each dictionary, can
        #just use the names of one to index into the rest.
        for ident in r_agg_dict:
            
            name = name_map[ident]
           
            avgs_dict[h][s].append({'Name': name, 'E': e_agg_dict[ident],
                                    'C': c_agg_dict[ident], 'Risk': r_agg_dict[ident]})

    return avgs_dict, name_map.values()

def make_risk_shapes(dir, crit_lists, h_dict, max_risk):
    '''This function will take in the current rasterized risk files for each
    habitat, and output a shapefile where the areas that are "HIGH RISK" (high
    percentage of risk over potential risk) are the only existing polygonized
    areas.

    Additonally, we also want to create a shapefile which is only the "low risk"
    areas- actually, those that are just not high risk (it's the combination of
    low risk areas and medium risk areas). 
    
    Since the raster_utils function can only take in ints, want to predetermine
    what areas are or are not going to be shapefile, and pass in a raster that
    is only 1 or nodata.
    
    Input:
        dir- Directory in which the completed shapefiles should be placed.
        crit_lists- A dictionary containing pre-burned criteria which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): ["indiv num raster URI", 
                                    "raster 1 URI", ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        's':   { stressA: ["indiv num raster URI", ...]
                               }
                     }
             'Recovery': { hab1: ["indiv num raster URI", ...],
                           hab2: ...
                         }
            }
        h_dict- A dictionary that contains raster dataseti URIs corresponding
            to each of the habitats in the model. The key in this dictionary is
            the name of the habiat, and it maps to the open dataset.
        max_risk- Double representing the highest potential value for a single
            h-s raster. The amount of risk for a given Habitat raster would be
            SUM(s) for a given h.

     Output:
        Returns two shapefiles for every habitat, one which shows features only for the
        areas that are "high risk" within that habitat, and one which shows features only
        for the combined low + medium risk areas. 

     Return:
        num_stress- A dictionary containing the number of stressors being associated with

            
     '''
    #For each h, want  to know how many stressors are associated with it. This
    #allows us to not have to think about whether or not a h-s pair was zero'd
    #out by weighting or DQ.
    num_stress = collections.Counter()
    for pair in crit_lists['Risk']['h-s']:
        h, _ = pair
        
        if h in num_stress:
            num_stress[h] += 1
        else:
            num_stress[h] = 1
    
    curr_top_risk = None

    def high_risk_raster(pixel):

        percent = float(pixel)/ curr_top_risk

        #Will need to be specified what percentage the cutoff for 'HIGH RISK'
        #areas are.
        if percent > 66.6:
            return 1
        else:
            return 0.

    def low_risk_raster(pixel):

        percent = float(pixel)/ curr_top_risk

        #Will need to be specified what percentage the cutoff for 'HIGH RISK'
        #areas are.
        if 0 < percent <= 66.6:
            return 1
        else:
            return 0.

    for h in h_dict:
        #Want to know the number of stressors for the current habitat        
        curr_top_risk = num_stress[h] * max_risk
        old_ds_uri = h_dict[h]
        grid_size = raster_utils.get_cell_size_from_uri(old_ds_uri)

        h_out_uri_r = os.path.join(dir, 'H[' + h + ']_HIGH_RISK.tif') 
        h_out_uri = os.path.join(dir, 'H[' + h + ']_HIGH_RISK.shp')
        
        raster_utils.vectorize_datasets([old_ds_uri], high_risk_raster, h_out_uri_r,
                        gdal.GDT_Float32, 0., grid_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)

        #Use gdal.Polygonize to take the raster, which should have only
        #data where there are high percentage risk values, and turn it into
        #a shapefile. 
        raster_to_polygon(h_out_uri_r, h_out_uri, h, 'VALUE')

        
        #Now, want to do the low + medium areas as well.
        l_out_uri_r = os.path.join(dir, 'H[' + h + ']_LOW_RISK.tif') 
        l_out_uri = os.path.join(dir, 'H[' + h + ']_LOW_RISK.shp')
        
        raster_utils.vectorize_datasets([old_ds_uri], low_risk_raster, l_out_uri_r,
                        gdal.GDT_Float32, 0., grid_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)

        #Use gdal.Polygonize to take the raster, which should have only
        #data where there are high percentage risk values, and turn it into
        #a shapefile. 
        raster_to_polygon(l_out_uri_r, l_out_uri, h, 'VALUE')

    return num_stress

def raster_to_polygon(raster_uri, out_uri, layer_name, field_name):
    '''This will take in a raster file, and output a shapefile of the same
    area and shape.

    Input:
        raster_uri- The raster that needs to be turned into a shapefile. This is
            only the URI to the raster, we will need to get the band. 
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
    raster = gdal.Open(raster_uri)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.CreateDataSource(out_uri)
                
    spat_ref = osr.SpatialReference()
    proj = raster.GetProjectionRef() 
    spat_ref.ImportFromWkt(proj)
    
    layer_name = layer_name.encode('utf-8')
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

            {'Risk': {  'h-s': { (hab1, stressA): ["indiv num raster URI", 
                                    "raster 1 URI", ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        's':   { stressA: ["indiv num raster URI", ...]
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
            '''We will have burned numerator values for the recovery potential
            equation. Want to add all of the numerators (r/dq), then divide by
            the denoms added together (1/dq).'''

            value = 0.

            for p in pixels:
                value += p
            
            value = value / denoms['Recovery'][h]

            return value

        curr_list = crit_lists['Recovery'][h]

        #Need to get the arbitrary first element in order to have a pixel size
        #to use in vectorize_datasets. One hopes that we have at least 1 thing
        #in here.
        pixel_size = raster_utils.get_cell_size_from_uri(curr_list[0])

        out_uri = os.path.join(dir, 'recov_potent_H[' + h + '].tif')
        
        raster_utils.vectorize_datasets(curr_list, add_recov_pix, out_uri, 
                    gdal.GDT_Float32, 0., pixel_size, "union", 
                    resample_method_list=None, dataset_to_align_index=None,
                    aoi_uri=None)

def make_ecosys_risk_raster(dir, h_dict):
    '''This will make the compiled raster for all habitats within the ecosystem.
    The ecosystem raster will be a direct sum of each of the included habitat
    rasters.

    Input:
        dir- The directory in which all completed should be placed.
        h_dict- A dictionary of raster dataset URIs which can be combined to 
            create an overall ecosystem raster. The key is the habitat name, 
            and the value is the dataset URI.
            
            {'Habitat A': "Overall Habitat A Risk Map URI",
            'Habitat B': "Overall Habitat B Risk URI"
             ...
            }
    Output:
        ecosys_risk.tif- An overall risk raster for the ecosystem. It will
            be placed in the dir folder.

    Returns nothing.
    '''
    #Need a straight list of the values from h_dict
    h_list = h_dict.values()
    pixel_size = raster_utils.get_cell_size_from_uri(h_list[0])

    out_uri = os.path.join(dir, 'ecosys_risk.tif')

    def add_e_pixels(*pixels):
        '''Sum all habitat pixels for ecosystem raster.'''
 
        pixel_sum = 0.0
        
        for p in pixels:
 
            pixel_sum += p
 
        return pixel_sum
     
    raster_utils.vectorize_datasets(h_list, add_e_pixels, out_uri, 
                gdal.GDT_Float32, 0., pixel_size, "union", 
                resample_method_list=None, dataset_to_align_index=None,
                aoi_uri=None)

def make_hab_risk_raster(dir, risk_dict):
    '''This will create a combined raster for all habitat-stressor pairings
    within one habitat. It should return a list of open rasters that correspond
    to all habitats within the model.

    Input:
        dir- The directory in which all completed habitat rasters should be 
            placed.
        risk_dict- A dictionary containing the risk rasters for each pairing of
            habitat and stressor. The key is the tuple of (habitat, stressor),
            and the value is the raster dataset URI corresponding to that
            combination.
            
            {('HabA', 'Stress1'): "A-1 Risk Raster URI",
            ('HabA', 'Stress2'): "A-2 Risk Raster URI",
            ...
            }
    Output:
        A cumulative risk raster for every habitat included within the model.
    
    Returns:
        h_rasters- A dictionary containing habitat names mapped to the dataset
            URI of the overarching habitat risk map for this model run.
            
            {'Habitat A': "Overall Habitat A Risk Map URI",
            'Habitat B': "Overall Habitat B Risk URI"
             ...
            }
    '''
    def add_risk_pixels(*pixels):
        '''Sum all risk pixels to make a single habitat raster out of all the 
        h-s overlap rasters.'''
        pixel_sum = 0.0

        for p in pixels:
            pixel_sum += p

        return pixel_sum


    #This will give us two lists where we have only the unique habs and
    #stress for the system. List(set(list)) cast allows us to only get the
    #unique names within each.
    habitats, stressors = zip(*risk_dict.keys())
    habitats = list(set(habitats))
    stressors = list(set(stressors))

    #Want to get an arbitrary element in order to have a pixel size.
    pixel_size = \
        raster_utils.get_cell_size_from_uri(risk_dict[(habitats[0], stressors[0])])

    #List to store the completed h rasters in. Will be passed on to the
    #ecosystem raster function to be used in vectorize_dataset.
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

        raster_utils.vectorize_datasets(ds_list, add_risk_pixels, out_uri,
                        gdal.GDT_Float32, 0., pixel_size, "union", 
                        resample_method_list=None, dataset_to_align_index=None,
                        aoi_uri=None)

        h_rasters[h] = out_uri 

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

            {'Risk': {  'h-s': { (hab1, stressA): ["indiv num raster URI", 
                                    "raster 1 URI", ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        's':   { stressA: ["indiv num raster URI", ...]
                               }
                     }
             'Recovery': { hab1: ["indiv num raster URI", ...],
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
    for pair in crit_lists['Risk']['h-s']:

        h, s = pair

        #Want to get E and C from the applicable subdictionaries
        #E and C should be rasters of their own that are calc'd using
        #vectorize raster to straight add the pixels and divide by denoms
        c_out_uri = os.path.join(inter_dir, h + '_' + s + '_C_Risk_Raster.tif')
        e_out_uri = os.path.join(inter_dir, h + '_' + s + '_E_Risk_Raster.tif')

        #E/C should take in all of the subdictionary data, and return a raster
        #to be used in risk calculation. 
        #E will only need to take in stressor subdictionary data
        #C will take in both h-s and habitat subdictionary data
        calc_E_raster(e_out_uri, crit_lists['Risk']['s'][s],
                    denoms['Risk']['s'][s])
        #C will need to take in both habitat and hab-stress subdictionary data
        calc_C_raster(c_out_uri, crit_lists['Risk']['h-s'][pair], 
                    denoms['Risk']['h-s'][pair], crit_lists['Risk']['h'][h],
                    denoms['Risk']['h'][h])

        #Function that we call now will depend on what the risk calculation
        #equation desired is.
        risk_uri = os.path.join(inter_dir, 'H[' + h + ']_S[' + s + ']_Risk.tif')

        #Want to get the relevant ds for this H-S pair
        base_ds_uri = h_s[pair]['DS']
        
        if risk_eq == 'Multiplicative':
            
            make_risk_mult(base_ds_uri, e_out_uri, c_out_uri, risk_uri)
        
        elif risk_eq == 'Euclidean':
            
            make_risk_euc(base_ds_uri, e_out_uri, c_out_uri, risk_uri)

        risk_rasters[pair] = risk_uri

    return risk_rasters

def make_risk_mult(base_uri, e_uri, c_uri, risk_uri):
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
            
    Returns the URI for a raster representing the multiplied E raster, C raster, 
    and the base raster.
    '''
    base_nodata = raster_utils.get_nodata_from_uri(base_uri)
    grid_size = raster_utils.get_cell_size_from_uri(base_uri)
    
    #Since we aren't necessarily sure what base nodata is coming in as, just
    #want to be sure that this will output 0.
    def combine_risk_mult(*pixels):

        #since the E and C are created within this module, we are very sure
        #that their nodata will be 0. Just need to check base, which we know
        #was the first ds passed.
        b_pixel = pixels[0]
        if b_pixel == base_nodata:
            return 0.       

        #Otherwise, straight multiply all of the pixel values. We assume that
        #base could potentially be decayed.
        value = 1.
 
        for p in pixels:
            value = value * p

        return value

    raster_utils.vectorize_datasets([base_uri, e_uri, c_uri], combine_risk_mult, risk_uri, 
                    gdal.GDT_Float32, 0., grid_size, "union", 
                    resample_method_list=None, dataset_to_align_index=None,
                    aoi_uri=None)

def make_risk_euc(base_uri, e_uri, c_uri, risk_uri):
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
    #Already have base open for nodata values, just using pixel_size
    #version of the function.
    base_nodata = raster_utils.get_nodata_from_uri(base_uri)
    e_nodata = raster_utils.get_nodata_from_uri(e_uri)
    grid_size = raster_utils.get_cell_size_from_uri(base_uri)

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
            c_val = 0.

        e_val -= 1

        #Now square both.
        c_val = c_val ** 2
        e_val = e_val ** 2
        
        #Combine, and take the sqrt
        value = math.sqrt(e_val + c_val)
        
        return value

    raster_utils.vectorize_datasets([base_uri, e_uri, c_uri], 
                    combine_risk_euc, risk_uri, gdal.GDT_Float32, 0., grid_size,
                    "union", resample_method_list=None, 
                    dataset_to_align_index=None, aoi_uri=None)

def calc_E_raster(out_uri, s_list, s_denom):
    '''Should return a raster burned with an 'E' raster that is a combination
    of all the rasters passed in within the list, divided by the denominator.

    Input:
        out_uri- The location to which the E raster should be burned.
        s_list- A list of rasters burned with the equation r/dq*w for every
            criteria applicable for that s.
        s_denom- A double representing the sum total of all applicable criteria
            using the equation 1/dq*w.

    Returns nothing.
    '''
    grid_size = raster_utils.get_cell_size_from_uri(s_list[0])

    def add_e_pix(*pixels):
        
        value = 0.
        
        for p in pixels:
            value += p
    
        return value / s_denom

    raster_utils.vectorize_datasets(s_list, add_e_pix, out_uri,
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
        stress- Similar to the h-s dictionary, a multi-level
            dictionary containing all stressor-specific criteria ratings and
            rasters. In this case, however, the outermost key is by stressor
            name, and stressors['habitatName']['DS'] points to the rasterized
            stressor shapefile URI provided by the user.
    
    Output:
        Creates a version of every criteria for every h-s paring that is
        burned with both a r/dq*w value for risk calculation, as well as a
        r/dq burned raster for recovery potential calculations.
    
    Returns:     
        crit_lists- A dictionary containing pre-burned criteria URI which can be
            combined to get the E/C for that H-S pairing.

            {'Risk': {  'h-s': { (hab1, stressA): ["indiv num raster", "raster 1", ...],
                                 (hab1, stressB): ...
                               },
                        'h':   { hab1: ["indiv num raster URI", "raster 1 URI", ...],
                                ...
                               },
                        's':   { stressA: ["indiv num raster URI", ...]
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
        base_ds_uri = h_s[pair]['DS']
        base_nodata = raster_utils.get_nodata_from_uri(base_ds_uri)
        base_pixel_size = raster_utils.get_cell_size_from_uri(base_ds_uri)

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
        crit_lists['Risk']['h-s'][pair].append(single_crit_C_uri)
        
        #H-S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.

        #.iteritems creates a key, value pair for each one.
        for crit, crit_dict in h_s[pair]['Crit_Rasters'].iteritems():

            crit_ds_uri = crit_dict['DS']
            crit_nodata = raster_utils.get_nodata_from_uri(crit_ds_uri)
            
            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['h-s'][pair] += 1/ float(dq * w)

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

            crit_lists['Risk']['h-s'][pair].append(crit_C_uri)
   
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

    #And now, loading in all of the stressors. Will just be the standard
    #risk equation (r/dq*w)
    for s in stress:

        crit_lists['Risk']['s'][s] = []
        denoms['Risk']['s'][s] = 0

        #The base dataset for all s criteria. Will need to load bases
        #for each of the h/s crits too.
        base_ds_uri = stress[s]['DS']
        base_nodata = raster_utils.get_nodata_from_uri(base_ds_uri) 
        base_pixel_size = raster_utils.get_cell_size_from_uri(base_ds_uri)
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
        def burn_numerator_s_single(pixel):
            
            if pixel == base_nodata:
                return 0.

            else:
                return crit_rate_numerator

        raster_utils.vectorize_datasets([base_ds_uri], burn_numerator_s_single,
                            single_crit_E_uri, gdal.GDT_Float32, 0., base_pixel_size, 
                            "union", resample_method_list=None, 
                            dataset_to_align_index=None, aoi_uri=None)

        #Add the burned ds containing only the numerator burned ratings to
        #the list in which all rasters will reside
        crit_lists['Risk']['s'][s].append(single_crit_E_uri)
        
        #S dictionary, Raster Criteria: should output multiple rasters, each
        #of which is reburned with the pixel value r, as r/dq*w.
        for crit, crit_dict in stress[s]['Crit_Rasters'].iteritems():
            crit_ds_uri = crit_dict['DS']
            crit_nodata = raster_utils.get_nodata_from_uri(crit_ds_uri)
            
            dq = crit_dict['DQ']
            w = crit_dict['Weight']
            denoms['Risk']['s'][s] += 1/ float(dq * w)

            crit_E_uri = os.path.join(pre_raster_dir, s + '_' + crit + \
                                                    '_' + 'E_Raster.tif')
            def burn_numerator_s(pixel):
            
                if pixel == crit_nodata:
                    return 0.

                else:
                    burn_rating = float(pixel) / (dq*w)
                    return burn_rating
        
            raster_utils.vectorize_datasets([crit_ds_uri], burn_numerator_s,
                            crit_E_uri, gdal.GDT_Float32, 0., base_pixel_size, 
                            "union", resample_method_list=None, 
                            dataset_to_align_index=None, aoi_uri=None)

            crit_lists['Risk']['s'][s].append(crit_E_uri)

    #This might help.
    return (crit_lists, denoms)
