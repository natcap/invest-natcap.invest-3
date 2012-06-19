#!/bin/bash
ENVDIR=invest_python_environment
deactivate
rm -rf build
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --clear --system-site-packages $ENVDIR
source $ENVDIR/bin/activate
python setup.py install

#Run pure python commands with the invest-3 platform installed here. Example:
#python invest_marine_water_quality_biophysical.py

#Uncomment any of the lines below to run the unit tests
pushd test

#nosetests timber_test.py timber_core_test.py carbon_biophysical_test.py carbon_valuation_test.py wave_energy_biophysical_test.py wave_energy_core_test.py wave_energy_valuation_test.py carbon_core_test.py invest_core_test.py

#This is how you run a single test and see all the output:
#nosetests -s --nologcapture sediment_biophysical_test.py
popd
