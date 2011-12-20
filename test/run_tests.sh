#!/bin/bash
pushd python/invest_core/
python ./setup.py build_ext --inplace
pushd test
python invest_test_suite.py
popd
popd
