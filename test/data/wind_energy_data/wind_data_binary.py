#N,LONG,LATI,IST,JST,DataCOVpct,Ram-010m,Ram-020m,Ram-030m,Ram-040m,Ram-050m,Ram-060m,Ram-070m,Ram-080m,Ram-090m,Ram-100m,Ram-110m,Ram-120m,Ram-130m,Ram-140m,Ram-150m,K-010m

import struct

wind_file = open('ECNA_EEZ_WEBPAR_Aug27_2012.txt')
wind_file_binary = open('ECNA_EEZ_WEBPAR_Aug27_2012.bin', 'wb')

wind_file.readline()

for line in wind_file:
    param_list = map(float, line.split(','))[1:]
    param_list = param_list[0:2] + param_list[5:]
    param_list_length = len(param_list)
    #print param_list
    
    binary_line = struct.pack('<'+'f'*param_list_length, *param_list)

    wind_file_binary.write(binary_line)

wind_file_binary.close()
wind_file_binary = open('ECNA_EEZ_WEBPAR_Aug27_2012.bin', 'rb')
while True:
    line = wind_file_binary.read(4*param_list_length)
    
    if len(line) == 0:
        break

    param_list = struct.unpack('<'+'f'*param_list_length, line)
    #print param_list 
