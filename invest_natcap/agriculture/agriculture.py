import logging

import os
from invest_natcap import raster_utils

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('agriculture')

def execute(args):
    workspace_dir = args["workspace_dir"]

    report_name = "report.htm"

    crop_cover_uri = args["crop_file_name"]
    
    report_uri = os.path.join(workspace_dir, report_name)

    report = open(report_uri, 'w')
    report.write("<HTML>")
    
    report.write("\n<TABLE>")
    report.write("\n<TR><TD>Crop</TD><TD>Count</TD></TR>")

    crop_counts = raster_utils.unique_raster_values_count(crop_cover_uri)
    crop_counts_keys = crop_counts.keys()
    crop_counts_keys.sort()

    for crop in crop_counts_keys:
        report.write("\n<TR><TD>%i</TD><TD>%i</TD></TR>" % (crop,
                                                            crop_counts_keys[crop]))

    report.write("\n<\TABLE>")
    report.write("\n</HTML>")
    report.close()
