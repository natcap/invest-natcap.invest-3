import cython

cdef double fmin(double a, double b):
     if a < b:
         return a
     return b

@cython.cdivision(True)
cpdef double fractp_op(double out_nodata, double seasonality_constant,
              double Kc, double eto, double precip, double root, double soil, double pawc, double veg,
              double Kc_nodata, double eto_nodata, double precip_nodata, double root_nodata, double soil_nodata, double pawc_nodata, double veg_nodata):
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
        veg - numpy array with a 1 or 0 where 1 depicts the land type as
                vegetation and 0 depicts the land type as non
                vegetation (wetlands, urban, water, etc...). If 1 use
                regular AET equation if 0 use: AET = Kc * ETo

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
    if veg == veg_nodata:
        return out_nodata
    #Check to make sure that variables are not zero to avoid dividing by
    #zero error
    if precip == 0.0 or Kc == 0.0 or eto == 0.0:
        return out_nodata

    #Compute Budyko Dryness index
    #Use the original AET equation if the land cover type is vegetation
    #If not vegetation (wetlands, urban, water, etc...) use
    #Alternative equation Kc * Eto

    # Initiate some variables to be used in the if/else block
    cdef double phi
    cdef double pet
    cdef double awc
    cdef double climate_w
    cdef double aet_p

    if veg == 1.0:
        phi = (Kc * eto) / (precip)
        pet = Kc * eto

        #Calculate plant available water content (mm) using the minimum
        #of soil depth and root depth
        awc = (fmin(root, soil) * pawc)

        #Calculate dimensionless ratio of plant accessible water
        #storage to expected precipitation during the year
        # Donohue et al. 2012 recommend the 1.25 factor which
        # corresponds to the minimum omega value and can be seen
        # in the User's Guide

        climate_w = ((awc / precip) * seasonality_constant) + 1.25

        # Capping to 5.0 to set to upper limit if exceeded
        if climate_w > 5.0:
            climate_w = 5.0

        #Compute evapotranspiration partition of the water balance
        aet_p = (1.0 + (pet / precip)) - ((1.0 + (pet / precip) ** climate_w) ** (1.0 / climate_w))

        #Currently as of release 2.2.2 the following operation is not
        #documented in the users guide. We take the minimum of the
        #following values (Rxj, (AETxj/Pxj) to determine the evapotranspiration
        #partition of the water balance (see users guide for variable
        #and equation references). This was confirmed by Yonas Ghile on
        #5/10/12
        #Folow up, Guy verfied this again on 10/22/2012 (see issue 1323)

        return fmin(phi, aet_p)

    else:
        return fmin(precip, Kc * eto) / precip