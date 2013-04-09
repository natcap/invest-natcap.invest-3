from libc.math cimport sin
from libc.math cimport atan
from libc.math cimport cos
from libc.math cimport fabs

def ls_factor_function(
    float aspect_angle, float slope, float flow_accumulation, float aspect_nodata, float slope_nodata, float flow_accumulation_nodata, float ls_nodata, float cell_area, float cell_size):
    """Calculate the ls factor

        aspect_angle - flow direction in radians
        slope - slope in terms of (units?)
        flow_accumulation - upstream pixels at this point

        returns the ls_factor calculation for this point"""

    #Skip the calculation if any of the inputs are nodata
    if aspect_angle == aspect_nodata or slope == slope_nodata or \
            flow_accumulation == flow_accumulation_nodata:
        return ls_nodata

    #Here the aspect direciton can range from 0 to 2PI, but the purpose
    #of the term is to determine the length of the flow path on the
    #pixel, thus we take the absolute value of each trigometric
    #function to keep the computation in the first quadrant
    cdef float xij = fabs(sin(aspect_angle)) + fabs(cos(aspect_angle))

    cdef float contributing_area = (flow_accumulation-1) * cell_area

    #To convert to radians, we need to divide the slope by 100 since
    #it's a percent. :(
    slope_in_radians = atan(slope / 100.0)

    #From Equation 4 in "Extension and validataion of a geographic
    #information system ..."
    if slope < 9:
        slope_factor =  10.8 * sin(slope_in_radians) + 0.03
    else:
        slope_factor =  16.8 * sin(slope_in_radians) - 0.5

    #Set the m value to the lookup table that's Table 1 in 
    #InVEST Sediment Model_modifications_10-01-2012_RS.docx in the
    #FT Team dropbox
    beta = (sin(slope_in_radians) / 0.0896) / \
        (3 * sin(slope_in_radians)**0.8 + 0.56)
    #slope table in percent
    cdef float * slope_table = [1., 3.5, 5., 9.]
    cdef float * exponent_table = [0.2, 0.3, 0.4, 0.5, beta/(1+beta)]

    #Use the bisect function to do a nifty range 
    #lookup. http://docs.python.org/library/bisect.html#other-examples
    cdef float m_exp = exponent_table[4]
    for i in range(4):
        if slope <= slope_table[i]:
            m_exp = exponent_table[i]

    #The length part of the ls_factor:
    ls_factor = (
        ((contributing_area + cell_area)**(m_exp+1) - 
         contributing_area ** (m_exp+1)) / 
        ((cell_size ** (m_exp + 2)) * (xij**m_exp) * (22.13**m_exp)))

    #From the paper "as a final check against exessively long slope
    #length calculations ... cap of 333m"
    if ls_factor > 333:
        ls_factor = 333

    return ls_factor * slope_factor
