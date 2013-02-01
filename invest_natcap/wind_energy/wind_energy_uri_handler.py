"""InVEST Wind Energy model file handler module"""
import logging

from invest_natcap.wind_energy import wind_energy_biophysical
from invest_natcap.wind_energy import wind_energy_valuation

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
     %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('wind_energy_uri_handler')

def execute(args):
    """This module handles the execution of the biophysical module and the
        valuation module given the following dictionary:
    
        args[workspace_dir] - a python string which is the uri path to where the
            outputs will be saved (required)
        args[wind_data_uri] - a text file where each row is a location with at
            least the Longitude, Latitude, Scale and Shape parameters (required)
        args[aoi_uri] - a uri to an OGR datasource that is of type polygon and 
            projected in linear units of meters. The polygon specifies the 
            area of interest for the wind data points. If limiting the wind 
            farm bins by distance, then the aoi should also cover a portion 
            of the land polygon that is of interest (optional for biophysical
            and no distance masking, required for biophysical and distance
            masking, required for valuation)
        args[bathymetry_uri] - a uri to a GDAL dataset that has the depth
            values of the area of interest (required)
        args[global_wind_parameters_uri] - a uri to a CSV file that holds the
            global parameter values for both the biophysical and valuation
            module (required)        
        args[bottom_type_uri] - a uri to an OGR datasource of type polygon
            that depicts the subsurface geology type (optional)
        args[turbine_parameters_uri] - a uri to a CSV file that holds the
            turbines biophysical parameters as well as valuation parameters 
            (required)
        args[hub_height] - an integer value for the hub height of the turbines
            as a factor of ten (meters) (required)
        args[num_days] - an integer value for the number of days for harvested
            wind energy calculation (days) (required)
        args[min_depth] - a float value for the minimum depth for offshore wind
            farm installation (meters) (required)
        args[max_depth] - a float value for the maximum depth for offshore wind
            farm installation (meters) (required)
        args[suffix] - a String to append to the end of the output files
            (optional)
        args[land_polygon_uri] - a uri to an OGR datasource of type polygon that
            provides a coastline for determining distances from wind farm bins.
            Enabled by AOI and required if wanting to mask by distances or
            run valuation
        args[min_distance] - a float value for the minimum distance from shore
            for offshore wind farm installation (meters) The land polygon must
            be selected for this input to be active (optional, required for 
            valuation)
        args[max_distance] - a float value for the maximum distance from shore
            for offshore wind farm installation (meters) The land polygon must
            be selected for this input to be active (optional, required for 
            valuation)
        args[grid_points_uri] - a uri to a CSV file that specifies the landing
            and grid point locations (optional)
        args[foundation_cost] - a float representing how much the foundation
            will cost for the specific type of turbine (required for valuation)
        args[number_of_machines] - an integer value for the number of machines
            for the wind farm (required for valuation)
        args[dollar_per_kWh] - a float value for the amount of dollars per
            kilowatt hour (kWh) (required for valuation)
        args[avg_grid_distance] - a float for the average distance in kilometers
            from a grid connection point to a land connection point 
            (required for valuation if grid connection points are not provided)

        returns - nothing"""
    
    # Run the biophysical uri module
    LOGGER.debug('Stepping into Biophysical URI Handler')
    wind_energy_biophysical.execute(args)
    
    try:
        # If valuation was checked in the UI then run valuation 
        if args['valuation_container']:
            # Run the valuation uri module
            LOGGER.debug('Stepping into Valuation URI Handler')
            wind_energy_valuation.execute(args)
    except KeyError:
        LOGGER.debug('Valuation Checkbox Disabled')

    LOGGER.debug('Leaving wind_energy_uri_handler')
