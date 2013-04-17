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


def plot_background_circle(max_value):
    
    circle_stuff = [(5, '#C44539'), (4.75, '#CF5B46'), (4.5, '#D66E54'), (4.25, '#E08865'), (4, '#E89D74'), (3.75, '#F0B686'), (3.5, '#F5CC98'), (3.25, '#FAE5AC'), (3, '#FFFFBF'), (2.75, '#EAEBC3'), (2.5, '#CFD1C5'), (2.25, '#B9BEC9'), (2, '#9FA7C9'), (1.75, '#8793CC'), (1.5, '#6D83CF'), (1.25, '#5372CF'), (1, '#305FCF')]
 
    index = 0
    for radius, color in circle_stuff:
        index += 1
        linestyle = 'solid' if index % 2 == 0 else 'dashed'
        cir = matplotlib.pyplot.Circle((0,0), edgecolor='.25', linestyle=linestyle, radius=radius*max_value/5.0, fc=color)
        matplotlib.pyplot.gca().add_patch(cir)

plot_index = 0
max_risk_value = 5
for hab_name, stressor_dict in the_dicto.iteritems():
    for stressor_name, aoi_list in stressor_dict.iteritems():
        plot_index += 1
        matplotlib.pyplot.subplot(2, 2, plot_index)
        plot_background_circle(max_risk_value)
        for aoi_dict in aoi_list:
            matplotlib.pyplot.plot(aoi_dict['E'], aoi_dict['C'], 'k^', markerfacecolor='black', markersize=8)
            matplotlib.pyplot.annotate(aoi_dict['Name'], xy=(aoi_dict['E'], aoi_dict['C']), xytext=(aoi_dict['E'], aoi_dict['C']+0.07))
        matplotlib.pyplot.title(hab_name + stressor_name)
        matplotlib.pyplot.xlim([0.5, max_risk_value])
        matplotlib.pyplot.ylim([0.5, max_risk_value])

matplotlib.pyplot.show()
