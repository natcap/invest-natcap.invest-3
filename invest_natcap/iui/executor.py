import threading
import os
import sys
import imp
from collections import deque
import traceback
import logging
import time
import subprocess
import platform
import datetime
import shutil

import invest_natcap
from invest_natcap.invest_core import fileio as fileio

logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ',
    stream=open(os.devnull, 'w'))

LOGGER = logging.getLogger()

# This class is to be used if certain WindowsErrors or IOErrors are encountered.
class InsufficientDiskSpace(Exception): pass

def locate_module(module_list, path=None):
    """Search for and return an executable module object as long as the target
        module is within the pythonpath.  This method recursively uses the
        find_module and load_module functions of the python imp module to
        locate the target module by its heirarchical module name.

        module_list - a python list of strings, where each element is the name
            of a contained module.  For example, os.path would be represented
            here as ['os', 'path'].
        path=None - the base path to search.  If None, the pythonpath will be
            used.

        returns an executeable python module object if it can be found.
        Returns None if not."""

    current_name = module_list[0]
    module_info = imp.find_module(current_name, path)
    imported_module = imp.load_module(current_name, *module_info)

    if len(module_list) > 1:
        return locate_module(module_list[1:], imported_module.__path__)
    else:
        return imported_module

class Controller(object):
    """The Controller class manages two Thread objects: Executor and
        PrintQueueChecker.  Executor runs models and queues up print statements
        in a local printqueue list.  Printqueue checks on Executor's printqueue
        and fetches the next message at a specified interval.

        The printqueuechecker exists to offload the work of list-related
        operations from the main thread, which leaves the main thread free to
        perform UI-related tasks."""

    def __init__(self):
        object.__init__(self)
        self.executor = Executor()
        self.msg_checker = PrintQueueChecker(self.executor)
        self.thread_finished = False
        self.thread_failed = False
        self.thread_exception = None

    def get_message(self):
        """Check to see if the message checker thread is alive and returns the
            current message if so.  If the message checker thread is not alive,
            None is returned and self.finished() is called."""

        if self.msg_checker.is_alive():
            return self.msg_checker.get_message()
        else:
            self.finished()

    def start_executor(self):
        """Starts the executor and message checker threads.  Returns nothing.
        """

        if not self.executor:
            self.executor = Executor()
            self.msg_checker = PrintQueueChecker(self.executor)

        self.thread_finished = False
        self.executor.start()
        self.msg_checker.start()

    def cancel_executor(self):
        """Trigger the executor's cancel event. Returns nothing."""

        self.executor.cancel()

    def finished(self):
        """Set the executor and message checker thread objects to none and set
            the thread_finished variable to True.

            Returns nothing."""

        self.thread_failed = self.executor.isThreadFailed()
        self.thread_exception = self.executor.failure_exception
        del self.executor
        self.executor = None
        del self.msg_checker
        self.executor = None
        self.thread_finished = True

    def is_finished(self):
        """Returns True if the threads are finished.  False if not."""

        return self.thread_finished

    def add_operation(self, op, args=None, uri=None, index=None):
        """Wrapper method for Executor.addOperation.  Creates new executor
            and message checker thread instances if necessary.

            Returns nothing."""

        if not self.executor:
            self.executor = Executor()
            self.msg_checker = PrintQueueChecker(self.executor)

        self.executor.addOperation(op, args, uri, index)


class PrintQueueChecker(threading.Thread):
    """PrintQueueChecker is a thread class that checks on a specified executor
        thread object.  By placing the responsibility of this operation in a
        separate thread, we allow the main thread to attend to more pressing UI
        related tasks."""

    def __init__(self, executor_object):
        threading.Thread.__init__(self)
        self.executor = executor_object
        self.message = None

    def get_message(self):
        """Check to see if there is a new message available.

        Returns the string message, if one is available.  None if not."""

        message = self.message
        self.message = None  # indicates the current message has been retrieved
        return message

    def run(self):
        """Fetch messages as long as the executor is alive or has messages.

            This method is reimplemented from threading.Thread and is started
            by calling self.start().

            This function calls the executor object function getMessage(),
            which uses the collections.deque queue object to manage the
            printqueue.

            The new message is only fetched from the executor if the main
            thread has fetched the current message from this
            PrintQueueChecker instance.

            returns nothing."""
        while self.executor.is_alive() or self.executor.hasMessages():
            #new_message = self.executor.getMessage()
            if self.message == None:
                #self.message = new_message
                self.message = self.executor.getMessage()
            #else:
            #    self.message += new_message
            time.sleep(0.025)


class Executor(threading.Thread):
    def __init__(self):

#        logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
#            %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ',
#            stream=self)

        format_string = '%(asctime)s %(name)-18s %(levelname)-8s %(message)s'
        date_format = '%m/%d/%Y %H:%M:%S '
        formatter = logging.Formatter(format_string, date_format)
        handler = logging.StreamHandler(self)
        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)

        threading.Thread.__init__(self)

        self.log_file = None
        self.printQueue = deque([])
        self.printQueueLock = threading.Lock()
        self.threadFailed = False
        self.failure_exception = None
        self.cancelFlag = threading.Event()
        self.operations = []
        self.funcMap = {'validator': self.runValidator,
                        'model': self.runModel,
                        'saveParams': self.saveParamsToDisk}

    def write(self, string):
        self.printQueueLock.acquire()
        self.printQueue.append(string)
        self.printQueueLock.release()

        if self.log_file != None:
            if not self.log_file.closed:
                self.log_file.write(string)

    def hasMessages(self):
        self.printQueueLock.acquire()
        has_messages = len(self.printQueue) > 0
        self.printQueueLock.release()
        return has_messages

    def getMessage(self):
        self.printQueueLock.acquire()
        msg = None
        try:
            msg = self.printQueue.popleft()
            #For some reason this thing barfs out if the printQueue only has
            #1 element on it.  I have *no* idea what is going on here. Can't
            #debug it either.  If you change this to > 0 nothing will print out.
            while len(self.printQueue) > 1:
                msg += self.printQueue.popleft()
            self.printQueueLock.release()
            return msg
        except IndexError:
            self.printQueueLock.release()
            return msg

    def cancel(self):
        LOGGER.debug('Cancellation request received; finishing current ' +
                     'operation')
        self.cancelFlag.set()

    def isCancelled(self):
        return self.cancelFlag.isSet()

    def setThreadFailed(self, state, exception=None):
        """Set the flag of whether the thread has failed.  exception should be a
        pointer to a python Exception or a boolean."""
        self.threadFailed = state
        self.failure_exception = exception

    def isThreadFailed(self):
        return self.threadFailed

    def printTraceback(self):
        LOGGER.debug('Printing traceback')
        print(str(traceback.print_exc()) + '\n')

    def addOperation(self, op, args=None, uri=None, index=None):
        #op is a string index to self.funcmap
        opDict = {'type': op,
                  'args': args,
                  'uri': uri}

        if index == None:
            self.operations.append(opDict)
        else:
            self.operations.insert(index, opDict)

    def print_args(self, args_dict):
        """Write args_dict to a formatted string to the self.write() function.
            args_dict - a dictionary.

        returns noting"""

        self.write("Arguments:\n")
        format_str = "%-20s %s\n"
        sorted_args = sorted(args_dict.iteritems(), key=lambda x: x[0])
        for name, value in sorted_args:
            self.write(format_str % (name, value))
        self.write("\n\n")


    def run(self):
        sys.stdout = self
        sys.stderr = self

        #determine what type of function needs to be run
        for operation in self.operations:
            self.setThreadFailed(False)

            if self.isCancelled():
                LOGGER.debug('Remaining operations cancelled')
                break
            else:
                self.funcMap[operation['type']](operation['uri'],
                                                operation['args'])

            if self.isThreadFailed():
                LOGGER.error('Exiting due to failures')
                break

        if not self.isThreadFailed():
            LOGGER.info('Operations completed successfully')

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def runValidator(self, uri, args):
        LOGGER.info('Starting validator')
        validator = imp.load_source('validator', uri)
        outputList = []

        try:
            validator.execute(args, outputList)

            if len(outputList) > 0:
                print('ERRORS:\n')
                for error in outputList:
                    self.write(error + '\n')
                self.setThreadFailed(True)
            else:
                print('Validation complete.')
        except Exception:
            print('\nProblem occurred while running validation.')
            self.printTraceback()
            self.setThreadFailed(True)

    def saveParamsToDisk(self, data=None):
        LOGGER.info('Saving parameters to disk')
        self.outputObj.saveLastRun()
        LOGGER.info('Parameters saved to disk')

    def move_log_file(self, workspace):
        self.log_file.close()
        shutil.move(self.log_file.name, workspace)
        log_file_name = os.path.basename(self.log_file.name)
        log_file_uri = os.path.join(workspace, log_file_name)
        LOGGER.info('Saving log file to %s', log_file_uri)

    def runModel(self, module, args):
        try:
            workspace = args['workspace_dir']
        except KeyError:
            # KeyError thrown when the key 'workspace_dir' is not used in the
            # args dictionary, print an inconsequential error.
            LOGGER.error('Cannot find args id \'workspace_dir\'.')
            workspace = None

        try:
            # Create the log filename from the current time and save that in the
            # root of the user's workspace.  The file is actually written to
            # whenever self.write() is called.
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d--%H_%M_%S")

            # the module name needs to be extracted differently if it's a python
            # module or if it's a file on disk.  While we're at it, we can also
            # locate the model to be loaded.
            if os.path.isfile(module):
                model = imp.load_source('model', module)
               # Model name is name of module file, minus the extension
                model_name = os.path.splitext(os.path.basename(module))[0]
            else:
                module_list = module.split('.')
                model = locate_module(module_list)
                model_name = module_list[-1]  # model name is last entry in list
            filename = '%s-log-%s.txt' % (model_name, timestamp)

            # we want to save this file to the current directory until the model
            # finishes, when we copy the log into the model's workspace
            settings_folder = invest_natcap.iui.fileio.settings_folder()
            log_file_uri = os.path.abspath(os.path.join(settings_folder,
                filename))
            self.log_file = open(log_file_uri, 'w')

            # Now that the log file is open, write the arguments to it.
            self.print_args(args)
            LOGGER.info('Logging will be saved to %s', filename)

            LOGGER.debug('Loaded the model from %s', module)
            LOGGER.info('Executing the loaded model')

            try:
                model_version = model.__version__
                LOGGER.info('Running model version %s', model_version)
            except AttributeError:
                model_version = None

            LOGGER.info('Disk space remaining for workspace: %s GB',
                        fileio.get_free_space(workspace, unit='GB'))
            invest_natcap.log_model(model_name, model_version)  # log model usage to ncp-dev
            model.execute(args)
        except Exception as e:
            LOGGER.info('Disk space free: %s MB',
                        fileio.get_free_space(workspace, unit='MB'))
            LOGGER.error('Error: a problem occurred while running the model')
            self.printTraceback()

            # If the exception indicates that we ran out of disk space, convert
            # e to a more informative exception.
            if hasattr(e,'__class__') and hasattr(e, 'errno'):
                LOGGER.debug('error %s number %s', e.__class__, e.errno)
                if (isinstance(e, WindowsError) and (e.errno in [8, 28])) or\
                        (isinstance(e, IOError) and (e.errno == 28)):
                    e = InsufficientDiskSpace('You do not have sufficient disk '
                                              'space available for this model to finish running.')
                    
            self.printTraceback()
            self.setThreadFailed(True, e)
            self.move_log_file(workspace)
            #Quit the rest of the function
            return

        if workspace != None:
            #Try opening up a file explorer to see the results.
            try:
                LOGGER.info('Opening file explorer to workspace directory')
                if platform.system() == 'Windows':
                    # Try to launch a windows file explorer to visit the workspace
                    # directory now that the operation has finished executing.
                    LOGGER.info('Using windows explorer to view files')
                    subprocess.Popen(r'explorer "%s"' % workspace)
                else:
                    # Assume we're on linux.  No biggie, just use xdg-open to use the
                    # default file opening scheme.
                    LOGGER.info('Not on windows, using default file browser')
                    subprocess.Popen(['xdg-open', workspace])
            except OSError:
                # OSError is thrown if the given file browser program (whether
                # explorer or xdg-open) cannot be found.  No biggie, just pass.
                LOGGER.error('Cannot find default file browser. Platform: %s |' +
                    ' folder: %s', platform.system(), workspace)

        LOGGER.info('Disk space free: %s GB',
                    fileio.get_free_space(workspace,unit='GB'))
        LOGGER.info('Finished.')
        self.move_log_file(workspace)
