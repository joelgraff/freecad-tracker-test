from pivy import coin

import FreeCADGui as Gui
import FreeCAD as App

from DraftGui import todo

class NodeTracker():
    """
    Class to manage interactive nodes at the scenegraph level
    """
    def __init__(self, id, coord):

        self.node = coin.SoSeparator()
        self.coordinate = coin.SoCoordinate3()
        self.transform = coin.SoTransform()
        self.point = coord

        _selection_node = \
            coin.SoType.fromName("SoFCSelection").createInstance()

        _selection_node.documentName.setValue('Document')
        _selection_node.objectName.setValue('Test Tracker')
        _selection_node.subElementName.setValue(str(id))

        self.node.addChild(_selection_node)
        self.node.addChild(self.transform)
        self.node.addChild(self.coordinate)
        self.node.addChild(coin.SoMarkerSet())

        self.coordinate.point.setValue(tuple(coord))

class TestTracker():

    def __init__(self):

        #generate coordinates
        _coords = self.generate_coordinates()

        #build node structure
        self.node = coin.SoSeparator()
        self.trackers = []

        self.active_node = -1
        self.size = 1.0

        self.tracker_node = coin.SoSeparator()
        self.crosshair_transform = coin.SoTransform()

        for _i, _v in enumerate(_coords):

            _t = NodeTracker(_i, _v)
            self.trackers.append(_t)
            self.tracker_node.addChild(_t.node)

        #build wire node structure
        _wire_coord = coin.SoCoordinate3()
        _wire_coord.point.setValues(_coords)

        _wire_node = coin.SoSeparator()
        _wire_node.addChild(_wire_coord)
        _wire_node.addChild(coin.SoLineSet())

        #add wire and node trackers to main node
        self.node.addChild(self.tracker_node)
        self.node.addChild(_wire_node)

        #set up event callbacks
        self.view = Gui.ActiveDocument.ActiveView
        self.view.addEventCallback(
            'SoLocation2Event', self.mouse_event)

        #add nodes and crosshair
        _fn = lambda _x: self.view.getSceneGraph().insertChild(_x, 0)

        self.crosshair = self.create_crosshair()

        todo.delay(_fn, self.node)
        todo.delay(_fn, self.crosshair)

        todo.delay(Gui.SendMsgToActiveView, "ViewFit")

    def generate_coordinates(self):
        """
        Generate coordinates for the tracker
        """

        return [
            (20.0, 20.0, 0.0), (10.0, -20.0, 0.0), (0.0, 0.0, 0.0),
            (-30.0, 20.0, 0.0)
        ]

    def create_crosshair(self):

        _scale = App.ParamGet("User parameter:BaseApp/Preferences/View").GetFloat("PickRadius")

        self.size = _scale / 5.0

        _view_scale = self.get_view_scale()

        _scale_vec = (self.size/_view_scale, self.size/_view_scale, 1.0)

        _switch = coin.SoSwitch()
        _node = coin.SoSeparator()
        _coord = coin.SoCoordinate3()

        _coord.point.setValues([
            (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)
        ])

        self.crosshair_transform.scaleFactor = _scale_vec

        _nodes = [self.crosshair_transform, _coord, coin.SoLineSet()]

        for _v in _nodes:
            _node.addChild(_v)

        _switch.addChild(_node)
        _switch.whichChild = -1

        return _switch

    def mouse_event(self, arg):

        _pos = self.view.getCursorPos()
        _info = self.view.getObjectInfo(_pos)

        print('\nmouse info:', _info)
        #nothing under the cursor - switch off crosshair and quit
        if not _info:
            self.crosshair.whichChild = -1
            self.active_node = -1
            return

        _cur_node = int(_info['Component'])

        #quit to avoid unnecessary redraw
        if self.active_node == _cur_node:
            return

        self.active_node = _cur_node

        #get view scale (units per pixel)
        _scale = self.get_view_scale()

        #set crosshair to coordinate of node and switch on
        _coord = self.trackers[self.active_node].point

        self.crosshair_transform.translation.setValue(_coord)
        self.crosshair_transform.scaleFactor = \
            (_scale, _scale, 1.0)

        self.crosshair.whichChild = -3

    def get_view_scale(self):
        """
        Return the current scale (units per pixel) of the view
        """

        #calculate the distance on a 100-pixel line
        coord_1 = self.view.getPoint((0, 0))
        coord_2 = self.view.getPoint((71, 71))

        #scale bhy crosshair size, and
        #divide by 20 to get a 5-pixel equivalent
        return (coord_2.sub(coord_1).Length*self.size) / 20.0
