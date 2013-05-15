import grass.script as grass

grass.run_command('r.viewshed',
        input='/home/mlacayo/Desktop/aq_sample/Input/claybark_dem.tif',
        output='/home/mlacayo/Desktop/viewshed.tif',
        coordinate=[295844, 5459791],
        obs_elev=1.75,
        tgt_elev=0.0,
        memory=4098,
        overwrite=True,
        quiet=True
)
