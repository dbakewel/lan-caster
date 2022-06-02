"""ClientMap for demo2 game."""

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
            "bgcolor": "#00000000",
            "bgbordercolor": "#00000000",
            "bgborderThickness": 4,
            "bgroundCorners": 4
            })

        self['SPEECHTEXT'].update({
            "bgcolor": "#00000080",
            "bgbordercolor": "#00000080"
            })

        # labelText defaults that differ from DEFAULTTEXT
        self['LABELTEXT'].update({
            "pixelsize": 12
            })

    def blitObject(self, destImage, offset, object):
        """Extends blitObject()

        When bliting a player, also blit all objects being held: key, idol, and weapon.
        """

        if object['type'] == 'player':
            validUntil = []
            validUntil.append(super().blitObject(destImage, offset, object))

            if 'weapon' in object:
                validUntil.append(
                    self.blitHeldObject(destImage, offset, object, object['weapon'], math.pi, object['width'] / 4))
            if 'key' in object:
                validUntil.append(
                    self.blitHeldObject(destImage, offset, object, object['key'], 0, object['width'] / 4))
            if 'idol' in object:
                # use time and % to make idol flash on/off so it is very visable to other players.
                now = time.perf_counter()
                if round(now * 10) % 2:
                    validUntil.append(
                        self.blitHeldObject(destImage, offset, object, object['idol'],
                                            math.pi * 0.5, object['width'] / 8))
                validUntil.append(now + 0.1)
            return min(validUntil)
        else:
            return super().blitObject(destImage, offset, object)

    def blitHeldObject(self, destImage, offset, object, holding, direction, distance):
        """ Render small version of held object"""

        if 'gid' in holding:
            # switch to a smaller icon
            holding['gid'] = self.findGid('fantasy-tileset32x32', holding['tilesetTileNumber'])
            holding['width'] = 32
            holding['height'] = 32

        anchorX, anchorY = geo.project(object['anchorX'], object['anchorY'], direction, distance)
        holding['x'] = anchorX - 16
        holding['y'] = anchorY - 16

        validUntil = super().blitObject(destImage, offset, holding)

        # if holding is a key then render it's key number
        if 'lockNumber' in holding:
            holding['y'] -= 8  # move lable up a bit for better look on screen.
            holding['labelText'] = f"{holding['lockNumber']}"
            self.blitLabelText(destImage, offset, holding)

        return validUntil
