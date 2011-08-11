#carbon_refactored.py
#

#attempting to extract the basic structure of the Arc tool

import sys, string, os, arcgisscripting, math, time, datetime, re

gp = arcgisscripting.create()

testParameter = gp.GetParameterAsText(0)
gp.addmessage("You entered " + testParameter)


    
