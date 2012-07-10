import sys

sys.path.append("/home/mlacayo/workspace/invest-natcap.invest-3")

import imp
import os
import platform
import time
import json
from optparse import OptionParser

from PyQt4 import QtGui, QtCore

import base_widgets
import executor
import iui_validator

CMD_FOLDER = '.'

class ModelUIRegistrar(base_widgets.ElementRegistrar):
    def __init__(self, root_ptr):
        super(ModelUIRegistrar, self).__init__(root_ptr)

        changes = {'file': base_widgets.FileEntry,
                   'folder': base_widgets.FileEntry,
                   'text': base_widgets.YearEntry
                    }

        self.update_map(changes)

class ModelUI(base_widgets.ExecRoot):
    def __init__(self, uri, use_gui):
        """Constructor for the DynamicUI class, a subclass of DynamicGroup.
            DynamicUI loads all setting from a JSON object at the provided URI
            and recursively creates all elements.
            
            uri - the string URI to the JSON configuration file.
            use_gui - a boolean.  Determines whether the UI will be presented
                to the user for interaction.  Necessary for testing.
            
            returns an instance of DynamicUI."""

        #the top buttonbox needs to be initialized before super() is called, 
        #since super() also creates all elements based on the user's JSON config
        #this is important because QtGui displays elements in the order in which
        #they are added.
        layout = QtGui.QVBoxLayout()

        self.links = QtGui.QLabel()
        self.links.setOpenExternalLinks(True)
        self.links.setAlignment(QtCore.Qt.AlignRight)
        layout.addWidget(self.links)

        registrar = ModelUIRegistrar(self)
        self.okpressed = False

        base_widgets.ExecRoot.__init__(self, uri, layout, registrar)


        self.layout().setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.use_gui = use_gui

        self.initUI()

    def initUI(self):
        """Initialize the User Interface elements specific to this class.
            Most elements are created with the call to super() in the __init__
            function, element creation is handled in 
            DynamicGroup.createElements().
            
            returns nothing"""

        #set the window's title
        try:
            self.setWindowTitle(self.attributes['label'])
        except KeyError:
            self.setWindowTitle('InVEST')

        self.addLinks()

        #reveal the assembled UI to the user, but only if not testing.
        if self.use_gui:
            self.show()

    def addLinks(self):
        docURI = 'file:///' + os.path.abspath(self.attributes['localDocURI'])
        self.feedbackBody = "Please include the following information:\
\n\n1) InVEST model you're having difficulty with\n2) Explicit error message or \
behavior\n3) If possible, a screenshot of the state of your InVEST toolset when \
you get the error.\n4)ArcGIS version and service pack number\n\n\
Feel free to also contact us about requests for collaboration, suggestions for \
improvement, or anything else you'd like to share."
        self.feedbackURI = 'mailto:richsharp@stanford.edu?subject=InVEST Feedback'
        self.links.setText('<a href=\"' + docURI + '\">Model documentation' + 
                             '</a> | <a href=\"' + self.feedbackURI + '\">' + 
                             'Send feedback</a>')
        self.links.linkActivated.connect(self.contactPopup)

    def contactPopup(self, uri):
        if str(uri) == self.feedbackURI:
            #open up a qdialog
            self.feedbackDialog = QtGui.QMessageBox()
            self.feedbackDialog.setWindowTitle('Send feedback')
            self.feedbackDialog.setText("If you'd like to report a problem with\
this model, send an email to richsharp@stanford.edu." + self.feedbackBody)
            self.feedbackDialog.show()

        QtGui.QDesktopServices.openUrl(QtCore.QUrl(uri))

    def queueOperations(self):
        modelArgs = self.assembleOutputDict()
        self.operationDialog.exec_controller.add_operation('model',
                                                   modelArgs,
                                                   self.attributes['targetScript'])


def getFlatDefaultArgumentsDictionary(args):
    flatDict = {}
    if isinstance(args, dict):
        if 'args_id' in args and 'defaultValue' in args:
            flatDict[args['args_id']] = args['defaultValue']
        if 'elements' in args:
            flatDict.update(getFlatDefaultArgumentsDictionary(args['elements']))
    elif isinstance(args, list):
        for element in args:
            flatDict.update(getFlatDefaultArgumentsDictionary(element))

    return flatDict


def main(uri, use_gui=True):
    app = QtGui.QApplication(sys.argv)
#    validate(json_args)

    # Check to see if the URI exists in the current directory.  If not, assume
    # it exists in the directory where this module exists.
    if not os.path.exists(uri):
        file_path = os.path.dirname(os.path.abspath(__file__))
        uri = os.path.join(file_path, os.path.basename(uri))

        # If the URI still doesn't exist, raise a helpful exception.
        if not os.path.exists(uri):
            raise Exception('Can\'t find the file %s.'%uri)

    ui = ModelUI(uri, use_gui)
    if use_gui == True:
        result = app.exec_()
    else:
        orig_args = json.loads(open(json_args).read())
        args = getFlatDefaultArgumentsDictionary(orig_args)

        thread = executor.Executor()
        thread.addOperation('model', args, orig_args['targetScript'])

        thread.start()

        while thread.isAlive() or thread.hasMessages():
            message = thread.getMessage()
            if message != None:
                print(message.rstrip())
            time.sleep(0.005)

if __name__ == '__main__':
    #Optparse module is deprecated since python 2.7.  Using here since OSGeo4W
    #is version 2.5.
    parser = OptionParser()
    parser.add_option('-t', '--test', action='store_false', default=True, dest='test')
    (options, uri) = parser.parse_args(sys.argv)
    print uri
    main(uri[1], options.test)

