import sys, os

cmd_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cmd_folder + '/../invest_core')

from PyQt4 import QtGui, QtCore
import simplejson as json
import jsonschema
import imp

class DynamicElement(QtGui.QWidget):
    def __init__(self, attributes):
        super(DynamicElement, self).__init__()
        self.attributes = attributes
        self.root = None
        self.required = False
        self.setEnabledBy()
        self.elements = []

    def setEnabledBy(self):
        if 'enabledBy' in self.attributes:
            self.enabledBy = self.attributes['enabledBy']
        else:
            self.enabledBy = None
            
    def getRoot(self):
        parent = self.parentWidget()
        if isinstance(parent, DynamicUI):
            return parent
        else:
            return parent.getRoot()
        
    def value(self):
        return None
    

        
class DynamicGroup(DynamicElement):
    def __init__(self, attributes, layout):
        super(DynamicGroup, self).__init__(attributes)
        self.setLayout(layout)
        self.createElements(attributes['elements'])
        
    def createElements(self, elementsArray):
        i = 0
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

            if isinstance(self.layout(), QtGui.QGridLayout):
                j = 0
                for subElement in widget.elements:
                    self.layout().addWidget(subElement, i, j)
                    j += 1
            else:
                self.layout().addWidget(widget)
                if isinstance(widget, DynamicText):
                    print widget
                    print widget.textField.text()

            self.elements.append(widget)
            i += 1

    def getElementsDictionary(self):
        """replacement for getTrackedElements"""
        outputDict = {}
        for element in self.elements:
            outputDict[element.attributes['id']] = element
            try:
                outputDict.update(element.getElementsDictionary())
            except AttributeError:
                pass
            
        return outputDict
    
    def enable(self):
        for element in self.elements:
            element.enable()
            
    def disable(self):
        for element in self.elements:
            element.disable()
    
    def isEnabled(self):
        return self.enabled

class DynamicPrimitive(DynamicElement):
    def __init__(self, attributes):
        super(DynamicPrimitive, self).__init__(attributes)
        self.attributes = attributes
        self.elements = [self]

        if "args_id" in attributes:
            self.args_id = attributes['args_id']
        else:
            self.args_id = None
            
    def getElementsDictionary(self):
        return {self.id : self}
    
    def enable(self):
        for element in self.elements:
            element.setDisabled(False)

    def disable(self):
        for element in self.elements:
            element.setDisabled(True)
            
class DynamicText(DynamicPrimitive):
    def __init__(self, attributes):
        super(DynamicText, self).__init__(attributes)
        self.label = QtGui.QLabel(attributes['label'])
        self.textField = QtGui.QLineEdit()
        
        if "required" in attributes:
            self.required = attributes['required']
            
        if "defaultText" in attributes:
            self.textField.insert(attributes['defaultText'])

        if 'validText' in attributes:
            self.setValidateField(attributes['validText'])
            
    def setValidateField(self, regexp):
        """field is a QWidget to be set as the widget to be validated
            regexp is a string representing the regexp to be evaluated"""

        regexpObj = QtCore.QRegExp(regexp)
        validator = QtGui.QRegExpValidator(regexpObj, self.textField)
        self.textField.setValidator(validator)
        
    def requirementsMet(self):
        if len(self.value()) > 0:
            return True
        else:
            return False
        
    def setBGcolor(self):
        if self.requirementsMet():
            self.label.setStyleSheet("QWidget { background-color: None }")
        else:
            self.label.setStyleSheet("QWidget { background-color: Red }")
        
    def parentWidget(self):
        return self.textField.parentWidget()
        
    def isEnabled(self):
        if len(self.textField.text()) > 0:
            return True
        else:
            return False
        
    def value(self):
        return self.textField.text()
    
    def setValue(self, text):
        self.textField.setText(text)

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
        self.setWindowTitle(self.attributes['label'])
        self.getLastRun(self.attributes['modelName'])
        self.initElements()
        self.addButtons()
        
        self.setGeometry(400, 400, self.attributes['width'], self.attributes['height'])
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
        
        self.textField.textChanged.connect(self.toggle)
            
    def toggle(self):
        if self.root == None:
            self.root = self.getRoot()   
        
        if self.root.okpressed == True:
            self.root.updateRequirementNotification()
            self.setBGcolor()
        
        self.root.recursiveToggle(self.attributes['id'])
        

    
    
class YearEntry(DynamicText):
    """This represents all the components of a 'Year' line in the LULC box.
        The YearEntry object consists of two objects: a label (QtGui.QLabel)
        and a year (QtGui.QLineEdit).  The year also has a min and max width."""
        
    def __init__(self, attributes):
        super(YearEntry, self).__init__(attributes)
        self.elements = [self.label, self.textField]

        self.textField.textChanged.connect(self.toggle)

        #set the min and max width to clarify that this entry should be a 4-digit year
        self.textField.setMaximumWidth(70)
        self.textField.setMinimumWidth(40)
        
    def toggle(self):
        if self.root == None:
            self.root = self.getRoot()   
        
        if self.root.okpressed == True:
            self.root.updateRequirementNotification()
            self.setBGcolor()
        
        self.root.recursiveToggle(self.attributes['id'])


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

    try:
        model = imp.load_source('module', ui.attributes['targetScript'])
        model.execute(ui.outputDict)
    except IOError:
        print "Error: Script provided in configuration file is invalid."
        
if __name__ == '__main__':
    modulename, json_args = sys.argv

    args = open(json_args)

    main(args.read())