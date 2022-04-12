"""Load Tiled Tileset Data."""

import json

import engine.log
from engine.log import log


class Tileset(dict):
    '''
    The Tileset class is responsible for loading Tiled tileset files so they can be used by the game engine.

    It is assumed this class will be sub-classed to add additional functionality.

    Tiles within a tileset are numbers from left to right and top to bottom. The top
    left tile is number 0, the tile to it's right is numbered 1, and so on.
    '''

    def __init__(self, tilesetFile):
        """Load tileset file and do data conversion.

        Note, all Tiled properites will be converted into an easier to access form.
            from: {object['properties'][{name: name1, value: value1}],[...]}
            to: {object['prop-name1']=value1,...}
        Note, duplicate property names is not supported!

        Args:
            tilesetFile (str): path and filename of tileset.
        """
        self['tilesetFile'] = tilesetFile
        # Tileset name is based on tilesetFile with .json removed
        self['name'] = tilesetFile.split("/")[-1].split(".")[0]

        with open(self['tilesetFile']) as f:
            ts = json.load(f)

        if ts['type'] != "tileset":
            log(f"{failename} does not appear to be a tileset!", "FAILURE")
            exit()

        # store for later use in case needed by a subclass.
        self['tilesetfiledata'] = ts

        self['tileheight'] = ts['tileheight']
        self['tilewidth'] = ts['tilewidth']
        self['imageheight'] = ts['imageheight']
        self['imagewidth'] = ts['imagewidth']
        self['tilecount'] = ts['tilecount']
        self['imagefile'] = ts['image']

        # convert tiled object properties
        if "properties" in ts:
            for prop in ts['properties']:
                self["prop-" + prop['name']] = prop['value']

        self['tiles'] = {}
        if "tiles" in ts:
            for tile in ts['tiles']:
                # convert tiled object properties
                if "properties" in tile:
                    for prop in tile['properties']:
                        tile["prop-" + prop['name']] = prop['value']
                    del tile['properties']

                # compute total length of animation
                if "animation" in tile:
                    tile['animationDuration'] = 0
                    for t in tile['animation']:
                        tile['animationDuration'] += t['duration']
                    # convert to seconds
                    tile['animationDuration'] /= 1000

                self['tiles'][tile['id']] = tile

    def __str__(self):
        return engine.log.objectToStr(self)

    def getAnchorX(self, tileNumber):
        """Return X anchor point of tileNumber.

        Search for most specific anchorX for tileNumber. Look first for
        "anchorX" property in the tile itself, then for "anchorX" property
        in the tileset. If nothing is found then assume the anchoX is in
        the middle of the the tile.

        Args:
            tileNumber (int)

        Returns:
            anchorX (int)
        """
        if tileNumber in self['tiles'] and 'prop-anchorX' in self['tiles'][tileNumber]:
            return self['tiles'][tileNumber]['prop-anchorX']
        elif 'prop-anchorX' in self:
            return self['prop-anchorX']
        else:
            return self['tilewidth'] / 2

    def getAnchorY(self, tileNumber):
        """Return Y anchor point of tileNumber.

        Search for most specific anchorY for tileNumber. Look first for
        "anchorY" property in the tile itself, then for "anchorY" property
        in the tileset. If nothing is found then assume the anchoY is in
        the middle of the the tile.

        Args:
            tileNumber (int)

        Returns:
            anchorY (int)
        """
        if tileNumber in self['tiles'] and 'prop-anchorY' in self['tiles'][tileNumber]:
            return self['tiles'][tileNumber]['prop-anchorY']
        elif 'prop-anchorY' in self:
            return self['prop-anchorY']
        else:
            return self['tileheight'] / 2
