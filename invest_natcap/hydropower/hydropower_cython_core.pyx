import cython

cdef inline float float_min(float a, float b): return a if a >= b else b

@cython.cdivision(True)
def fractp_op(fractp_nodata_dict, float out_nodata, float seasonality_constant, 
              float etk, float eto, float precip, float root, float soil, float pawc):
    """Function that calculates the fractp (actual evapotranspiration
       fraction of precipitation) raster

        etk - numpy array with the etk (plant evapotranspiration 
              coefficient) raster values
        eto - numpy array with the potential evapotranspiration raster 
              values (mm)
        precip - numpy array with the precipitation raster values (mm)
        root - numpy array with the root depth (maximum root depth for
               vegetated land use classes) raster values (mm)
        soil - numpy array with the soil depth raster values (mm)
        pawc - numpy array with the plant available water content raster 
               values

    returns - fractp value """

    #If any of the local variables which are in the 'fractp_nodata_dict' 
    #dictionary are equal to a out_nodata value, then return out_nodata
    for var_name, value in locals().items():
        if var_name in fractp_nodata_dict and value == fractp_nodata_dict[var_name]:
            return out_nodata

    #Check to make sure that variables are not zero to avoid dividing by
    #zero error
    if precip == 0.0 or etk == 0.0 or eto == 0.0:
        return out_nodata

    #Compute Budyko Dryness index
    #Converting to a percent because 'etk' is stored in the table 
    #as int(percent * 1000)
    cdef float phi = (etk * eto) / (precip * 1000)

    #Calculate plant available water content (mm) using the minimum
    #of soil depth and root depth
    cdef float awc = (float_min(root, soil) * pawc)  

    #Calculate dimensionless ratio of plant accessible water
    #storage to expected precipitation during the year

    cdef float w_x = (awc / precip) * seasonality_constant

    #Compute evapotranspiration partition of the water balance
    cdef float aet_p = (1+ w_x * phi) / (1 + w_x * phi + 1 / phi)

    #Currently as of release 2.2.2 the following operation is not
    #documented in the users guide. We take the minimum of the
    #following values (Rxj, (AETxj/Pxj) to determine the evapotranspiration
    #partition of the water balance (see users guide for variable
    #and equation references). This was confirmed by Yonas Ghile on
    #5/10/12
    #Folow up, Guy verfied this again on 10/22/2012 (see issue 1323)

    return float_min(phi, aet_p)


def wyield_op(float out_nodata, float precip_nodata, float fractp, float precip):
    """Function that calculates the water yeild raster

       fractp - numpy array with the fractp raster values
       precip - numpy array with the precipitation raster values (mm)

       returns - water yield value (mm)"""

    if fractp == out_nodata or precip == precip_nodata:
        return out_nodata
    else:
        return (1.0 - fractp) * precip


@cython.cdivision(True)
def volume_op(float out_nodata, float wyield_mn, float wyield_area):
    """Function to compute the water yield volume raster

        wyield_mn - numpy array with the water yield mean raster values (mm)
        wyield_area - numpy array with the water yield area raster 
                      values (square meters)

        returns - water yield volume value (cubic meters)"""
    #Divide by 1000 because wyield is in mm, so convert to meters
    if wyield_mn != out_nodata and wyield_area != out_nodata:
        return (wyield_mn * wyield_area / 1000.0)
    else:
        return out_nodata

@cython.cdivision(True)
def ha_vol(float out_nodata, float wyield_vol, float wyield_area):
    """Function to compute water yield volume in units of ha

        wyield_vol - numpy array with the water yield volume raster values
                     (cubic meters)
        wyield_area - numpy array with the water yield area raster values
                      (squared meters)

        returns - water yield volume in ha value"""
    #Converting area from square meters to hectares 1 meter = .0001 hectare
    if wyield_vol != out_nodata and wyield_area != out_nodata:
        return wyield_vol / (0.0001 * wyield_area)
    else:
        return out_nodata

def aet_op(float precip_nodata, float out_nodata, float fractp, float precip):
    """Function to compute the actual evapotranspiration values

        fractp - numpy array with the fractp raster values
        precip - numpy array with the precipitation raster values (mm)

        returns - actual evapotranspiration values (mm)"""

    #checking if fractp >= 0 because it's a value that's between 0 and 1
    #and the nodata value is -1.  It's possible that vectorize rasters will
    #attempt to interpoalte the nodata value thus yielding intermiedate
    #values <0 but not == -1, thus we only accept values >= 0
    if fractp >= 0 and precip != precip_nodata:
        return fractp * precip
    else:
        return out_nodata

def cyield_vol_op(float out_nodata, float wyield_vol_nodata, 
                  float wyield_vol, float calib_val):
    """Function that computes the calibrated water yield volume
       per sub-watershed

       wyield_vol - a numpy array of water yield volume values
       calib_val - a numpy array of calibrated values

       returns - the calibrated water yield volume value (cubic meters)
    """

    if wyield_vol != wyield_vol_nodata and calib_val != out_nodata:
        return wyield_vol * calib_val
    else:
        return out_nodata

def rsupply_vol_op(float nodata_calib, float nodata_consump,
                   float rsupply_out_nodata, float wyield_calib,
                   float consump_vol):
    """Function that computes the realized water supply volume

       wyield_calib - a numpy array with the calibrated water yield values
                      (cubic meters)
       consump_vol - a numpy array with the total water consumptive use
                     values (cubic meters)

       returns - the realized water supply volume value (cubic meters)
    """
    if wyield_calib != nodata_calib and consump_vol != nodata_consump:
        return wyield_calib - consump_vol
    else:
        return rsupply_out_nodata

def rsupply_mean_op(float wyield_mn_nodata, float mn_raster_nodata, 
                    float rsupply_mean_out_nodata, float wyield_mean, float consump_mean):
    """Function that computes the mean realized water supply

       wyield_mean - a numpy array with the mean calibrated water yield 
                     values (mm)
       consump_mean - a numpy array with the mean water consumptive use
                     values (cubic meters)

       returns - the mean realized water supply value
    """
    #THIS MAY BE WRONG. DOING OPERATION ON (mm) and (cubic m)#
    if wyield_mean != wyield_mn_nodata and consump_mean != mn_raster_nodata:
        return wyield_mean - consump_mean
    else:
        return rsupply_mean_out_nodata
