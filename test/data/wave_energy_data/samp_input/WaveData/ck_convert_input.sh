#!/bin/bash
sed 's/,[^,0-9]*$//g' | sed 's/^TPbin=//' | sed 's/^HSbin=//'
