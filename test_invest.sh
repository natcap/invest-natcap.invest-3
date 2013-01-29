#!/bin/bash -e

ENVDIR=invest_python_environment
#deactivate
rm -rf build  # rebuilding build/ takes a VERY long time.  Don't uncomment.
rm -rf $ENVDIR  # revuilding this also takes a VERY long time.
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --clear --system-site-packages $ENVDIR
ls invest_python_environment/bin
source $ENVDIR/bin/activate
echo 'Activated'
python setup.py install --user
pushd test


echo "Using python " $(which python)
echo "STARTING TESTS"
pwd
timeout=600

# Can't use multiple processor cores to run tests concurrently since most
# tests write to the same directory.  Use a single process instead.
# It's necessary to declare a single process, as the process-timeout option
# only works when we specify how many processes we're using.
#processes=$(grep "^core id" /proc/cpuinfo | sort -u | wc -l)
processes=1
echo $processes

if [ $# -eq 0 ]
# If there are no arguments, run all tests
then
    nosetests -v --process-timeout=$timeout --processes=$processes
elif [ $1 == 'release' ]
then
# If the first argument is 'release', run the specified tests for released models.
    test_files=(
        carbon_biophysical_test.py
        carbon_core_test.py
        carbon_valuation_test.py
        fileio_test.py
        finfish_aquaculture_test.py
        finfish_aquaculture_core_test.py
        hydropower_core_test.py
        hydropower_valuation_test.py
        invest_core_fileio_test.py
        invest_core_test.py
        invest_cython_core_test.py
        iui_validator_test.py
        marine_water_quality_test.py
        overlap_analysis_test.py
        overlap_analysis_mz_core_test.py
        overlap_analysis_core_test.py
        pollination_biophysical_test.py
        raster_utils_test.py
        reclassify_test.py
        sediment_biophysical_test.py
        sediment_core_test.py
        timber_core_test.py
        timber_test.py
        water_scarcity_test.py
        water_yield_test.py
        wave_energy_biophysical_test.py
        wave_energy_core_test.py
        wave_energy_valuation_test.py
        )
    echo "Testing " ${test_files[*]}
    nosetests -v --process-timeout=$timeout --processes=$processes ${test_files[*]}
elif [ $1 == 'all' ]
then
# If the user specifies all as the first argument, run all tests
    nosetests -v --process-timeout=$timeout --processes=$processes
else
# Otherwise, take the arguments and pass them to nosetests
    nosetests -v --process-timeout=$timeout --processes=$processes $@
fi

popd
deactivate
