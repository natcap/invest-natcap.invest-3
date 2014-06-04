import re
import os
import random

rasters = {}

fertilizer_dir_uri = "/home/mlacayo/workspace/ag_converted/Fertilizer"
climate_dir_uri = "/home/mlacayo/workspace/ag_converted/ClimateBinAnalysis"
production_dir_uri = "/home/mlacayo/workspace/ag_converted/Monfreda"
cbi_dir_uri = "/home/mlacayo/workspace/data/CropProduction/input/CBI"
cbi_mod_yield_dir_uri = "/home/mlacayo/workspace/data/CropProduction/input/CBI_mod_yield"
cbi_yield_dir_uri = "/home/mlacayo/workspace/data/CropProduction/input/CBI_yield"
income_climate_dir_uri = "/home/mlacayo/workspace/data/CropProduction/input/income_climate"
yield_mod_dir_uri = "/home/mlacayo/workspace/data/CropProduction/input/yield_mod"

fertilizer_pattern = "([a-z]+)([0-9A-Z]+)([a-z]+)"
climate_pattern = "([A-Za-z]+[_])([a-z]+)([_])([A-Za-z]+[_][0-9])([_][A-Za-z]+[_][0-9]+[_][A-Za-z]+[_][0-9]+[x][0-9]+[_][a-z]+[_])([A-Za-z]+)"
production_pattern = "([a-z]+)([_])([a-z]+)"
cbi_pattern = "([A-Z]+)([_][a-z]+[_])([a-z]+)"
cbi_mod_yield_pattern = "([A-Z]+[_][a-z]+[_])([a-z]+)"
cbi_yield_pattern = "([A-Z]+[_][a-z]+)([_])([a-z]+)"
income_climate_pattern = "([A-Z]+[_][a-z]+[_])([a-z]+)"
yield_mod_pattern = "([a-z]+)"

unknown_files = []
column_header = set()
for base_name in os.listdir(fertilizer_dir_uri):
    raster_uri = os.path.join(fertilizer_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(fertilizer_pattern, base_name)
        if m != None:
            crop = m.group(1)
            column = "_".join([m.group(2), m.group(3)])
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(climate_dir_uri):
    raster_uri = os.path.join(climate_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(climate_pattern, base_name)
        if m != None:
            crop = m.group(2)
            column = "_".join([m.group(4), m.group(6)])
            column_header.add(column) 

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(production_dir_uri):
    raster_uri = os.path.join(production_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(production_pattern, base_name)
        if m != None:
            crop = m.group(1)
            column = m.group(3)
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(cbi_dir_uri):
    raster_uri = os.path.join(cbi_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(cbi_pattern, base_name)
        if m != None:
            crop = m.group(3)
            column = m.group(1)
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(cbi_mod_yield_dir_uri):
    raster_uri = os.path.join(cbi_mod_yield_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(cbi_mod_yield_pattern, base_name)
        if m != None:
            crop = m.group(2)
            column = "CBI_mod_yield"
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(cbi_yield_dir_uri):
    raster_uri = os.path.join(cbi_yield_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(cbi_yield_pattern, base_name)
        if m != None:
            crop = m.group(3)
            column = m.group(1)
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(income_climate_dir_uri):
    raster_uri = os.path.join(income_climate_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(income_climate_pattern, base_name)
        if m != None:
            crop = m.group(2)
            column = "Income_Climate"
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

for base_name in os.listdir(yield_mod_dir_uri):
    raster_uri = os.path.join(yield_mod_dir_uri, base_name)
    if os.path.isfile(raster_uri):
        m = re.search(yield_mod_pattern, base_name)
        if m != None:
            crop = m.group(1)
            column = "Yield_mod"
            column_header.add(column)

            if not (crop in rasters):
                rasters[crop] = {}
                
            rasters[crop][column] = raster_uri
        else:
            unknown_files.append(raster_uri)

column_header = list(column_header)
column_header.sort()

crops = list(rasters.keys())
crops.sort()

print column_header
print crops
print unknown_files
