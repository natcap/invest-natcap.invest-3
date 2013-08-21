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
python setup.py install --no-compile
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

# I can't output xunit test reports with an individual process timeout.  I
# assume that the program or programmer running this test file will have a
# top-level timing mechanism.  It's a known but with nosetests.  See:
# http://stackoverflow.com/a/13306487
#run_tests="nosetests -v --logging-filter=None --process-timeout=$timeout --processes=$processes"
run_tests="nosetests -v --with-xunit --with-coverage --cover-tests --cover-package=invest_natcap  --logging-filter=None"
test_files=""

if [ $# -eq 0 ]
# If there are no arguments, run all tests
then
    test_files=""
elif [ $1 == 'release' ]
then
# If the first argument is 'release', run the specified tests for released models.
    test_files=(
        finfish_aquaculture_test.py  # see issue 1848.  Quincy times out if this isn't first.
        biodiversity_biophysical_test.py
        biodiversity_core_test.py
        carbon_test.py
        fileio_test.py
        finfish_aquaculture_core_test.py
        html_gen_test.py
        hra_test.py
        invest_core_fileio_test.py
        invest_core_test.py
        invest_init_test.py
        iui_validator_test.py
        marine_water_quality_test.py
        nutrient_test.py
        overlap_analysis_test.py
        overlap_analysis_mz_core_test.py
        overlap_analysis_core_test.py
        pollination_test.py
        raster_utils_test.py
        reclassify_test.py
        routing_test.py
        sediment_test.py
        testing_test.py
        timber_core_test.py
        timber_test.py
        wave_energy_test.py
        wind_energy_biophysical_test.py
        wind_energy_core_test.py
        wind_energy_valuation_test.py
        wind_energy_uri_handler_test.py
        coastal_vulnerability_test.py
	marine_water_quality_regression_test.py
#        coastal_vulnerability_core_test.py
        )
    echo "Testing " ${test_files[*]}
    test_files="${test_files[*]}"
elif [ $1 == 'all' ]
then
# If the user specifies all as the first argument, run all tests
    test_files=""
else
# Otherwise, take the arguments and pass them to nosetests
    test_files="$@"
fi

${run_tests} ${test_files} 3>&1 1>&2 2>&3 | tee test_errors.log

popd
deactivate
