#!/bin/bash
deactivate
python bootstrap_invest_environment.py > setup_environment.py
python setup_environment.py --system-site-packages invest_python_environment

#Put a trigger to run unit tests here, or start front end, or whatever
