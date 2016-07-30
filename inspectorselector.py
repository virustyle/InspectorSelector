
import os, sys, time
from functools import partial

from PySide import QtGui, QtCore
import shiboken, pysideuic

from maya import cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as mui

import isolation
reload(isolation)

import xml.etree.ElementTree as xml
from cStringIO import StringIO


#---------------------------------------------------------------
# GLOBALS
#---------------------------------------------------------------

WIDTH = 125 
HEIGHT = 180

PANEORDER = ("single", "quad",
			 "vertical2", "horizontal2",
			 "vertical3", "horizontal3", "vertical4", "horizontal4",
			 "bottom3", "top3", "left3", "right3",
			 "bottom4", "top4", "left4", "right4")

#---------------------------------------------------------------

def getMayaWindow():
	ptr = mui.MQtUtil.mainWindow()
	return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)

#---------------------------------------------------------------

def getActiveView():
	return mui.M3dView.active3dView()

#---------------------------------------------------------------

def get3dViews():
	views = []
	widgets = []
	viewCount = mui.M3dView.numberOf3dViews()
	
	for v in xrange(viewCount):
		view, widget = wrapViewWidget(v)
		views.append(view)
		widgets.append(widget)

	return views, widgets

#---------------------------------------------------------------

def wrapViewWidget(viewIndex):
	view = mui.M3dView()
	mui.M3dView.get3dView(viewIndex, view)
	widget = shiboken.wrapInstance(long(view.widget()), QtGui.QWidget)

	return view, widget

#---------------------------------------------------------------

def loadUiType(uiFile):	
	parsed = xml.parse(uiFile)
	widget_class = parsed.find('widget').get('class')
	form_class = parsed.find('class').text
 
	with open(uiFile, 'r') as f:
		o = StringIO()
		frame = {}
 
		pysideuic.compileUi(f, o, indent=0)
		pyc = compile(o.getvalue(), '<string>', 'exec')
		exec pyc in frame
 
		form_class = frame['Ui_%s'%form_class]
		base_class = eval('QtGui.%s'%widget_class)
 
	return form_class, base_class

#---------------------------------------------------------------


pwd = os.path.dirname(__file__)
uiName = "inspectorselector.ui"
uiFile = os.path.join( pwd, uiName )
form_class, base_class = loadUiType(uiFile)



class IsolationWindow(form_class, base_class):
	
	def __init__(self, parent=getMayaWindow()):
		super(IsolationWindow, self).__init__(parent)      

		self.setupUi(self)
		self.parent = parent
		self.setObjectName('inspectorselecter')

		self.setFixedSize(WIDTH, HEIGHT)
		self.setWindowFlags(QtCore.Qt.FramelessWindowHint);
		# self.setAttribute(QtCore.Qt.WA_TranslucentBackground);

		sel = om.MSelectionList()
		om.MGlobal.getActiveSelectionList(sel)
		self._isolate = isolation.Isolation(nodes=sel, state=False, panes=[])

		self.memoryClickFilter = MemoryClickFilter(self)
		self.viewRefreshFilter = ViewRefreshFilter(self)

		self.views, self.viewWidgets = get3dViews()
		self.viewPort = self.parent.findChild(QtGui.QWidget, "viewPanes")
		self.moveToPosition()

		self.viewBtns = {}
		self.panelStates = {}
		self.panelLocations = {}

		self._memoryBtns = self.getMemoryButtons()
		
		self.initConnections()
		self.initViewBtns()
		self.refreshViewBtns()

	#---------------------------------------------------------------

	def closeEvent(self, event):
		self._removeEventFilters()

	#---------------------------------------------------------------
	
	def showEvent(self, event):
		self._createEventFilters()
		
	#---------------------------------------------------------------

	def hideEvent(self, event):
		self._removeEventFilters()
		
	#---------------------------------------------------------------

	def moveToPosition(self):

		topRight = self.viewPort.mapTo(getMayaWindow(), self.viewPort.rect().topRight())
		self.move(topRight.x() - (WIDTH + 1), topRight.y() + 41) # subtract window border and invisible title bar.
		self.raise_()

	#---------------------------------------------------------------

	def initConnections(self):
		self.addBTN.clicked.connect(self.on_add)
		self.subtractBTN.clicked.connect(self.on_subtract)
		self.reloadBTN.clicked.connect(self.on_reload)
		self.isolateBTN.clicked.connect(self.on_isolate)

	#---------------------------------------------------------------
	
	def initViewBtns(self):

		for modelPanel in ("modelPanel1", "modelPanel2", "modelPanel3", "modelPanel4"):
			
			state = cmds.isolateSelect(modelPanel, query=True, state=True)
			self.panelStates[modelPanel] = state
			
			if state:
				self._isolate._state = True
				self.isolateBTN.setChecked(True)
				self._isolate.addPanes([modelPanel])

		
		for page in self.stackedWidget.children():
			for btn in page.findChildren(QtGui.QPushButton):
				btn.setCheckable(True)
				
				panel = btn.property("view")
				
				btns = self.viewBtns.setdefault(panel, [])
				btns.append(btn)

	#---------------------------------------------------------------

	def _createEventFilters(self):
		for btn in self._memoryBtns:
			btn.installEventFilter(self.memoryClickFilter)
		
		self.viewPort.installEventFilter(self.viewRefreshFilter)

	#---------------------------------------------------------------

	def _removeEventFilters(self):
		for btn in self._memoryBtns:
			btn.removeEventFilter(self.memoryClickFilter)
		
		self.viewPort.removeEventFilter(self.viewRefreshFilter)

	#---------------------------------------------------------------

	def getMemoryButtons(self):
		return [btn for btn in self.memoryFrame.children() if str(btn.objectName()).startswith("memory")]

	#---------------------------------------------------------------

	def setMemoryState(self, btn, state):
		btn.setProperty("state", state)
		btn.style().polish(btn)

	#---------------------------------------------------------------

	def refreshViewBtns(self):
		config = cmds.paneLayout("viewPanes", query=True, configuration=True)
		self.stackedWidget.setCurrentIndex( PANEORDER.index(config) )
		
		self.panelLocations = self._panelLocations()
		self.connectViewBtns()

	#---------------------------------------------------------------
	
	def connectViewBtns(self):
		for btn in self.stackedWidget.currentWidget().findChildren(QtGui.QPushButton):
			
			pane = btn.property("view")
			modelPanel = self.panelLocations[pane]

			if not cmds.getPanel(typeOf=self.panelLocations[pane]) == "modelPanel":
				continue

			btn.clicked.connect( partial(self.on_view, pane, btn) )
			btn.setChecked(self.panelStates[modelPanel])

	#---------------------------------------------------------------

	def _panelLocations(self):
		
		return { "pane1" : cmds.paneLayout("viewPanes", query=True, pane1=True),
				 "pane2" : cmds.paneLayout("viewPanes", query=True, pane2=True),
				 "pane3" : cmds.paneLayout("viewPanes", query=True, pane3=True),
				 "pane4" : cmds.paneLayout("viewPanes", query=True, pane4=True) }      






	#===============================================================================
	#
	# Connections
	#
	#===============================================================================

	def on_add(self):
		sel = om.MSelectionList()
		om.MGlobal.getActiveSelectionList(sel)
		if sel.isEmpty():
			return

		self._isolate.addMembers(sel)

	#---------------------------------------------------------------

	def on_subtract(self):
		sel = om.MSelectionList()
		om.MGlobal.getActiveSelectionList(sel)
		if sel.isEmpty():
			return
		
		self._isolate.removeMembers(sel)

	#---------------------------------------------------------------

	def on_reload(self):
		sel = om.MSelectionList()
		om.MGlobal.getActiveSelectionList(sel)
		if sel.isEmpty():
			return

		self._isolate.replaceMembers(sel, setDefault=True)

	#---------------------------------------------------------------

	def on_isolate(self):
		self._isolate.toggleIsolate()

	#---------------------------------------------------------------

	def on_view(self, pane, btn):

		if pane == "pane1":
			modelPanel = [ cmds.paneLayout('viewPanes', query=True, pane1=True) ]            

		elif pane == "pane2":
			modelPanel = [ cmds.paneLayout('viewPanes', query=True, pane2=True) ]            

		elif pane == "pane3":
			modelPanel = [ cmds.paneLayout('viewPanes', query=True, pane3=True) ]            

		elif pane == "pane4":
			modelPanel = [ cmds.paneLayout('viewPanes', query=True, pane4=True) ]                        

		btnState = btn.isChecked()        
		if btnState:
			self._isolate.addPanes(modelPanel)
		else:
			self._isolate.removePanes(modelPanel)

		self.panelStates[ modelPanel[0] ] = btnState

	#---------------------------------------------------------------

	def on_enableMemory(self, btn):
	
		try:
			self._isolate.goToMemory(key=btn.objectName())
			state = "active"
		except:
			self._isolate.goToDefaultMemory()
			state = "clear"

		for b in self._memoryBtns:
			if b.property("state") == "active":    
				self.setMemoryState(b, state="set")
	
		self.setMemoryState(btn, state)

	#---------------------------------------------------------------

	def on_clearMemory(self, btn):
		self._isolate.removeMemory(key=btn.objectName())
		
		if btn.property("state") == "active":
			self._isolate.goToDefaultMemory()
		
		self.setMemoryState(btn, state="clear")
	
	#---------------------------------------------------------------

	def on_setMemory(self, btn):
		sel = om.MSelectionList()
		om.MGlobal.getActiveSelectionList(sel)
		
		if sel.isEmpty():
			sel = self._isolate.members()
		
		self._isolate.addMemory(nodes=sel, key=btn.objectName())
		self.setMemoryState(btn, state="set")
	
	#---------------------------------------------------------------  	




def run():
	global isolationWindow
	try:
		isolationWindow.close()
		isolationWindow.deleteLater()
	except: pass
	isolationWindow = IsolationWindow()
	isolationWindow.show()



#---------------------------------------------------------------    
# FILTERS
#---------------------------------------------------------------    

class ViewRefreshFilter(QtCore.QObject):
	
	def __init__(self, parent):
		super(ViewRefreshFilter, self).__init__()

		self.parent = parent


	def eventFilter(self, obj, event):

		if event.type() == QtCore.QEvent.Show: # I cant find a better event to use. this gets called at most 4x
			self.parent.refreshViewBtns()

		elif event.type() == QtCore.QEvent.Resize:
			self.parent.moveToPosition()

		return QtCore.QObject.eventFilter(self, obj, event)    

#---------------------------------------------------------------    

class MemoryClickFilter(QtCore.QObject):

	def __init__(self, parent):
		super(MemoryClickFilter, self).__init__()

		self.parent = parent


	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.MouseButtonRelease:
			btn = event.button()

			if btn == QtCore.Qt.LeftButton:
				self.parent.on_enableMemory(obj)
				return True

			elif btn == QtCore.Qt.MiddleButton:
				self.parent.on_setMemory(obj)
				return True

			elif btn == QtCore.Qt.RightButton:
				self.parent.on_clearMemory(obj)
				return True
	   
		return QtCore.QObject.eventFilter(self, obj, event)














