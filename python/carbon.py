#carbon_refactored.py
#

#attempting to extract the basic structure of the Arc tool


import sys, string, os, arcgisscripting, math, time, datetime, re, arc_interface

gp = arcgisscripting.create()

testParameter = gp.GetParameterAsText(0)
gp.addmessage("You entered " + testParameter)

a = arc_interface.arcInterface()
gp.addmessage("done.")
