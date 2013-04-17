import matplotlib.pyplot

the_dicto = {
    'HabitatName':
        {'StressorName':
             [{'Name': 'Jojuba', 'E': 4.6, 'C': 2.8, 'Risk': 4.2},
              {'Name': 'Doug', 'E': 2.6, 'C': 1.2, 'Risk': 2.2}],
         'StressorName2':
             [{'Name': 'Marble', 'E': 4.6, 'C': 2.8, 'Risk': 4.2},
              {'Name': 'Birthday', 'E': 2.6, 'C': 1.2, 'Risk': 2.2}]
         },
    'Habotat':
        {'StresserNamo':
             [{'Name': 'James', 'E': 2.6, 'C': 4.3, 'Risk': 8.2},
              {'Name': 'Doug', 'E': 3.2, 'C': 2.9, 'Risk': 12.2}],
         'StressoPedia':
             [{'Name': 'Jambajuice', 'E': 2.6, 'C': 4.8, 'Risk': 3.2},
              {'Name': 'MrsCoffee', 'E': 1.6, 'C': 3.3, 'Risk': 4.1}]
         }
}


plot_index = 0
for hab_name, stressor_dict in the_dicto.iteritems():
    for stressor_name, aoi_list in stressor_dict.iteritems():
        plot_index += 1
        matplotlib.pyplot.subplot(2, 2, plot_index)
        for aoi_dict in aoi_list:
            matplotlib.pyplot.plot(aoi_dict['E'], aoi_dict['C'], 'k^', markerfacecolor='black', markersize=8)
            matplotlib.pyplot.annotate(aoi_dict['Name'], xy=(aoi_dict['E'], aoi_dict['C']), xytext=(aoi_dict['E'], aoi_dict['C']+0.07))
        matplotlib.pyplot.title(hab_name + stressor_name)
        matplotlib.pyplot.xlim([1, 5])
        matplotlib.pyplot.ylim([1, 5])

matplotlib.pyplot.show()
