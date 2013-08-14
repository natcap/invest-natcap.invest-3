import numpy

dem_array = numpy.array(
	[[9,9,9,9,9,9,9],
	 [9,6,6,6,6,6,9],
	 [8,6,6,6,6,6,9],
	 [8,6,6,6,6,6,9],
	 [7,6,6,6,6,6,8],
	 [7,7,5,7,7,8,8]])
	 
#Identify flat downhill cells (neighboring uphill doesn't count)
#Identify sink cells
#Iterate out from sink increasing along the way

#Identify edge increasing cells
#Iterate out from increasing cells