import threading
import os
import sys
import imp
from collections import deque
import traceback
import logging


#logging.basicConfig(format='%(asctime)s %(name)-18s %(levelname)-8s \
#    %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %H:%M:%S ')

LOGGER = logging.getLogger('executor')

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
#        LOGGER.debug('Cancellation request received; finishing current operation')
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
#                LOGGER.debug('Remaining operations cancelled')
                print('Cancelled.')
                break
            else:
                self.funcMap[operation['type']](operation['uri'], operation['args'])

            if self.isThreadFailed():
#                LOGGER.debug('Exiting due to failures')
                print('Exiting due to failures')
                break

        if not self.isThreadFailed():
            print('Operations completed successfully')

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def runValidator(self, uri, args):
        print('starting validator.')
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
        self.outputObj.saveLastRun()
        print('Parameters saved to disk')

    def runModel(self, uri, args):
        try:
            print('Running the model.')
            model = imp.load_source('model', uri)
            model.execute(args)
        except:
            print('Problem running the model')
            self.printTraceback()
            self.setThreadFailed(True)

