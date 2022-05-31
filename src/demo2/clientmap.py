"""ClientMap for demo game."""

import pygame
from pygame.locals import *

import engine.geometry as geo
import math

import engine.time as time

from engine.log import log
import engine.clientmap


class ClientMap(engine.clientmap.ClientMap):
    """Extends engine.clientmap.ClientMap"""

    def __init__(self, tilesets, mapDir):
        """Extends ___init__ and updates text defaults."""

        super().__init__(tilesets, mapDir)

        self['DEFAULTTEXT'].update({
            "fontfamily": "Orbitron-Regular",
            "bgcolor": "#000000b0",
            "bgbordercolor": "#000000b0",
            "bgborderThickness": 4,
            "bgroundCorners": 4
            })

        self['SPEACHTEXT'].update({
            "bgcolor": "#00000080",
            "bgbordercolor": "#00000080"
            })

        # labelText defaults that differ from DEFAULTTEXT
        self['LABELTEXT'].update({
            "pixelsize": 8,
            "bgcolor": "#00000000",
            "bgborderThickness": 0,
            "bgroundCorners": 0
            })

    def blitObject(self, destImage, offset, object):
        """Extends blitObject()"""

        if object['type'] == 'player':
            validUntil = []
            validUntil.append(super().blitObject(destImage, offset, object))

            if 'weapon' in object:
                validUntil.append(self.blitHeldObject(destImage, offset, object, object['weapon'], math.pi))
            if 'key' in object:
                validUntil.append(self.blitHeldObject(destImage, offset, object, object['key'], 0))
            if 'idol' in object:
                now = time.perf_counter()
                if round(now*10)%2:
                    validUntil.append(self.blitHeldObject(destImage, offset, object, object['idol'], math.pi*0.5))
                validUntil.append(now+0.1)
            return min(validUntil)
        else:
            return super().blitObject(destImage, offset, object)


    def blitHeldObject(self, destImage, offset, object, holding, direction):
        if 'gid' in holding:
            # switch to a smaller icon
            holding['gid'] = self.findGid('fantasy-tileset32x32', holding['tilesetTileNumber'])
            holding['width'] = 32
            holding['height'] = 32

        holding['x'], holding['y'] = geo.project(
                object['x']+object['width']/2,
                object['y']+object['height']/2,
                direction,
                object['width']/4
                )
        holding['x'] -= holding['width']/2
        holding['y'] -= holding['height']/2
        return super().blitObject(destImage, offset, holding)

