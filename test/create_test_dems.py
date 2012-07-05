import invest_test_core

points = {
    (0.0,0.0): 50,
    (0.0,1.0): 100,
    (1.0,0.0): 90,
    (1.0,1.0): 0,
    (0.5,0.5): 45}

invest_test_core.make_sample_dem(100,100,points, 0.0, -1, 'random_dem.tif')
