import sys
import imp
import os
import time

from PyQt4 import QtGui, QtCore

import iui_validator
import executor
import registrar
import fileio

#This is for something
CMD_FOLDER = '.'
INVEST_ROOT = './'

class DynamicElement(QtGui.QWidget):
    """Create an object containing the skeleton of most functionality in the
        UI Interpreter's related classes.  It is not invoked directly by other
        IUI classes, but is instead used as a base class for almost all classes
        in the UI interpreter.  A diagram of this class heirarchy can be found
        at https://docs.google.com/drawings/d/13QZ6SsUwvoBPjvr0gf_X1X20sc35tLTr9oedX1vaUh8/edit
        
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
        QtGui.QWidget.__init__(self)

        #save a copy of the user-defined attributes for this element.  Based
        # on the specification of the JSON config file, the attributes array 
        #may contain the attributes for other, to-be-created, elements.
        self.attributes = attributes

        #We initialize self.required as False here, since some widgets may not
        #actually be input elements.  This ensures that all widgets will be 
        #marked optional unless specified by the user.
        if 'required' in self.attributes:
            self.required = self.attributes['required']

        #These attributes are set in self.updateLinks()
        self.root = None #a pointer to the root of this UI
        self.enabledBy = None #a pointer to an element, if an ID is specified.
        self.enables = [] #a list of pointers
        self.requiredIf = [] #a list of pointers

        #initialize the elements array in case the user has defined sub-elements
        self.elements = []

    def getRoot(self):
        """Search up the Qt widget tree until we find the root element, which
            is by definition an instance of the class DynamicUI.  A pointer to
            the root is usually saved to the local object as self.root.
            
            returns a pointer to the instance of DynamicUI"""

        parent = self.parentWidget()
        if issubclass(parent.__class__, RootWindow):
            return parent
        else:
            return parent.getRoot()

#    def isEnabled(self):
#        """Retrieve the status of the self.enabled boolean attribute.
#            self.enabled is an attribute of the QtGui.QWidget object.
#            
#            returns a boolean"""
#        return self.enabled

    def requirementsMet(self):
        return True

    def updateLinks(self, rootPointer):
        """Update dependency links for this element.
        
            All elements (although usually only subclasses of DynamicPrimitive) 
            have the ability to be enabled by other elements"""

        self.root = rootPointer

        #enabledBy is only a single string ID
        if 'enabledBy' in self.attributes:
            idString = self.attributes['enabledBy']
            self.enabledBy = self.root.allElements[idString]
            self.enabledBy.enables.append(self)

        #requiredIf is a list
        if 'requiredIf' in self.attributes:
            for idString in self.attributes['requiredIf']:
                elementPointer = self.root.allElements[idString]
                self.requiredIf.append(elementPointer)

    def isRequired(self):
        """Check to see if this element is required.
        
            An element is required if element.required == True or if the element
            has a 'requiredIf' attribute list and at least one of the elements 
            in the 'requiredIf' list is required.
                    
            returns a boolean"""

        if hasattr(self, 'required'):
            return self.required
        else:
            for element in self.requiredIf:
                if element.requirementsMet():
                    return True
        return False

    def setState(self, state, includeSelf=True, recursive=True):
        if includeSelf:
            for element in self.elements:
                element.setEnabled(state)

        if recursive:
            for element in self.enables:
                element.setState(state)

    def getLabel(self):
        if 'inheritLabelFrom' in self.attributes:
            target_id = self.attributes['inheritLabelFrom']
            return self.root.allElements[target_id].attributes['label']
        elif 'label' in self.attributes:
            id = self.attributes['label']
            if id in self.root.allElements:
                return self.root.allElements[id].attributes['label']
            else:
                return self.attributes['label']
        else:
            return ''

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

    def __init__(self, attributes, layout, registrar=None):
        """Constructor for the DynamicGroup class.
            Most object construction has been abstracted to the DynamicElement
            class.  The defining feature of a DynamicGroup from a DynamicElement
            is that a DynamicGroup has a layout and can contain elements if
            they have been defined by the user.
        
            attributes - a python dictionary with the attributes for this group
                parsed from the user-defined JSON object.
            layout - a layout mechanism compatible with Qt4 or a subclass of 
                such a layout manager.
            registrar=None - An (optional) instance of 
                base_widgets.ElementRegistrar.  Required if creating elements 
                within this DynamicGroup.
        
            returns an instance of DynamicGroup"""

        #create the object by initializing its superclass, DynamicElement.
        DynamicElement.__init__(self, attributes)

        #set the layout for this group(a subclass of DynamicElement, which
        #itself is a subclass of QtGui.QWidget) so that we can add widgets 
        #as necessary.
        self.setLayout(layout)

        self.registrar = registrar
        if registrar != None:
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
            widget = self.registrar.eval(values['type'], values)
            #If an unusual layoutManager has been declared, it may be necessary 
            #to add a new clause to this conditional block.
            if isinstance(self.layout(), QtGui.QGridLayout):
                j = 0
                for subElement in widget.elements:
                    self.layout().addWidget(subElement, i, j)
                    j += 1
                    
                if (issubclass(widget.__class__, DynamicPrimitive) and 
                    widget.display_error()):
                    i += 1 #display the error on the row below
                    self.layout().addWidget(widget.error, i,
                        widget.error.get_setting('start'),
                        widget.error.get_setting('width'), 1)
                    i += 1
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

    def getOutputValue(self):
        if 'args_id' in self.attributes and self.isEnabled():
            return self.value()

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
        
        Note that all implemented instances of DynamicPrimitive must implement
        their own setValue(value) function, specific to the target QWidget.
         - self.setValue(value) is a function that allows a developer to specify
             the value of the current element, depending on how the value needs
             to be set based on the class and class elements and the type of 
             the value.
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
        self.validator = iui_validator.Validator(self)
        self.error = ErrorString()
        self.set_display_error(True)

    def resetValue(self):
        """If a default value has been specified, reset this element to its
            default.  Otherwise, leave the element alone.
            
            returns nothing."""

        if 'defaultValue' in self.attributes:
            self.setValue(self.attributes['defaultValue'])

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

    def cast_value(self):
        try:
            return self.root.type_registrar.eval(self.attributes['dataType'],
                self.value())
        except KeyError:
            return str(self.value())

    def getOutputValue(self):
        if 'args_id' in self.attributes:
            if self.isEnabled():
                value = str(self.value())
                if value != '':
                    return self.cast_value()

    def set_error(self, error):
        if error == None:
            msg = ''
            self.setBGcolorSatisfied()
        else:
            msg = str(error)
            self.setBGcolorSatisfied(False)
        self.error.set_error(msg)

    def has_error(self):
        if str(self.error.text()) == '':
            return False
        return True
        
    def validate(self):
        if self.isEnabled():
            self.set_error(self.validator.validate())
        
    def display_error(self):
        """returns a boolean"""
        return self._display_error
    
    def set_display_error(self, display):
        """display is a boolean"""
        
        self._display_error = display

class ErrorString(QtGui.QLabel):
    def __init__(self, display_settings={'start':0, 'width':1}):
        """display_settings is a python dict:
            {'start': int,
             'width': int}"""
             
        QtGui.QLabel.__init__(self)
        self._settings = display_settings
        self.setStyleSheet('QLabel { color: red; font-weight: normal; ' + 
            'padding-bottom: 10px}')
        #set a stylesheet here

    def get_setting(self, key):
        return self._settings[key]
    
    def set_setting(self, key, value):
        self._settings[key] = value

    def set_error(self, error_string=''):
        self.setText(error_string)

class LabeledElement(DynamicPrimitive):
    def __init__(self, attributes):
        DynamicPrimitive.__init__(self, attributes)
        self.label = QtGui.QLabel(attributes['label'])
        self.elements = [self.label]
        self.error.set_setting('start', 1)

    def addElement(self, element):
        self.elements.append(element)

    def initState(self):
        if self.isEnabled():
            self.validate()

    def setState(self, state, includeSelf=True, recursive=True):
        DynamicPrimitive.setState(self, state, includeSelf, recursive)

        if state == True:
            self.validate()

class DynamicText(LabeledElement):
    """Creates an object containing a label and a sigle-line text field for
        user input.
        
        DynamicText is a subclass of DynamicPrimitive and thus inherits all its
        methods and attributes.
        
        FileEntry and YearEntry inherit DynamicText.
        
        As the superclass to a number of text-based elements, DynamicText 
        implements a text-only option, namely validText.  DynamicText also 
        implements the attribute defaultValue.
        """

    def __init__(self, attributes):
        """Constructor for the DynamicText class.
            The defining features for this class have primarily to do with user
            interaction: a child of DynamicText can be required, can have
            defaultValue and can have valid text.
            
            attributes -a python dictionary of element attributes.

            returns a constructed DynamicText object."""

        #create the object by initializing its superclass, DynamicElement.    
        super(DynamicText, self).__init__(attributes)

        #create the new Label widget and save it locally.  This label is 
        #consistent across all included subclasses of DynamicText.
#        self.label = QtGui.QLabel(attributes['label'])

        #create the new textField widget and save it locally.  This textfield
        #is consistent across all included subclasses of DynamicText, though
        #the way the textfield is used may differ from class to class.
        self.textField = QtGui.QLineEdit()

        #All subclasses of DynamicText must contain at least these two elements.
        self.addElement(self.textField)

        #Set self.required to the user's specification (could be True or False)
        if "required" in attributes:
            self.required = attributes['required']

        #If the user has defined some default text for this text field, insert 
        #it into the text field.
        if "defaultValue" in attributes:
            self.textField.insert(attributes['defaultValue'])

        #If the user has defined a string regular expression of text the user is
        #allowed to input, set that validator up with the setValidateField()
        #function.
        if 'validText' in attributes:
            self.setValidateField(attributes['validText'])

        #Connect the textfield's textChanged signal to the toggle() function.
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

        #If the user has already pressed the OK button and some text is updated,
        #we need to check all other elements and update the main window 
        #notifications accordingly.
        if self.isEnabled():
            if self.isRequired() and not self.requirementsMet():
                self.setBGcolorSatisfied(False)
            else:
                self.setBGcolorSatisfied(True)

        #This function attempts to enable or disable elements as appropriate.
        self.setState(self.requirementsMet(), includeSelf=False)

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

    def resetValue(self):
        DynamicPrimitive.resetValue(self)
        self.setBGcolorSatisfied(True)


    def updateLinks(self, rootPointer):
        LabeledElement.updateLinks(self, rootPointer)

        self.textField.editingFinished.connect(self.validate)
        
class Container(QtGui.QGroupBox, DynamicGroup):
    """Class Container represents a QGroupBox (which is akin to the HTML widget
        'fieldset'.  It has a Vertical layout, but may be subclassed if a 
        different layout is needed."""

    def __init__(self, attributes, registrar=None):
        """Constructor for the Container class.
            
            attributes - a python dictionary containing all attributes of this
                container, including its elements.  Elements are initialized in
                DynamicGroup.createElements().
                
            returns an instance of Container."""

        super(Container, self).__init__(attributes, QtGui.QVBoxLayout(), registrar)
        #set the title of the container
        self.setTitle(attributes['label'])

        if 'collapsible' in self.attributes:
            #this attribute of QtGui.QGroupBox determines whether the container
            #will sport a hide/reveal checkbox.
            self.setCheckable(self.attributes['collapsible'])
            self.setChecked(False)

            if self.attributes['collapsible'] == True:
                for element in self.elements:
                    element.setVisible(False)

                self.toggled.connect(self.toggleHiding)

    def toggleHiding(self, state):
        """Show or hide all sub-elements of container (if collapsible) as
            necessary.  This function is a callback for the toggled() signal.
            
            returns nothing."""

        for element in self.elements:
            if element.isVisible() == True:
                element.setVisible(False)
            else:
                element.setVisible(True)

        self.setState(state, includeSelf=False, recursive=True)

    def resetValue(self):
        if 'defaultValue' in self.attributes:
            self.setChecked(self.attributes['defaultValue'])

        self.setState(False, includeSelf=False, recursive=True)

class GridList(DynamicGroup):
    """Class GridList represents a DynamicGroup that has a QGridLayout as a 
        layout manager."""

    def __init__(self, attributes, registrar=None):
        """Constructor for the GridList class.
        
            attributes -a python dictionary containing all attributes of this 
                DynamicGroup, including the elements it contains.  Elements are
                initialized in DynamicGroup.createElements().
            
            returns an instance of the GridList class."""

        super(GridList, self).__init__(attributes, QtGui.QGridLayout(), registrar)

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
        self.addElement(self.button)
        self.error.set_setting('width', 2)

    def setValue(self, text):
        """Set the value of the uri field.  If parameter 'text' is an absolute
            path, set the textfield to its value.  If parameter 'text' is a 
            relative path, set the textfield to be the absolute path of the
            input text, relative to the invest root.
            
            returns nothing."""

        if os.path.isabs(text):
            self.textField.setText(text)
        else:
            self.textField.setText(os.path.abspath(INVEST_ROOT + text))

class YearEntry(DynamicText):
    """This represents all the components of a 'Year' line in the LULC box.
        The YearEntry object consists of two objects: a label (QtGui.QLabel)
        and a year (QtGui.QLineEdit).  The year also has a min and max width."""

    def __init__(self, attributes):
        super(YearEntry, self).__init__(attributes)

        #set the width attribute, if it's provided.
        if 'width' in self.attributes:
            self.textField.setMaximumWidth(self.attributes['width'])

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
        self.setIcon(QtGui.QIcon(CMD_FOLDER + '/document-open.png'))
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

        if self.filetype == 'file':
            filename = QtGui.QFileDialog.getOpenFileName(self, 'Select ' + self.text, '.')
        elif self.filetype == 'folder':
            filename = QtGui.QFileDialog.getExistingDirectory(self, 'Select ' + self.text, '.')

        #Set the value of the URIfield.
        if filename == '':
            self.URIfield.setText(oldText)
        else:
            self.URIfield.setText(filename)

class SliderSpinBox(DynamicPrimitive):
    """expects these attributes:
        label: string
        type: sliderSpinBox
        min: number
        max: number
        sliderSteps: int
        spinboxSteps: int
        """
    def __init__(self, attributes):
        super(SliderSpinBox, self).__init__(attributes)

        self.label = QtGui.QLabel(self.attributes['label'])
        self.slider = QtGui.QSlider()
        self.spinbox = QtGui.QDoubleSpinBox()
        self.elements = [self.label, self.slider, self.spinbox]

        slidermax = self.attributes['max'] * self.attributes['sliderSteps']
        slidermin = self.attributes['min'] * self.attributes['sliderSteps']
        self.slider.setMaximum(slidermax)
        self.slider.setMinimum(slidermin)
        self.slider.setOrientation(QtCore.Qt.Horizontal)

        steps = float(self.attributes['max']) / self.attributes['spinboxSteps']
        self.spinbox.setMinimum(self.attributes['min'])
        self.spinbox.setMaximum(self.attributes['max'])
        self.spinbox.setSingleStep(steps)

        self.slider.valueChanged.connect(self.setSpinbox)
        self.spinbox.valueChanged.connect(self.setSlider)

    def setSpinbox(self):
        sliderValue = int(self.slider.value())
        self.spinbox.setValue(float(sliderValue) / self.attributes['sliderSteps'])

    def setSlider(self):
        fieldValue = self.spinbox.value()
        self.slider.setValue(int(fieldValue * self.attributes['sliderSteps']))


class HideableFileEntry(FileEntry):
    def __init__(self, attributes):
        super(HideableFileEntry, self).__init__(attributes)

        self.checkbox = QtGui.QCheckBox(attributes['label'])
        self.checkbox.toggled.connect(self.toggleHiding)
        self.checkbox.toggled.connect(self.toggle)

        #remove the label, as it is being subsumed by the new checkbox's label.
        self.elements.remove(self.label)
        self.elements.insert(0, self.checkbox)
        self.error.set_setting('start', 2)

        self.hideableElements = [self.textField, self.button]
        self.toggleHiding(False)

    def toggleHiding(self, checked):
        for element in self.hideableElements:
            if checked:
                element.show()
            else:
                element.hide()

    def requirementsMet(self):
        return self.checkbox.isChecked()

class Dropdown(LabeledElement):
    def __init__(self, attributes):
        LabeledElement.__init__(self, attributes)

        self.dropdown = QtGui.QComboBox()

        for option in self.attributes['options']:
            self.addItem(option)

        self.addElement(self.dropdown)

class OperationDialog(QtGui.QDialog):
    """ModelDialog is a class defining a modal window presented to the user
        while the model is running.  This modal window prevents the user from
        interacting with the main UI window while the model is processing and 
        provides status updates for the model.
        
        This window is not configurable through the JSON configuration file."""

    def __init__(self, root):
        """Constructor for the ModelDialog class.
            
            root - a pointer to the parent window

            returns an instance of ModelDialog."""
        QtGui.QDialog.__init__(self)
#        Testator.__init__(self)

        self.root = root
        self.exec_controller = executor.Controller()

        #set window attributes
        self.setLayout(QtGui.QVBoxLayout())
        self.setWindowTitle("Running the model")
        self.setGeometry(400, 400, 700, 400)
        self.setWindowIcon(QtGui.QIcon('natcap_logo.png'))

        self.cancel = False

        #create statusArea-related widgets for the window.        
        self.statusAreaLabel = QtGui.QLabel('Messages:')
        self.statusArea = QtGui.QPlainTextEdit()
        self.statusArea.setReadOnly(True)
        self.cursor = self.statusArea.textCursor()

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
        self.quitButton = QtGui.QPushButton(' Quit')
        self.backButton = QtGui.QPushButton(' Back')
        self.cancelButton = QtGui.QPushButton(' Cancel')

        #add button icons
        self.quitButton.setIcon(QtGui.QIcon('dialog-close.png'))
        self.backButton.setIcon(QtGui.QIcon('dialog-ok.png'))
        self.cancelButton.setIcon(QtGui.QIcon('dialog-cancel.png'))

        #disable the 'Back' button by default
        self.backButton.setDisabled(True)
        self.quitButton.setDisabled(True)
        self.cancelButton.setDisabled(False)

        #create the buttonBox (a container for buttons) and add the buttons to
        #the buttonBox.
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(self.quitButton, QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.addButton(self.backButton, QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.cancelButton, QtGui.QDialogButtonBox.ResetRole)

        #connect the buttons to their callback functions.
        self.backButton.clicked.connect(self.closeWindow)
        self.quitButton.clicked.connect(sys.exit)
        self.cancelButton.clicked.connect(self.exec_controller.cancel_executor)

        #add the buttonBox to the window.        
        self.layout().addWidget(self.buttonBox)

        self.timer = QtCore.QTimer()

    def showEvent(self, event):
        QtCore.QTimer.singleShot(100, self.startExecutor)
    
    def startExecutor(self):
        self.statusArea.clear()
        self.start_buttons()

        self.exec_controller.start_executor()

        self.timer.timeout.connect(self.check_messages)
        self.timer.start(100)
        
    def check_messages(self):
        if not self.exec_controller.is_finished():
            message = self.exec_controller.get_message()
            if message != None:
                self.write(message)
        else:
            self.finished()
        
        

    def start_buttons(self):
        self.progressBar.setMaximum(0) #start the progressbar.
        self.backButton.setDisabled(True)
        self.quitButton.setDisabled(True)
        self.cancelButton.setDisabled(False)
                
    def stop_buttons(self):
        self.progressBar.setMaximum(1) #stops the progressbar.
        self.backButton.setDisabled(False)
        self.quitButton.setDisabled(False)
        self.cancelButton.setDisabled(True)
        
    def write(self, text):
        """Write text.  If printing to the status area, also scrolls to the end 
            of the text region after writing to it.  Otherwise, print to stdout.
            
            text - a string to be written to self.statusArea.
            
            returns nothing."""

        self.statusArea.insertPlainText(QtCore.QString(text))
        self.cursor.movePosition(QtGui.QTextCursor.End)
        self.statusArea.setTextCursor(self.cursor)

    def finished(self):
        """Notify the user that model processing has finished.
        
            returns nothing."""

        self.timer.stop()
        self.stop_buttons()

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

        self.cancel = False
        self.done(0)

    def cancelled(self):
        return self.cancel



class RootWindow(DynamicElement):
    def __init__(self, attributes, layout, object_registrar):
        DynamicElement.__init__(self, attributes)

        self.type_registrar = registrar.DatatypeRegistrar()
        self.setLayout(layout)

        self.body = DynamicGroup(attributes, QtGui.QVBoxLayout(), object_registrar)

        if 'scrollable' in self.attributes:
            make_scrollable = self.attributes['scrollable']
        else:
            make_scrollable = True

        if make_scrollable:
            self.scrollArea = QtGui.QScrollArea()
            self.layout().addWidget(self.scrollArea)
            self.scrollArea.setWidget(self.body)
            self.scrollArea.setWidgetResizable(True)
            self.body.layout().insertStretch(-1)
            self.scrollArea.verticalScrollBar().rangeChanged.connect(self.updateScrollBorder)

            self.updateScrollBorder(self.scrollArea.verticalScrollBar().minimum(),
                                    self.scrollArea.verticalScrollBar().maximum())
        else:
            self.layout().addWidget(self.body)

        self.last_run_handler = fileio.LastRunHandler(self.attributes['modelName'])
        self.lastRun = last_run_handler.get_attributes()

        self.outputDict = {}
        self.allElements = self.body.getElementsDictionary()

        for id, element in self.allElements.iteritems():
            element.updateLinks(self)

        self.operationDialog = OperationDialog(self)

        self.messageArea = QtGui.QLabel('')
        self.layout().addWidget(self.messageArea)
        self.initElements()
        self.addBottomButtons()

        self.setWindowSize()

        return

    def updateScrollBorder(self, min, max):
        if min == 0 and max == 0:
            self.scrollArea.setStyleSheet("QScrollArea { border: None } ")
        else:
            self.scrollArea.setStyleSheet("")

    def setWindowSize(self):
        #this groups all elements together at the top, leaving the
        #buttons at the bottom of the window.

        if 'width' in self.attributes:
            width = self.attributes['width']
        else:
            width = 400

        if 'height' in self.attributes:
            height = self.attributes['height']
        else:
            height = 400

        self.setGeometry(400, 400, width, height)
        self.setWindowIcon(QtGui.QIcon('natcap_logo.png'))

    def closeWindow(self):
        """Terminates the application.
        
            This function is called when the user closes the window by any of
            Qt's recognized methods (often including closing the window via the
            little x in the corner of the window and/or pressing the Esc key).
        
            returns nothing"""

        sys.exit(0)

    def closeEvent(self, event=None):
        """Terminates the application. This function is a Qt-defined callback 
            for when the window is closed.
            
            returns nothing"""

        sys.exit(0)

    def resetParametersToDefaults(self):
        """Reset all parameters to defaults provided in the configuration file.
        
            returns nothing"""

        self.messageArea.setText('Parameters reset to defaults')

        for id, element in self.allElements.iteritems():
            if issubclass(element.__class__, DynamicPrimitive):
                element.resetValue()
            elif issubclass(element.__class__, Container):
                element.resetValue()

    def okPressed(self):
        """A callback, run when the user presses the 'OK' button.
        
            returns nothing."""

        if not self.errors_exist():
            self.queueOperations()
            self.runProgram()

    def errors_exist(self):
        """Check to see if any elements in this UI have errors.
        
            Returns True if an error is found.  False if not."""
            
        for id, element in self.allElements.iteritems():
            if issubclass(element.__class__, DynamicPrimitive):
                if element.has_error():
                    return True
        return False

    def queueOperations(self):
        #placeholder for custom implementations.
        #intended for the user to call executor.addOperation() as necessary
        #for the given model.
        return

    def runProgram(self):
        self.operationDialog.exec_()

        if self.operationDialog.cancelled():
            QtCore.QCoreApplication.instance().exit()

    def saveLastRun(self):
        """Saves the current values of all input elements to a JSON object on 
            disc.
            
            returns nothing"""

        user_args = {}

        #loop through all elements known to the UI, assemble into a dictionary
        #with the mapping element ID -> element value
        for id, element in self.allElements.iteritems():
            if issubclass(element.__class__, DynamicPrimitive):
                user_args[id] = str(element.value())

        self.last_run_handler.write_to_disk(user_args)

    def initElements(self):
        """Set the enabled/disabled state and text from the last run for all 
            elements
        
            returns nothing"""

        if self.lastRun == {}:
            self.resetParametersToDefaults()
        else:
            for id, value in self.lastRun.iteritems():
                element = self.allElements[id]
                element.setValue(value)

            self.messageArea.setText('Parameters from your last run have \
been loaded.')


    def assembleOutputDict(self):
        """Assemble an output dictionary for use in the target model
        
            Saves a python dictionary to self.outputDict.  This dictionary has
            the mapping: element args_id -> element value.  Values are converted
            to their appropriate dataType where specified in the JSON config
            file.
        
            returns nothing"""

        #initialize the outputDict, in case it has been already written to
        #in a previous run.
        outputDict = {}

        for id, element in self.allElements.iteritems():

            element_value = element.getOutputValue()
            if element_value != None:
                args_id = element.attributes['args_id']
                if args_id not in outputDict:
                    outputDict[args_id] = {}
                if 'sub_id' in element.attributes:
                    sub_id = element.attributes['sub_id']

                    if sub_id in self.allElements:
                        sub_id = self.allElements[sub_id].getLabel()

                    outputDict[args_id][sub_id] = element_value
                else:
                    outputDict[args_id] = element_value

        return outputDict

    def addBottomButtons(self):
        """Assembles buttons and connects their callbacks.
        
            returns nothing."""

        self.runButton = QtGui.QPushButton(' Run')
        self.runButton.setIcon(QtGui.QIcon(CMD_FOLDER + '/dialog-ok.png'))

        self.cancelButton = QtGui.QPushButton(' Quit')
        self.cancelButton.setIcon(QtGui.QIcon(CMD_FOLDER + '/dialog-close.png'))

        self.resetButton = QtGui.QPushButton(' Reset')
        self.resetButton.setIcon(QtGui.QIcon(CMD_FOLDER + '/edit-undo.png'))

        #create the buttonBox (a container for buttons)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.addButton(self.runButton, QtGui.QDialogButtonBox.AcceptRole)
        self.buttonBox.addButton(self.cancelButton, QtGui.QDialogButtonBox.RejectRole)
        self.buttonBox.addButton(self.resetButton, QtGui.QDialogButtonBox.ResetRole)

        #connect the buttons to their functions.
        self.runButton.clicked.connect(self.okPressed)
        self.cancelButton.clicked.connect(self.closeWindow)
        self.resetButton.clicked.connect(self.resetParametersToDefaults)

        #add the buttonBox to the window.        
        self.layout().addWidget(self.buttonBox)

    def showMessages(self, messageList):
        """Add all messages in messageList to the messageArea QLabel.
        
            messageList - a python list of either tuples or strings.
                If the list is of strings, messages are presumed to be status
                messages.  If the list is of tuples, the tuples are expected
                to have the structure (element pointer, error string).
                
            returns nothing. """

        self.messageArea.setText('')
        label = ''
        for element in messageList:
            if issubclass(element.__class__, tuple):
                element[0].setBGcolorSatisfied(False)
                label += str(element[1] + '\n')
            else:
                label += str(element + '\n')
        self.messageArea.setText(label.rstrip())

class ElementRegistrar(registrar.Registrar):
    def __init__(self):
        registrar.Registrar.__init__(self)
        updates = {'container' : Container,
                   'list': GridList,
                   'file': FileEntry,
                   'folder': FileEntry,
                   'text': YearEntry,
                   'sliderSpinBox': SliderSpinBox,
                   'hideableFileEntry': HideableFileEntry
                   }
        self.update_map(updates)
        
    def eval(self, type, op_values):
        widget = registrar.Registrar.get_func(self, type)
        if issubclass(widget, DynamicGroup):
            return widget(op_values, self)
        else:
            return widget(op_values)

if __name__ == "__main__":
    reg = Registrar()
    reg.create('checkbox', {'label': 'lala'})
