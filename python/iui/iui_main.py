import sys, os, imp
from PyQt4 import QtGui, QtCore


cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../invest_core')

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
            
        return {self.id : self}
    
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
        
        #Connect the textfield's textChanged signal to the toggle() function.
        #This function will trigger any time the user changes the text in the
        #textfield.
        self.textField.textChanged.connect(self.toggle)
            
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
            self.setBGcolor()
        
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
        
    def setBGcolor(self):
        """Check to see if the current element's requirements have been met.
            If not, we color the background of the label red to signify an 
            error.
            
            returns nothing"""
        if self.requirementsMet():
            self.label.setStyleSheet("QWidget { background-color: None }")
        else:
            self.label.setStyleSheet("QWidget { background-color: Red }")
        
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
            
        if len(self.textField.text()) > 0:
            return True
        else:
            return False
        
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
        
    def __init__(self, uri, inputDict):
        """Constructor for the ModelDialog class.
            
            uri - a string URI to the script to be run
            inputDict - a python dictionary of arguments to be passed to the 
                model's execute function.
        
            returns an instance of ModelDialog."""
        super(ModelDialog, self).__init__()

        #set window attributes
        self.setLayout(QtGui.QVBoxLayout())
        self.setWindowTitle("Running the model")
        self.setGeometry(400, 400, 400, 400)
        
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
        
        #set up an instance of StdoutNotifier to capture all stdout.
        self.stdoutNotifier = StdoutNotifier(0, QtCore.QSocketNotifier.Read, self)

        #tell python to run all stdout and stderr through the StdoutNotifier.
        sys.stdout = self.stdoutNotifier
        sys.stderr = sys.stdout
        
        #When the notifier detects text in stdout, it should run the callback
        #self.write.
        self.connect(self.stdoutNotifier, QtCore.SIGNAL("activated(int)"), self.write)
        
        #Run the model if possible.  If we encounter an error running the model,
        #print the error message to the modal window.
        try:
            model = imp.load_source('module', uri)
            self.thread = ModelThread(model, inputDict)
            
            #when the thread is finished, run self.threadFinished.
            self.thread.finished.connect(self.threadFinished)
            
            #start the thread
            self.thread.start()
            
        except ImportError as e:
            self.thread = None
            self.write("Error running the model: "+ str(e))
            self.threadFinished()

    def write(self, text):
        """Write text to the statusArea.
            
            text - a string to be written to self.statusArea.
            
            returns nothing."""
            
        self.statusArea.insertPlainText('\n' + text)
        
    def threadFinished(self):
        """Notify the user that model processing has finished.
        
            returns nothing."""
            
        print 'Completed.' #prints a status message in the statusArea.
        self.progressBar.setMaximum(1) #stops the progressbar.
        self.runButton.setDisabled(False) #enables the runButton

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
        """Close the window and ensure the thread has completed.
        
            returns nothing."""
        
        self.stdoutNotifier = None
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        if self.thread != None:
            self.thread.__del__()
        self.cancel = True
        self.done(0)

class StdoutNotifier(QtCore.QSocketNotifier):
    """The QtCore.QSocketNotifier class allows us to listen for and receive
        text written to a socket or file descriptor.  It is aware of a parent 
        object to which text should be written."""
        
    def __init__(self, socket, type, parent):
        """Constructor for the StdoutNotifier class.
        
            socket - an int representing a socket number
            type - an int represented by one of the following (from Qt docs):
                Constant indentifier      Value    Description
                -----------------------------------------------------------
                QSocketNotifier.Read      0        There is data to be read
                QSocketNotifier.Write     1        Data can be written
                QSocketNotifier.Exception 2        An exception has occurred
                
            parent - a reference to the parent object.  The parent object must
                have an implemented self.write() method.
        
            returns an instance of StdoutNotifier"""
            
        super(StdoutNotifier, self).__init__(socket, type)
        self.setParent(parent)
        
    def write(self, text):
        """Write text to the parent's write method.
        
            text - the python string to be written.
            
            returns nothing."""
            
        self.parent().write(text)
        

class ModelThread(QtCore.QThread):
#class ModelThread(QtCore.QProcess):
    def __init__(self, model, inputDict):
        super(ModelThread, self).__init__()
        self.model = model
        self.inputDict = inputDict

    def __del__(self):
        self.terminate()
        #put code here to ensure the thread finishes processing when destroyed
        return
    
    def run(self):
        #this is called by the thread once the environment is set up.
        self.model.execute(self.inputDict)
        

class DynamicUI(DynamicGroup):
    def closeWindow(self):
        """exits the entire application, bypassing even the main() function"""
        
        print 'Cancelled.'
        sys.exit(0)

    def saveLastRun(self):
        user_args = {}
        for id, element in self.allElements.iteritems():
            if isinstance(element, DynamicPrimitive):
                user_args[id] = str(element.value())
                
        user_args_file = open(self.attributes['modelName'] +
                              '_args_lastrun.json', 'w')
        user_args_file.writelines(json.dumps(user_args))
        user_args_file.close()
        
    def elementIsRequired(self, element):
        if element.required:
            return True
        else:
            if 'requiredIf' in element.attributes:
                for item in element.attributes['requiredIf']:
                    if self.allElements[item].isEnabled():
                        return True
            return False
        
    def assembleOutputDict(self):
        for id, element in self.allElements.iteritems():
            if isinstance(element, DynamicPrimitive):
                if 'args_id' in element.attributes:
                    if 'dataType' in element.attributes:
                        if element.attributes['dataType'] == 'int':
                            value = int(element.value())
                        elif element.attributes['dataType'] == 'float':
                            value = float(element.value())
                        else:
                            value = str(element.value())                            
                    else:
                        value = str(element.value())
                    self.outputDict[element.attributes['args_id']] = value

    def updateRequirementNotification(self, numUnsatisfied=None):
        if numUnsatisfied == None:
            numUnsatisfied = self.countRequiredElements()
        
        if numUnsatisfied > 0:
            self.messageArea.setText(str(numUnsatisfied) + ' required elements missing input')
        else:
            self.messageArea.setText("")

    def countRequiredElements(self):
        numRequired = 0 #the number of elements found to be required
        numVerified = 0 #the number of elements with satisfied requirement
        self.messageArea.setText("")
        for id, element in self.allElements.iteritems():
            if isinstance(element, DynamicPrimitive):
                if self.elementIsRequired(element):
                    numRequired += 1
                    if element.requirementsMet():
                        numVerified += 1
                    else:
                        element.setBGcolor()
                        
        return numRequired - numVerified

    def okPressed(self):
        self.okpressed = True
        numUnsatisfied = self.countRequiredElements()
        
        if numUnsatisfied == 0:
            self.runProgram()
        else:
            self.updateRequirementNotification(numUnsatisfied)
            return #return to the previous state of the UI

    def runProgram(self):
        """Quit the UI, returning to the main() function"""
        self.saveLastRun()
        self.assembleOutputDict()
        self.modelDialog = ModelDialog(self.attributes['targetScript'], self.outputDict)
        
        self.modelDialog.exec_()
        if self.modelDialog.cancel == False:
            QtCore.QCoreApplication.instance().exit()
    
    def closeEvent(self, event):
        sys.exit(0)
        
    def getLastRun(self, modelname):
        user_args_uri = modelname + '_args_lastrun.json'
        try:
            self.lastRun = json.loads(open(user_args_uri).read())
        except IOError:
            self.lastRun = {}
            

        
    def __init__(self, uri):
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
        try:
            self.setWindowTitle(self.attributes['label'])
        except KeyError:
            self.setWindowTitle('InVEST')
        
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
        self.show()
                    
    def addButtons(self):
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
        for elementID, elementObj in self.allElements.iteritems():
            try:
                controller = elementObj.enabledBy
                if controller != None:
                    if self.allElements[controller].isEnabled() == False:
                        elementObj.disable()
                    else:
                        elementObj.enable()
                if isinstance(elementObj, DynamicPrimitive):
                    if elementID in self.lastRun:
                        elementObj.setValue(self.lastRun[elementID])
            except AttributeError as e:
                print e

    def recursiveToggle(self, controllingID):
        controller = self.allElements[controllingID]
        for id, object in self.allElements.iteritems():
            enabledBy = object.enabledBy
            if enabledBy == controllingID:
                if controller.isEnabled() == True:
                    object.enable()
                    self.recursiveSetState(id, True)
                else:
                    object.disable()
                    self.recursiveSetState(id, False)

    def recursiveSetState(self, controllingID, state = False):
        """False means disable; true means enable"""
        controller = self.allElements[controllingID]
        for id, object in self.allElements.iteritems():
            enabledBy = object.enabledBy
            if enabledBy == controllingID:
                if state == False:
                    object.disable()
                    self.recursiveSetState(id, False)
                else:
                    if controller.isEnabled() == True:
                        object.enable()
                        self.recursiveSetState(id, True)

class Container(QtGui.QGroupBox, DynamicGroup):
    def __init__(self, attributes):
        super(Container, self).__init__(attributes, QtGui.QVBoxLayout())
        self.setTitle(attributes['label'])

class CollapsibleContainer(Container):
    def __init__(self, attributes):
        super(CollapsibleContainer, self).__init__(attributes)
        self.setCheckable(True)

        #Uncheck and hide contained elements by default.
        self.setChecked(False)
        for element in self.elements:
            element.setVisible(False)

        self.toggled.connect(self.toggleHiding)

    def toggleHiding(self):
        for element in self.elements:
            if element.isVisible() == True:
                element.setVisible(False)
            else:
                element.setVisible(True)

class GridList(DynamicGroup):
    def __init__(self, attributes):
        super(GridList, self).__init__(attributes, QtGui.QGridLayout())
        
        
class CheckBox(QtGui.QCheckBox, DynamicPrimitive):
    """This class represents the checkboxes used.  Because of the 
        enable/disable requirement, this implementation is necessary.
        
        Arguments:
        text - the string used for the checkbox's label."""
         
    def __init__(self, attributes):
        super(CheckBox, self).__init__(attributes)

        #set the text of the checkbox
        self.setText(attributes['label'])
        
        #connect the button to the toggle function.
        self.toggled.connect(self.toggle)
        
    def toggle(self):
        if self.root == None:
            self.root = self.getRoot()   
        
        self.root.recursiveToggle(self.attributes['id'])
        
    def isEnabled(self):
        return self.isChecked()
    
    def value(self):
        return self.isChecked()
    
    def setValue(self, value):
        if isinstance(value, unicode):
            if value == 'True':
                value = True
            else:
                value = False
        elif isinstance(value, boolean):
            self.setChecked(value)
             
class FileEntry(DynamicText):
    """This object represents a file.  It has three components, all of which
        are subclasses of QtGui.QWidget: a label (QtGui.QLabel), a textfield
        for the URI (QtGui.QLineEdit), and a button to engage the file dialog
        (a custom FileButton object ... Qt doesn't have a 'FileWidget' to 
        do this for us, hence the custom implementation)."""
        
    def __init__(self, attributes):
        """initialize the object"""
        super(FileEntry, self).__init__(attributes)
        self.button = FileButton('...', self.textField, attributes['type'])
        self.elements = [self.label, self.textField, self.button]
        
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
        text - the string text of the QPushButton itself.
        URIField - a QtGui.QLineEdit.  This object will receive the string URI
            from the QFileDialog."""
        
    def __init__(self, text, URIfield, filetype='file'):
        super(FileButton, self).__init__()
        self.setText(text)
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
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.')
        elif self.filetype == 'folder':
            filename = QtGui.QFileDialog.getExistingDirectory(self, 'Select folder', '.')

        #Set the value of the URIfield.
        if filename == '':
            self.URIfield.setText(oldText)
        else:
            self.URIfield.setText(filename)



def validate(jsonObject):
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
    except ValueError as e:
#        print e
        print 'Error detected in your JSON syntax.\nExiting.'
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