"""A script to matplotlib the results from uniliever analysis"""

import csv
import os
import sys
import re

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
from matplotlib.colors import hsv_to_rgb
from mpl_toolkits.mplot3d import Axes3D

table_to_label = {
    'composite_carbon_stock_change_20_60.csv': '20/60 - 60/20 Composite', 
    'composite_carbon_stock_change_20_80.csv': '20/80 - 80/20 Composite', 
    'composite_carbon_stock_change_20_80_50.csv': '20/60 - 50/20 Composite',
    'pre_calculated_scenarios_carbon_stock_change.csv': 'ArcGIS Random Composite'
    }

data_lookup = {}
max_percent = None
for filename, label in table_to_label.iteritems():
    with open(filename, 'rb') as csvfile:
        table_reader = csv.reader(csvfile)
        header_row = table_reader.next()
        current_max_percent = 0
        data_lookup[label] = []
        for row in table_reader:
            current_max_percent = int(row[0])
            data_lookup[label].append(float(row[1]))
        if max_percent == None:
            max_percent = current_max_percent
        elif max_percent != current_max_percent:
            raise Exception("Max percent %s but current max is %s" % (max_percent,current_max_percent))
           
           
colors = plt.get_cmap('Paired')(np.linspace(0, 1.0, 6))
fig, ax = plt.subplots()
index = 0
for label, data in data_lookup.iteritems():
    ax.plot(range(max_percent+1), data, c=colors[index], label=label)
    index += 1

ax.set_xlabel("Percent Soybean Expansion", fontsize=14)
ax.set_ylabel(r'Total Carbon Stocks (Mg)', fontsize=14)
ax.set_title('Composite percent change')

fig.tight_layout()
plt.xlim([0,400])
#plt.ylim([50,100])
plt.savefig('percent_change.png', bbox_inches=0)
    
# create a second figure for the legend
figLegend = plt.figure(figsize = (5.5,1.5))
# produce a legend for the objects in the other figure
plt.figlegend(*ax.get_legend_handles_labels(), loc='upper left', fancybox=True, shadow=True)
plt.savefig("legend.png")
plt.show()
