"""Load and Manage Tiled Map Data."""
import json
import os

import engine.log
from engine.log import log
import engine.geometry as geo
from engine.geometry import collidesFast


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
            to: {object['prop-name1']=value1,...}
        Note, duplicate property names is not supported!

        Args:
            tilesets (dict): a dict of Tileset objects.
            mapDir (str): path to map directory.
        """
        self['tilesets'] = tilesets
        self['mapDir'] = mapDir

        # Flag to say something on this map has changed
        self.setMapChanged()

        # self['follow'] is an array of game objects that follow other game objects.
        # Form: [{'leader': leaderObject, 'followers': [(followerObject, deltaAnchorX, deltaAnchorY),...]}, ...]
        # See FOLLOW section below.
        self['follow'] = []

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

                    # default all objects on these layers to have collisonType == 'rect'. If they were left
                    # with collisionType=='anchor' then they would not collid with anything and would not
                    # function as expected.
                    if layer['name'] in ('triggers', 'inBounds', 'outOfBounds'):
                        object['collisionType'] = 'rect'

                    # finally check the object for any other missing data or other issues that is not directly
                    # related to the tiled file format.
                    self.checkObject(object)
                # sort objects by area from largest to smallest. This will make finding collisions slightly faster.
                layer['objects'].sort(key=lambda o: o['width']*o['height'], reverse=True)

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
                log(f"Object layer '{l['name']}' contains {len(l['objects'])} objects.","VERBOSE")
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
    # TILE GID (Tile Map Global Identifier)
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
    # FOLLOW
    ########################################################

    def addFollower(self, leaderObject, followerObject):
        """Add leaderObject/followerObject relationship to self['follow']
        This also records the relative position of the objects.

        This information is used by setObjectLocationByAnchor() and setObjectMap()
        and causes the followerObject to follow the position of the leaderObject.

        Once a followerObject has been added it should not longer be used with
        setObjectLocationByAnchor() or setObjectMap(), only the leaderObject
        should.
        """
        deltaAnchorX = followerObject['anchorX'] - leaderObject['anchorX']
        deltaAnchorY = followerObject['anchorY'] - leaderObject['anchorY'] 
        for i in range(len(self['follow'])):
            if self['follow'][i]['leader'] == leaderObject:
                for fo in self['follow'][i]['followers']:
                    if fo[0] == followerObject:
                        return  # followerObject has already been added.
                self['follow'][i]['followers'].append((followerObject,deltaAnchorX,deltaAnchorY))
                return
        self['follow'].append({'leader': leaderObject, 'followers': [(followerObject,deltaAnchorX,deltaAnchorY)]})


    def removeFollower(self, leaderObject, followerObject):
        """Remove leaderObject/followerObject relationship from self['follow']"""

        for i in range(len(self['follow'])):
            if self['follow'][i]['leader'] == leaderObject:
                for fo in self['follow'][i]['followers']:
                    if fo[0] == followerObject:
                        self['follow'][i]['followers'].remove(fo)
                    if len(self['follow'][i]['followers']) == 0:
                        del self['follow'][i]
                return

    def getFollowers(self, leaderObject):
        """Returns array of objects that follow leaderObject: [object,object,object]"""
        followers = []
        for i in range(len(self['follow'])):
            if self['follow'][i]['leader'] == leaderObject:
                for followerObject, deltaAnchorX, deltaAnchorY in self['follow'][i]['followers']:
                    followers.append(followerObject)
        return followers

    def logFollow(self, m):
        """log() a human readable version of m['follow'] (for debugging)"""
        f=m['follow']
        log(f"***** {m['name']}['follow'] ****")
        for a in f:
            line = f"{a['leader']['name']} -> "
            for b in a['followers']:
                line = f"{line} {b[0]['name']} "
            log(line)


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

    def findObject(self, name=False, type=False, collisionType=False, 
                   collidesWith=False, overlap='partial',
                   objectList=False, exclude=False, returnAll=False):
        '''Find a Tiled object that matches ALL criteria provided.

        Args:
            name (str): Find object with object['name'] == name
            type (str): Find object with object['type'] == type   
            collisionType(str): Find object with object['collisionType'] == collisionType
            collidesWith(dict): Find object which collides with object provided. See
                geometry.collides() for details.
            overlap(str): Only used if collidesWith is given. Passed to geometry.collides() 
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
        
        found = []
        for object in objectList:
            if name != False and object['name'] != name:
                continue
            if type != False and object['type'] != type:
                continue
            if collisionType != False and object['collisionType'] != collisionType:
                continue
            if exclude != False and exclude == object:
                continue
            if collidesWith != False and not geo.collides(collidesWith, object, overlap=overlap):
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
            'collisionType': (str) One of 'none', 'anchor', 'rect', 'circle'
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
            object['collisionType'] = 'anchor'

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
        if object['collisionType'] == 'none':
            return True

        # if object is a player and player move checking has been turned off then return True
        if object['type'] == 'player' and not engine.server.SERVER['playerMoveCheck']:
            return True

        newX = newAnchorX - (object['anchorX'] - object['x'])
        newY = newAnchorY - (object['anchorY'] - object['y'])
        collidesWith = {
            'x':newX,
            'y':newY,
            'anchorX':newAnchorX,
            'anchorY':newAnchorY,
            'width':object['width'],
            'height':object['height'],
            'collisionType':object['collisionType']
        }

        # if object collides (overlaps) with another sprite then it is NOT valid.
        # The next two lines were removed and replaced with the lines below to increase performance.
        #if self.findObject(collidesWith=collidesWith, exclude=object):
        #    return False
        for o in self['sprites']:
            # do a quick check to see if we can avoid collidesFast() function call.
            if collidesWith['collisionType'] != 'line' and ((o['collisionType']!='rect' and o['collisionType']!='circle') or \
                o['x'] > collidesWith['x']+collidesWith['width'] or o['y'] > collidesWith['y']+collidesWith['height'] or \
                collidesWith['x'] > o['x']+o['width'] or collidesWith['y'] > o['y']+o['height']):
                continue
            # using collidesFast() assumes sprite objects have collision types of rect or circle. Others will return False
            if collidesFast(collidesWith,collidesWith['collisionType'], o,o['collisionType']) and o != object:
                return False

        # if object does not fully collide (overlap) with the map then it is NOT valid.
        if not collidesFast(collidesWith,
                collidesWith['collisionType'],
                {
                    'x':0,
                    'y':0,
                    'anchorX':self['pixelWidth']/2,
                    'anchorY':self['pixelHeight']/2,
                    'width':self['pixelWidth'],
                    'height':self['pixelHeight']
                },
                'rect',
                overlap='full'):
            return False

        # if object collides (overlaps) with an object on the outOfBounds layer then it is NOT valid.
        # The next two lines were removed and replaced with the lines below to increase performance.
        #if self.findObject(collidesWith=collidesWith, objectList=self['outOfBounds']):
        #    return False
        for o in self['outOfBounds']:
            # do a quick check to see if we can avoid collidesFast() function call.
            if collidesWith['collisionType'] != 'line' and ((o['collisionType']!='rect' and o['collisionType']!='circle') or \
                o['x'] > collidesWith['x']+collidesWith['width'] or o['y'] > collidesWith['y']+collidesWith['height'] or \
                collidesWith['x'] > o['x']+o['width'] or collidesWith['y'] > o['y']+o['height']):
                continue
            # using collidesFast() assumes outOfBounds objects have collision types of rect or circle
            if collidesFast(collidesWith,collidesWith['collisionType'], o,o['collisionType']) and o != object:
                return False

        # if the inBounds layer is empty or explicitly ignoring inBounds then it IS valid
        if len(self['inBounds']) == 0 or ignoreInBounds:
            return True

        # if object is fully inside an object or objects on the inBounds layer then it IS valid.
        # ============================================
        # BUG: THIS CODE DOES NOT WORK IF OBJECTS NEEDS TO BE ON MULTIPLE inBounds OBJECTS TO BE INBOUNDS.
        # ============================================
        # The next two lines were removed and replaced with the lines below to increase performance.
        #if self.findObject(collidesWith=collidesWith, overlap='full', objectList=self['inBounds']):
        #    return True
        for o in self['inBounds']:
            # do a quick check to see if we can avoid collidesFast() function call.
            if collidesWith['collisionType'] != 'line' and ((o['collisionType']!='rect' and o['collisionType']!='circle') or \
                o['x'] > collidesWith['x']+collidesWith['width'] or o['y'] > collidesWith['y']+collidesWith['height'] or \
                collidesWith['x'] > o['x']+o['width'] or collidesWith['y'] > o['y']+o['height']):
                continue
            # using collidesFast() assumes outOfBounds objects have collision types of rect or circle
            if collidesFast(collidesWith,collidesWith['collisionType'], o,o['collisionType'], overlap='full') and o != object:
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
        
        ***Do not use without good reason. Most objects should have their
        location set by setObjectLocationByAnchor()***

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
        Also updates the relative position of any following objects.

        Args:
            object (dict): A Tiled Object
            x (float)
            y (float)
        """

        object['anchorX'], object['anchorY'] = anchorX, anchorY

        if "gid" in object:
            object['x'] = anchorX - self['tilesets'][object['tilesetName']].getAnchorX(object['tilesetTileNumber'])
            object['y'] = anchorY - self['tilesets'][object['tilesetName']].getAnchorY(object['tilesetTileNumber'])
        else:
            # set anchor to be the middle of the objects rect.
            object['x'] = anchorX - object['width'] / 2
            object['y'] = anchorY - object['height'] / 2

        for i in range(len(self['follow'])):
            if self['follow'][i]['leader'] == object:
                for followerObject, deltaAnchorX, deltaAnchorY in self['follow'][i]['followers']:
                    self.setObjectLocationByAnchor(followerObject, anchorX+deltaAnchorX, anchorY+deltaAnchorY)
                
        self.setMapChanged()

    def setObjectMap(self, object, destMap):
        """Move a Tiled object to a different map.

        Remove object from all known layers on this map and add
        it to the same layers on destMap. Also move any following
        objects to the new map.

        Args:
            object (dict): Tiled object
            destMap (engine.map.Map)

        """

        # if we are moving the object from one map to the same map then we are done.
        if(self == destMap):
            return

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

        followObjects = self.getFollowers(object)
        for f in followObjects:
            self.removeFollower(object,f)
            self.setObjectMap(f, destMap)
            destMap.addFollower(object,f)


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
