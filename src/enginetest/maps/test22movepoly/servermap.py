"""ServerMap for Engine Test Map."""
import random
import math

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """This servermap implements a move mechanic that follows a poly object.

    POLY MOVE

    Better comments to be added later.

    """

    ########################################################
    # MOVE POLY MECHANIC
    ########################################################

    def initMovePoly(self):
        """Set up sprites for poly movement."""
        self.setMovePoly(self.findObject(name='monster1'), 'track1', 200, bounce=True)
        self.setMovePoly(self.findObject(name='monster2'), 'track2', 200, bounce=True)

        # make it so we can see tracks (not needed to make movement work)
        self.addObject(self.findObject(name='track1', objectList=self['reference']))
        self.addObject(self.findObject(name='track2', objectList=self['reference']))

    def stepMovePoly(self, sprite):
        """MOVE POLY MECHANIC: stepMove method.

        Add attributes to sprite: direction
        """
        if 'move' in sprite and sprite['move']['type'] == 'Poly':
            polyObject = self.findObject(name=sprite['move']['polyName'], objectList=self['reference'])
            if not polyObject:
                log(f"PolyObject {sprite['move']['polyName']} not found on reference layer.", "ERROR")
                self.delMovePoly(sprite)
                return
            if not polyObject or ('polyline' not in polyObject and 'polygon' not in polyObject):
                log(f"Object {sprite['move']['polyName']} is not a poly object.", "ERROR")
                self.delMovePoly(sprite)
                return

            if 'polyline' in polyObject:
                pts = polyObject['polyline']
            else:
                pts = polyObject['polygon']

            if 'totalDistance' not in polyObject:
                polyObject['totalDistance'] = 0
                pts[0]['dis'] = polyObject['totalDistance']
                for i in range(1,len(pts)):
                    polyObject['totalDistance'] += geo.distance(pts[i-1]['x'],pts[i-1]['y'],pts[i]['x'],pts[i]['y'])
                    pts[i]['dis'] = polyObject['totalDistance']
                if 'polygon' in polyObject:
                    polyObject['totalDistance'] += geo.distance(pts[0]['x'],pts[0]['y'],
                        pts[len(pts)-1]['x'],pts[len(pts)-1]['y'])
            
            bounce = sprite['move']['b']

            moveSpeed = sprite['move']['s']
            # convert pixels per second to pixels per step
            stepSpeed = moveSpeed / engine.server.SERVER['fps']

            position = sprite['move']['df'] * polyObject['totalDistance']
            newposition = position + stepSpeed

            if newposition < 0:
                if bounce:
                    newposition *= -1
                    sprite['move']['s'] *= -1
                else:
                    if 'polygon' in polyObject:
                        # loop around to end of polygon
                        newposition = polyObject['totalDistance'] + newposition
                    else:
                        # just go to start of polyline
                        newposition = 0

            if newposition > polyObject['totalDistance']:
                if bounce:
                    newposition = polyObject['totalDistance'] - (newposition - polyObject['totalDistance'])
                    sprite['move']['s'] *= -1
                else:
                    if 'polygon' in polyObject:
                        # loop around to beginning of polygon
                        newposition -= polyObject['totalDistance']
                    else:
                        # just go to end of polyline
                        newposition = polyObject['totalDistance']
            
            found = False
            for i in range(1,len(pts)):
                if pts[i-1]['dis'] <= newposition and newposition < pts[i]['dis']:
                    sprite['direction'] = geo.angle(
                        pts[i-1]['x'],
                        pts[i-1]['y'],
                        pts[i]['x'],
                        pts[i]['y'])
                    newAnchorX, newAnchorY = geo.project(
                        pts[i-1]['x']+polyObject['x'],
                        pts[i-1]['y']+polyObject['y'],
                        sprite['direction'],
                        newposition - pts[i-1]['dis'])
                    found = True
                    break

            if not found: # this is a polygon and we are on the last segment back to the first point.
                sprite['direction'] = geo.angle(
                        pts[len(pts)-1]['x'],
                        pts[len(pts)-1]['y'],
                        pts[0]['x'],
                        pts[0]['y'])
                newAnchorX, newAnchorY = geo.project(
                    pts[len(pts)-1]['x']+polyObject['x'],
                    pts[len(pts)-1]['y']+polyObject['y'],
                    sprite['direction'],
                    newposition - pts[len(pts)-1]['dis'])

            inBounds = self.checkLocation(sprite, newAnchorX, newAnchorY)

            if inBounds:
                # move sprite to new location
                sprite['move']['df'] = newposition / polyObject['totalDistance']
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)

                # if we are at the end and not bouncing then stop
                if not bounce and newposition == polyObject['totalDistance'] or newposition == 0:
                    self.delMovePoly(sprite)
            else:
                # sprite cannot move.
                if bounce:
                    newposition *= -1
                else:
                    self.delMovePoly(sprite)

    def setMovePoly(self, sprite, polyName, moveSpeed, disfrac=0, bounce=False):
        """MOVE POLY MECHANIC: Set sprites poly to follow and speed.
    

        In the sprite['move'] dict the attributes for 'type' == 'Poly' are:

        'polyName' is the poly object on the reference layer to follow.

        'df' is the current position of the sprite represented as a 
        fraction between 0 and 1 of the total length (distance) of
        the poly object.

        's' is the move speed in pixels/sec

        'b'' is weather or not to bounce (reverse) at the end of the poly
        or not.

        Add attributes to sprite: move
        """
        sprite['move'] = {'type': 'Poly', 'polyName': polyName, 'df': disfrac, 's': moveSpeed, 'b': bounce}
        self.setMapChanged()

    def delMovePoly(self, sprite):
        """MOVE POLY MECHANIC: Stop Sprite

        Remove attributes from sprite: move
        """
        if 'move' in sprite and sprite['move']['type'] == 'Poly':
            del sprite['move']
            self.setMapChanged()