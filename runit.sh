#!/bin/bash
deactivate
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --no-site-packages invest_python_environment
source invest_python_environment/bin/activate
