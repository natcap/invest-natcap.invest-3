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
    scenarioScript="scenario.php"
    regressionScript="regression.php"
    dataFolder="data"
    logName="log.txt"
    resultsZip="results.zip"
    
    #parameters
    LOGGER.debug("Processing parameters.")
    gridFileName = args["gridFileName"]
    paramsFileName = args["paramsFileName"]
    data_dir = args["data_dir"]
    workspace_dir = args["workspace_dir"]
    comments = args["comments"]
    
    LOGGER.info("Validating grid.")
    dirname=os.path.dirname(gridFileName)+os.sep
    fileName, fileExtension = os.path.splitext(gridFileName)
    gridFileNameSHP = fileName+".shp"
    gridFileNameSHX = fileName+".shx"
    gridFileNameDBF = fileName+".dbf"
    gridFileNamePRJ = fileName+".prj"
    
    if not os.path.exists(gridFileNamePRJ):
        LOGGER.error("The shapefile must have a PRJ file.")
        raise IOError, "Missing PRJ file."

    LOGGER.info("Processing predictors.")
    predictors = []
    userCategorization = []
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
            elif fileExtension == ".tsv":
                LOGGER.info("Found %s categorization." % fileName)
                userCategorization.append(fileName)

    attachments={}                
    for predictor in predictors:
        attachments[predictor+".shp"]= open(data_dir+predictor+".shp","rb")
        attachments[predictor+".shx"]= open(data_dir+predictor+".shx","rb")
        attachments[predictor+".dbf"]= open(data_dir+predictor+".dbf","rb")
        attachments[predictor+".prj"]= open(data_dir+predictor+".prj","rb")

    for tsv in userCategorization:
        attachments[tsv+".tsv"]= open(data_dir+tsv+".tsv","rb")
        
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = severPath+"/"+predictorScript
    request = urllib2.Request(url, datagen, headers)
    sessid = urllib2.urlopen(request).read().strip()
    LOGGER.debug("Server session %s." % (sessid))
    
    attachments = {"sessid": sessid,
                   "gridSHP": open(gridFileNameSHP, "rb"),
                   "gridSHX": open(gridFileNameSHX, "rb"),
                   "gridDBF": open(gridFileNameDBF, "rb"),
                   "gridPRJ": open(gridFileNamePRJ, "rb"),
                   "comments": comments}
    
    datagen, headers = multipart_encode(attachments)
    
    # Create the Request object
    url = severPath+"/"+scenarioScript
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
    if len(sys.argv)==6:
        LOGGER.info("Running model with user provided parameters.")
        gridFileName = sys.argv[1]
        paramsFileName = sys.argv[2]
        data_dir = sys.argv[3]        
        workspace_dir = sys.argv[4]
        comments = sys.argv[5]

    else:
        raise ValueError, "There is no default scenario run."

    LOGGER.debug("Constructing args dictionary.")
    args["grid"] = gridFileName
    args["params"] = paramsFileName
    args["data_dir"] = data_dir    
    args["workspace_dir"] = workspace_dir
    args["comments"] = comments

    execute(args)
