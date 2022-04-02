"""Load and Manage Tiled Map Data."""
import json
import os

import engine.log
from engine.log import log
import engine.geometry as geo


class Map(dict):
    """
    The Map class is responsible for:
        1) Loading Tiled map files and cleaning the data so it an be used by the game engine.
        2) Provide utility functions for manipulating and searching map data.
    It is assumed the map class with be sub-classed to add additional functionality.

    Most of the data cleaning is performed on objects from Tiled object layers.
    Tiled layer objects are stored as Python Dictionaries.
    (https://www.w3schools.com/python/python_dictionaries.asp)

    The Map class also implements one game mechanic that is available to both
    the server and client:

    LAYER VISABILITY MECHANIC
        The layer visibility mechanic allows layers that were loaded from the Tiled
        map file to be shown or hidden. Normally the server and servermap set layer
        visibility and send it to the client in a step message as a bitmask. The
        client can then use that bitmask to match its visible layers to those
        on the server.
    """

    def __init__(self, tilesets, mapDir):
        """Load map file and do data conversion.

        Note, all Tiled properties will be converted into an easier to access form.
            from: {object['properties'][{name: name1, value: value1}],[...]}
            to: {object.prop-name1=value1,...}
        Note, duplicate property names is not supported!

        Args:
            tilesets (dict): a dict of Tileset objects.
            mapDir (str): path to map directory.
        """
        self['tilesets'] = tilesets
        self['mapDir'] = mapDir

        # Flag to say something on this map has changed
        self.setMapChanged()

        # Maps are named based on their mapDirectory
        self['name'] = mapDir.split("/")[-1]

        # store the game name in case we need it.
        self['game'] = mapDir.split("/")[-3]

        # find if map filename is same name as dir name or just "map.json"
        mapfile = False
        if os.path.isfile(mapDir + "/" + self['name'] + ".json"):
            mapfile = mapDir + "/" + self['name'] + ".json"
        elif os.path.isfile(mapDir + "/map.json"):
            mapfile = mapDir + "/map.json"
        if not mapfile:
            log(f"Mapfile for map {self['name']} not found.", "FAILURE")
            quit()
        log(f"Loading mapfile {mapfile}", "VERBOSE")

        # read tiled map file.
        with open(mapfile) as f:
            mapfiledata = json.load(f)

        # ensure tiled map file is correct format.
        if mapfiledata['type'] != "map" or \
           mapfiledata['orientation'] != "orthogonal" or \
           mapfiledata['renderorder'] != "right-down":
            log(f"{mapDir} does not appear to be an orthogonal map!", "FAILURE")
            exit()

        # store for later use in case needed by a subclass.
        self['mapfiledata'] = mapfiledata

        # extract basic data from map file
        self['height'] = mapfiledata['height']
        self['width'] = mapfiledata['width']
        self['tileheight'] = mapfiledata['tileheight']
        self['tilewidth'] = mapfiledata['tilewidth']
        self['pixelHeight'] = self['height'] * self['tileheight']
        self['pixelWidth'] = self['width'] * self['tilewidth']
        self['layers'] = mapfiledata['layers']

        self['backgroundcolor'] = (32, 32, 32, 255)
        if 'backgroundcolor' in mapfiledata:
            self['backgroundcolor'] = self.convertTiledColor(mapfiledata['backgroundcolor'])

        if "properties" in mapfiledata:
            self["properties"] = mapfiledata['properties']
            self.convertTiledProps(self)

        '''
        Create quick reference dict from tileset name to firstgid.
        {filesetName1: firstgid1, tilesetName2: firstgid2, ...}
        '''
        self['tsFirstGid'] = {}
        for ts in mapfiledata['tilesets']:
            name = ts['source'].split("/")[-1].split(".")[0]
            self['tsFirstGid'][name] = ts['firstgid']

        # convert layer visibility data into a more compact form that is better for sending over network.
        self['layerVisabilityMask'] = 0
        for layerIndex in range(len(self['layers'])):
            if self['layers'][layerIndex]['visible'] == True:
                self.setLayerVisablitybyIndex(layerIndex, True)

        # set up quick reference to object lists of well known object layers.
        # these can be used directly rather than searching for these layers over and over.
        # it also ensures all these layers exist (via these refernces) in case they were not in the Tiled file.
        self['triggers'] = []
        self['sprites'] = []
        self['reference'] = []
        self['inBounds'] = []
        self['outOfBounds'] = []
        for l in self['layers']:
            if l['type'] == "objectgroup":
                if l['name'] == "triggers":
                    self['triggers'] = l['objects']
                elif l['name'] == "sprites":
                    self['sprites'] = l['objects']
                elif l['name'] == "reference":
                    self['reference'] = l['objects']
                elif l['name'] == "inBounds":
                    self['inBounds'] = l['objects']
                elif l['name'] == "outOfBounds":
                    self['outOfBounds'] = l['objects']

        '''
        layers and objects loaded from tiled need some data conversion and clean up to be useful
        '''
        for layer in self['layers']:
            self.convertTiledProps(layer)
            if layer['type'] == "tilelayer":
                if "compression" in layer:
                    log(f"Map {self['name']} contains a compressed tile layer (only CSV format is supported).", "FAILURE")
                    exit()
            elif layer['type'] == "objectgroup":
                for object in layer['objects']:
                    self.convertTiledProps(object)

                    # if this is a tiled "tile object"
                    if "gid" in object:
                        '''
                        tiled tile objects are anchored at bottom left but we want to anchor
                        all objects to the top left.
                        '''
                        object['y'] -= object['height']

                    if "text" in object:
                        if "color" in object['text']:
                            object['text']['color'] = self.convertTiledColor(object['text']['color'])

                    # remove object keys that Tiled saves but the game engine does not use/support.
                    # Doing this will help reduce unneeded data from being sent over the network.
                    for key in ("rotation", "id", "visible"):
                        if key in object:
                            del object[key]

                    # finally check the object for any other missing data or other issues that is not directly
                    # related to the tiled file format.
                    self.checkObject(object)

    def __str__(self):
        return engine.log.objectToStr(self, depth=2)

    def convertTiledColor(self, tiledColor):
        """Convert Tiled color HEX format to pygame format.

        Tiled hex colors with alpha are '#AARRGGBB' format but pygame
        needs '#RRGGBBAA' so flip alpha to the end.
        """
        if isinstance(tiledColor, str) and len(tiledColor) == 9 and tiledColor.startswith('#'):
            return f"#{tiledColor[3:9]}{tiledColor[1:3]}"
        return tiledColor

    def convertTiledProps(self, object):
        '''Convert Tiled properties to easy to use format.

        If 'properties' is in object then remove it and
        add prop-<name> to object for each property in
        'properties'.

        Args:
            object (dict): An object to evaluate.
        '''
        if "properties" in object:
            for prop in object['properties']:
                if prop['type'] == 'color':
                    prop['value'] = self.convertTiledColor(prop['value'])
                object["prop-" + prop['name']] = prop['value']
            del object['properties']

    ########################################################
    # MAP CHANGED
    ########################################################

    def setMapChanged(self, changed=True):
        """flag the map has changed (True) or not changed (False).

        This is used to determine if the server needs to send an
        update to clients.
        """
        self.changed = changed

    ########################################################
    # TILE GID
    ########################################################

    def findTile(self, tileGid):
        """Converts Tiled Gid for this map to a specific tileset name and tileset tile number.

        Args:
            tileGid (int): a map global tile number.

        Returns:
            tilesetName (str): name of tileset which contians tileGid
            tilesetTileNumber (int): tileNumber relative to tilesetName
        """
        for tilesetName in self['tsFirstGid']:
            firstGid = self['tsFirstGid'][tilesetName]
            lastGid = firstGid + self['tilesets'][tilesetName]['tilecount'] - 1
            if firstGid <= tileGid and tileGid <= lastGid:
                tilesetTileNumber = tileGid - firstGid
                return tilesetName, tilesetTileNumber

        # By design, this should never happen so we need to quit!
        log(f"tileGid {str(tileGid)} not found in map {self['name']}!", "FAILURE")
        exit()

    def findGid(self, tilesetSearchName, tilesetTileSearchNumber):
        """Converts a tileset specific tile number to a Gid of this map.

        This requires that tilesetSearchName is a tileset in this map!

        Args:
            tilesetSearchName (str): The name of a tileset.
            tilesetTileSearchNumber (int): A tile number from tilesetSearchName

        Returns:
            tileGid (int): A map global tile number.
        """
        for tilesetName in self['tsFirstGid']:
            if tilesetName == tilesetSearchName:
                return self['tsFirstGid'][tilesetName] + tilesetTileSearchNumber

        # By design this should never happen so we need to quit!
        # This probably means a tile object was added to this map but this map does
        # not have the required tileset added to it.
        log(f"tilesetName {str(tilesetSearchName)} not found in map {self['name']}!", "FAILURE")
        exit()

    ########################################################
    # OBJECT LIST (default objectList is self['sprites'])
    ########################################################

    def addObject(self, object, objectList=False):
        """Add a Tiled object to an object list.

        Used to add Tiled objects (e.g. sprites) to the object list of a layer.
        The default objectList is self['sprites'].

        Args:
            object (dict): Tiled object
            objectList (dict): An objectList from a layer on this map.
        """

        if not isinstance(objectList, list):
            objectList = self['sprites']

        # record in the object itself that it is now on this map.
        object['mapName'] = self['name']

        # add object to list
        objectList.append(object)

        # Update tile gid since destMap may have a different gid for the same tile image.
        if "gid" in object:
            object['gid'] = self.findGid(object['tilesetName'], object['tilesetTileNumber'])

        self.setMapChanged()

    def removeObject(self, object, objectList=False):
        """Remove a Tiled object from an object list.

        Used to remove Tiled objects (e.g. sprites) from the object list of a layer.
        The default objectList is self['sprites'].

        Note, this does not alter object['mapName'] since the object could be in
        other objectLists on this map.

        Args:
            object (dict): Tiled object
            objectList (dict): An objectList from a layer on this map.
        """

        if not isinstance(objectList, list):
            objectList = self['sprites']

        objectList.remove(object)
        self.setMapChanged()

    def removeObjectFromAllLayers(self, object):
        """Remove a Tiled object from all layers of this map.

        Used to remove Tiled objects (e.g. sprites) from the object list
        of all layers on this map.

        Note, this does not alter object['mapName'] since the object could
        be in the middle of being processed by a step loop that needs that
        data.

        Args:
            object (dict): Tiled object
        """

        # remove object from all object layers.
        if object in self['triggers']:
            self.removeObject(object, objectList=self['triggers'])
        if object in self['sprites']:
            self.removeObject(object, objectList=self['sprites'])
        if object in self['reference']:
            self.removeObject(object, objectList=self['reference'])
        if object in self['inBounds']:
            self.removeObject(object, objectList=self['inBounds'])
        if object in self['outOfBounds']:
            self.removeObject(object, objectList=self['outOfBounds'])

        # also remove object from any other layers (other than the well known ones above)
        for layer in self['layers']:
            if layer['type'] == "objectgroup":
                if object in layer['objects']:
                    layer['objects'].remove(object)

        self.setMapChanged()

    def findObject(self, x=None, y=None, width=0, height=0, forceCollisionType=False,
                   collisionType=False, name=False, type=False,
                   objectList=False, exclude=False, returnAll=False):
        '''Find a Tiled object that matches ALL criteria provided.

        Args:
            Collision detection can be done one of 2 ways:
                1) x (float), y (float), width==0, height==0:
                    Find object which collides (overlaps) with point: x, y
                2) x (float), y (float), width (float), height (float):
                    Find object which collides (overlaps) with rect: x, y, width, height.
                For 1) and 2) above:
                    - if width == 0 and height == 0 in arguments or in object
                      then it is treated as a point.
                    - if forceCollisionType != False then forceCollisionType will be used
                      in place of object['collisionType']. Some layers automatically have
                      forceCollisionType set to 'rect': triggers, inBounds, outOfBounds.
            collisionType(str): Find object with object['collisionType'] == collisionType
            name (str): Find object with object['name'] == name
            type (str): Find object with object['type'] == type
            objectList (dict): a list of objects to search. default is self['sprites']
            exclude (dict): a Tiled object. Skip this object while searching. Normally used
                to ensure an object does not find itself.
            returnAll (bool): Return a list of all matching objects, else return only the first
                matching object found.

        Returns: (one of the following)
            object (dict): A single Tiled object if a matching object was found and returnAll==False.
            False (bool): If no object was found and returnAll==False.
            objects (list): A possibly empty list of matching Tiled objects if returnAll==True.

        '''
        if not isinstance(objectList, list):
            objectList = self['sprites']

        # check for layers where we force rect collision for all objects on layer
        if objectList in (self['triggers'], self['inBounds'], self['outOfBounds']):
            forceCollisionType = 'rect'

        found = []
        for object in objectList:
            if type != False and object['type'] != type:
                continue
            if name != False and object['name'] != name:
                continue
            if exclude != False and exclude == object:
                continue
            if collisionType != False and object['collisionType'] != collisionType:
                continue
            if x is not None and y is not None:
                if forceCollisionType == 'anchor' or (
                        forceCollisionType == False and object['collisionType'] == 'anchor'):
                    if not geo.objectContains({'x': x, 'y': y, 'width': width, 'height': height},
                                              object['anchorX'], object['anchorY']):
                        continue
                elif forceCollisionType == 'rect' or (forceCollisionType == False and object['collisionType'] == 'rect'):
                    if not geo.objectContains(object, x, y, width, height):
                        continue
                else:
                    continue

            if not returnAll:
                return object
            found.append(object)

        if not returnAll:
            return False
        return found

    ########################################################
    # OBJECTS (mostly useful for sprites)
    ########################################################

    def checkObject(self, object):
        """Check that object has required keys.

        Ensure object meets all basic criteria that are required by the server.
        If an empty object ({}) is passed then it is populated with default
        values until it meets the minimum requirements of a Tiled object.

        The minimum object contains:
        {
            'name': (str)
            'type': (str)
            'x': (float)
            'y': (float)
            'width': (float)
            'height': (float)
            'anchorX': (float)
            'anchorY': (float)
            'collisionType': (str)
            'mapName': (str) The last map the object was on (or is still on).

            Only for tile objects have the following:
            'gid': (int) Map Global Tile ID.
            'tilesetName': (str) Tile Tileset Name.
            'tilesetTileNumber': (int) Tileset Tile Number.
        }

        Args:
            object (dict)

        Returns:
            object (dict): Object is both edited in place and also returned.
        """

        if "mapName" not in object:
            object['mapName'] = self['name']
        if "name" not in object:
            object['name'] = ""
        if "type" not in object:
            object['type'] = ""
        if "width" not in object:
            object['width'] = 0
        if "height" not in object:
            object['height'] = 0
        if "collisionType" not in object:
            object['collisionType'] = "anchor"

        # if this is a Tile Object
        if "gid" in object and ("tilesetName" not in object or "tilesetTileNumber" not in object):
            '''
            objects may move between maps so in addition to the gid in this map we need to store
            the tileset name and tile number relative to the tileset so it can be used in other maps.
            '''
            object['tilesetName'], object['tilesetTileNumber'] = self.findTile(object['gid'])

        # we assume that if object has x then it has y AND if it has anchorX then it has anchorY
        if "x" not in object and "anchorX" not in object:
            object['x'] = 0
            object['anchorX'] = 0
            object['y'] = 0
            object['anchorY'] = 0
        elif "x" in object and "anchorX" not in object:
            self.setObjectLocationByXY(object, object['x'], object['y'])
        elif "x" not in object and "anchorX" in object:
            self.setObjectLocationByAnchor(object, object['anchorX'], object['anchorY'])

        # The original object has been edited but also return it so the function can be passed
        return object

    def checkLocation(self, object, newAnchorX, newAnchorY, ignoreInBounds=False):
        """Check if a location for an object is valid.

        Determines if (newAnchorX, newAnchorY) would be a valid anchor point for
        object while taking several things into account, including map size, inBounds layer,
        and outOfBounds layer, collision with other sprites.

        Note, the priority evaluation is as follows:
        1) if object collides (overlaps) with another sprite then it is NOT valid.
           Note, two objects with collisionType == 'anchor' are allowed in the same location.
        2) if object does not fully collide (overlap) with the map then it is NOT valid.
        3) if object collides (overlaps) with an object on the outOfBounds layer then it is NOT valid.
        4) if the inBounds layer is empty or ignoreInBounds == True then it IS valid
        5) if object is fully inside an object or objects on the inBounds layer then it IS valid.
        6) else it is NOT valid.

        Args:
            object (dict): A Tiled object.
            newAnchorX (float): x coordiate to check if valid
            newAnchorY (float): y coordiate to check if valid
            ignoreInBounds (bool): if True then do not consider inBounds layers (default False)

        Returns:
            bool: True if an anchor point of (newAnchorX, newAnchorY) would be a valid for object, else False
        """

        # if object is a player and player move checking has been turned off then return True
        if object['type'] == 'player' and not engine.server.SERVER['playerMoveCheck']:
            return True

        if object['collisionType'] == 'anchor':
            newX = newAnchorX
            newY = newAnchorY
            width = 0
            height = 0
            # Only check for other sprites with collisionType=='rect' since we allow
            # two sprites with collisionType=='anchor' to overlap.
            otherSpriteCollisionType = 'rect'
        elif object['collisionType'] == 'rect':
            newX = newAnchorX - (object['anchorX'] - object['x'])
            newY = newAnchorY - (object['anchorY'] - object['y'])
            width = object['width']
            height = object['height']
            # these types of objects can collide with all other types of sprites.
            otherSpriteCollisionType = False
        else:
            log(f"collisionType is not supported.", "ERROR")
            return False

        # if object collides (overlaps) with another sprite then it is NOT valid.
        if self.findObject(x=newX, y=newY, width=width, height=height,
                           collisionType=otherSpriteCollisionType, exclude=object):
            return False

        # if object does not fully collide (overlap) with the map then it is NOT valid.
        if 0 > newX or newX + width > self['pixelWidth'] or 0 > newY or newY + height > self['pixelHeight']:
            return False

        # if object collides (overlaps) with an object on the outOfBounds layer then it is NOT valid.
        if width == 0 and height == 0:  # for speed only do one check in this case since the 4 below are all the same.
            if self.findObject(x=newX, y=newY, objectList=self['outOfBounds']):
                return False
        else:
            if self.findObject(x=newX, y=newY, objectList=self['outOfBounds']) or \
                    self.findObject(x=newX + width, y=newY, objectList=self['outOfBounds']) or \
                    self.findObject(x=newX, y=newY + height, objectList=self['outOfBounds']) or \
                    self.findObject(x=newX + width, y=newY + height, objectList=self['outOfBounds']):
                return False

        # if the inBounds layer is empty then it IS valid
        if len(self['inBounds']) == 0 or ignoreInBounds:
            return True

        # if object is fully inside an object or objects on the inBounds layer then it IS valid.
        if width == 0 and height == 0:  # for speed only do one check in this case since the 4 below are all the same.
            if self.findObject(x=newX, y=newY, objectList=self['inBounds']):
                return True
        else:
            if self.findObject(x=newX, y=newY, objectList=self['inBounds']) and \
                    self.findObject(x=newX + width, y=newY, objectList=self['inBounds']) and \
                    self.findObject(x=newX, y=newY + height, objectList=self['inBounds']) and \
                    self.findObject(x=newX + width, y=newY + height, objectList=self['inBounds']):
                return True

        # else it is NOT valid.
        return False

    def checkKeys(self, object, props):
        """Check if all props are keys in object.

        This can be used by a method to check if an object has all the
        data required. If data is missing then a warning
        is logged that suggests where the data may be missing from.

        Args:
            object (dict): Tiled object
            props (list): A list of keys. e.g. ["prop-deltaX", "anchorX"]

        Returns:
            bool: True if all props are in object else False
        """
        result = True
        for p in props:
            if p not in object:
                result = False
                name = "object"
                if object['name']:
                    name = f"object with name={object['name']}"
                elif object['type']:
                    name = f"object with type={object['type']}"
                if p.startswith('prop-'):
                    tiledProp = p[5:]
                    log(f"Missing Tiled property {tiledProp} in {name}", "WARNING")
                else:
                    log(f"Missing key {p} in {name}", "WARNING")
        return result

    def setObjectLocationByXY(self, object, x, y):
        """Set an objects location using its top/left corner.

        Updates an object x,y and then sets it anchor point to match.
        Do not use without good reason. Most objects should have their
        location set by setObjectLocationByAnchor()

        Args:
            object (dict): A Tiled Object
            x (float)
            y (float)
        """

        object['x'], object['y'] = x, y
        '''
        set the anchor for the object, this is the point we consider to be the point
        location of the object.
        '''
        if "gid" in object:
            # for tile objects, the tileset will define the anchor point.
            object['anchorX'] = object['x'] + self['tilesets'][object['tilesetName']
                                                               ].getAnchorX(object['tilesetTileNumber'])
            object['anchorY'] = object['y'] + self['tilesets'][object['tilesetName']
                                                               ].getAnchorY(object['tilesetTileNumber'])
        else:
            # set anchor to be the middle of the objects rect.
            object['anchorX'] = object['x'] + object['width'] / 2
            object['anchorY'] = object['y'] + object['height'] / 2

        self.setMapChanged()

    def setObjectLocationByAnchor(self, object, anchorX, anchorY):
        """Set an objects location using its anchor point.

        Updates an object anchor point and then sets it x, y to match.

        Args:
            object (dict): A Tiled Object
            x (float)
            y (float)
        """

        # make sure object stays on map:
        if anchorX < 0:
            anchorX = 0
        elif anchorX >= self['pixelWidth']:
            anchorX = self['pixelWidth'] - 1
        if anchorY < 0:
            anchorY = 0
        elif anchorY >= self['pixelHeight']:
            anchorY = self['pixelHeight'] - 1

        object['anchorX'], object['anchorY'] = anchorX, anchorY

        if "gid" in object:
            object['x'] = anchorX - self['tilesets'][object['tilesetName']].getAnchorX(object['tilesetTileNumber'])
            object['y'] = anchorY - self['tilesets'][object['tilesetName']].getAnchorY(object['tilesetTileNumber'])
        else:
            # set anchor to be the middle of the objects rect.
            object['x'] = anchorX - object['width'] / 2
            object['y'] = anchorY - object['height'] / 2
        self.setMapChanged()

    def setObjectMap(self, object, destMap):
        """Move a Tiled object to a differnt map.

        Remove object from all known layers on this map and add
        it to the same layers on destMap.

        Args:
            object (dict): Tiled object
            destMap (engine.map.Map)

        """

        if object in self['triggers']:
            self.removeObject(object, objectList=self['triggers'])
            destMap.addObject(object, objectList=destMap['triggers'])

        if object in self['sprites']:
            self.removeObject(object, objectList=self['sprites'])
            destMap.addObject(object, objectList=destMap['sprites'])

        if object in self['reference']:
            self.removeObject(object, objectList=self['reference'])
            destMap.addObject(object, objectList=destMap['reference'])

        if object in self['inBounds']:
            self.removeObject(object, objectList=self['inBounds'])
            destMap.addObject(object, objectList=destMap['inBounds'])

        if object in self['outOfBounds']:
            self.removeObject(object, objectList=self['outOfBounds'])
            destMap.addObject(object, objectList=destMap['outOfBounds'])

    ########################################################
    # LAYER VISABILITY MECHANIC
    ########################################################

    def setLayerVisablitybyName(self, layerName, visable):
        """LAYER VISABILITY MECHANIC: Show/Hide layer by name.

        Args:
            layerName (str): The name of a layer as defined in Tiled.
            visable (bool): True == visible.
        """
        for layerIndex in range(len(self['layers'])):
            if self['layers'][layerIndex]['name'] == layerName:
                self.setLayerVisablitybyIndex(layerIndex, visable)

    def setLayerVisablitybyIndex(self, layerIndex, visable):
        """LAYER VISABILITY MECHANIC: Show/Hide layer by index.

        Args:
            layerIndex (str): The index of a layer in self['layers'].
            visable (bool): True == visible.
        """
        old = self['layerVisabilityMask']
        if visable:
            self['layerVisabilityMask'] = self['layerVisabilityMask'] | (1 << layerIndex)
        else:
            self['layerVisabilityMask'] = self['layerVisabilityMask'] & ~(1 << layerIndex)
        if old != self['layerVisabilityMask']:
            self.setMapChanged()

    def getLayerVisablitybyName(self, layerName):
        """LAYER VISABILITY MECHANIC: Return true if layer is set to visible else return False.

        Args:
            layerName (str)

        Returns:
            bool
        """
        for layerIndex in range(len(self['layers'])):
            if self['layers'][layerIndex]['name'] == layerName:
                return self.getLayerVisablitybyIndex(layerIndex)

    def getLayerVisablitybyIndex(self, layerIndex):
        """LAYER VISABILITY MECHANIC: Return true if layer is set to visible else return False.

        Args:
            layerIndex (int)

        Returns:
            bool
        """
        if self['layerVisabilityMask'] & (1 << layerIndex) != 0:
            return True
        return False

    def getLayerVisablityMask(self):
        """LAYER VISABILITY MECHANIC: Return bit mask for the visibility of all layers in self['layers']

        Returns:
            layerVisabilityMask (int): bitmask where left most bit relates
                the visibility of layerIndex 0, the next bit relates to
                layerIndex 1, and so on.
        """
        return self['layerVisabilityMask']

    def setLayerVisablityMask(self, layerVisabilityMask):
        """LAYER VISABILITY MECHANIC: Set bit mask for the visibility of all layers in self['layers']

        Args:
            layerVisabilityMask (int): bitmask where left most bit relates
                the visibility of layerIndex 0, the next bit relates to
                layerIndex 1, and so on.

        Returns:
            bool: True if the layerVisabilityMask mask was different from
                the mask that was already set.
        """
        if self['layerVisabilityMask'] == layerVisabilityMask:
            return False
        self['layerVisabilityMask'] = layerVisabilityMask
        self.setMapChanged()
        return True
