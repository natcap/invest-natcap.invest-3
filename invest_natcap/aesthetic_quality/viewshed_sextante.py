import sys

sys.path.append("/usr/share/qgis/python/plugins")
sys.path.append("/home/mlacayo/.qgis//python/plugins")

import PyQt4
import sextante
import qgis
import qgis.utils

def main():
    """ main function or something """
    # as per http://qgis.org/pyqgis-cookbook/intro.html#using-pyqgis-in-custom-application
    #from qgis.core import *
    #import qgis.utils

    app = PyQt4.QtGui.QApplication(sys.argv)
    # supply path to where is your qgis installed
    qgis.core.QgsApplication.setPrefixPath("/usr/lib/qgis", True)
    # load providers
    qgis.core.QgsApplication.initQgis()
    # how???
    #qgis.utils.iface = qgis.core.QgisInterface.instance()
    sextante.core.Sextante.Sextante.initialize()
    run_script(qgis.utils.iface)

def run_script(iface):
    """ this shall be called from Script Runner"""
    sextante.alglist()
    sextante.alghelp("grass:r.resample")

    sextante.runalg("grass:r.resample",
                    "/home/mlacayo/Desktop/test_out/pop_vs.tif",
                    "211084.959353,372584.959353,5356029.35524,5495529.35524",
                    1000,
                    "/home/mlacayo/Desktop/grass.tif")

if __name__=="__main__":
    main()
