#!/bin/bash
LDFLAGS="-L./clib" \
    python ./setup.py build_ext --inplace
