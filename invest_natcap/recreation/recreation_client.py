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
    predictorScript="predictors.php"
    recreationScript="recreation.php"
    regressionScript="regression.php"
    dataFolder="data"
    logName="log.txt"
    resultsZip="results.zip"
    
    #parameters
    LOGGER.debug("Processing parameters.")
    aoiFileName = args["aoiFileName"]
    cellSize = args["cellSize"]
    cellUnit = float(args["cellUnit"])
    workspace_dir = args["workspace_dir"]
    comments = args["comments"]

    data_dir = args["data_dir"]
    
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
        LOGGER.debug("Interpreting standard predictor mask.")
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
    
    
    LOGGER.info("Validating AOI.")
    dirname=os.path.dirname(aoiFileName)+os.sep
    fileName, fileExtension = os.path.splitext(aoiFileName)
    aoiFileNameSHP = fileName+".shp"
    aoiFileNameSHX = fileName+".shx"
    aoiFileNameDBF = fileName+".dbf"
    aoiFileNamePRJ = fileName+".prj"
    
    if not os.path.exists(aoiFileNamePRJ):
        LOGGER.error("The shapefile must have a PRJ file.")
        raise IOError, "Missing PRJ file."

    LOGGER.info("Processing predictors.")
    predictors = []
    if not data_dir == "":
        for f in os.listdir(data_dir):
            fileName, fileExtension = os.path.splitext(f)
            if fileExtension == ".shp":
                if os.path.exists(data_dir+fileName+".shx") and \
                os.path.exists(data_dir+fileName+".shp") and \
                os.path.exists(data_dir+fileName+".prj"):
                    LOGGER.info("Found %s predictor." % (fileName))
                    predictors.append(fileName)
                else:
                    LOGGER.error("Predictor %s is missing file(s)." % (fileName))

    attachments={}                
    for i,predictor in enumerate(predictors):
        attachments[predictor+".shp"]= open(data_dir+predictor+".shp","rb")
        attachments[predictor+".shx"]= open(data_dir+predictor+".shx","rb")
        attachments[predictor+".dbf"]= open(data_dir+predictor+".dbf","rb")
        attachments[predictor+".prj"]= open(data_dir+predictor+".prj","rb")
        
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = severPath+"/"+predictorScript
    request = urllib2.Request(url, datagen, headers)
    sessid = urllib2.urlopen(request).read().strip()
    LOGGER.debug("Server session %s." % (sessid))
    
    attachments = {"sessid": sessid,
                   "aoiSHP": open(aoiFileNameSHP, "rb"),
                   "aoiSHX": open(aoiFileNameSHX, "rb"),
                   "aoiDBF": open(aoiFileNameDBF, "rb"),
                   "aoiPRJ": open(aoiFileNamePRJ, "rb"),
                   "cellSize": cellSize*cellUnit,
                   "comments": comments,
                   "landscan": landscan,
                   "osm_point": osm_point,
                   "osm_line": osm_line,
                   "osm_poly": osm_poly,
                   "protected": protected,
                   "lulc": lulc,
                   "mangroves": mangroves,
                   "reefs": reefs,
                   "grass": grass}
    
    datagen, headers = multipart_encode(attachments)
    
    # Create the Request object
    url = severPath+"/"+recreationScript
    request = urllib2.Request(url, datagen, headers)
    
    LOGGER.info("Sending request to server.")
    sessid2 =urllib2.urlopen(request).read().strip()
    if not sessid == sessid2:
        LOGGER.error("Session id error.")
        raise ValueError, "The session id has changed."
    
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
        data_dir = dirname+"recreation_data/FIPS-11001/"
        mask = [True, True, True, True, True, True, False, False, False]

    LOGGER.debug("Constructing args dictionary.")
    args["aoiFileName"] = aoiFileName
    args["cellSize"] = cellSize
    args["cellUnit"] = cellUnit
    args["workspace_dir"] = workspace_dir
    args["comments"] = comments
    args["data_dir"] = data_dir
    args["mask"] = mask

    execute(args)