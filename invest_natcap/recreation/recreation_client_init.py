import os, sys
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import time

import json
import logging

import datetime

import zipfile
from invest_natcap.raster_utils import temporary_filename

import invest_natcap

logging.basicConfig(format='%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_client_init')

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
    msgType=msgType.strip()
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

def logcheck(url,flag="Dropped intermediate tables.",delay=15,log=LOGGER,line=0):
    log.debug("Begin log check at line %i.", line)
    complete = False
    count=0
    
    while not complete:
        serverLog = urllib2.urlopen(url).read()
        serverLog = serverLog.strip().split("\n")

        if (len(serverLog) > 0) and (serverLog[-1] != "") and (serverLog[-1][-1] != "."):
            serverLogging.pop(-1)
        
        if len(serverLog[line+count:]) > 0:           
            for entry in serverLog[line + count:]:
                timestamp,msgType,msg = entry.split(",")
                reLOGGER(log,msgType,msg)
                count = count + 1
                if msg.strip()==flag.strip():
                    log.debug("Detected log check exit message.")
                    complete = True
                    if len(serverLog[line+count:]) > 0:
                        log.warn("There are unwritten messages on the remote log.")
                    break
            
        else:
            log.info("Please wait.")
            time.sleep(delay)

    line = line + count
    log.debug("End log check at line %i.", line)

    return line
            
def execute(args):    
    # Register the streaming http handlers with urllib2
    register_openers()

    #load configuration
    configFileName=os.path.dirname(os.path.abspath(__file__))+os.sep+"recreation_client_config.json"
    LOGGER.debug("Loading server configuration from %s." % configFileName)
    configFile=open(configFileName,'r')
    config=json.loads(configFile.read())
    configFile.close()

    #VERSION AND RELEASE CHECK
    args["version_info"] = invest_natcap.__version__
    args["is_release"] = invest_natcap.is_release()


    #constructing model parameters
    attachments = {"version_info" : args["version_info"],
                   "is_release": args["is_release"]}
    
    datagen, headers = multipart_encode(attachments)
    
    #constructing server side version
    url = config["server"]+config["files"]["PHP"]["version"]
    LOGGER.info("URL: %s." % url)
    request = urllib2.Request(url, datagen, headers)
    
    #opening request and comparing session id
    success, sessid = urlopen(url,request,config["tries"],config["delay"],LOGGER)

    if success:
        args["sessid"]=sessid
    else:
        LOGGER.error("Failed to establish sesssion.")
        raise urllib2.URLError, msg

    #check log and echo messages while not done
    log_url = config["server"]+"/"+config["paths"]["relative"]["data"]+"/"+args["sessid"]+"/"+config["files"]["log"]
    log_line = 0
    
    LOGGER.info("Checking version.")
    log_line=logcheck(log_url,"End version PHP script.",15,LOGGER,log_line)
    
    LOGGER.info("Finished checking version.")

       
    #VALIDATING MODEL PARAMETERS
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
    
    if not reduce(bool.__and__,map(os.path.exists,[aoiFileNameSHP,aoiFileNameSHX,aoiFileNameDBF,aoiFileNamePRJ])):
        LOGGER.error("The AOI is missing a shapefile component.")
        raise ValueError, "The AOI is missing a shapefile component."

    #scanning data directory for shapefiles
    LOGGER.info("Processing predictors.")
    predictors = []
    userCategorization = []
    if not args["data_dir"] == "":
        for f in os.listdir(args["data_dir"]):
            fileName, fileExtension = os.path.splitext(f)
            #checking for complete shapefile
            if fileExtension == ".shp":
                if os.path.exists(args["data_dir"]+fileName+".shx") and \
                os.path.exists(args["data_dir"]+fileName+".shp") and \
                os.path.exists(args["data_dir"]+fileName+".prj"):
                    LOGGER.info("Found %s predictor." % (fileName))
                    predictors.append(fileName)
                else:
                    LOGGER.error("Predictor %s is missing file(s)." % (fileName))
            #checking if categorization table
            elif fileExtension == ".tsv":
                LOGGER.info("Found %s categorization." % fileName)
                userCategorization.append(fileName)

    #making sure there is not landscan categorization
    if "landscan.tsv" in userCategorization:
        LOGGER.error("The categorization of the Landscan data is not allowed.")
        raise ValueError, "The categorization of the Landscan data is not allowed."

    #UPLOADING PREDICTORS
    LOGGER.info("Opening predictors for uploading.")
    
    #opening shapefiles
    attachments={}
    attachments["sessid"] = args["sessid"]
    zip_file_uri=temporary_filename()
    zip_file=zipfile.ZipFile(zip_file_uri, mode='w')

    #check if comprssion supported
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
        LOGGER.debug("Predictors will be compressed.")
    except ImportError:
        compression = zipfile.ZIP_STORED
        LOGGER.debug("Predictors will not be compressed.")
    
    for predictor in predictors:
##        attachments[predictor+".shp"]= open(args["data_dir"]+predictor+".shp","rb")
##        attachments[predictor+".shx"]= open(args["data_dir"]+predictor+".shx","rb")
##        attachments[predictor+".dbf"]= open(args["data_dir"]+predictor+".dbf","rb")
##        attachments[predictor+".prj"]= open(args["data_dir"]+predictor+".prj","rb")
        zip_file.write(args["data_dir"]+predictor+".shp",predictor+".shp",compression)
        zip_file.write(args["data_dir"]+predictor+".shx",predictor+".shx",compression)
        zip_file.write(args["data_dir"]+predictor+".dbf",predictor+".dbf",compression)
        zip_file.write(args["data_dir"]+predictor+".prj",predictor+".prj",compression)
        

    #opening categorization table
    for tsv in userCategorization:
##        attachments[tsv+".tsv"]= open(args["data_dir"]+tsv+".tsv","rb")
        zip_file.write(aargs["data_dir"]+tsv+".tsv",tsv+".tsv",compression)

    zip_file.close()
    attachments["zip_file"]=open(zip_file_uri,'rb')

    args["user_predictors"]=len(predictors)
    args["user_tables"]=len(userCategorization)

    #constructing upload predictors request
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = config["server"]+config["files"]["PHP"]["predictor"]
    request = urllib2.Request(url, datagen, headers)



    #recording server to model parameters
    args["server"]=config["server"]

    #opening request and saving session id
    success,sessid=urlopen(url,request,config["tries"],config["delay"],LOGGER)

    if not success:
        LOGGER.error("Failed to reestabilish sesssion.")
        raise urllib2.URLError, msg
        
    LOGGER.debug("Server session %s." % (args["sessid"]))

    #wait for server to finish saving predictors.
    log_line=logcheck(log_url,"End predictors PHP script.",15,LOGGER,log_line)

    #EXECUTING SERVER SIDE PYTHON SCRIPT
    LOGGER.info("Uploading AOI and running model.")
    
    #constructing model parameters
    attachments = {"json" : json.dumps(args, indent=4),
                   "aoiSHP": open(aoiFileNameSHP, "rb"),
                   "aoiSHX": open(aoiFileNameSHX, "rb"),
                   "aoiDBF": open(aoiFileNameDBF, "rb"),
                   "aoiPRJ": open(aoiFileNamePRJ, "rb")}
    
    datagen, headers = multipart_encode(attachments)
    
    #constructing server side recreation python script request
    url = config["server"]+config["files"]["PHP"]["recreation"]
    LOGGER.info("URL: %s." % url)
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
    LOGGER.info("Model running.")
    log_line = logcheck(log_url,"Dropped intermediate tables.",15,LOGGER, log_line)
    
    LOGGER.info("Finished processing data.")

    #EXECUTING SERVER SIDE R SCRIPT
    LOGGER.info("Running regression.")

    #construct server side R script request
    url = config["server"]+config["files"]["PHP"]["regression"]
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
    log_line=logcheck(log_url,"End regression PHP script.",15,LOGGER,log_line)

    #ZIP SERVER SIDE RESULTS
    url = config["server"]+config["files"]["PHP"]["results"]
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
        modelRunFileName=os.path.dirname(os.path.abspath(__file__))+os.sep+"default.json"

    #load model run parameters
    modelRunFile=open(modelRunFileName,'r')
    args=json.loads(modelRunFile.read())
    modelRunFile.close()

    execute(args)
