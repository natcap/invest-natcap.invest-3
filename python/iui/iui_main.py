import sys, os, imp
import platform

cmd_folder = os.path.dirname(os.path.abspath(__file__))
print cmd_folder
sys.path.insert(0, cmd_folder + '/../invest_core')

if platform.system() == 'Windows':
    sys.path.append(cmd_folder + '/../../OSGeo4W/lib/site-packages')

from PyQt4 import QtGui, QtCore

import simplejson as json
import jsonschema

class DynamicElement(QtGui.QWidget):
    """Create an object containing the skeleton of most functionality in the
        UI Interpreter's related classes.  It is not invoked directly by other
        IUI classes, but is instead used as a base class for almost all classes
        in the UI interpreter.
        
        DynamicElement serves as a base class for DynamicGroup and 
        DynamicPrimitive.  The functions and object data it declares are shared
        by all subclasses."""
    
    def __init__(self, attributes):
        """This is the constructor for the DynamicElement object.
        
            attributes - a Python dictionary with the attributes of the element
                taken from the input JSON file.
                
            returns a DynamicElement object
            """
        
        #DynamicElement inherits QtGui.QWidget, so we'll call the constructor
        #for QWidget here.
        super(DynamicElement, self).__init__()

        #save a copy of the user-defined attributes for this element.  Based
        # on the specification of the JSON config file, the attributes array 
        #may contain the attributes for other, to-be-created, elements.
        self.attributes = attributes
        
        #Self.root is a pointer to the root window of the user interface, which
        # is an instance of the class DynamicUI.
        #self.root is set after the GUI has been constructed to take advantage 
        #of Qt's ability to keep track of the parent of an element. 
        self.root = None
        
        #We initialize self.required as False here, since some widgets may not
        #actually be input elements.  This ensures that all widgets will be 
        #marked optional unless specified by the user.
        self.required = False
        
        #If the user has specified an attribute 'enabledBy', we save it in the
        #object.  Otherwise, we set it to None.  We do this to slightly simplify
        #the enabling/disabling process in the DynamicUI class.
        self.setEnabledBy()
        
        #initialize the elements array in case the user has defined sub-elements
        self.elements = []

    def setEnabledBy(self):
        """Sets the local variable self.enabledBy if one is provided in the
            self.attributes dictionary.
            
            returns nothing"""
            
        if 'enabledBy' in self.attributes:
            self.enabledBy = self.attributes['enabledBy']
        else:
            self.enabledBy = None
            
    def getRoot(self):
        """Search up the Qt widget tree until we find the root element, which
            is by definition an instance of the class DynamicUI.  A pointer to
            the root is usually saved to the local object as self.root.
            
            returns a pointer to the instance of DynamicUI"""
            
        parent = self.parentWidget()
        if isinstance(parent, DynamicUI):
            return parent
        else:
            return parent.getRoot()
        
    def isEnabled(self):
        """Retrieve the status of the self.enabled boolean attribute.
            self.enabled is an attribute of the QtGui.QWidget object.
            
            returns a boolean"""
        return self.enabled
        
    def requirementsMet(self):
        return True  
          
class DynamicGroup(DynamicElement):
    """Creates an object intended for grouping other elements together.
    
        DynamicGroup is a subclass of DynamicElement and thus inherits all 
        attributes and functions of the DynamicElement class.
        
        DynamicUI, Container, CollapsibleContainer and List are all
        subclasses of DynamicGroup.
    
        The DynamicGroup object allows other elements to be grouped together
        using any arbitrary layout mechanism compatible with Qt.  If a custom
        layout manager is used, it may be necessary to revisit the
        DynamicGroup.createElements() function to define exactly how the
        elements created are to be added to the new layout.
        
        As all possible grouping objects in this Interpreter subclass 
        DynamicGroup, if a new widget is to be added, it must likewise be added
        to the if-elif block in createElements.  The element will not be created
        if there is no corresponding entry in createElements()
        """
        
    def __init__(self, attributes, layout):
        """Constructor for the DynamicGroup class.
            Most object construction has been abstracted to the DynamicElement
            class.  The defining feature of a DynamicGroup from a DynamicElement
            is that a DynamicGroup has a layout and can contain elements if
            they have been defined by the user.
        
            attributes - a python dictionary with the attributes for this group
                parsed from the user-defined JSON object.
            layout - a layout mechanism compatible with Qt4 or a subclass of 
                such a layout manager.
        
            returns an instance of DynamicGroup"""
            
        #create the object by initializing its superclass, DynamicElement.
        super(DynamicGroup, self).__init__(attributes)
        
        #set the layout for this group(a subclass of DynamicElement, which
        #itself is a subclass of QtGui.QWidget) so that we can add widgets 
        #as necessary.
        self.setLayout(layout)
        
        #if the user has defined elements for this group, iterate through the 
        #elements ductionary and create them.
        if 'elements' in attributes:
            self.createElements(attributes['elements'])
        
    def createElements(self, elementsArray):
        """Create the elements defined in elementsArray as widgets within 
            this current grouping widget.  All elements are created as widgets
            within this grouping widget's layout.
            
            elementsArray - a python array of elements, where each element is a
                python dictionary with string keys to each of its attributes as
                defined in the input JSON file.
                
            no return value"""
        
        #We initialize a counter here to keep track of which row we occupy
        # in this iteration of the loop.  Used excluseively when the layout
        #manager is an instance of QtGui.QGridLayout(), as both the row and
        #column indices are required in QGridLayout's addWidget() method.    
        i = 0
        
        #loop through all entries in the input elementsArray and create the 
        #appropriate elements.  As new element classes are created, they must
        #likewise be entered here to be created.
        for values in elementsArray:
            if values['type'] == 'checkbox':
                widget = CheckBox(values)
            elif values['type'] == 'container':
                if 'collapsible' in values:
                    if values['collapsible'] == True:
                        widget = CollapsibleContainer(values)
                    elif values['collapsible'] == False:
                        widget = Container(values)
            elif values['type'] == 'list':
                widget = GridList(values)
            elif values['type'] == 'checkbox':
                widget = CheckBox(values)
            elif (values['type'] == 'file') or (values['type'] == 'folder'):
                widget = FileEntry(values)
            elif values['type'] == 'text':
                widget = YearEntry(values)
            
            #If an unusual layoutManager has been declared, it may be necessary 
            #to add a new clause to this conditional block.
            if isinstance(self.layout(), QtGui.QGridLayout):
                j = 0
                for subElement in widget.elements:
                    self.layout().addWidget(subElement, i, j)
                    j += 1
            else:
                self.layout().addWidget(widget)

            #the self.elements array is used for maintaining a list of pointers
            #to elements associated with this group.
            self.elements.append(widget)
            i += 1

    def getElementsDictionary(self):
        """Assemble a flat dictionary of all elements contained in this group.
            
            This function loops through the self.elements array and attempts to 
            retrieve a dictionary for each sub-element.  If a sub-element
            dictionary can be retrieved, it is concatenated with the existing 
            dictionary.
            
            Such a flat dictionary structure is convenient for iterating over 
            all elements in the UI.
            
            returns a python dictionary mapping widget id (a string) to an
                element pointer."""
                
        outputDict = {}
        for element in self.elements:
            #Create an entry in the output dictionary for the current element
            outputDict[element.attributes['id']] = element
            try:
                outputDict.update(element.getElementsDictionary())
            except AttributeError:
                pass
            
        return outputDict
    
    def enable(self):
        """Enable all elements listed in the elements array (all elements 
            created by createElements() are listed in the elements array).
        
            returns nothing"""
            
        for element in self.elements:
            element.enable()
            
    def disable(self):
        """Disable Enable all elements listed in the elements array (all elements 
            created by createElements() are listed in the elements array).
        
            returns nothing"""
            
        for element in self.elements:
            element.disable()
    
class DynamicPrimitive(DynamicElement):
    """DynamicPrimitive represents the class of all elements that can be listed
        individually in the JSON file that themselves cannot group other 
        elements.  As such, DynamicPrimitive is the superclass of all input 
        elements.
        
        DynamicText and CheckBox inherit DynamicPrimitive, and FileEntry,
        YearEntry inherit DynamicText (thus also inheriting DynamicPrimitive).
        
        There are two defining attributes of DynamicPrimitive:
         - self.elements (a python Array)
         - self.attributes['args_id'] (a string)
         
        self.elements is an array of the widgets that make up this element.  By
        default, this is set to [self], implying that a subclass has at least 
        one widget.  In cases where a subclass of DynamicPrimitive has multiple
        widgets, the elements array is used to determine the order in which the 
        elements are added to the GUI in DynamicGroup.createElements().
        
        self.attributes['args_id'] is an optional string provided by the user 
        that enables the construction of an arguments dictionary in python that
        will be passed to the specified python program.  The args_id must 
        conform with the API specified by the desired model. 
        """

    def __init__(self, attributes):
        """Constructor for the DynamicPrimitive class.
            Because DynamicPrimitive inherits DynamicElement, most of the obect
            construction has been abstracted away to the DynamicElement 
            constructor or to the superclass of DynamicElement, QWidget.
            
            attributes - a python dictionary with attributes for this element.
                Attribute keys are defined in the JSON schema declaration in 
                this python file.
        
            returns an instance of DynamicPrimitive"""
            
        super(DynamicPrimitive, self).__init__(attributes)
        
        #create the elements array such that it only includes the present object
        self.elements = [self]

        #if the user has provided an 'args_id' attribute, set self.args_id to it
        if "args_id" in attributes:
            self.args_id = attributes['args_id']
        else:
            self.args_id = None
            
    def getElementsDictionary(self):
        """Assemble a python dictionary mapping this object's string ID to its
            pointer.
            
            self.getElementsDictionary is called to build a flat dictionary of
            all elements in the entire UI.  Considering that subclasses of 
            DynamicPrimitive are the most atomic elements the user can control
            in the JSON file, it follows that subclasses of DynamicPrimitive 
            should return the most primitive such dictionary.
            
            returns a python dict mapping string ID -> this object's pointer."""
        
        return {self.attributes['id'] : self}
    
    def enable(self):
        """Loop through all widgets in self.elements and enable them via the
            Qt API.
            
            returns nothing."""
            
        for element in self.elements:
            element.setDisabled(False)

    def disable(self):
        """Loop through all widgets in self.elements and disable them via the
            Qt API.
            
            returns nothing."""
            
        for element in self.elements:
            element.setDisabled(True)
            
class DynamicText(DynamicPrimitive):
    """Creates an object containing a label and a sigle-line text field for
        user input.
        
        DynamicText is a subclass of DynamicPrimitive and thus inherits all its
        methods and attributes.
        
        FileEntry and YearEntry inherit DynamicText.
        
        As the superclass to a number of text-based elements, DynamicText 
        implements a number of text-only options, namely defaultText and 
        validText.
        """

    def __init__(self, attributes):
        """Constructor for the DynamicText class.
            The defining features for this class have primarily to do with user
            interaction: a child of DynamicText can be required, can have
            defaultText and can have valid text.
            
            attributes -a python dictionary of element attributes.

            returns a constructed DynamicText object."""
        
        #create the object by initializing its superclass, DynamicElement.    
        super(DynamicText, self).__init__(attributes)
        
        #create the new Label widget and save it locally.  This label is 
        #consistent across all included subclasses of DynamicText.
        self.label = QtGui.QLabel(attributes['label'])
        
        #create the new textField widget and save it locally.  This textfield
        #is consistent across all included subclasses of DynamicText, though
        #the way the textfield is used may differ from class to class.
        self.textField = QtGui.QLineEdit()
        
        #All subclasses of DynamicText must contain at least these two elements.
        self.elements = [self.label, self.textField]
        
        #Set self.required to the user's specification (could be True or False)
        if "required" in attributes:
            self.required = attributes['required']
            
        #If the user has defined some default text for this text field, insert 
        #it into the text field.
        if "defaultText" in attributes:
            self.textField.insert(attributes['defaultText'])

        #If the user has defined a string regular expression of text the user is
        #allowed to input, set that validator up with the setValidateField()
        #function.
        if 'validText' in attributes:
            self.setValidateField(attributes['validText'])
        
        #Connect the textfield's textEdited signal to the toggle() function.
        #This function will trigger any time the user changes the text in the
        #textfield.  The signal textChanged() is not used because it is toggled
        #even when the text is programmatically changed.
        self.textField.textEdited.connect(self.toggle)
            
    def toggle(self):
        """Toggle all elements associated with this element's ID.
            
            This function has several purposes:
              - It instructs the root element to update its requirement 
                notification based on the current status of all elements
              - It sets the backgroundColor of this object's label if its
                completion requirements have not been met
              - It instructs the root element to toggle all other elements 
                appropriately.
                
            returns nothing."""
            
        #self.root is set to None by default, as the self.getRoot function 
        #cannot operate until all widgets have been added to the main UI window.
        #Since user interaction necessarily happens after the UI is constructed,
        #this is a natural place to request a pointer to the root element if it
        #has not already been set.
        if self.root == None:
            self.root = self.getRoot()
        
        #If the user has already pressed the OK button and some text is updated,
        #we need to check all other elements and update the main window 
        #notifications accordingly.
        if self.root.okpressed == True:
            self.root.updateRequirementNotification()
            
            if self.root.elementIsRequired(self):
                if self.requirementsMet():
                    self.setBGcolorSatisfied(True)
                else:
                    self.setBGcolorSatisfied(False)
            else:
                self.setBGcolorSatisfied(True)
            
        #This function attempts to enable or disable elements as appropriate.
        self.root.recursiveToggle(self.attributes['id'])
        
                    
    def setValidateField(self, regexp):
        """Set input validation on the text field to conform with the input
            regular expression.  Validation takes place continuously, so the 
            user will be unable to enter text in this field unless it conforms
            to the regexp.
            
            regexp - a string regular expression
            
            returns nothing"""

        regexpObj = QtCore.QRegExp(regexp)
        validator = QtGui.QRegExpValidator(regexpObj, self.textField)
        self.textField.setValidator(validator)
        
    def requirementsMet(self):
        """Determine whether the textfield is considered 'complete'.
            This is used to determine whether a dependent element should be
            enabled or disabled and may need to be reimplemented for a subclass
            as new text-based elements arise.
            
            As a basic form of completion, we assume that this field is 
            satisfied when some text (any text) has been entered.
            
            returns a boolean"""
            
        if len(self.value()) > 0:
            return True
        else:
            return False
        
    def setBGcolorSatisfied(self, satisfied=True):
        """Color the background of this element's label.
            
            satisfied=True - a boolean, indicating whether this element's
                requirements have been satisfied.
            
            returns nothing"""
            
        if satisfied:
            self.label.setStyleSheet("QWidget { color: black }")
            self.textField.setStyleSheet("QWidget {}")
        else:
            self.label.setStyleSheet("QWidget { color: red }")
            self.textField.setStyleSheet("QWidget { border: 1px solid red } ")
        
    def parentWidget(self):
        """Return the parent widget of one of the QWidgets of this object.
        
            Because DynamicText objects by definition have at least two widgets
            which individually could be added to separate layouts of separate 
            widgets, it is necessary to specify which local widget we wish to 
            identify as having the parent.
            
            In this case, self.textField has been selected.
            
            returns a pointer to an instance of a QWidget."""
            
        return self.textField.parentWidget()
        
    def isEnabled(self):
        """Check to see if this element is 'enabled'.
        
            This status is commonly used to determine whether other fields 
            should be enabled or disabled (to allow or prevent the user from 
            interacting with the widget)
        
            This is tested by checking the length of the string entered into 
            self.textField.  Specific implementations may differ as appropriate
            to the subclass.
            
            returns a boolean."""
            
        return self.textField.isEnabled()
        
    def value(self):
        """Fetch the value of the user's input, stored in self.textField.
        
            returns a string."""
        return self.textField.text()
    
    def setValue(self, text):
        """Set the value of self.textField.
        
            text - a string, the text to be inserted into self.textField.
            
            returns nothing."""
            
        self.textField.setText(text)
        
        
        
class ModelDialog(QtGui.QDialog):
    """ModelDialog is a class defining a modal window presented to the user
        while the model is running.  This modal window prevents the user from
        interacting with the main UI window while the model is processing and 
        provides status updates for the model.
        
        This window is not configurable through the JSON configuration file."""    
        
    def __init__(self, uri, inputDict, modelname):
        """Constructor for the ModelDialog class.
            
            uri - a string URI to the script to be run
            inputDict - a python dictionary of arguments to be passed to the 
                model's execute function.
        
            returns an instance of ModelDialog."""
        super(ModelDialog, self).__init__()

        #set window attributes
        self.setLayout(QtGui.QVBoxLayout())
        self.setWindowTitle("Running the model")
        self.setGeometry(400, 400, 700, 400)
        
        self.cancel = False

        #create statusArea-related widgets for the window.        
        self.statusAreaLabel = QtGui.QLabel('Messages:')
        self.statusArea = QtGui.QPlainTextEdit()
        self.statusArea.setReadOnly(True)

        #set the background color of the statusArea widget to be white.
        self.statusArea.setStyleSheet("QWidget { background-color: White }")

        #create an indeterminate progress bar.  According to the Qt 
        #documentation, an indeterminate progress bar is created when a 
        #QProgressBar's minimum and maximum are both set to 0.
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)

        #Add the new widgets to the window
        self.layout().addWidget(self.statusAreaLabel)
        self.layout().addWidget(self.statusArea)
        self.layout().addWidget(self.progressBar)


        #create Quit and Cancel buttons for the window        
        self.runButton = QtGui.QPushButton('Quit')
        self.cancelButton = QtGui.QPushButton('Cancel') 
        
        #disable the 'Quit' button by default
        self.runButton.setDisabled(True)
       
        #create the buttonBox (a container for buttons) and add the buttons to
        #the buttonBox.
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(self.runButton, 0)
        self.buttonBox.addButton(self.cancelButton, 1)
        
        #connect the buttons to their callback functions.
        self.runButton.clicked.connect(self.okPressed)
        self.cancelButton.clicked.connect(self.closeWindow)

        #add the buttonBox to the window.        
        self.layout().addWidget(self.buttonBox)
        
        #Run the model if possible.  If we encounter an error running the model,
        #print the error message to the modal window.
        try:
            self.errors = []
            self.validatorThread = processThread(modelname, inputDict, self.errors)
            self.validatorThread.finished.connect(self.startQProcess)
                
            #run the model as separate QProcess.
            self.modelProcess = QtCore.QProcess()
            
            #connect the read stdout/stderr signals from the QProcess to their
            #callback functions.
            self.modelProcess.readyReadStandardOutput.connect(self.readOutput)
            self.modelProcess.readyReadStandardError.connect(self.readError)
            
            #when the modelProcess is finished, run self.threadFinished.
            self.modelProcess.finished.connect(self.threadFinished)
            
            #specify the path to the python executeable.  This is uniform across
            #all models at the moment.
            if platform.system() == 'Windows':
                command = './OSGeo4W/gdal_python_exec.bat'
            else:
                command = 'python'

            #create a QStringlist to hold the arguments to the QProcess.
            argslist = QtCore.QStringList()
            argslist.append(QtCore.QString(uri))
            argslist.append(QtCore.QString(json.dumps(inputDict)))
            
            self.command = command
            self.argslist = argslist
            
            #Start the thread immediately after opening this dialog.
            QtCore.QTimer.singleShot(50, self.startValidation)

        except ImportError:
            self.modelProcess = None
            self.write("Error running the model: "+ str(ImportError))
            self.threadFinished()
        except IOError:
            self.modelProcess.terminate()
            self.modelProcess = None
            self.write('Error locating file: ' + str(uri))
            self.write('current location: ' + str(os.getcwd()))
            self.threadFinished()

    def startQProcess(self):
        if len(self.errors) > 0:
            self.write('Errors detected while validating inputs:\n')
            for error in self.errors:
                self.write(error)
            self.threadFinished()
        else:
            self.write('Validation complete.\n')
            self.modelProcess.start(self.command, self.argslist)

    def startValidation(self):
        """Write a short status message to the notifications area and start
            the input validation thread.
            
            This function is a callback and is called immediately after the 
            modal window is shown.
            
            returns nothing"""
            
        self.write('Validating inputs.\n')
        self.validatorThread.start()
        
        
    def write(self, text):
        """Write text to the statusArea.
            
            text - a string to be written to self.statusArea.
            
            returns nothing."""
            
        self.statusArea.insertPlainText(QtCore.QString(text))
        
    def readOutput(self):
        """Write all available stdout from self.modelProcess, a QProcess, to the 
            notifications area of the modal window.  This function is a callback
            ('slot') for the QProcess readyReadStandardOutput signal.
            
            returns nothing"""
            
        self.write(self.modelProcess.readAllStandardOutput())

    def readError(self):
        """Write all available stderr from self.modelProcess, a QProcess, to the
            notifications area of the modal window.  This function is a callback
            ('slot') for the QProcess readyReadStandardError signal.
            
            returns nothing"""
            
        self.write(self.modelProcess.readAllStandardError())
                
    def threadFinished(self):
        """Notify the user that model processing has finished.
        
            returns nothing."""
            
        self.write('\n\nComplete.') #prints a status message in the statusArea.
        self.progressBar.setMaximum(1) #stops the progressbar.
        self.runButton.setDisabled(False) #enables the runButton
        self.stdoutNotifier=None

    def closeEvent(self, data=None):
        """When a closeEvent is detected, run self.closeWindow().
        
            returns nothing."""
            
        self.closeWindow()
        
    def okPressed(self):
        """When self.runButton is pressed, halt the statusbar and close the 
            window with a siccessful status code.
            
            returns nothing."""
            
        self.threadFinished()
        self.accept() # this is a built-in Qt signal.
        
    def closeWindow(self):
        """Close the window and ensure the modelProcess has completed.
        
            returns nothing."""
        
        self.stdoutNotifier = None
        if self.modelProcess != None:
            self.modelProcess.terminate()
        self.cancel = True
        self.done(0)
        
class processThread(QtCore.QThread):
    """Class processThread loads a python module from source and runs its
        execute function with the provided inputDict as input and writes errors
        to the python list outputList."""
    
    def __init__(self, modelname, inputDict, outputList):
        """Constructor for the processThread class.
        
            modelname - the string name of the InVEST model being currently run.
                        Used to get the correct validator file from source.
            inputDict - A python dictionary of arguments to the validator.
            outputList- A pointer to a python list.  Used for returning error
                        messages to the modal window.
                        
            returns an instance of the processThread class."""
            
        super(processThread, self).__init__()
        self.inputDict = inputDict
        self.outputList = outputList
        self.modelname = modelname
        
    def run(self):
        """Imports the desired model's validator and execute it.  If an error is
            detected, errors are appended to self.outputList.
        
            This is a custom implementation of the Qt-defined function run().
            This function is invoked when self.start() is called.
            
            returns nothing"""
            
        #cmd_folder is declared at the very beginning of this file.  It 
        #contains the absolute path to the current file (iui_main.py).
        path = cmd_folder + '/../invest_core/' + self.modelname + '_validator.py'
        try:
            model = imp.load_source('validator', path)
            self.outputList = model.execute(self.inputDict, self.outputList)
        except IOError:
            self.outputList.append('Could not locate validator at ' + 
                                   os.path.abspath(path))
            
        

class DynamicUI(DynamicGroup):
    def closeWindow(self):
        """Terminates the application.
        
            This function is called when the user closes the window by any of
            Qt's recognized methods (often including closing the window via the
            little x in the corner of the window and/or pressing the Esc key).
        
            returns nothing"""
        
        print 'Cancelled.'
        sys.exit(0)

    def saveLastRun(self):
        """Saves the current values of all input elements to a JSON object on 
            disc.
            
            returns nothing"""
        
        user_args = {}
        
        #loop through all elements known to the UI, assemble into a dictionary
        #with the mapping element ID -> element value
        for id, element in self.allElements.iteritems():
            if isinstance(element, DynamicPrimitive):
                user_args[id] = str(element.value())
                
        #create a file in the current directory
        user_args_file = open(cmd_folder + '/' + self.attributes['modelName'] +
                              '_args_lastrun.json', 'w')
        
        #save a json rendition of the arguments dictionary to the newly opened
        #file
        user_args_file.writelines(json.dumps(user_args))
        user_args_file.close()
        
        
    def elementIsRequired(self, element):
        """Check to see if an element is required.
        
            An element is required if element.required == True or if the element
            has a 'requiredIf' attribute and at least one of the elements in the 
            'requiredIf' array is required.
        
            element - a pointer to an instance of DynamicElement.
            
            returns a boolean"""
        
        #if an element is declared to be required, it's always required    
        if element.required:
            return True
        
        #otherwise, we check to see if the element can be made required by other
        #elements.  If so, we check on its status.  If not, the element is not
        #required.
        else:
            
            #The 'requiredIf' element is optional, so if the attribute is
            #provided, we need to check its array contents.
            if 'requiredIf' in element.attributes:
                for item in element.attributes['requiredIf']:
                    
                    #if even one of the elements in the 'requiredIf' array is
                    #enabled, the current element is required.
                    if self.allElements[item].requirementsMet():
                        return True
            
            #if we find no elements making this element required, this element
            #is optional.
            return False
        
    def assembleOutputDict(self):
        """Assemble an output dictionary for use in the target model
        
            Saves a python dictionary to self.outputDict.  This dictionary has
            the mapping: element args_id -> element value.  Values are converted
            to their appropriate dataType where specified in the JSON config
            file.
        
            returns nothing"""
        
        for id, element in self.allElements.iteritems():

            #All input elements are instances of DynamicPrimitive, so we ignore
            #any elements not decended from DynamicPrimitive.
            if isinstance(element, DynamicPrimitive):

                #The args_id element is optional in the JSON config file.  If
                #provided, we use it to assemble the output dictionary
                if 'args_id' in element.attributes:
                    #We don't want to assemble disabled elements, as the model
                    #may run differently given the presence or absence of 
                    #elements
                    if element.isEnabled() == True:
                        #If the user has not specified a value for this element,
                        #we don't need to bother casting it to any other type.
                        #element.value() returns a QString, so we need to cast
                        #to a python string.
                        value = str(element.value())
                        if value != '':
                            #if the user has specified a dataType in the JSON config,
                            #ensure the data is casted appropriately.
                            if 'dataType' in element.attributes:
                                if element.attributes['dataType'] == 'int':
                                    value = int(value)
                                elif element.attributes['dataType'] == 'float':
                                    value = float(value)
                                else:
                                    value = str(value)     
                            #If the user has not specified a dataType, cast from 
                            #QtCore.QString to python string.                   
                            else:
                                value = str(value)
                        
                        #save the value to the output Dictionary.
                        self.outputDict[element.attributes['args_id']] = value

    def updateRequirementNotification(self, numUnsatisfied=None):
        """Updates the QLabel at the bottom of the DynamicUI window to reflect
            the number of required elements missing input.
        
            numUnsatisfied=None - an int.  An optional parameter for cases where
                the number of unsatisfied elements is already calculated before
                this method is called.
            
            returns nothing"""
        
        #if the user did not provide an input number of unsatisfied elements,
        #fetch that number.    
        if numUnsatisfied == None:
            numUnsatisfied = self.countRequiredElements()
        
        #update the message to reflect the number of unsatisfied elements.
        if numUnsatisfied > 0:
            if numUnsatisfied == 1:
                string = '1 required element'
            else:
                string = str(numUnsatisfied) + ' required elements'
                
            self.messageArea.setText(string + ' missing input')
        else:
            self.messageArea.setText("")

    def countRequiredElements(self):
        """Count the number of required elements in self.allElements.
        
            An element is required if element.required == True or if the element
            has a 'requiredIf' attribute and at least one of the elements in the 
            'requiredIf' array is required.
            
            returns an int: the number of unsatisfied elements."""
            
        numRequired = 0 #the number of elements found to be required
        numVerified = 0 #the number of elements with satisfied requirement
        for id, element in self.allElements.iteritems():
            
            #Instances of DynamicPrimitive are the only elements that can
            #contain user input and thus the only elements that can effectively
            #have required input.
            if isinstance(element, DynamicPrimitive):
                
                if self.elementIsRequired(element):
                    numRequired += 1
                    if element.requirementsMet():
                        #if the element is satisfied, increment nunVerified
                        numVerified += 1
                    else:
                        #if the element is unsatisfied, color the label's 
                        #background accordingly. 
                        element.setBGcolorSatisfied(False)
                else:
                    if isinstance(element, DynamicText):
                        element.setBGcolorSatisfied(True)
        
        #return the number of unsatisfied required elements.
        return numRequired - numVerified

    def okPressed(self):
        """A callback, run when the user presses the 'OK' button.
        
            returns nothing."""
            
        self.okpressed = True
        self.messageArea.setText("")
        numUnsatisfied = self.countRequiredElements()
        
        #if some required element has not been satisfied, alert the user and 
        #return to the UI.  Otherwise (if the user has provided all required
        #inputs), run the model.
        if numUnsatisfied == 0:
            self.runProgram()
        else:
            self.updateRequirementNotification(numUnsatisfied)
            return #return to the previous state of the UI

    def runProgram(self):
        """Assembles output, saves user's parameters and runs the model 
            specified in the config file.
        
            returns nothing"""
            
        self.saveLastRun()
        self.assembleOutputDict()
        self.modelDialog = ModelDialog(self.attributes['targetScript'],
                                       self.outputDict,
                                       self.attributes['modelName'])
        
        #Run the modelDialog.
#        self.modelDialog.open()
        self.modelDialog.exec_()

        #if the user presses cancel (which sets modelDialog.cancel to True)
        #we should return to the UI.  Otherwise, quit the application.
        if self.modelDialog.cancel == False:
            QtCore.QCoreApplication.instance().exit()
    
    def closeEvent(self, event):
        """Terminates the application. This function is a Qt-defined callback 
            for when the window is closed.
            
            returns nothing"""
            
        sys.exit(0)
        
    def getLastRun(self, modelname):
        """Retrieve the user's last run from the json file (if it exists).
            The resulting dictionary is saved as self.lastRun.
        
            modelname - the string modelname specified in the JSON config file.
            
            returns nothing."""
        
        user_args_uri = cmd_folder + '/' + modelname + '_args_lastrun.json'
        try:
            self.lastRun = json.loads(open(user_args_uri).read())
        except IOError:
            self.lastRun = {}
            
    def __init__(self, uri):
        """Constructor for the DynamicUI class, a subclass of DynamicGroup.
            DynamicUI loads all setting from a JSON object at the provided URI
            and recursively creates all elements.
            
            uri - the string URI to the JSON configuration file.
            
            returns an instance of DynamicUI."""
            
        super(DynamicUI, self).__init__(json.loads(uri), QtGui.QVBoxLayout())
        self.lastRun = {}
        self.messageArea = QtGui.QLabel('')
        self.layout().addWidget(self.messageArea)
        self.okpressed = False
        self.outputDict = {}
        self.allElements = self.getElementsDictionary()
        self.layout().setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        
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
        
        #attempt to get saved arguments from the user's last run
        try:
            self.getLastRun(self.attributes['modelName'])
        except KeyError:
            print 'Modelname required in config file to load last run\'s arguments'
        
        self.initElements()
        self.addButtons()
        
        if 'width' in self.attributes:
            width = self.attributes['width']
        else:
            width = 400
            
        if 'height' in self.attributes:
            height = self.attributes['height']
        else:
            height = 400
        
        self.setGeometry(400, 400, width, height)
        
        #reveal the assembled UI to the user
        self.show()
                    
    def addButtons(self):
        """Assembles buttons and connects their callbacks.
        
            returns nothing."""
            
        self.runButton = QtGui.QPushButton('OK')
        self.cancelButton = QtGui.QPushButton('Cancel') 
       
        #create the buttonBox (a container for buttons)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(self.runButton, 0)
        self.buttonBox.addButton(self.cancelButton, 1)
        
        #connect the buttons to their functions.
        self.runButton.clicked.connect(self.okPressed)
        self.cancelButton.clicked.connect(self.closeWindow)

        #add the buttonBox to the window.        
        self.layout().addWidget(self.buttonBox)
                    
    def initElements(self):
        """Set the enabled/disabled state and text from the last run for all 
            elements
        
            returns nothing"""
            
        for elementID, elementObj in self.allElements.iteritems():
            try:
                #If an item is enabled by an element, its id is stored at 
                #element.enabledBy
                controller = elementObj.enabledBy
                if controller != None:
                    #enable or disable all elements controlled by controller
                    #depending on controller's state
                    if self.allElements[controller].isEnabled() == False:
                        elementObj.disable()
                    else:
                        elementObj.enable()
                        
                #Set the value for the current element from the user's last run.
                if isinstance(elementObj, DynamicPrimitive):
                    if elementID in self.lastRun:
                        elementObj.setValue(self.lastRun[elementID])
            
            #print an error if it is encountered.  In rare cases, 
            #element.enabledBy is not initialized properly.
            except AttributeError:
                print str(AttributeError)

    def recursiveToggle(self, controllingID):
        """Enable or disable all objects enabledBy controllingID based on 
            the state of the object identified by controllingID.
            
            controllingID - a string ID for an element.
        
            returns nothing"""
            
        controller = self.allElements[controllingID]
        for id, object in self.allElements.iteritems():
            enabledBy = object.enabledBy
        
            #If the current object is controlled by the controller, enable or
            #disable it and its dependents according to the state of the 
            #controller.
            if enabledBy == controllingID:
                if controller.isEnabled() == True:
                    object.enable()
                    self.recursiveSetState(id, True)
                else:
                    object.disable()
                    self.recursiveSetState(id, False)

    def recursiveSetState(self, controllingID, state=False):
        """Set the state of all elements controlled by controllingID or any 
            elements controlled by those elements, etc to the provided state.
            
            This function differs from recursiveToggle() in that the intention 
            is to set a specific state, not simply to toggle the state.
            
            returns nothing"""

        controller = self.allElements[controllingID]
        for id, object in self.allElements.iteritems():
            enabledBy = object.enabledBy
            if enabledBy == controllingID:
                
                #Disable this element an all elements enabledBy/disabledBy this
                #element.
                if state == False:
                    object.disable()
                    self.recursiveSetState(id, False)
                    
                #If we are to enable this element, first check to see that its
                #controller has been enabled.  If so, attempt to enable all
                #elements controlled by this element.
                else:
                    if controller.isEnabled() == True:
                        object.enable()
                        self.recursiveSetState(id, True)

class Container(QtGui.QGroupBox, DynamicGroup):
    """Class Container represents a QGroupBox (which is akin to the HTML widget
        'fieldset'.  It has a Vertical layout, but may be subclassed if a 
        different layout is needed."""
        
    def __init__(self, attributes):
        """Constructor for the Container class.
            
            attributes - a python dictionary containing all attributes of this
                container, including its elements.  Elements are initialized in
                DynamicGroup.createElements().
                
            returns an instance of Container."""
            
        super(Container, self).__init__(attributes, QtGui.QVBoxLayout())
        
        #set the title of the container
        self.setTitle(attributes['label'])

class CollapsibleContainer(Container):
    """Class CollapsibleContainer is a container whose elements can be shown
        and hidden at the whim of the user if the container's checkbox is
        toggled."""
        
    def __init__(self, attributes):
        """Constructor for the CollapsibleContainer class.
        
            attributes - a python dictionary containing all attributes of this
                container, including its elements.  Elements are initialized in 
                DynamicGroup.createElements().
                
            returns an instance of CollapsibleContainer"""
            
        super(CollapsibleContainer, self).__init__(attributes)
        
        #this attribute of QtGui.QGroupBox determines whether the container
        #will sport a hide/reveal checkbox.
        self.setCheckable(True)

        #Uncheck and hide contained elements by default.
        self.setChecked(False)
        for element in self.elements:
            element.setVisible(False)

        #connect the toggled() signal of the QGroupBox to its callback
        self.toggled.connect(self.toggleHiding)

    def toggleHiding(self):
        """Show or hide all sub-elements of this collapsible container as
            necessary.  This function is a callback for the toggled() signal.
            
            returns nothing."""
            
        for element in self.elements:
            if element.isVisible() == True:
                element.setVisible(False)
            else:
                element.setVisible(True)

class GridList(DynamicGroup):
    """Class GridList represents a DynamicGroup that has a QGridLayout as a 
        layout manager."""
        
    def __init__(self, attributes):
        """Constructor for the GridList class.
        
            attributes -a python dictionary containing all attributes of this 
                DynamicGroup, including the elements it contains.  Elements are
                initialized in DynamicGroup.createElements().
            
            returns an instance of the GridList class."""
            
        super(GridList, self).__init__(attributes, QtGui.QGridLayout())
        
        
class CheckBox(QtGui.QCheckBox, DynamicPrimitive):
    """This class represents a checkbox for our UI interpreter.  It has the 
        ability to enable and disable other elements."""
         
    def __init__(self, attributes):
        """Constructor for the CheckBox class.
 
            attributes - a python dictionary containing all attributes of this 
                checkbox as defined by the user in the json configuration file.
            
            returns an instance of CheckBox"""
            
        super(CheckBox, self).__init__(attributes)

        #set the text of the checkbox
        self.setText(attributes['label'])
        
        #connect the button to the toggle function.
        self.toggled.connect(self.toggle)
        
    def toggle(self):
        """Enable/disable all elements controlled by this element.
        
            returns nothing."""
            
        if self.root == None:
            self.root = self.getRoot()   
        
        self.root.updateRequirementNotification()
        self.root.recursiveToggle(self.attributes['id'])
        
    def isEnabled(self):
        """Check to see if this element is checked.
        
            returns a boolean"""
            
        return self.isChecked()
    
    def value(self):
        """Get the value of this checkbox.
        
            returns a boolean."""
        return self.isChecked()
    
    def setValue(self, value):
        """Set the value of this element to value.
            
            value - a string or boolean representing
            
            returns nothing"""
            
        if isinstance(value, unicode):
            if value == 'True':
                value = True
            else:
                value = False
        elif isinstance(value, boolean):
            self.setCheckState(value)
             
    def requirementsMet(self):
        return self.value()
             
class FileEntry(DynamicText):
    """This object represents a file.  It has three components, all of which
        are subclasses of QtGui.QWidget: a label (QtGui.QLabel), a textfield
        for the URI (QtGui.QLineEdit), and a button to engage the file dialog
        (a custom FileButton object ... Qt doesn't have a 'FileWidget' to 
        do this for us, hence the custom implementation)."""
        
    def __init__(self, attributes):
        """initialize the object"""
        super(FileEntry, self).__init__(attributes)
        self.button = FileButton(attributes['label'], self.textField, attributes['type'])
        self.elements = [self.label, self.textField, self.button]
        
        #expand the given relative path if provided
        if 'defaultText' in self.attributes:
            self.textField.setText(os.path.abspath(attributes['defaultText']))
        
class YearEntry(DynamicText):
    """This represents all the components of a 'Year' line in the LULC box.
        The YearEntry object consists of two objects: a label (QtGui.QLabel)
        and a year (QtGui.QLineEdit).  The year also has a min and max width."""
        
    def __init__(self, attributes):
        super(YearEntry, self).__init__(attributes)
        self.elements = [self.label, self.textField]

        #set the min and max width to clarify that this entry should be a 4-digit year
        self.textField.setMaximumWidth(70)
        self.textField.setMinimumWidth(40)


class FileButton(QtGui.QPushButton):
    """This object is the button used in the FileEntry object that, when
        pressed, will open a file dialog (QtGui.QFileDialog).  The string URI
        returned by the QFileDialog will be set as the text of the provided
        URIField.
        
        Arguments:
        text - the string text title of the popup window.
        URIField - a QtGui.QLineEdit.  This object will receive the string URI
            from the QFileDialog."""
        
    def __init__(self, text, URIfield, filetype='file'):
        super(FileButton, self).__init__()
        self.text = text
        self.setIcon(QtGui.QIcon(cmd_folder + '/document-open.png'))
        self.URIfield = URIfield
        self.filetype = filetype
        
        #connect the button (self) with the filename function.
        self.clicked.connect(self.getFileName)
        
    def getFileName(self, filetype='file'):
        """Get the URI from the QFileDialog.
        
            If the user presses OK in the QFileDialog, the dialog returns the
            URI to the selected file.
            
            If the user presses 'Cancel' in the QFileDialog, the dialog returns
            ''.  As a result, we must first save the previous contents of the 
            QLineEdit before we open the dialog.  Then, if the user presses
            'Cancel', we can restore the previous field contents."""
        
        oldText = self.URIfield.text()
        filename = ''
        
        if self.filetype =='file':
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Select ' + self.text, '.')
        elif self.filetype == 'folder':
            filename = QtGui.QFileDialog.getExistingDirectory(self, 'Select ' + self.text, '.')

        #Set the value of the URIfield.
        if filename == '':
            self.URIfield.setText(oldText)
        else:
            self.URIfield.setText(filename)



def validate(jsonObject):
    """Validates a string containing a JSON object against our schema.  Uses the
        JSONschema project to accomplish this. 
        
        jsonschema draft specification: 
            http://tools.ietf.org/html/draft-zyp-json-schema-03
            
        jsonschema project sites:
            http://json-schema.org/implementations.html
            http://code.google.com/p/jsonschema/
            
        arguments:
        jsonObject - a string containing a JSON object.
        
        returns nothing."""
    
    data = json.loads(jsonObject)
    
    primitives = {"type" : "object",
                 "properties": {
                    "id":{"type" : "string",
                          "optional": False},
                    "args_id": {"type" : "string",
                                "optional": True},
                    "type": {"type": "string",
                             "pattern": "^((file)|(folder)|(text)|(checkbox))$"},
                    "label": {"type": "string",
                              "optional": True},
                    "defaultText": {"type": "string",
                                    "optional": True},
                    "required":{"type": "boolean",
                                "optional" : True},
                    "validText": {"type": "string",
                                  "optional": True},
                    "dataType": {"type" : "string",
                                 "optional": True},
                    "requiredIf":{"type": "array",
                                  "optional": True,
                                  "items": {"type": "string"}
                                  }
                    }
                }

    lists = {"type": "object",
             "properties":{
               "id": {"type": "string",
                      "optional": False},
                "type": {"type": "string",
                         "optional": False,
                         "pattern": "^list$"},
                "elements": {"type": "array",
                             "optional": True,
                             "items": {
                               "type": primitives
                               }
                             }
               }
             }
    
    containers = {"type": "object",
                  "properties": {
                     "id": {"type": "string",
                            "optional" : False},
                     "type":{"type": "string",
                             "optional": False,
                             "pattern": "^container$"},
                     "collapsible": {"type": "boolean",
                                     "optional": False},
                     "label": {"type": "string",
                               "optional": False},
                     "elements":{"type": "array",
                                 "optional": True,
                                 "items": {
                                   "type": [lists, primitives]
                                   }
                                 }
                     }
                  }

    elements = {"type": "array",
                "optional": True,
                "items": {
                   "type":[primitives, lists, containers]
                   }
                }

#, lists, containers

    schema = {"type":"object",
              "properties":{
                "id": {"type": "string",
                       "optional": False},
                "label": {"type" : "string",
                          "optional" : False},
                "targetScript": {"type" : "string",
                                 "optional": False},
                "height": {"type": "integer",
                           "optional": False},
                "width": {"type": "integer",
                          "optional": False},
                "elements": elements
                }
              }
    try:
        jsonschema.validate(data, schema)
    except ValueError:
        print 'Error detected in your JSON syntax: ' + str(ValueError)
        print 'Exiting.'
        sys.exit()

def main(json_args):
    app = QtGui.QApplication(sys.argv)
    validate(json_args)
    ui = DynamicUI(json_args)
    result = app.exec_()

        
if __name__ == '__main__':
    modulename, json_args = sys.argv

    args = open(json_args)

    main(args.read())