"""ServerMap for Engine Test Map."""
import random
import math

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """This servermap implements a circular move mechanic.

    ORBIT MOVE

    Better comments to be added later.


    """

    ########################################################
    # MOVE ORBIT MECHANIC
    ########################################################

    def initMoveOrbit(self):
        """Set up sprites for orbit movement."""

        # add the sun and planet to the reference layer so other sprites can orbit them.
        self.addObject(self.findObject(name='sun'), objectList=self['reference'])
        self.addObject(self.findObject(name='planet'), objectList=self['reference'])

        # set the planet on the sprite layer to orbit the 'sun' on the reference layer.
        self.setMoveOrbit(self.findObject(name='planet'), 'sun', 200, bounce=True, radius=False)

        # set the moon on the sprite layer to orbit the 'planet' on the reference layer.
        self.setMoveOrbit(self.findObject(name='moon'), 'planet', 100, bounce=True, radius=False)

    def stepMoveOrbit(self, sprite):
        """MOVE ORBIT MECHANIC: stepMove method.

        Add attributes to sprite: direction
        """
        
        if 'move' in sprite and sprite['move']['type'] == 'Orbit':
            orbitObject = self.findObject(name=sprite['move']['orbitName'], objectList=self['reference'])
            if not orbitObject:
                log(f"OrbitObject {sprite['move']['orbitName']} not found on reference layer.", "ERROR")
                self.delMoveOrbit(sprite)
                return
            currentAngle = sprite['move']['a']
            radius = sprite['move']['r']

            moveSpeed = sprite['move']['s']
            # convert pixels per second to pixels per step
            stepSpeed = moveSpeed / engine.server.SERVER['fps']
            circumference = 2 * math.pi * radius
            newAngle = geo.normalizeAngle(currentAngle + (stepSpeed/circumference) * (2 * math.pi))
            newAnchorX, newAnchorY = geo.project(
                        orbitObject['anchorX'],
                        orbitObject['anchorY'],
                        newAngle,
                        radius)

            inBounds = self.checkLocation(sprite, newAnchorX, newAnchorY)

            if inBounds:
                # move sprite to new location
                sprite['move']['a'] = newAngle
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)
            else:
                # sprite cannot move.
                bounce = sprite['move']['b']
                if bounce:
                    sprite['move']['s'] *= -1 # reverse direction
                else:
                    self.delMoveOrbit(sprite)

    def setMoveOrbit(self, sprite, orbitName, moveSpeed, bounce=False, radius=False, angle=False):
        """MOVE ORBIT MECHANIC: Set sprites orbit to follow and speed.

        Add attributes to sprite: move
        """
        orbitObject = self.findObject(name=orbitName, objectList=self['reference'])
        if not orbitObject:
            log(f"OrbitObject {orbitName} not found on reference layer.", "ERROR")
            return

        # if radius not provided then use the current distance between sprite and what it orbits.
        if not radius:
            radius = geo.distance(orbitObject['anchorX'],orbitObject['anchorY'],sprite['anchorX'],sprite['anchorY'])

        # if start angle not provided then use the current angle between sprite and what it orbits.
        if not angle:
            angle = geo.angle(orbitObject['anchorX'],orbitObject['anchorY'],sprite['anchorX'],sprite['anchorY'])

        sprite['move'] = {'type': 'Orbit', 'orbitName': orbitName, 's': moveSpeed, 'b': bounce, 'r':radius, 'a': angle}
        self.setMapChanged()

    def delMoveOrbit(self, sprite):
        """MOVE ORBIT MECHANIC: Stop Sprite

        Remove attributes from sprite: move
        """
        if 'move' in sprite and sprite['move']['type'] == 'Orbit':
            del sprite['move']
            self.setMapChanged()