from dbfpy import dbf
import random

MAXPERCENT = 0.2

uncertainPools = dbf.Dbf("uncertain_carbon_pools_samp.dbf", new=True)
uncertainPools.addField(('C_ABOVE_L', 'F', 13, 11),
                        ('C_ABOVE_A', 'F', 13, 11),
                        ('C_ABOVE_H', 'F', 13, 11),
                        ('C_BELOW_L', 'F', 13, 11),
                        ('C_BELOW_A', 'F', 13, 11),
                        ('C_BELOW_H', 'F', 13, 11),
                        ('C_SOIL_L', 'F', 13, 11),
                        ('C_SOIL_A', 'F', 13, 11),
                        ('C_SOIL_H', 'F', 13, 11),
                        ('C_DEAD_L', 'F', 13, 11),
                        ('C_DEAD_A', 'F', 13, 11),
                        ('C_DEAD_H', 'F', 13, 11),
                        ('LULC', 'N', 4),
                        ('LULC_NAME', 'C', 50))

inPools = dbf.Dbf('../../carbon_pools_samp.dbf', readOnly=1)
print inPools
#LULC, LULC_NAME
for i in range(inPools.recordCount):
    rec = uncertainPools.newRecord()
    rec['LULC'] = inPools[i]['LULC']
    rec['LULC_NAME'] = inPools[i]['LULC_NAME']
    for field in ('C_ABOVE', 'C_BELOW', 'C_SOIL', 'C_DEAD'):
        val = inPools[i][field]
        ranges = [('_L', val * (1 - random.random()*MAXPERCENT)),
                  ('_A', val),
                  ('_H', val * (1 + random.random()*MAXPERCENT))]
        for x in ranges:
            rec[field + x[0]] = x[1]
    rec.store()

print uncertainPools
inPools.close()
uncertainPools.close()
