import cython

from libc.math cimport fmin

@cython.cdivision(True)
cpdef double fractp_op(double out_nodata, double seasonality_constant,
              double Kc, double eto, double precip, double root, double soil, double pawc,
              double Kc_nodata, double eto_nodata, double precip_nodata, double root_nodata, double soil_nodata, double pawc_nodata):
    """Function that calculates the fractp (actual evapotranspiration
       fraction of precipitation) raster

        Kc - numpy array with the Kc (plant evapotranspiration 
              coefficient) raster values
        eto - numpy array with the potential evapotranspiration raster 
              values (mm)
        precip - numpy array with the precipitation raster values (mm)
        root - numpy array with the root depth (maximum root depth for
               vegetated land use classes) raster values (mm)
        soil - numpy array with the depth to root restricted layer raster
            values (mm)
        pawc - numpy array with the plant available water content raster 
               values

    returns - fractp value """

    #If any of the local variables which are in the 'fractp_nodata_dict' 
    #dictionary are equal to a out_nodata value, then return out_nodata
    if Kc == Kc_nodata:
        return out_nodata
    if eto == eto_nodata:
        return out_nodata
    if precip == precip_nodata:
        return out_nodata
    if root == root_nodata:
        return out_nodata
    if soil == soil_nodata:
        return out_nodata
    if pawc == pawc_nodata:
        return out_nodata

    #Check to make sure that variables are not zero to avoid dividing by
    #zero error
    if precip == 0.0 or Kc == 0.0 or eto == 0.0:
        return out_nodata

    #Compute Budyko Dryness index
    #Converting to a percent because 'Kc' is stored in the table 
    #as int(percent * 1000)
    cdef double phi = (Kc * eto) / (precip * 1000)

    #Calculate plant available water content (mm) using the minimum
    #of soil depth and root depth
    cdef double awc = (fmin(root, soil) * pawc)  

    #Calculate dimensionless ratio of plant accessible water
    #storage to expected precipitation during the year

    cdef double w_x = (awc / precip) * seasonality_constant

    #Compute evapotranspiration partition of the water balance
    cdef double aet_p = (1+ w_x * phi) / (1 + w_x * phi + 1 / phi)

    #Currently as of release 2.2.2 the following operation is not
    #documented in the users guide. We take the minimum of the
    #following values (Rxj, (AETxj/Pxj) to determine the evapotranspiration
    #partition of the water balance (see users guide for variable
    #and equation references). This was confirmed by Yonas Ghile on
    #5/10/12
    #Folow up, Guy verfied this again on 10/22/2012 (see issue 1323)

    return fmin(phi, aet_p)
