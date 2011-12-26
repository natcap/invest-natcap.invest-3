#!/bin/bash
ENVDIR=invest_python_environment
deactivate
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --clear --system-site-packages $ENVDIR
source $ENVDIR/bin/activate
python setup.py install
pushd test
nosetests timber_core_test.py
nosetests timber_test.py
nosetests carbon_core_test.py
nosetests carbon_biophysical_test.py
popd
