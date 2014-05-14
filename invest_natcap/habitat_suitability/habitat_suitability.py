"""Habitat suitability model"""

def execute(args):
    """Calculates habitat suitability scores and patches given biophysical 
        rasters and classification curves. 
        
        workspace_dir - uri to workspace directory for output files
        output_cell_size - (optional) size of output cells
        depth_biophysical_uri - uri to a depth raster 
        salinity_biophysical_uri - uri to salinity raster
        temperature_biophysical_uri - uri to temperature raster
        oyster_habitat_suitability_depth_table_uri - uri to a csv table that
            has that has columns "Suitability" in (0,1) and "Depth" in
            range(depth_biophysical_uri)
        oyster_habitat_suitability_salinity_table_uri -  uri to a csv table that
            has that has columns "Suitability" in (0,1) and "Salinity" in 
            range(salinity_biophysical_uri)
        oyster_habitat_suitability_temperature_table_uri - uri to a csv table
            that has that has columns "Suitability" in (0,1) and  "Temperature"
            in range(temperature_biophysical_uri)
           """
    pass