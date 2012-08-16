import os, sys
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import time

import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_client')


def execute(args):
    # Register the streaming http handlers with urllib2
    register_openers()
    
    #constants
    severPath="http://ncp-skookum.stanford.edu/~mlacayo"
    recreationScript="recreation.php"
    regressionScript="regression.php"
    dataFolder="data"
    logName="log.txt"
    resultsZip="results.zip"
    
    #parameters
    aoiFileName = args["aoiFileName"]
    cellSize = args["cellSize"]
    cellUnit = float(args["cellUnit"])
    workspace_dir = args["workspace_dir"]
    comments = args["comments"]

    predictorKeys = ["landscan",
                     "osm_point",
                     "osm_line",
                     "osm_poly",
                     "protected",
                     "lulc",
                     "mangroves",
                     "reefs",
                     "grass"]
    if args.has_key("mask"):
        for k,b in zip(predictorKeys,args["mask"]):
            args[k]=b
    landscan=args["landscan"]
    osm_point=args["osm_point"]
    osm_line=args["osm_line"]
    osm_poly=args["osm_poly"]
    protected=args["protected"]
    lulc=args["lulc"]
    mangroves=args["mangroves"]
    reefs=args["reefs"]
    grass=args["grass"]
    
    
    
    dirname=os.path.dirname(aoiFileName)+os.sep
    fileName=os.path.basename(aoiFileName)[:-4]
    aoiFileNameSHP = dirname+fileName+".shp"
    aoiFileNameSHX = dirname+fileName+".shx"
    aoiFileNameDBF = dirname+fileName+".dbf"
    aoiFileNamePRJ = dirname+fileName+".prj"
    
    if not os.path.exists(aoiFileNamePRJ):
        LOGGER.error("The shapefile must have a PRJ file.")
        raise IOError, "Missing PRJ file."
    
    # Start the multipart/form-data encoding of the file "DSC0001.jpg"
    # "image1" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"aoiSHP": open(aoiFileNameSHP, "rb"),
                                         "aoiSHX": open(aoiFileNameSHX, "rb"),
                                         "aoiDBF": open(aoiFileNameDBF, "rb"),
                                         "aoiPRJ": open(aoiFileNamePRJ, "rb"),
                                         "cellSize": cellSize*cellUnit,
                                         "comments": comments})
    
    # Create the Request object
    url = severPath+"/"+recreationScript
    request = urllib2.Request(url, datagen, headers)
    
    LOGGER.info("Sending request to server.")
    
    # Actually do the request, and get the response
    # This will display the output from the model including the path for the results
    sessid = urllib2.urlopen(request).read().strip()
    LOGGER.debug("Server session %s." % (sessid))
    
    LOGGER.info("Processing data.")

    url = severPath+"/"+dataFolder+"/"+sessid+"/"+logName    
    complete = False
    oldlog=""
    time.sleep(5)
    while not complete:
        log = urllib2.urlopen(url).read()
        serverLogging = log[len(oldlog):].strip()
        if len(serverLogging) > 0:
            serverLogging=serverLogging.split("\n")        
            if serverLogging[-1][-1] != ".":
                serverLogging.pop(-1)
        else:
            serverLogging=[]
            
        for entry in serverLogging:
            timestamp,msgType,msg = entry.split(",")
            if msgType == "INFO":
                LOGGER.info(msg)
            elif msgType == "DEBUG":
                LOGGER.debug(msg)
            elif msgType == "WARNING":
                LOGGER.warn(msg)
            elif msgType == "ERROR":
                LOGGER.error(msg)
                raise IOError, "Error on server: %s" % (msg)
            else:
                LOGGER.warn("Unknown logging message type %s: %s" % (msgType,msg))
            
        oldlog=log
        
        if msg=="Dropped intermediate tables.":
            complete = True            
        else:
            LOGGER.info("Please wait.")
            time.sleep(15)                    
                
    LOGGER.info("Running regression.")
    url = severPath+"/"+regressionScript
    datagen, headers = multipart_encode({"sessid": sessid})
    request = urllib2.Request(url, datagen, headers)
    sessid2 = urllib2.urlopen(request).read().strip()

    if sessid2 != sessid:
        raise ValueError,"Something weird happened the sessid didn't match."
    
    url = severPath+"/"+dataFolder+"/"+sessid+"/"+resultsZip

    req = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    with open(workspace_dir+os.sep+resultsZip, 'wb') as fp:
      while True:
        chunk = req.read(CHUNK)
        if not chunk: break
        fp.write(chunk)
        
    LOGGER.info("Transaction complete")
        
if __name__ == "__main__":
    args = {}
    if len(sys.argv)>1:
        LOGGER.info("Running model with user provided parameters.")
        aoiFileName = sys.argv[1]
        cellSize = float(sys.argv[2])
        cellUnit = float(sys.argv[3])
        workspace_dir = sys.argv[4]
        comments = sys.argv[5]
        data_dir = sys.argv[6]
        mask = map(bool,sys.argv[7:16])

    else:
        LOGGER.info("Runnning model with test parameters.")
        dirname=os.sep.join(os.path.abspath(os.path.dirname(sys.argv[0])).split(os.sep)[:-2])+"/test/data/"
        aoiFileName = dirname+"recreation_data/"+"FIPS-11001.shp"
        cellSize = 3
        cellUnit = 1000
        workspace_dir = dirname+"test_out/"
        comments = "Runnning model with test parameters."
        data_dir = ""
        mask = [True]*9

    args["aoiFileName"] = aoiFileName
    args["cellSize"] = cellSize
    args["cellUnit"] = cellUnit
    args["workspace_dir"] = workspace_dir
    args["comments"] = comments
    args["data_dir"] = data_dir
    args["mask"] = mask

    execute(args)