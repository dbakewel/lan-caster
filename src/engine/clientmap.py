"""Render (blit) Tiled Map Data"""
import pygame
from pygame.locals import *
import engine.time as time
import os
import sys
import re

from engine.log import log
import engine.map
import engine.geometry as geo


class ClientMap(engine.map.Map):
    """
    The ClientMap class is responsible for rendering a map for the player to see.
    """

    #####################################################
    # INIT METHODS
    #####################################################

    def __init__(self, tilesets, mapDir):
        """Set defaults, sort data, and allocate images (pygame surfaces) for rendering."""

        super().__init__(tilesets, mapDir)

        # Layers with these names will not normally be rendered to the screen unless a direct
        # call to blitLayer or blitObjectList is made.
        self['HIDELAYERS'] = (
            "sprites",  # the sprites in the arg list of stepMap will be rendered but not the self['layers']['sprites']
            "inBounds",
            "outOfBounds",
            "triggers",
            "reference"
            )

        # default values for optional keys in a textObject['text'] dict.
        self['DEFAULTTEXT'] = {
            "bold": False,
            "color": "#00ff00",
            "fontfamily": None,
            "halign": "left",
            "pixelsize": 16,
            "underline": False,
            "valign": "top",
            "wrap": True,
            "bgcolor": "#000000",
            "bgbordercolor": "#000000",
            "bgborderThickness": 0,
            "bgroundCorners": 0,
            "antialiased": True
            }

        # speechText defaults that differ from DEFAULTTEXT
        self['SPEACHTEXT'] = {
            "valign": "bottom",
            "halign": "center"
            }

        # labelText defaults that differ from DEFAULTTEXT
        self['LABELTEXT'] = {
            "halign": "center",
            "valign": "top"
            }

        # sort object layers for right-down rendering
        for layer in self['layers']:
            if layer['type'] == "objectgroup":
                geo.sortRightDown(layer['objects'], self['pixelWidth'])

        # allocate image for each layer (exclude hidden layers since we will never need the image)
        for layer in self['layers']:
            if layer['name'] not in self['HIDELAYERS']:
                layer['image'] = pygame.Surface(
                    (self['width'] * self['tilewidth'], self['height'] * self['tileheight']),
                    pygame.SRCALPHA,
                    32)
                layer['image'] = layer['image'].convert_alpha()
                layer['imageValidUntil'] = 0  # invalid and needs to be rendered.

        self['bottomImage'] = pygame.Surface(
            (self['width'] * self['tilewidth'], self['height'] * self['tileheight']),
            pygame.SRCALPHA,
            32)
        self['bottomImage'] = self['bottomImage'].convert_alpha()
        self['bottomImageValidUntil'] = 0  # invalid and needs to be rendered.

        self['topImage'] = pygame.Surface(
            (self['width'] * self['tilewidth'], self['height'] * self['tileheight']),
            pygame.SRCALPHA,
            32)
        self['topImage'] = self['topImage'].convert_alpha()
        self['topImageValidUntil'] = 0  # invalid and needs to be rendered.

    ########################################################
    # LAYER VISABILITY
    ########################################################

    def setLayerVisablityMask(self, layerVisabilityMask):
        """If layer visibility changes then mark top and bottom images as invalid."""

        if super().setLayerVisablityMask(layerVisabilityMask):  # returns True only if mask changed.
            # invalidate top and bottom images since they may have changed.
            self['bottomImageValidUntil'] = 0
            self['topImageValidUntil'] = 0

    #####################################################
    # BLIT MAP
    #####################################################

    def blitMap(self, destImage, offset, sprites):
        """Render map onto destImage.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            sprites (list): List of Tiled objects. While most layers are static
                on the client, a new sprite layer can be sent from the server
                each step.
        """
        # sort sprites for right-down render order.
        geo.sortRightDown(sprites, self['pixelWidth'])

        destImage.fill(self['backgroundcolor'])

        validUntil = []
        # start with all visible layers below the sprites.
        validUntil.append(self.blitBottomImage(destImage, offset))

        # blit the sprite label text from the server under all sprites.
        validUntil.append(self.blitObjectListLabelText(destImage, offset, sprites))

        # blit the sprite layer from the server
        validUntil.append(self.blitObjectList(destImage, offset, sprites))

        # add all visible layers above the sprites
        validUntil.append(self.blitTopImage(destImage, offset))

        # blit the sprite speech text from the server on top of everything.
        validUntil.append(self.blitObjectListSpeechText(destImage, offset, sprites))

        return min(validUntil)

    def blitBottomImage(self, destImage, offset):
        """Blit together all the visible layers BELOW the sprite layer.

        Store in self['bottomImage']. self['bottomImage'] can then be used for faster
        screen updates rather than doing all the work of blitting these layers together
        every frame.

        Note object layer "sprites" will not be rendered since is is
        provided by the server and must be rendered separately with a direct
        call to blitObjectList()

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
        """

        # if there is already a valid image then don't render a new one
        if self['bottomImageValidUntil'] < time.perf_counter():
            # Start with transparent background and a black border. The border will normally not be seen it other
            # graphics go on top of it.
            self['bottomImage'].fill((0, 0, 0, 0))
            self.blitRectObject(self['bottomImage'], (0, 0), {
                'x': 0,
                'y': 0,
                'width': self['pixelWidth'],
                'height': self['pixelHeight']
                },
                fillColor=(0, 0, 0, 0),
                borderColor=(0, 0, 0, 255))

            self['bottomImageValidUntil'] = sys.float_info.max
            for layerNumber in range(len(self['layers'])):
                if self['layers'][layerNumber]['name'] == "sprites":
                    break
                if self['layers'][layerNumber]['name'] in self['HIDELAYERS']:
                    continue
                # if the layer is visible then add it to the destImage
                if self.getLayerVisablitybyIndex(layerNumber):
                    vu = self.blitLayer(self['bottomImage'], (0, 0), self['layers'][layerNumber])
                    if self['bottomImageValidUntil'] > vu:
                        self['bottomImageValidUntil'] = vu

        destImage.blit(self['bottomImage'], offset)
        return self['bottomImageValidUntil']

    def blitTopImage(self, destImage, offset):
        """Blit together all the visible layers ABOVE the sprite layer.

        Store in self['topImage']. self['topImage'] can then be used for faster
        screen updates rather than doing all the work of blitting these layers
        together every frame.

        Note object layer named "sprites" will not be rendered since
        they are provided by the server and must be rendered separately with a direct
        call to blitObjectList()

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
        """

        # if there is already a valid image then don't render a new one
        if self['topImageValidUntil'] < time.perf_counter():
            # Start with transparent background.
            self['topImage'].fill((0, 0, 0, 0))

            self['topImageValidUntil'] = sys.float_info.max
            passedSpriteLayer = False
            for layerNumber in range(len(self['layers'])):
                if self['layers'][layerNumber]['name'] == "sprites":
                    passedSpriteLayer = True
                    continue
                if self['layers'][layerNumber]['name'] in self['HIDELAYERS']:
                    continue
                if passedSpriteLayer == True:
                    # if the layer is visible then add it to the destImage
                    if self.getLayerVisablitybyIndex(layerNumber):
                        vu = self.blitLayer(self['topImage'], (0, 0), self['layers'][layerNumber])
                        if self['topImageValidUntil'] > vu:
                            self['topImageValidUntil'] = vu

        destImage.blit(self['topImage'], offset)
        return self['topImageValidUntil']

    #####################################################
    # BLIT LAYER, GRIDS, and OBJECTLISTS
    #####################################################

    def blitLayer(self, destImage, offset, layer):
        """Blit layer onto destImage.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            layer (dict): Tiled layer from self['layers']
        """

        # if there is already a valid image then don't render a new one
        if layer['imageValidUntil'] < time.perf_counter():
            # Start with transparent background.
            layer['image'].fill((0, 0, 0, 0))

            if layer['type'] == "tilelayer":
                layer['imageValidUntil'] = self.blitTileGrid(layer['image'], (0, 0), layer['data'])
            elif layer['type'] == "objectgroup":
                layer['imageValidUntil'] = self.blitObjectList(layer['image'], (0, 0), layer['objects'])

        destImage.blit(layer['image'], offset)
        return layer['imageValidUntil']

    def blitTileGrid(self, destImage, offset, grid):
        """Blit tile grid onto destImage.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            grid (list of int): A list ints ([0,0,5,27,2,...]) where each
                int is the map global tile id (gid) to render into that grid
                position. The length of the list must match the number of tiles
                that make up the map. Tile order is top left corner first, then
                move right to end of row and then move down to next row (right-down).
                Note, a gid of 0 means do not render a tile in that position.
        """

        validUntil = sys.float_info.max
        for i in range(len(grid)):
            if grid[i] != 0:
                tileX = i % self['width']
                tileY = int(i / self['width'])
                destPixelX = tileX * self['tilewidth'] + offset[0]
                destPixelY = tileY * self['tileheight'] + offset[1]

                tilesetName, tilesetTileNumber = self.findTile(grid[i])
                ts = self['tilesets'][tilesetName]

                # tiles that are bigger than the grid tiles are indexed from the bottom left tile of the grid
                # so we need to adjust the destPixelY to the true pixel top left.
                if(ts['tileheight'] > self['tileheight']):
                    destPixelY -= (ts['tileheight'] - self['tileheight'])
                elif(ts['tileheight'] < self['tileheight']):
                    log("using tiles smaller than tile layer is not supported yet.", "FAILURE")
                    exit()

                vu = ts.blitTile(tilesetTileNumber, destImage, destPixelX, destPixelY)
                if validUntil > vu:
                    validUntil = vu

        return validUntil

    def blitObjectList(self, destImage, offset, objectList):
        """Blit each object in objectList.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            objectList (list of Tiled objects): [(dict),(dict),...]
        """
        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            vu = self.blitObject(destImage, offset, object)
            validUntil = min(validUntil, vu)
        return validUntil

    def blitObject(self, destImage, offset, object):
        """Blit object.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            object: dict
        """
        validUntil = sys.float_info.max
        if "gid" in object:
            validUntil = self.blitTileObject(destImage, offset, object)
        elif "text" in object:
            validUntil = self.blitTextObject(destImage, offset, object)
        elif "ellipse" in object:
            validUntil = self.blitRoundObject(destImage, offset, object)
        elif "point" in object:
            validUntil = self.blitRoundObject(destImage, offset, object)
        elif "polyline" in object:
            validUntil = self.blitPolyObject(destImage, offset, object)
        elif "polygon" in object:
            validUntil = self.blitPolyObject(destImage, offset, object)
        else:  # this is a rect
            validUntil = self.blitRectObject(destImage, offset, object)
        return validUntil

    #####################################################
    # BLIT TILE OBJECT
    #####################################################

    def blitTileObject(self, destImage, offset, tileObject):
        """Blit Tiled object to destImage.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            tileObject (dict): Tiled Object
        """
        tilesetName, tilesetTileNumber = self.findTile(tileObject['gid'])
        tileset = self['tilesets'][tilesetName]

        # bit the tile
        validUntil = tileset.blitTile(
            tilesetTileNumber,
            destImage,
            tileObject['x'] + offset[0],
            tileObject['y'] + offset[1],
            tileObject)

        return validUntil

    #####################################################
    # BLIT TEXT
    #####################################################

    def blitObjectListSpeechText(self, destImage, offset, objectList):
        """Call blitSpeechText() for all objects in objectList."""

        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            vu = self.blitSpeechText(destImage, offset, object)
            validUntil = min(validUntil, vu)
        return validUntil

    def blitSpeechText(self, destImage, offset, object):
        """Blit speechText if speechText found in object

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            object (dict): Tiled Object
        """
        validUntil = sys.float_info.max
        # If speechText is present then render it above the tile.
        if "speechText" in object:
            text = self['SPEACHTEXT'].copy()
            text['text'] = object['speechText']
            textObject = {
                'x': object['x'] + object['width'] / 2 - 64,
                'y': object['y'],
                'width': 128,
                'height': 0,
                'text': text
                }

            validUntil = self.blitTextObject(destImage, offset, textObject)
        return validUntil

    def blitObjectListLabelText(self, destImage, offset, objectList):
        """Call blitLabelText() for all objects in objectList."""

        validUntil = sys.float_info.max
        vu = validUntil
        for object in objectList:
            vu = self.blitLabelText(destImage, offset, object)
            validUntil = min(validUntil, vu)
        return validUntil

    def blitLabelText(self, destImage, offset, object):
        """Blit labelText if labelText found in object

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            object (dict): Tiled Object
        """
        validUntil = sys.float_info.max
        # If labelText is present then render it under the tile. Normally used to display player names.
        if "labelText" in object:
            text = self['LABELTEXT'].copy()
            text['text'] = object['labelText']
            textObject = {
                'x': object['x'] + object['width'] / 2 - 64,
                'y': object['y'] + object['height'],
                'width': 128,
                'height': 0,
                'text': text
                }

            validUntil = self.blitTextObject(destImage, offset, textObject)
        return validUntil

    def blitTextObject(self, destImage, offset, textObject, mapRelative=True):
        """Blit text from Tiled object.

        Supports several font styles, alignments, and wrapping.

        Args:
            deskImage (pygame Surface)
            offset (int, int): Render entire map offset by (x, y) onto destImage
            textObject (dict): Tiled Object containing object['text']
            mapRelative (bool): If True then use map coordinates, else use
                destImage/screen coordinates. Normally user interface elements
                that are relative to the screen (not the map) use mapRelative=False
        """
        maxWidth = textObject['width']

        # add text defaults if they are missing
        text = self['DEFAULTTEXT'].copy()
        text.update(textObject['text'])
        textObject['text'] = text

        fontFilename = f"src/{self['game']}/fonts/{textObject['text']['fontfamily']}.ttf"
        if not os.path.isfile(fontFilename):
            fontFilename = None

        if not 'fonts' in self:
            self['fonts'] = {}

        if fontFilename:
            fontKey = f"{fontFilename}-{textObject['text']['pixelsize']}"
            if fontKey in self['fonts']:
                font = self['fonts'][fontKey]
            else:  
                font = pygame.freetype.Font(fontFilename, textObject['text']['pixelsize'])
                self['fonts'][fontKey] = font
        else:
            fontKey = f"{textObject['text']['fontfamily']}-{textObject['text']['pixelsize']}"
            if fontKey in self['fonts']:
                font = self['fonts'][fontKey]
            else:
                font = pygame.freetype.SysFont(textObject['text']['fontfamily'], textObject['text']['pixelsize'])
                self['fonts'][fontKey] = font

        font.strong = textObject['text']['bold']
        font.underline = textObject['text']['underline']
        font.antialiased = textObject['text']['antialiased']

        font.fgcolor = pygame.Color(textObject['text']['color'])

        lines = []
        if textObject['text']['wrap']:
            #words = textObject['text']['text'].split()
            words = re.split('([ \n])', textObject['text']['text'])
            pixelWidth = 0
            maxLineHeight = 0
            while len(words) > 0:
                # get as many words as will fit within allowed_width
                lineWords = words.pop(0)
                r = font.get_rect(lineWords)
                fw, fh = r.width, r.height
                while fw < maxWidth and len(words) > 0:
                    r = font.get_rect(lineWords + ' ' + words[0])
                    if r.width > maxWidth:
                        if len(words) > 0 and words[0] == " ":
                            # line is wrapping. Remove " " at start of next line
                            words.pop(0)
                        break
                    nextWord = words.pop(0)
                    if nextWord == " ":
                        continue
                    elif nextWord == "\n":
                        break
                    lineWords = lineWords + ' ' + nextWord
                    fw, fh = r.width, r.height

                # add a line consisting of those words
                line = lineWords
                if pixelWidth < fw:
                    pixelWidth = fw
                if maxLineHeight < fh:
                    maxLineHeight = fh
                # add line to lines
                lines.append((fw, fh, line))
        else:
            r = font.get_rect(text)
            pixelWidth = r.width
            maxLineHeight = r.height
            lines.append((r.width, r.height, textObject['text']['text']))

        pixelHeight = maxLineHeight * len(lines)
        pixelWidth += 4
        pixelHeight += 4
        image = pygame.Surface((pixelWidth, pixelHeight), pygame.SRCALPHA, 32)
        image = image.convert_alpha()
        image.fill((0, 0, 0, 0))

        ty = 2
        for line in lines:
            if textObject['text']['halign'] == "left":
                tx = 2
            elif textObject['text']['halign'] == "center":
                tx = pixelWidth / 2 - line[0] / 2
            elif textObject['text']['halign'] == "right":
                tx = pixelWidth - line[0] - 2
            font.render_to(image, (tx, ty), line[2])
            ty += maxLineHeight

        if textObject['text']['halign'] == "left":
            destX = textObject['x']
        elif textObject['text']['halign'] == "center":
            destX = textObject['x'] + textObject['width'] / 2 - pixelWidth / 2
        elif textObject['text']['halign'] == "right":
            destX = textObject['x'] + textObject['width'] - pixelWidth
        else:
            log(f"halign == {textObject['text']['halign']} is not supported", 'FAILURE')
            exit()

        if textObject['text']['valign'] == "top":
            destY = textObject['y']
        elif textObject['text']['valign'] == "center":
            destY = textObject['y'] + textObject['height'] / 2 - pixelHeight / 2
        elif textObject['text']['valign'] == "bottom":
            destY = textObject['y'] + textObject['height'] - pixelHeight
        else:
            log(f"valign == {textObject['text']['valign']} is not supported", 'FAILURE')
            exit()

        buffer = textObject['text']['bgborderThickness'] + textObject['text']['bgroundCorners']

        if mapRelative:
            destWidth = self['pixelWidth']
            destHeight = self['pixelHeight']
        else:
            destWidth = destImage.get_width()
            destHeight = destImage.get_height()

        if destX - buffer < 0:
            destX = buffer
        if destY - buffer < 0:
            destY = buffer
        if destX + pixelWidth + buffer * 2 > destWidth:
            destX = destWidth - pixelWidth - buffer
        if destY + pixelHeight + buffer * 2 > destHeight:
            destY = destHeight - pixelHeight - buffer

        destX += offset[0]
        destY += offset[1]

        self.blitRectObject(destImage, (0, 0), {
            'x': destX - buffer,
            'y': destY - buffer,
            'width': pixelWidth + buffer * 2,
            'height': pixelHeight + buffer * 2
            },
            fillColor=textObject['text']['bgcolor'],
            borderColor=textObject['text']['bgbordercolor'],
            borderThickness=textObject['text']['bgborderThickness'],
            roundCorners=textObject['text']['bgroundCorners'])

        destImage.blit(image, (destX, destY))

        # text does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    #####################################################
    # BLIT/DRAW SHAPE OBJECTS
    #####################################################

    def blitRectObject(self, destImage, offset, rectObject, fillColor=(0, 0, 0, 0),
                       borderColor=(0, 0, 0, 255), borderThickness=1, roundCorners=0):
        """Draw a Rectangle Object onto destImage"""

        image = pygame.Surface((rectObject['width'], rectObject['height']), pygame.SRCALPHA, 32)
        image = image.convert_alpha()

        rect = pygame.Rect(0, 0, rectObject['width'], rectObject['height'])
        pygame.draw.rect(image, fillColor, rect, 0, roundCorners)
        if borderThickness > 0:
            pygame.draw.rect(image, borderColor, rect, borderThickness, roundCorners)

        destImage.blit(image, (rectObject['x'] + offset[0], rectObject['y'] + offset[1]))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    def blitRoundObject(self, destImage, offset, roundObject, fillColor=(0, 0, 0, 0),
                        borderColor=(0, 0, 0, 255), borderThickness=1):
        """Draw a Circle or Ellipse Object onto destImage"""

        width = roundObject['width']
        height = roundObject['height']
        # points are drawn as small circles
        if width == 0 and height == 0:
            width = height = 3

        image = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        image = image.convert_alpha()

        rect = pygame.Rect(0, 0, width, height)
        pygame.draw.ellipse(image, fillColor, rect, 0)
        pygame.draw.ellipse(image, borderColor, rect, borderThickness)

        destImage.blit(image, (roundObject['x'] + offset[0], roundObject['y'] + offset[1]))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil

    def blitPolyObject(self, destImage, offset, polyObject,
                       lineColor=(0, 0, 0, 255), lineThickness=1):
        """Draw a Poly Object (polyline or polygon) onto destImage"""

        image = pygame.Surface(
            (self['width'] *
             self['tilewidth'],
                self['height'] *
                self['tileheight']),
            pygame.SRCALPHA,
            32)
        image = image.convert_alpha()

        # build polyline with orgin at destImage 0,0
        points = []
        if 'polyline' in polyObject:
            closed = False
            pointsDict = polyObject['polyline']
        elif 'polygon' in polyObject:
            closed = True
            pointsDict = polyObject['polygon']
        else:
            log('polyObject did not contain a polygon or polyline attribute.', "ERROR")
            closed = False
            pointsDict = {}

        for p in pointsDict:
            points.append((p['x'] + polyObject['x'], p['y'] + polyObject['y']))

        pygame.draw.lines(image, lineColor, closed, points, lineThickness)

        destImage.blit(image, (offset[0], offset[1]))

        # rect does not have an end time so just sent back a long time from now
        validUntil = sys.float_info.max
        return validUntil
