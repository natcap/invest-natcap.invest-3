import os
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import time

import json
import logging

import datetime

import zipfile
import imp
from invest_natcap.raster_utils import temporary_filename

import invest_natcap

logging.basicConfig(format = '%(asctime)s %(name)-20s %(levelname)-8s \
%(message)s', level = logging.DEBUG, datefmt = '%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('recreation_client_init')

def urlopen(url, request, tries = 3, delay = 15, log = LOGGER):
    for attempt in range(tries):
        log.info("Trying URL: %s.", url)
        try:
            msg = urllib2.urlopen(request).read().strip()
            break
        except urllib2.URLError, msg:
            log.warn("Encountered error: %s", msg)
            if attempt < tries-1:
                log.info("Waiting %i for retry.", delay)
                time.sleep(delay)
            else:
                raise urllib2.URLError, msg

    return msg

def relogger(log, msg_type, msg):
    msg_type = msg_type.strip()
    if msg_type == "INFO":
        log.info(msg)
    elif msg_type == "DEBUG":
        log.debug(msg)
    elif msg_type == "WARNING":
        log.warn(msg)
    elif msg_type == "ERROR":
        log.error(msg)
        raise IOError, "Error on server: %s" % (msg)
    else:
        log.warn("Unknown logging message type %s: %s" % (msg_type, msg))    

def log_check(url, flag = "Dropped intermediate tables.", delay = 15, log = LOGGER, line = 0):
    log.debug("Begin log check at line %i.", line)
    complete = False
    count = 0
    
    while not complete:
        server_log = urllib2.urlopen(url).read()
        server_log = server_log.strip().split("\n")

        if (len(server_log) > 0) and (server_log[-1] != "") and (server_log[-1][-1] != "."):
            server_log.pop(-1)
        
        if (len(server_log[line + count:])) > 0 and (server_log[line + count:] != [""]):
            for entry in server_log[line + count:]:
                log.debug("Parsing log entry: %s.", repr(entry))
                msg_type, msg = entry.split(",")[1:]
                relogger(log, msg_type, msg)
                count = count + 1
                if msg.strip() == flag.strip():
                    log.debug("Detected log check exit message.")
                    complete = True
                    if len(server_log[line + count:]) > 0:
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
    config_file_name = os.path.dirname(os.path.abspath(__file__)) + os.sep + "recreation_client_config.json"
    LOGGER.debug("Loading server configuration from %s.", config_file_name)
    config_file = open(config_file_name, 'r')
    config = json.loads(config_file.read())
    config_file.close()

    #VERSION AND RELEASE CHECK
    args["version_info"] = invest_natcap.__version__
    args["is_release"] = invest_natcap.is_release()


    #constructing model parameters
    attachments = {"version_info" : args["version_info"],
                   "is_release": args["is_release"]}
    
    datagen, headers = multipart_encode(attachments)
    
    #constructing server side version
    url = config["server"] + config["files"]["PHP"]["version"]
    LOGGER.info("URL: %s.", url)
    request = urllib2.Request(url, datagen, headers)
    
    #opening request and comparing session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    args["sessid"] = sessid

    #check log and echo messages while not done
    log_url = config["server"] + "/" + config["paths"]["relative"]["data"] + "/" + args["sessid"] + "/" + config["files"]["log"]
    log_line = 0
    
    LOGGER.info("Checking version.")
    log_line = log_check(log_url, "End version PHP script.", 15, LOGGER, log_line)
    
    LOGGER.info("Finished checking version.")

       
    #VALIDATING MODEL PARAMETERS
    LOGGER.debug("Processing parameters.")

    #adding os separator to paths if needed
    if args["workspace_dir"][-1] != os.sep:
        args["workspace_dir"] = args["workspace_dir"] + os.sep

    if args["data_dir"] != "" and args["data_dir"][-1] != os.sep:
        args["data_dir"] = args["data_dir"] + os.sep  

    #validating shapefile    
    LOGGER.info("Validating AOI.")
##    dirname = os.path.dirname(args["aoi_file_name"]) + os.sep
    file_name_stem = os.path.splitext(args["aoi_file_name"])[0]
    aoi_shp_file_name = file_name_stem +".shp"
    aoi_shx_file_name = file_name_stem +".shx"
    aoi_dbf_file_name = file_name_stem +".dbf"
    aoi_prj_file_name = file_name_stem +".prj"
    
    for file_name in [aoi_shp_file_name, aoi_shx_file_name, aoi_dbf_file_name, aoi_prj_file_name]:
        if not os.path.exists(file_name):
            LOGGER.error("The AOI is missing a shapefile component.")
            raise ValueError, "The AOI is missing a shapefile component."

    #scanning data directory for shapefiles
    LOGGER.info("Processing predictors.")
    predictors = []
    user_categorization = []
    if not args["data_dir"] == "":
        for file_name in os.listdir(args["data_dir"]):
            file_name_stem, file_extension = os.path.splitext(file_name)
            #checking for complete shapefile
            if file_extension == ".shp":
                if os.path.exists(args["data_dir"] + file_name_stem + ".shx") and \
                os.path.exists(args["data_dir"] + file_name_stem + ".shp") and \
                os.path.exists(args["data_dir"] + file_name_stem + ".prj"):
                    LOGGER.info("Found %s predictor.", file_name_stem)
                    predictors.append(file_name_stem)
                else:
                    LOGGER.error("Predictor %s is missing file(s).", file_name_stem)
            #checking if categorization table
            elif file_extension == ".tsv":
                LOGGER.info("Found %s categorization.", file_name_stem)
                user_categorization.append(file_name_stem)

    #making sure there is not landscan categorization
    if "landscan.tsv" in user_categorization:
        LOGGER.error("The categorization of the Landscan data is not allowed.")
        raise ValueError, "The categorization of the Landscan data is not allowed."

    #UPLOADING PREDICTORS
    LOGGER.info("Opening predictors for uploading.")
    
    #opening shapefiles
    attachments = {}
    attachments["sessid"] = args["sessid"]
    zip_file_uri = temporary_filename()
    zip_file = zipfile.ZipFile(zip_file_uri, mode = 'w')

    #check if comprssion supported
    try:
        imp.find_module('zlib')
        compression = zipfile.ZIP_DEFLATED
        LOGGER.debug("Predictors will be compressed.")
    except ImportError:
        compression = zipfile.ZIP_STORED
        LOGGER.debug("Predictors will not be compressed.")
    
    for predictor in predictors:
        zip_file.write(args["data_dir"] + predictor + ".shp", predictor + ".shp", compression)
        zip_file.write(args["data_dir"] + predictor + ".shx", predictor + ".shx", compression)
        zip_file.write(args["data_dir"] + predictor + ".dbf", predictor + ".dbf", compression)
        zip_file.write(args["data_dir"] + predictor + ".prj", predictor + ".prj", compression)
        
    #opening categorization table
    for tsv in user_categorization:
        zip_file.write(args["data_dir"] + tsv + ".tsv", tsv + ".tsv", compression)

    zip_file.close()
    attachments["zip_file"] = open(zip_file_uri, 'rb')

    args["user_predictors"] = len(predictors)
    args["user_tables"] = len(user_categorization)

    #constructing upload predictors request
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = config["server"] + config["files"]["PHP"]["predictor"]
    request = urllib2.Request(url, datagen, headers)

    #recording server to model parameters
    args["server"] = config["server"]

    #opening request and saving session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)
        
    LOGGER.debug("Server session %s.", args["sessid"])

    #wait for server to finish saving predictors.
    log_line = log_check(log_url, "End predictors PHP script.", 15, LOGGER, log_line)

    #EXECUTING SERVER SIDE PYTHON SCRIPT
    LOGGER.info("Uploading AOI and running model.")
    
    #constructing model parameters
    attachments = {"json" : json.dumps(args, indent = 4),
                   "aoiSHP": open(aoi_shp_file_name, "rb"),
                   "aoiSHX": open(aoi_shx_file_name, "rb"),
                   "aoiDBF": open(aoi_dbf_file_name, "rb"),
                   "aoiPRJ": open(aoi_prj_file_name, "rb")}
    
    datagen, headers = multipart_encode(attachments)
    
    #constructing server side recreation python script request
    url = config["server"] + config["files"]["PHP"]["recreation"]
    LOGGER.info("URL: %s.", url)
    request = urllib2.Request(url, datagen, headers)
    
    #opening request and comparing session id
    sessid2 = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    if not sessid2 == args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."

    #check log and echo messages while not done
    LOGGER.info("Model running.")
    log_line = log_check(log_url, "Dropped intermediate tables.", 15, LOGGER, log_line)
    
    LOGGER.info("Finished processing data.")

    #EXECUTING SERVER SIDE R SCRIPT
    LOGGER.info("Running regression.")

    #construct server side R script request
    url = config["server"] + config["files"]["PHP"]["regression"]
    datagen, headers = multipart_encode({"sessid": args["sessid"]})
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    sessid2 = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    if not sessid2 == args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."

    #check log and echo messages while not done
    log_line = log_check(log_url, "End regression PHP script.", 15, LOGGER, log_line)

    #ZIP SERVER SIDE RESULTS
    url = config["server"] + config["files"]["PHP"]["results"]
    datagen, headers = multipart_encode({"sessid": args["sessid"]})
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    sessid2 = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    if not sessid2 == args["sessid"]:
        LOGGER.error("There was a session id mismatch.")
        raise ValueError, "The session id unexpectedly changed."
    
    #download results
    url = config["server"] + config["paths"]["relative"]["data"] + args["sessid"] + "/" + config["files"]["results"]
    LOGGER.info("URL: %s.", url)

    req = urllib2.urlopen(url)
    chunk_size = 16 * 1024
    zip_file_name_format = args["workspace_dir"] + "results%s.zip"
    zip_file_name = zip_file_name_format %\
                    datetime.datetime.now().strftime("-%Y-%m-%d--%H_%M_%S")
    with open(zip_file_name, 'wb') as zip_file:
        while True:
            chunk = req.read(chunk_size)
            if not chunk:
                break
            zip_file.write(chunk)
        
    LOGGER.info("Transaction complete")
