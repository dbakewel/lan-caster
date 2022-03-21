"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap
import engine.geometry as geo
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """PUSH MECHANIC

        A sprite of type == pushable will be moved with a player sprite
        collides with it. However this will only occur if the pushable sprite
        can be moved away from the player while still staying in bounds.

        Pushable sprites also act as outOfBounds areas for other sprites.

        Uses Mechanics: move
    """

    def initPush(self):
        """PUSH MECHANIC: init method.

        Copy (by reference) all pushable sprites to the outOfBounds layer.
        """
        for pushable in self.findObject(type="pushable", returnAll=True):
            pushable['collisionType'] = "rect"

    def checkLocation(self, object, x, y):
        """Extend checkLocation().

        If the object being moved is a player and they impact a pushable then
        move the pushable away from the object but only if:
            1) moving the pushable would be a valid move. This means
            that full rect collision detection must be done, not just anchor to
            rect collision detection.
            2) moving the pushable would not make it overlap with any
            other sprite.

        Assumes player collisionType == 'anchor'
        """

        validMove = super().checkLocation(object, x, y)
        # if the move is not valid and it's a player trying to move then try to move a pushable out of the way.
        if validMove == False and object["type"] == "player":
            #if the player is moving between maps then do not try and push
            if self['name'] != object['mapName']:
                return False

            # if the player is not moving normally within a map (transport of some kind) then do not push
            if geo.distance(x,y,object['x'],object['y']) > 50:
                return False

            # find all sprites that player anchor would intersect (excluding player object)
            overlapingSprites = self.findObject(x=x, y=y, exclude=object, returnAll=True)
            
            # if more than one sprite found or a non pushable was found then we cannot push
            if len(overlapingSprites) != 1 or overlapingSprites[0]['type'] != 'pushable':
                return False

            pushable = overlapingSprites[0]

            # find out what way to try and push pushable and compute new location. 
            # Only directions are directly left, right, up, or down.
            newX = pushable['x']
            newY = pushable['y']
            if object['anchorX'] < newX and newX < x:
                # move right
                newX = x + 0.0001
            elif object['anchorX'] > newX+pushable['width'] and newX+pushable['width'] > x:
                # move left
                newX = x - pushable['width'] - 0.0001
            elif object['anchorY'] < newY and newY < y:
                # move down
                newY = y + 0.0001
            elif object['anchorY'] > newY+pushable['height'] and newY+pushable['height'] > y:
                # move up
                newY = y - pushable['height'] - 0.0001
            
            newAnchorX = newX + (pushable['anchorX'] - pushable['x'])
            newAnchorY = newY + (pushable['anchorY'] - pushable['y'])

            # if pushable can be moved to new location then move it and allow player to move.
            if self.checkLocation(pushable, newAnchorX, newAnchorY):
                self.setObjectLocationByAnchor(pushable, newAnchorX, newAnchorY)
                return True

            # don't allow player to move because we were not able to push pushable out of the way.
            return False

        return validMove