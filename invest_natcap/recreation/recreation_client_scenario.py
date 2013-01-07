import os, sys
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import time

import logging
import json

import datetime

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_client')

def reLOGGER(log,entry):
    timestamp,msgType,msg = entry.split(",")
    if msgType == "INFO":
        log.info(msg)
    elif msgType == "DEBUG":
        log.debug(msg)
    elif msgType == "WARNING":
        log.warn(msg)
    elif msgType == "ERROR":
        log.error(msg)
        raise IOError, "Error on server: %s" % (msg)
    else:
        log.warn("Unknown logging message type %s: %s" % (msgType,msg))

def execute(args):
    # Register the streaming http handlers with urllib2
    register_openers()

    #load configuration
    configFileName=os.path.dirname(os.path.abspath(__file__))+os.sep+"recreation_client_config.json"
    LOGGER.debug("Loading server configuration from %s." % configFileName)
    configFile=open(configFileName,'r')
    config=json.loads(configFile.read())
    configFile.close()
    
    if args["data_dir"][-1] != os.sep:
        args["data_dir"]=args["data_dir"]+os.sep

    if args["workspace_dir"][-1] != os.sep:
        args["workspace_dir"]=args["workspace_dir"]+os.sep
        

##    LOGGER.info("Validating grid.")
##    dirname=os.path.dirname(args["gridFileName"])+os.sep
##    fileName, fileExtension = os.path.splitext(args["gridFileName"])
##    gridFileNameSHP = fileName+".shp"
##    gridFileNameSHX = fileName+".shx"
##    gridFileNameDBF = fileName+".dbf"
##    gridFileNamePRJ = fileName+".prj"
##    
##    if not os.path.exists(gridFileNamePRJ):
##        LOGGER.error("The shapefile must have a PRJ file.")
##        raise IOError, "Missing PRJ file."

    LOGGER.info("Processing predictors.")
    predictors = []
    userCategorization = []
    if not args["data_dir"] == "":
        for f in os.listdir(args["data_dir"]):
            fileName, fileExtension = os.path.splitext(f)
            if fileExtension == ".shp":
                if os.path.exists(args["data_dir"]+fileName+".shx") and \
                os.path.exists(args["data_dir"]+fileName+".dbf") and \
                os.path.exists(args["data_dir"]+fileName+".prj"):
                    LOGGER.info("Found %s predictor." % (fileName))
                    predictors.append(str(fileName))
                else:
                    LOGGER.error("Predictor %s is missing file(s)." % (fileName))
                    if not os.path.exists(args["data_dir"]+fileName+".shx"):
                        LOGGER.debug("Missing %s." % args["data_dir"]+fileName+".shx")
                    if not os.path.exists(args["data_dir"]+fileName+".dbf"):
                        LOGGER.debug("Missing %s." % args["data_dir"]+fileName+".dbf")
                    if not os.path.exists(args["data_dir"]+fileName+".prj"):
                        LOGGER.debug("Missing %s." % args["data_dir"]+fileName+".prj")
                        
                    
            elif fileExtension == ".tsv":
                LOGGER.info("Found %s categorization." % fileName)
                userCategorization.append(fileName)

    attachments={}                
    for predictor in predictors:
        attachments[predictor+".shp"]= open(args["data_dir"]+predictor+".shp","rb")
        attachments[predictor+".shx"]= open(args["data_dir"]+predictor+".shx","rb")
        attachments[predictor+".dbf"]= open(args["data_dir"]+predictor+".dbf","rb")
        attachments[predictor+".prj"]= open(args["data_dir"]+predictor+".prj","rb")

    for tsv in userCategorization:
        attachments[tsv+".tsv"]= open(args["data_dir"]+tsv+".tsv","rb")
        
    LOGGER.debug("Uploading predictors.")
    LOGGER.debug ("Attachments: %s" % str(attachments.keys()))
    datagen, headers = multipart_encode(attachments)
    url = config["server"]+config["files"]["PHP"]["predictor"]
    request = urllib2.Request(url, datagen, headers)
    sessid = urllib2.urlopen(request).read().strip()
    args["sessid"] = sessid
    LOGGER.debug("Server session %s." % (sessid))
    
    attachments = {"json" : json.dumps(args, indent=4),
                   "init" : open(args["json"],'rb'),
                   "comments": args["comments"]}
    
    datagen, headers = multipart_encode(attachments)
    
    # Create the Request object
    url = config["server"]+config["files"]["PHP"]["scenario"]
    request = urllib2.Request(url, datagen, headers)
    
    LOGGER.info("Sending request to server.")
    sessid2 =urllib2.urlopen(request).read().strip()
    if not sessid == sessid2:
        LOGGER.error("Session id error.")
        raise ValueError, "The session id has changed."
    
    LOGGER.info("Processing data.")

    url = config["server"]+config["paths"]["relative"]["data"]+sessid+"/"+config["files"]["log"]    
    complete = False
    oldlog=""
    msg=""
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
            reLOGGER(LOGGER,entry)
            
        oldlog=log
        
        if msg=="Dropped intermediate tables.":
            complete = True            
        else:
            LOGGER.info("Please wait.")
            time.sleep(15)                    
                
    LOGGER.info("Running regression.")
    url = config["server"]+config["files"]["PHP"]["regression"]
    datagen, headers = multipart_encode({"sessid": sessid})
    request = urllib2.Request(url, datagen, headers)
    sessid2 = urllib2.urlopen(request).read().strip()

    if sessid2 != sessid:
        LOGGER.error("The first session id was %s the second session id was %s." % (repr(sessid2),repr(sessid)))
        raise ValueError,"Something weird happened the sessid didn't match."
    
    url = config["server"]+config["paths"]["relative"]["data"]+sessid+"/"+config["files"]["results"]

    req = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    with open(args["workspace_dir"]+"results"+datetime.datetime.now().strftime("-%Y-%m-%d--%H_%M_%S")+".zip", 'wb') as fp:
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
