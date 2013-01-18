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

def urlopen(url,request,tries=3,delay=15,log=LOGGER):
    success=False
    for attempt in range(tries):
        log.info("Trying URL: %s." % url)
        try:
            msg=urllib2.urlopen(request).read().strip()
            success=True
            break
        except urllib2.URLError, msg:
            log.warn("Encountered error: %s" % msg)
            if attempt < tries-1:
                log.info("Waiting %i for retry." % delay)
                time.sleep(delay)

    return success, msg

def reLOGGER(log,msgType,msg):
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

def logcheck(url,flag="Dropped intermediate tables.",delay=15,log=LOGGER):    
    complete = False
    oldServerLog=""
    msg=""

    while not complete:
        severLog = urllib2.urlopen(url).read()
        serverLogging = severLog[len(oldServerLog):].strip()
        if len(serverLogging) > 0:
            serverLogging=serverLogging.split("\n")        
            if serverLogging[-1][-1] != ".":
                serverLogging.pop(-1)
        else:
            serverLogging=[]
            
        for entry in serverLogging:
            timestamp,msgType,msg = entry.split(",")
            reLOGGER(log,msgType,msg)
            
        oldServerLog=severLog

        if msg==flag:
            complete = True            
        else:
            log.info("Please wait.")
            time.sleep(delay)

def execute(args):
    # Register the streaming http handlers with urllib2
    register_openers()

    #load configuration
    configFileName=os.path.dirname(os.path.abspath(__file__))+os.sep+"recreation_client_config.json"
    LOGGER.debug("Loading server configuration from %s." % configFileName)
    configFile=open(configFileName,'r')
    config=json.loads(configFile.read())
    configFile.close()

    #adding os separator to paths if needed    
    if args["workspace_dir"][-1] != os.sep:
        args["workspace_dir"]=args["workspace_dir"]+os.sep

    if args["data_dir"][-1] != os.sep:
        args["data_dir"]=args["data_dir"]+os.sep        

    LOGGER.info("Validating grid.")
    dirname=os.path.dirname(args["json"])+os.sep
    if not (os.path.exists(dirname+config["files"]["grid_tmp"]["shp"]) and \
            os.path.exists(dirname+config["files"]["grid_tmp"]["shx"]) and \
            os.path.exists(dirname+config["files"]["grid_tmp"]["dbf"]) and \
            os.path.exists(dirname+config["files"]["grid_tmp"]["prj"])):
        LOGGER.error("The grid is missing a shapefile component.")
        raise ValueError, "The grid is missing a shapefile component."

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

    #UPLOADING PREDICTORS        
    LOGGER.debug("Uploading predictors.")
    LOGGER.debug ("Attachments: %s" % str(attachments.keys()))

    #constructing upload predictors request    
    datagen, headers = multipart_encode(attachments)
    url = config["server"]+config["files"]["PHP"]["predictor"]
    request = urllib2.Request(url, datagen, headers)

    #opening request and saving session id
    success,sessid=urlopen(url,request,config["tries"],config["delay"],LOGGER)
    
    if success:
        args["sessid"]=sessid
    else:
        LOGGER.error("Failed to start new sesssion.")
        raise urllib2.URLError, msg
    
    LOGGER.debug("Server session %s." % (sessid))

    #EXECUTING SERVER SIDE PYTHON SCRIPT
    LOGGER.info("Running server side model.")
    
    #aggregating attachments
    attachments = {"json" : json.dumps(args, indent=4),
                   "init" : open(args["json"],'rb'),
                   "comments": args["comments"]}

    #constructing request
    datagen, headers = multipart_encode(attachments)
    url = config["server"]+config["files"]["PHP"]["scenario"]
    request = urllib2.Request(url, datagen, headers)
    
    #opening request and comparing session id
    success,sessid2=urlopen(url,request,config["tries"],config["delay"],LOGGER)

    if not success:
        LOGGER.error("Failed to restablish sesssion.")
        raise urllib2.URLError, msg

    if not sessid2==args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."
    
    #check log and echo messages while not done
    url = config["server"]+"/"+config["paths"]["relative"]["data"]+"/"+args["sessid"]+"/"+config["files"]["log"]    
    logcheck(url,"Dropped intermediate tables.",15,LOGGER)
    
    LOGGER.info("Finished processing data.")

    #EXECUTING SERVER SIDE R SCRIPT
    LOGGER.info("Running regression.")

    #construct server side R script request
    url = config["server"]+"/"+config["files"]["PHP"]["regression"]
    datagen, headers = multipart_encode({"sessid": args["sessid"]})
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    success,sessid2=urlopen(url,request,config["tries"],config["delay"],LOGGER)

    if not success:
        LOGGER.error("Failed to restablish sesssion.")
        raise urllib2.URLError, msg

    if not sessid2==args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."

    #check log and echo messages while not done
    url = config["server"]+"/"+config["paths"]["relative"]["data"]+"/"+args["sessid"]+"/"+config["files"]["log"]    
    logcheck(url,"Wrote regression statistics.",15,LOGGER)

    #ZIP SERVER SIDE RESULTS
    url = config["server"]+"/"+config["files"]["PHP"]["results"]
    datagen, headers = multipart_encode({"sessid": args["sessid"]})
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    success,sessid2=urlopen(url,request,config["tries"],config["delay"],LOGGER)

    if not success:
        LOGGER.error("Failed to restablish sesssion.")
        raise urllib2.URLError, msg

    if not sessid2==args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."
    
    #download results
    url = config["server"]+config["paths"]["relative"]["data"]+args["sessid"]+"/"+config["files"]["results"]
    LOGGER.info("URL: %s." % url)

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
