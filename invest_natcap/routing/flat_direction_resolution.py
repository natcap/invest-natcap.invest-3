import numpy

dem_array = numpy.array(
	[[9,9,9,9,9,9,9],
	 [9,6,6,6,6,6,9],
	 [8,6,6,6,6,6,9],
	 [8,6,6,6,6,6,9],
	 [7,6,6,6,6,6,8],
	 [7,7,5,7,7,8,8]])


flat_cells = numpy.zeros(dem_array.shape, dtype=numpy.bool)	 
#Identify flat downhill cells (neighboring uphill doesn't count)
for row_index in range(1, flat_cells.shape[0] - 1):
	for col_index in range(1, flat_cells.shape[1] - 1):
		flat_cells[row_index, col_index] = (dem_array[row_index-1:row_index+2, col_index-1:col_index+2] >= dem_array[row_index, col_index]).all()
print flat_cells
#Identify sink cells
#Iterate out from sink increasing along the way

#Identify edge increasing cells
#Iterate out from increasing cells

