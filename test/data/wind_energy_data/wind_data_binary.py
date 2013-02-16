#N,LONG,LATI,IST,JST,DataCOVpct,Ram-010m,Ram-020m,Ram-030m,Ram-040m,Ram-050m,Ram-060m,Ram-070m,Ram-080m,Ram-090m,Ram-100m,Ram-110m,Ram-120m,Ram-130m,Ram-140m,Ram-150m,K-010m

import struct

# Wind Points Text file to convert to a binary file
wind_file = open('../Global_EEZ_WEBPAR_90pct_100ms.txt')
# URI path for the binary file output
wind_file_binary = open('../Global_EEZ_WEBPAR_90pct_100ms_360.bin', 'wb')

# We don't want the first row which is the field values listed at the top of
# this file
wind_file.readline()

for line in wind_file:
    # Split the row on a comma into separate fields and convert to float values.
    # We don't want the 'N' value so take from index 1 to the end
    param_list = map(float, line.split(','))[1:]
    # We also do not want IST, JST, or DataCOVpct
    param_list = param_list[0:2] + param_list[5:]
    # Subtract 360 from longitude value for Global data because Longitude is in
    # positive degrees (0 to 360) where as we have been using negative. Comment
    # this out if using another wind data file that is not global
    param_list[0] = param_list[0] - 360.0

    param_list_length = len(param_list)
    #print param_list
    
    # Pack up the data as floats using big indian '<'
    binary_line = struct.pack('<'+'f'*param_list_length, *param_list)

    wind_file_binary.write(binary_line)

wind_file_binary.close()
# Open the made binary file to make sure that it unpacks nicely and properly.
# This code is just for testing if we can read it back in from binary format
wind_file_binary = open('../Global_EEZ_WEBPAR_90pct_100ms_360.bin', 'rb')
while True:
    line = wind_file_binary.read(4*param_list_length)
    
    if len(line) == 0:
        break

    param_list = struct.unpack('<'+'f'*param_list_length, line)
    #print param_list 
