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
    severPath="http://ncp-skookum.stanford.edu/~mlacayo"
    recreationScript="recreation.php"
    regressionScript="regression.php"
    dataFolder="data"
    logName="log.txt"
    resultsZip="results.zip"
    
    aoiFileName = args["aoiFileName"]
    cellSize = args["cellSize"]
    workspace_dir = args["workspace_dir"]
    try:
        comments = args["comments"]
    except KeyError:
        comments =""
    
    dirname=os.path.dirname(aoiFileName)+os.sep
    fileName=os.path.basename(aoiFileName).strip(".shp") 
    aoiFileNameSHP = dirname+fileName+".shp"
    aoiFileNameSHX = dirname+fileName+".shx"
    aoiFileNameDBF = dirname+fileName+".dbf"
    aoiFileNamePRJ = dirname+fileName+".prj"
    
    if not os.path.exists(aoiFileNamePRJ):
        LOGGER.error("The shapefile must have a PRJ file.")
        raise IOError, "Missing PRJ file."
    
    # Register the streaming http handlers with urllib2
    register_openers()
    
    # Start the multipart/form-data encoding of the file "DSC0001.jpg"
    # "image1" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"aoiSHP": open(aoiFileNameSHP, "rb"),
                                         "aoiSHX": open(aoiFileNameSHX, "rb"),
                                         "aoiDBF": open(aoiFileNameDBF, "rb"),
                                         "aoiPRJ": open(aoiFileNamePRJ, "rb"),
                                         "cellSize": cellSize,
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
            elif msgType == "ERROR":
                LOGGER.error(msg)
                raise IOError, "Error on server: %s" % (msg)
            
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
        workspace_dir = sys.argv[3]
        comments = sys.argv[3]

    else:
        LOGGER.info("Runnning model with test parameters.")
        dirname=os.sep.join(os.path.abspath(os.path.dirname(sys.argv[0])).split(os.sep)[:-2])+"/test/data/"
        aoiFileName = dirname+"recreation_data/"+"FIPS-11001.shp"
        cellSize = 1000
        workspace_dir = dirname+"test_out/"
        comments = "Runnning model with test parameters."

    args["aoiFileName"] = aoiFileName
    args["cellSize"] = cellSize
    args["workspace_dir"] = workspace_dir
    args["comments"] = comments

    execute(args)