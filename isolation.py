from maya import mel, cmds
import maya.OpenMaya as om




class Isolation(object):

    def __init__(self, nodes=om.MSelectionList(), panes=[], state=True, autoLoad=True):
        '''
        Methods for isolate selection of nodes
        @param  nodes   OpenMaya.MSelectionList, nodes to isolate
        @param  panes   list, list of viewport panes to isolate nodes in
        @param  state   bool, isolate nodes True or False?
        @param  autoLoad    bool, add newly created nodes to isolated panes
        '''
        self._members = nodes
        self._panes = panes
        self._state = state
        self._autoLoad = autoLoad
        self._memories = {}

        self.setDefaultMemory(self._members)

        if self._state:    
            self.isolatePanes(self._panes)

        if self._autoLoad:    
            self._autoLoadNewObjects(self._panes)

    #---------------------------------------------------------------

    def members(self):
        return self._members

    def panes(self):
        return self._panes

    def state(self):
        return self._state

    def autoLoad(self):
        return self._autoLoad

    #---------------------------------------------------------------

    def isolatePanes(self, panes=[]):
        sel = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(sel)
        
        om.MGlobal.setActiveSelectionList(self._members)

        for pane in panes:
            cmds.isolateSelect(pane, state=True)
        
        om.MGlobal.setActiveSelectionList(sel)

    #---------------------------------------------------------------

    def exitIsolate(self, panes=[]):
        for pane in panes:
            cmds.isolateSelect(pane, state=False)

    #---------------------------------------------------------------

    def addMembers(self, nodes=om.MSelectionList()):
        self._members.merge(nodes)
        
        if self._state:
            om.MGlobal.setActiveSelectionList(nodes)
            for pane in self._panes:
                cmds.isolateSelect(pane, addSelected=True)

    #---------------------------------------------------------------

    def removeMembers(self, nodes=om.MSelectionList()):
        self._members.merge(nodes, om.MSelectionList().kRemoveFromList )
        
        if self._state:
            om.MGlobal.setActiveSelectionList(nodes)
            for pane in self._panes:
                cmds.isolateSelect(pane, removeSelected=True)

    #---------------------------------------------------------------

    def selectMembers(self):
        om.MGlobal.setActiveSelectionList(self._members)

    #---------------------------------------------------------------

    def _autoLoadNewObjects(self, panes=[]):
        for pane in panes:
            mel.eval('setIsolateSelectAutoAdd {0} true'.format(pane))

    #---------------------------------------------------------------

    def replaceMembers(self, nodes=om.MSelectionList(), setDefault=False):

        self._members = nodes
        

        if setDefault:
            self.setDefaultMemory(self._members)
        
        if self._state:
        
            sel = om.MSelectionList()
            om.MGlobal.getActiveSelectionList(sel)

            om.MGlobal.setActiveSelectionList(nodes)
            for pane in self._panes:
                cmds.isolateSelect(pane, loadSelected=True)
                cmds.isolateSelect(pane, addSelected=True)

            om.MGlobal.setActiveSelectionList(sel)

    #---------------------------------------------------------------

    def toggleIsolate(self):
        if self._state:
            self.exitIsolate(self._panes)
        
        else:
            self.isolatePanes(self._panes)
        
        self._state = not self._state

    #---------------------------------------------------------------

    def setPanes(self, panes=[]):
        self._panes = []
        self.addPanes(panes)
        
        if self._state:
            self.isolatePanes(panes)

        if self._autoLoad:    
            self._autoLoadNewObjects(panes)
       
    #---------------------------------------------------------------

    def addPanes(self, panes=[]):
        if self._state:
            self.isolatePanes(panes)
        
        self._panes.extend(panes)
        
        if self._autoLoad:
            self._autoLoadNewObjects(panes)

    #---------------------------------------------------------------

    def removePanes(self, panes=[]):
        
        self.exitIsolate(panes)
        
        for pane in panes:
            try:
                self._panes.remove(pane)
            except: pass

    #---------------------------------------------------------------      

    def addMemory(self, nodes=om.MSelectionList(), key=None):
        self._memories[key] = nodes

    #---------------------------------------------------------------      

    def removeMemory(self, key=None):
        try:
            del self._memories[key]
        except: pass

    #---------------------------------------------------------------      

    def goToMemory(self, key=None):
        self.replaceMembers(nodes=self._memories[key], setDefault=False)

    #---------------------------------------------------------------      

    def setDefaultMemory(self, nodes=om.MSelectionList()):
        self._memories["default"] = nodes

    #---------------------------------------------------------------      

    def goToDefaultMemory(self):
        self.goToMemory("default")

    #---------------------------------------------------------------
