import threading
import os
import sys
import imp
from collections import deque
import traceback
import logging
import time

LOGGER = logging.getLogger('executor')


class Controller(object):
    def __init__(self):
        object.__init__(self)
        self.executor = Executor()
        self.msg_checker = PrintQueueChecker(self.executor)
        self.thread_finished = False
    
    def get_message(self):
        if self.msg_checker.is_alive():
            return self.msg_checker.get_message()
        else:
            self.finished()
        
    def start_executor(self):
        self.executor.start()
        self.msg_checker.start()
        
    def cancel_executor(self):
        self.executor.cancel()
        
    def finished(self):
        self.executor = None
        self.msg_checker = None
        self.thread_finished = True
        
    def is_finished(self):
        return self.thread_finished
        
    def add_operation(self, op, args=None, uri=None, index=None):
        if not self.executor:
            self.executor = executor.Executor()
            self.msg_checker = PrintQueueChecker(self.executor)
            
        self.executor.addOperation(op, args, uri, index)
    

class PrintQueueChecker(threading.Thread):
    def __init__(self, executor_object):
        threading.Thread.__init__(self)
        self.executor = executor_object
        self.message = None
    
    def get_message(self):
        message = self.message
        self.message = None #indicates the current message has been retrieved
        return message
        
    def run(self):
        while self.executor.is_alive() or self.executor.hasMessages():
            if self.message == None:
                self.message = self.executor.getMessage()
            time.sleep(0.1)
    
class Executor(threading.Thread):
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
            %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ',
            stream=self)
        
        threading.Thread.__init__(self)

        self.printQueue = deque([])
        self.threadFailed = False
        self.cancelFlag = threading.Event()
        self.operations = []
        self.funcMap = {'validator': self.runValidator,
                        'model': self.runModel,
                        'saveParams': self.saveParamsToDisk}

    def write(self, string):
        self.printQueue.append(string)
        
    def hasMessages(self):
        try:
            if self.printQueue[0]:
                return True
        except IndexError:
            return False

    def getMessage(self):
        try:
            return self.printQueue.popleft()
        except IndexError:
            return None

    def cancel(self):
        LOGGER.debug('Cancellation request received; finishing current operation')
        self.cancelFlag.set()

    def isCancelled(self):
        return self.cancelFlag.isSet()

    def setThreadFailed(self, state):
        self.threadFailed = state
        
    def isThreadFailed(self):
        return self.threadFailed

    def printTraceback(self):
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
                self.funcMap[operation['type']](operation['uri'], operation['args'])

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

    def runModel(self, uri, args):
        try:
            LOGGER.info('Loading the queued model')
            model = imp.load_source('model', uri)
            LOGGER.info('Executing the loaded model')
            model.execute(args)
        except:
            LOGGER.error('Error: a problem occurred while running the model')
            self.printTraceback()
            self.setThreadFailed(True)

