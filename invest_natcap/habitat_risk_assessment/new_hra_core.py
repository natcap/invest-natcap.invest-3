''' This will be temporary until I can integrate these into the HRA core. It
will act as scratch space for a variety of functions.'''


def make_recovery_rast(dir, hab):

    raster_list = []
    sum_dq = 0

    for h in hab:
        sum = 0
        for crit in h['Crit_Ratings']:
            r = crit['Rating']
            dq = crit['DQ']

            sum += r/dq
            sum_dq += 1/dq
        #Burn all numeric criteria to a single raster so that it could be combined
        #with raster criteria after the fact.
        
        for crit in h['Crit_Rasters']
            dq = crit['DQ']

            sum_dq += 1/ dq
            
            #Burn r/dq to a new temporary raster so that it can be combined with the others,
            #then divided out over 1/dq once they're summed. Add to raster stack for later
            #vectorizing...again.
            old_band = crit['DS'].GetRasterBand(1)
            old_array = old_band.ReadAsArray()

            new_array = old_array / dq

            #Make a new raster here and burn the above array to it. Then add it to the stack.

            raster_list.append(new_ds)
    
    
def make_risk_rasters(dir, h_s, hab, stress, risk_eq):
    
    risk_rasters = {}
    denoms = {}

    for pair in h_s:
        
        h,s = pair     
        e_sum, c_sum = 0

        for sub_dict in (h_s[pair], hab[h]):
            for crit in (sub_dict['Crit_Ratings'], sub_dict['Crit_Rasters']):
                
                dq = crit['DQ']
                w = crit['Weight']

                c_sum += 1/(dq * w)
        
        denoms[pair]['C'] = c_sum

        for crit in (stress[s]['Crit_Ratings'], stress[s]['Crit_Rasters']):

            dq = crit['DQ']
            w = crit['Weight']

            e_sum += 1 / (dq * w)
        
        denoms[pair]['E'] = e_sum

    #At this point, denoms exists, and we can pass the particular one to the calc_C
    #and calc_E functions to rasterize.
    out_dir = os.path.join(dir, 'Temp_Calc_Rast')

    for pair in h_s:
        
        h, s = pair
       
        #e_out_path = os.path.join(out_dir, h + s + 'E.tif')
        #c_out_path = os.path.join(out_dir, h + s + 'C.tif')
        
        #Let's try throwing everything (criteria that are E/C burned as
        #well as the overarching E/C into one file within the out_dir folder.
        e_out_dir = os.path.join(out_dir, h + '_' +  s)
        c_out_path = os.path.join(out_dir, h + '_' + s)

        #E and C are both raster burned spatially explicit versions of E
        E = calc_E_value(h_s[pair]['DS'], stress[s], denoms[pair]['E'], e_out_path)
        C = calc_C_value(h_s[pair]['DS'], h_s[pair], hab[h], denoms[pair]['C'], c_out_path)

        r_ds = h_s[pair]['DS']
        r_band = r_ds.GetRasterBand(1)

        if risk_eq == 'Multiplicative':
            make_risk_mult(r_band, E, C, out_URI)
        elif risk_eq == 'Euclidean':
            make_risk_euc(r_band, E, C, out_URI)

def make_risk_euc(band, E, C, out_URI)
     
    layers = [band, E, C]

    #Know explicitly that this is the order the layers are passed in as.  
    def vec_euc(b_pixel, e_pixel, c_pixel):

        if e_pixel == 0 or b_pixel == 0:
            return 0

        e_pixel = e_pixel * b_pixel
        e_tot = (e_pixel - 1) ** 2
        c_tot = (c_pixel - 1) ** 2

        under_tot = e_tot + c_tot

        return math.sqrt(under_tot)

    #Vectorize raster using the layers list, and the vec_euc function

def calc_E_value(ds, s_dicts, denom, out_path):
    '''This will take in the stressor subdictionary for the given h,s pair and
    calculate an "E raster" based on the numerical criteria and the raster
    criteria. This will be combined with the C raster according to the risk
    equation, and allow us to return a final risk raster. 

    Input:
        ds- The base (h, s) overlap raster which we should use for rasterizing
            the numeric ratings data for combination with the raster ratings data.
        s_dicts- A subdictionary containing two dictionaries 'Crit_Ratings' and
            'Crit_Rasters' that contain all criteria rating data for the specific
            stressor being examined. 
        denom- The denominator for the E calculation equation. This should be
            applied after all of the E numerator equations are summed.
        out_path- The name (directory) that should be used to hold the E burned
            criteria, as well as the final E raster value for that pairing of H-S'''
    e_out_uri = os.path.join(out_path, 'E_Raster.tif'        
    new_ds = raster_utils.new_raster_from_base(ds, out_path, 'GTiff', 0,
                                gdal.GDT_Float32)
    band, nodata = raster_utils.extract_band_and_nodata(new_ds)
    band.Fill(nodata)

    e_num = 0
    for crit in s_dicts['Crit_Ratings']:
        
        dq = crit['DQ']
        w = crit['Weight']
        r = crit['Rating']

        e_num += r / (dq * w)

    raster_list = []
    #Want to re-rasterize each criteria with the r/dq * w value, then throw it
    #into a list so that they all can be combined on top of one another, and
    #divided by denom
    for crit in s_dicts['Crit_Rasters']:

        indiv_crit_uri = os.path.join(out_path, crit + '_E.tif')
        dataset = raster_utils.new_raster_from_base(crit['DS'], indiv_crit_uri, 
                            'GTiff', 0, gdal.GDT_Float32)
        band, nodata = raster_utils.extract_band_and_nodata(dataset)
        band.Fill(nodata)

        crit_array = crit['DS'].GetRasterBand(1).ReadAsArray()

        dq = crit['DQ']
        w = crit['Weight']
        bottom = dq * w

        #We should be burning an array with this criteria's r/dq*w here.
        new_array = crit_array / bottom
        band.WriteArray(new_array)
        
        #Add to stack so that they all can be added together.
        raster_list.append(dataset)
    
    def e_combine(*pixels):
        
        p_sum = o

        for p in pixels:
            sum += p
        p_sum += e_num
        
        #Denom is pre-calculated, and represents the bottom half of the E/C
        #calculation equation. This allowed us to get all numerator rasters together
        #before completing the equation. 
        return e_num / denom

    #vectorize using the raster band as the base, and all potential rasters on top of that.
    #The equation itself will add in the non-raster criteria to the numerator sum as long
    # as we use e-combine 

def calc_C_value(ds, h_s_dicts, h_dicts, denom, out_path):
    '''This will take in the habitat-stressor and habitat subdictionaries
    for the given h,s pair and calculate a "C raster" based on the numerical 
    criteria and the raster criteria. This will be combined with the E raster 
    according to the risk equation, and allow us to return a final risk raster. 

    Input:
        ds- The base (h, s) overlap raster which we should use for rasterizing
            the numeric ratings data for combination with the raster ratings data.
        h_s_dicts- A subdictionary containing two dictionaries 'Crit_Ratings' and
            'Crit_Rasters' that contain all criteria rating data related to the
            specific overlap of this habitat and stressor.
        h_dicts- A subdictionary containing two dictionaries 'Crit_Ratings' and
            'Crit_Rasters' that contain all criteria rating data related to the
            specific habitat being examined.
        denom- The denominator for the E calculation equation. This should be
            applied after all of the E numerator equations are summed.
        out_path- The name (directory and filename) that should be used as the
            URI when vectorizing the E raster.
    '''
    new_ds = raster_utils.new_raster_from_base(ds, out_path, 'GTiff', 0,
                                gdal.GDT_Float32)
    band, nodata = raster_utils.extract_band_and_nodata(new_ds)
    band.Fill(nodata)

    #We first want to get the rating information for all non-spatially explicit
    #rasters so that it can be summed along with the raster criteria.
    c_num = 0
    for dict in (h_s_dicts['Crit_Ratings'], h_dicts['Crit_Ratings']):
        for crit in dict:
        
            dq = crit['DQ']
            w = crit['Weight']
            r = crit['Rating']

            e_num += r / (dq * w)

    def e_combine(*pixels):
        
        p_sum = o

        for p in pixels:
            sum += p
        p_sum += c_num
        
        #Denom is pre-calculated, and represents the bottom half of the E/C
        #calculation equation. This allowed us to get all numerator rasters together
        #before completing the equation. 
        return p_sum / denom

    #First need to do a vectorize on every criteria within crit rasters to get it to
    #r/dq *w
    raster_list = []
    for crit in s_dicts['Crit_Rasters']:
        raster_list.append(crit['DS'])
    
    #vectorize using the raster band as the base, and all potential rasters on top of that.
def make_risk_mult(band, E, C, out_URI):
    ''' This uses the multiplicative value of risk to produce a final risk
    raster based off of the appropriate E and C rasters for that h-s combination.

    Input:
        band- The h-s overlap band, potentially containing decayed stressor values.
        E- A raster containing values calculated from the stressor criteria.
            These criteria could potentially be either individual ratings, or have
            come from spatially explicit rasters.
        C- A raster containing values calculated from h-s criteria, and habitat
            criteria. These could have come from either individual ratings or
            spatially explicit rasters.
        out_uri- The location into which the rasterized risk values should be
            placed.
    '''
    layers = [band, E, C]

    def vec_mult(*pixels):
        
        base_p = 1
        
        #If any of these things are 0, should return a 0 instead of calculating
        #an explicit risk value. This is good.
        for p in pixels:
            base_p = base_p * p
        
        return p

    #Call vectorize using vec_mult and band as a base, and burning to out_URI

#OKAY, NEW PLAN. SINCE WE KNOW THE EQ'S THAT WE NEED TO USE TO RASTERIZE ANYWAY,
#JUST GET THEM ALL, AND RASTERIZE THEM AHEAD OF TIME, THEN THROW TO LISTS CONTAINED
#IN DICTIONARIES, AS WELL AS THE DENOMS DICTIONARY.
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

    #OHAI. This might help.
    return (crit_lists, denoms)

#SO, SHOULD BE NOTED THAT AT THIS POINT, WE HAVE LISTS OF RASTERS SPECIFIC TO EACH H_S,
#S, AND H, BURNED WITH EITHER THE NUMERATOR FOR THE E/C EQUATIONS, OR THE RECOVERY
#POTENTIAL EQUATION. ADDITIONALLY, FOR EVERY ONE OF THOSE, WE ALSO HAVE THEIR SUMMED
#DENOMINATORS. WHEN WE DO THE TOTAL E/C FOR A GIVEN H-S OVERLAP, WE CAN JUST ADD THE
#RELEVANT DENOMINATORS.

