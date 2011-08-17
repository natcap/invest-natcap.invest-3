
import sys

f = open('C:\Users\jadoug06\log.txt', 'w')
try: 
    import osgeo.gdal
    f.write("pass")
except Exception as e:
    f.write(str(e))
f.close()

