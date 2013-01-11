def execute(args):
    
    inter_dir = os.path.join(args['workspace_dir'], 'Intermediate')
    output_dir = os.path.join(args['workspace_dir'], 'Output')

    crit_lists, denoms = pre_calc_denoms_and_criteria(inter_dir, args['h-s'],
                                    args['habitats'], args['stressors'])

    risk_dict = make_risk_rasters(inter_dir, crit_lists, denoms, 
                                    args['risk_eq'])

def make_risk_rasters(inter_dir, crit_lists, denoms, risk_eq):
    '''This will combine all of the intermediate criteria rasters that we
    pre-processed with their r/dq*w. At this juncture, we should be able to 
    straight add the E/C within themselven. The way in which the E/C rasters
    are combined depends on the risk equation desired.

    Input:
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

        #E will only need to take in stressor subdictionary data
        E = calc_E_raster(e_out_uri, crit_lists['Risk']['s'][s],
                        denoms['Risk']['s'][s])
        #C will need to take in both habitat and hab-stress subdictionary data
        C = calc_C_raster(c_out_uri, crit_lists['Risk']['h-s'][pair], 
                        denoms['Risk']['h-s'][pair], crit_lists['Risk']['h'][h],
                        denoms['Risk']['h'][h])

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

    return e_ratser

def calc_C_raster(out_uri, h_s_list, h_s_denom, h_list, h_denom)
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

    c_raster = raster_utils.vectorize_rasters(tot_crit_list, add_c_pix, aoi = None,
                            raster_out_uri = out_uri, datatype=gdal.GDT_Float32,
                            nodata = 0)
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
            #We will pre-sum all r / (dq*w), and then vectorize that with the spatially
            #explicit criteria later. Should be okay, as long as we keep the denoms
            #separate until after all raster crits are added.
    
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

            i_burned_array = base_array * crit_rate_numerator
            band.WriteArray(i_burned_array)

            #Add the burned ds containing only the numerator burned ratings to
            #the list in which all rasters will reside
            crit_lists['Risk']['h_s'][pair].append(c_ds)
            
            #H-S dictionary, Raster Criteria: should output multiple rasters, each
            #of which is reburned with the pixel value r, as r/dq*w.
            for crit in h_s[pair]['Crit_Rasters']:
                dq = crit['DQ']
                w = crit['Weight']
                denoms['Risk']['h_s'][pair] += 1/ float(dq * w)

                crit_C_uri = os.path.join(pre_raster_dict, pair + '_' + crit + \
                                                        '_' + 'C_Raster.tif')
                c_ds = raster_utils.new_raster_from_base(base_ds, crit_C_uri, 
                                                'GTiff', 0, gdal.GDT_Float32)
                band, nodata = raster_utils.extract_band_and_nodata(c_ds)
                band.Fill(nodata)

                edited_array = base_array / float(dq * w)
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

        i_burned_array = base_array * risk_crit_rate_numerator
        band.WriteArray(i_burned_array)

        crit_lists['Risk']['h'][h].append(c_ds)

        #Now, burn the recovery potential raster, and add that.
        single_crit_C_uri = os.path.join(pre_raster_dict, h + 
                                                        '_Indiv_Recov_Raster.tif')
        c_ds = raster_utils.new_raster_from_base(base_ds, single_crit_C_uri,
                                                 'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(c_ds)
        band.Fill(nodata)

        i_burned_array = base_array * rec_crit_rate_numerator
        band.WriteArray(i_burned_array)

        crit_lists['Recovery'][h].append(c_ds)
        
        #Raster Criteria: should output multiple rasters, each
        #of which is reburned with the old pixel value r as r/dq*w.
        for crit in h_s[pair]['Crit_Rasters']:
            dq = crit['DQ']
            w = crit['Weight']
            
            denoms['Risk']['h'][h] += 1/ float(dq * w)
            denoms['Recovery'][h] += 1/ float(dq)

            #First the risk rasters
            crit_C_uri = os.path.join(pre_raster_dict, h + '_' + crit + \
                                                    '_' + 'C_Raster.tif')
            c_ds = raster_utils.new_raster_from_base(base_ds, crit_C_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(c_ds)
            band.Fill(nodata)

            edited_array = base_array / float(dq * w)
            band.WriteArray(edited_array)
            crit_lists['Risk']['h'][h].append(c_ds)
            
            #Then the recovery rasters
            crit_recov_uri = os.path.join(pre_raster_dict, h + '_' + crit + \
                                                    '_' + 'Recov_Raster.tif')
            r_ds = raster_utils.new_raster_from_base(base_ds, crit_recov_uri, 
                                            'GTiff', 0, gdal.GDT_Float32)
            band, nodata = raster_utils.extract_band_and_nodata(r_ds)
            band.Fill(nodata)

            edited_array = base_array / float(dq)
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
            #We will pre-sum all r / (dq*w), and then vectorize that with the spatially
            #explicit criteria later. Should be okay, as long as we keep the denoms
            #separate until after all raster crits are added.
    
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

            i_burned_array = base_array * crit_rate_numerator
            band.WriteArray(i_burned_array)

            #Add the burned ds containing only the numerator burned ratings to
            #the list in which all rasters will reside
            crit_lists['Risk']['s'][s].append(e_ds)
            
            #H-S dictionary, Raster Criteria: should output multiple rasters, each
            #of which is reburned with the pixel value r, as r/dq*w.
            for crit in stress[s]['Crit_Rasters']:
                dq = crit['DQ']
                w = crit['Weight']
                denoms['Risk']['s'][s] += 1/ float(dq * w)

                crit_E_uri = os.path.join(pre_raster_dict, pair + '_' + crit + \
                                                        '_' + 'E_Raster.tif')
                e_ds = raster_utils.new_raster_from_base(base_ds, crit_E_uri, 
                                                'GTiff', 0, gdal.GDT_Float32)
                band, nodata = raster_utils.extract_band_and_nodata(e_ds)
                band.Fill(nodata)

                edited_array = base_array / float(dq * w)
                band.WriteArray(edited_array)
                crit_lists['Risk']['s'][s].append(e_ds)

    #This might help.
    return (crit_lists, denoms)
