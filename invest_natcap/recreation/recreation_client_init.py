import os, sys
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import time

import json
import logging

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_client')


def execute(args):
    # Register the streaming http handlers with urllib2
    register_openers()

    #load configuration
    configFileName=os.path.dirname(os.path.abspath(__file__))+os.sep+"config.json"
    LOGGER.debug("Loading server configuration from %s." % configFileName)
    configFile=open(configFileName,'r')
    config=json.loads(configFile.read())
    configFile.close()
   
    #parameters
    LOGGER.debug("Processing parameters.")

    #adding os separator to paths if needed
    if args["workspace_dir"][-1]!=os.sep:
        args["workspace_dir"] = args["workspace_dir"] + os.sep

    if args["data_dir"] != "" and args["data_dir"][-1]!=os.sep:
        args["data_dir"] = args["data_dir"] + os.sep  

    #validating shapefile    
    LOGGER.info("Validating AOI.")
    dirname=os.path.dirname(args["aoiFileName"])+os.sep
    fileName, fileExtension = os.path.splitext(args["aoiFileName"])
    aoiFileNameSHP = fileName+".shp"
    aoiFileNameSHX = fileName+".shx"
    aoiFileNameDBF = fileName+".dbf"
    aoiFileNamePRJ = fileName+".prj"
    
    if not os.path.exists(aoiFileNamePRJ):
        LOGGER.debug("File %s is missing." % aoiFileNamePRJ)
        LOGGER.error("The shapefile must have a PRJ file.")
        raise IOError, "Missing PRJ file."

    #scanning data directory for shapefiles
    LOGGER.info("Processing predictors.")
    predictors = []
    userCategorization = []
    if not args["data_dir"] == "":
        for f in os.listdir(args["data_dir"]):
            fileName, fileExtension = os.path.splitext(f)
            if fileExtension == ".shp":
                if os.path.exists(args["data_dir"]+fileName+".shx") and \
                os.path.exists(args["data_dir"]+fileName+".shp") and \
                os.path.exists(args["data_dir"]+fileName+".prj"):
                    LOGGER.info("Found %s predictor." % (fileName))
                    predictors.append(fileName)
                else:
                    LOGGER.error("Predictor %s is missing file(s)." % (fileName))
            elif fileExtension == ".tsv":
                LOGGER.info("Found %s categorization." % fileName)
                userCategorization.append(fileName)

    #open data directory shapefiles for uploading
    attachments={}                
    for predictor in predictors:
        attachments[predictor+".shp"]= open(args["data_dir"]+predictor+".shp","rb")
        attachments[predictor+".shx"]= open(args["data_dir"]+predictor+".shx","rb")
        attachments[predictor+".dbf"]= open(args["data_dir"]+predictor+".dbf","rb")
        attachments[predictor+".prj"]= open(args["data_dir"]+predictor+".prj","rb")

    for tsv in userCategorization:
        attachments[tsv+".tsv"]= open(args["data_dir"]+tsv+".tsv","rb")

    #upload predictors        
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = config["server"]+config["files"]["PHP"]["predictor"]
    LOGGER.info("URL: %s." % url)
    request = urllib2.Request(url, datagen, headers)

    #save session id
    args["sessid"] = urllib2.urlopen(request).read().strip()
    LOGGER.debug("Server session %s." % (args["sessid"]))
    
    #upload aoi and model parameters
    attachments = {"json" : json.dumps(args, indent=4),
                   "aoiSHP": open(aoiFileNameSHP, "rb"),
                   "aoiSHX": open(aoiFileNameSHX, "rb"),
                   "aoiDBF": open(aoiFileNameDBF, "rb"),
                   "aoiPRJ": open(aoiFileNamePRJ, "rb")}
    
    datagen, headers = multipart_encode(attachments)
    
    #initiate server side recreation python script
    url = config["server"]+config["files"]["PHP"]["recreation"]
    LOGGER.info("URL: %s." % url)
    request = urllib2.Request(url, datagen, headers)
    
    LOGGER.info("Sending request to server.")
    urllib2.urlopen(request).read()
    
    LOGGER.info("Processing data.")

    #check log and echo messages while not done
    url = config["server"]+"/"+config["paths"]["relative"]["data"]+"/"+args["sessid"]+"/"+config["files"]["log"]    
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

    #initiate server side regression R script                
    LOGGER.info("Running regression.")
    url = config["server"]+"/"+config["files"]["PHP"]["regression"]
    datagen, headers = multipart_encode({"sessid": args["sessid"]})
    request = urllib2.Request(url, datagen, headers)
    urllib2.urlopen(request).read()

    #download results
    url = config["server"]+"/"+config["paths"]["relative"]["data"]+"/"+args["sessid"]+"/"+config["files"]["results"]
    LOGGER.info("URL: %s." % url)

    req = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    with open(args["workspace_dir"]+config["files"]["results"], 'wb') as fp:
      while True:
        chunk = req.read(CHUNK)
        if not chunk: break
        fp.write(chunk)
        
    LOGGER.info("Transaction complete")
        
if __name__ == "__main__":
    if len(sys.argv)>1:
        modelRunFileName=sys.argv[1]
    else:
        modelRunFileName=os.path.abspath(os.path.dirname(sys.argv[0]))+os.sep+"default.json"

    #load model run parameters
    modelRunFile=open(modelRunFileName,'r')
    args=json.loads(modelRunFile.read())
    modelRunFile.close()

    execute(args)
