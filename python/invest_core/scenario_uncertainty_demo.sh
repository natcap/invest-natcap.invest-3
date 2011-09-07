#!/bin/bash
python carbon_scenario_uncertainty_test.py && qgis --nologo ../../test_data/test_output/uncertainty_sequestration.tif ../../test_data/test_output/uncertainty_colormap.tif 
