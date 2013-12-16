"""The front end to the recreation server side model.
"""
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
    """An error tolerant URL opener with retries and delays.
    """
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
    """Logs a message to a logger using the method named by a string.
    """
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

def log_check(url, flag = "Dropped intermediate tables.", delay = 15,
              log = LOGGER, line = 0):
    """Echoes a remote log until the flag message is found.
    """
    log.debug("Begin log check at line %i.", line)
    complete = False
    count = 0
    
    while not complete:
        server_log = urllib2.urlopen(url).read()
        server_log = server_log.strip().split("\n")

        if (len(server_log) > 0) and \
           (server_log[-1] != "") and \
           (server_log[-1][-1] != "."):
            server_log.pop(-1)
        
        if (len(server_log[line + count:]) > 0) and \
           (server_log[line + count:] != [""]):
            for entry in server_log[line + count:]:
                log.debug("Parsing log entry: %s.", repr(entry))
                msg_type, msg = entry.split(",")[1:]
                relogger(log, msg_type, msg)
                count = count + 1
                if msg.strip() == flag.strip():
                    log.debug("Detected log check exit message.")
                    complete = True
                    if len(server_log[line + count:]) > 0:
                        log.warn("Unwritten messages on the remote log.")
                    break
            
        else:
            log.info("Please wait.")
            time.sleep(delay)

    line = line + count
    log.debug("End log check at line %i.", line)

    return line

def complete_shapefile(shapefile_name):
    """Checks that there is a .shp, .shx, .dbf, and .prj file by the same name.
    """
    file_name_base = os.path.splitext(shapefile_name)[0]

    complete = True
    for file_extension in ["shp", "shx", "dbf", "prj"]:
        LOGGER.debug(os.extsep.join([file_name_base, file_extension]))
        complete &= os.path.exists(os.extsep.join([file_name_base,
                                                   file_extension]))

    return complete
            
def execute(args):
    """The main function called by IUI.
    """
    #multiprocess cleanup
    args.pop("_process_pool")
    
    #disabling protected predictor
    args["protected"] = False
    args["ouoc"] = False
    
    LOGGER.setLevel(logging.INFO)
    
    # Register the streaming http handlers with urllib2
    register_openers()

    #load configuration
    config_file_name = os.path.splitext(__file__)[0] + "_config.json"
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

    #saving session id to model parameters
    LOGGER.info("Assigned server session id %s.", sessid)
    args["sessid"] = sessid

    #check log and echo messages while not done
    session_path = config["server"] + "/" + config["paths"]["relative"]["data"] + "/" + args["sessid"] + "/"
    log_url = session_path + config["files"]["log"]
    log_line = 0
    
    LOGGER.info("Checking version.")
    log_line = log_check(log_url, "End version PHP script.", 15, LOGGER,
                         log_line)
    
    LOGGER.info("Finished checking version.")

       
    #VALIDATING MODEL PARAMETERS
    LOGGER.debug("Processing parameters.")
    if not args["mode"] in ["initial", "scenario"]:
        msg = "The mode must be specified as \'initial\' or \'scenario\'."
        raise ValueError, msg

    #adding os separator to paths if needed
    if args["workspace_dir"][-1] != os.sep:
        args["workspace_dir"] = args["workspace_dir"] + os.sep

    if args["data_dir"] != "" and args["data_dir"][-1] != os.sep:
        args["data_dir"] = args["data_dir"] + os.sep  

    #validating shapefile
    if args["mode"] == "initial":
        LOGGER.info("Validating AOI.")
        if not complete_shapefile(args["aoi_file_name"]):
            raise ValueError, "The AOI shapefile is missing a component."

    #scanning data directory for shapefiles
    LOGGER.info("Processing predictors.")
    predictors = []
    user_categorization = []
    if not args["data_dir"] == "":
        for file_name in os.listdir(args["data_dir"]):
            file_name_stem, file_extension = os.path.splitext(file_name)
            #checking for complete shapefile
            if file_extension == ".shp":
                if complete_shapefile(os.path.join(args["data_dir"],
                                                   file_name)):
                    LOGGER.info("Found %s predictor.", file_name_stem)
                    predictors.append(file_name_stem)
                else:
                    LOGGER.error("Predictor %s is missing file(s).",
                                 file_name_stem)
            #checking if categorization table
            elif file_extension == ".tsv":
                LOGGER.info("Found %s categorization.", file_name_stem)
                user_categorization.append(file_name_stem)

##    for cat_table in set(user_categorization).difference(predictors):
##        msg = "Categorization table %s has no predictor and will be ignored."
##        LOGGER.warn(msg, cat_table)
##        user_categorization.pop(user_categorization.index(cat_table))

    #making sure there is not landscan categorization
    if "landscan" in user_categorization:
        msg = "The categorization of the Landscan data is not allowed."
        LOGGER.error(msg)
        raise ValueError, msg

    #UPLOADING PREDICTORS
    LOGGER.info("Opening predictors for uploading.")
    
    #opening shapefiles
    attachments = {}
    attachments["sessid"] = sessid
    zip_file_uri = temporary_filename()
    zip_file = zipfile.ZipFile(zip_file_uri, 'w')

    #check if comprssion supported
    try:
        imp.find_module('zlib')
        compression = zipfile.ZIP_DEFLATED
        LOGGER.debug("Predictors will be compressed.")
    except ImportError:
        compression = zipfile.ZIP_STORED
        LOGGER.debug("Predictors will not be compressed.")
    
    for predictor in predictors:
        predictor_base = args["data_dir"] + predictor
        zip_file.write(predictor_base + ".shp", predictor + ".shp",
                       compression)
        zip_file.write(predictor_base + ".shx", predictor + ".shx",
                       compression)
        zip_file.write(predictor_base + ".dbf", predictor + ".dbf",
                       compression)
        zip_file.write(predictor_base + ".prj", predictor + ".prj",
                       compression)
        
    #opening categorization table
    for tsv in user_categorization:
        zip_file.write(args["data_dir"] + tsv + ".tsv", tsv + ".tsv",
                       compression)

    zip_file.close()

    #check upload size
    if os.path.getsize(zip_file_uri) >  20e6:
        msg = "The upload size exceeds the maximum."
        LOGGER.error(msg)
        raise ValueError, msg
    
    attachments["zip_file"] = open(zip_file_uri, 'rb')

    args["user_predictors"] = len(predictors)
    args["user_tables"] = len(user_categorization)

    #count up standard predictors
    args["global_predictors"] = 0    
    if args["mode"] == "initial" and args["global_data"]:
        args["global_predictors"] += args["landscan"]
        args["global_predictors"] += args["protected"]

        if args["osm"]:
            args["global_predictors"] += args["osm_0"]
            args["global_predictors"] += args["osm_1"]
            args["global_predictors"] += args["osm_2"]
            args["global_predictors"] += args["osm_3"]
            args["global_predictors"] += args["osm_4"]

        if args["lulc"]:
            args["global_predictors"] += args["lulc_1"]
            args["global_predictors"] += args["lulc_2"]
            args["global_predictors"] += args["lulc_3"]
            args["global_predictors"] += args["lulc_4"]
            args["global_predictors"] += args["lulc_5"]
            args["global_predictors"] += args["lulc_6"]
            args["global_predictors"] += args["lulc_7"]
            args["global_predictors"] += args["lulc_8"]

        if args["ouoc"]:
            args["global_predictors"] += args["mangroves"]
            args["global_predictors"] += args["reefs"]
            args["global_predictors"] += args["grass"]

    #raise error if no predictors
    LOGGER.debug("There are %i global predictors.", args["global_predictors"])
    LOGGER.debug("There are %i user predictors.", args["user_predictors"])
    if args["user_predictors"] + args["global_predictors"] == 0:
        msg = "You must include predictors for the analysis."
        LOGGER.error(msg)
        raise ValueError, msg   

    #constructing upload predictors request
    LOGGER.debug("Uploading predictors.")
    datagen, headers = multipart_encode(attachments)
    url = config["server"] + config["files"]["PHP"]["predictor"]
    request = urllib2.Request(url, datagen, headers)

    #recording server to model parameters
    args["server"] = config["server"]

    #opening request and saving session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)
        
    LOGGER.debug("Server session %s.", sessid)

    #wait for server to finish saving predictors.
    log_line = log_check(log_url, "End predictors PHP script.", 15, LOGGER,
                         log_line)

    #EXECUTING SERVER SIDE PYTHON SCRIPT
    LOGGER.info("Running server side processing.")
    
    #constructing model parameters
    attachments = {}

    if args["mode"] == "initial":
        base_file_name = str(os.path.splitext(args["aoi_file_name"])[0])
        attachments["aoiSHP"] = open(os.extsep.join([base_file_name, "shp"]),
                                     "rb")
        attachments["aoiSHX"] = open(os.extsep.join([base_file_name, "shx"]),
                                     "rb")
        attachments["aoiDBF"] = open(os.extsep.join([base_file_name, "dbf"]),
                                     "rb")
        attachments["aoiPRJ"] = open(os.extsep.join([base_file_name, "prj"]),
                                     "rb")
    elif args["mode"] == "scenario":
        attachments["init"] = open(args["json"],'rb')
    else:
        raise ValueError, "A valid mode was not detected."
    
    attachments["json"] = json.dumps(args, indent = 4)

    datagen, headers = multipart_encode(attachments)
    
    #constructing server side recreation python script request
    if args["mode"] == "initial":
        LOGGER.debug("Recreation intial run mode.")
        url = config["server"] + config["files"]["PHP"]["recreation"]
    else:
        LOGGER.debug("Scenario run mode.")
        url = config["server"] + config["files"]["PHP"]["scenario"]
        
    LOGGER.info("URL: %s.", url)
    request = urllib2.Request(url, datagen, headers)
    
    #opening request and comparing session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    #check log and echo messages while not done
    LOGGER.info("Model running.")
    log_line = log_check(log_url, "Dropped intermediate tables.", 15, LOGGER,
                         log_line)
    
    LOGGER.info("Finished processing data.")

    #EXECUTING SERVER SIDE R SCRIPT
    LOGGER.info("Running regression.")

    #construct server side R script request
    url = config["server"] + config["files"]["PHP"]["regression"]

    attachments = {}
    attachments = {"sessid": args["sessid"]}
    
    datagen, headers = multipart_encode(attachments)
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)

    #check log and echo messages while not done
    log_line = log_check(log_url, "End regression PHP script.", 15, LOGGER,
                         log_line)

    #ZIP SERVER SIDE RESULTS
    url = config["server"] + config["files"]["PHP"]["results"]

    attachments = {}
    attachments = {"sessid": sessid}
    
    datagen, headers = multipart_encode(attachments)
    request = urllib2.Request(url, datagen, headers)

    #opening request and comparing session id
    sessid = urlopen(url, request, config["tries"], config["delay"], LOGGER)
    
    #download results
    url = session_path + config["files"]["results"]
    LOGGER.info("URL: %s.", url)

    req = urllib2.urlopen(url)
    chunk_size = 16 * 1024
    zip_file_name_format = args["workspace_dir"] + "results%s.zip"
    zip_file_name = zip_file_name_format % \
                    datetime.datetime.now().strftime("-%Y-%m-%d--%H_%M_%S")
    with open(zip_file_name, 'wb') as zip_file:
        while True:
            chunk = req.read(chunk_size)
            if not chunk:
                break
            zip_file.write(chunk)
        
    LOGGER.info("Transaction complete")
