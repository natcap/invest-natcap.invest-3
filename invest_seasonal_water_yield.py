import faulthandler
faulthandler.enable()

import invest_natcap.iui.modelui

if __name__ == '__main__':
    invest_natcap.iui.modelui.main('seasonal_water_yield.json')
