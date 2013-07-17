def execute(args):
    pass

    ###
    #get parameters, set outputs
    ###

    ###
    #validate data
    ###

    #raise warning if nothing going to happen, ie no criteria provided

    ###
    #resample, align and rasterize data
    ###
    
    ###
    #compute intermediate data if needed
    ###

    #contraints raster (reclass using permability values, filters on clump size)

    #normalize probabilities to be on a 10 point scale
    #probability raster (reclass using probability matrix)

    #proximity raster (gaussian for each landcover type, using max distance)
    #InVEST 2 uses 4-connectedness?

    #combine rasters for weighting into sutibility raster, multiply proximity by 0.3
    #[suitability * (1-factor weight)] + (factors * factor weight) or only single raster
    
    ###
    #reallocate pixels (disk heap sort, randomly reassign equal value pixels, applied in order)
    ###

    #reallocate

    #apply override

    ###
    #tabulate coverages
    ###
