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

    def checkLocation(self, object, newAnchorX, newAnchorY):
        """Extend checkLocation().

        If the object being moved is a player and they impact a pushable then
        move the pushable away from the object but only if moving the pushable
        would be a valid move. Note, this using 'rect' based collision on the
        pushable. Assumes player collisionType == 'anchor'
        """

        validMove = super().checkLocation(object, newAnchorX, newAnchorY)
        # if the move is not valid and it's a player trying to move then try to move a pushable out of the way.
        if validMove == False and object["type"] == "player":
            # if the player is moving between maps then do not try and push
            if self['name'] != object['mapName']:
                return False

            # if the player is not moving normally within a map (transport of some kind) then do not push
            if geo.distance(newAnchorX, newAnchorY, object['anchorX'], object['anchorY']) > 50:
                return False

            newObjectX = newAnchorX - (object['anchorX'] - object['x'])
            newObjectY = newAnchorY - (object['anchorY'] - object['y'])

            # try and find a pushable object that can be moved out of the way.
            pushable = self.findObject(
                collidesWith={
                    'x':newObjectX,
                    'y':newObjectY,
                    'anchorX':newAnchorX,
                    'anchorY':newAnchorY,
                    'width':object['width'],
                    'height':object['height'],
                    'collisionType':object['collisionType']
                },
                type='pushable',
                exclude=object)
            if not pushable:
                return False

            # find out what way to try and push pushable and compute new location.
            # Only directions are directly left, right, up, or down.
            newX = pushable['x']
            newY = pushable['y']
            if object['anchorX'] < newX and newX < newAnchorX:
                # move right
                newX = newAnchorX + 0.0001
            elif object['anchorX'] > newX + pushable['width'] and newX + pushable['width'] > newAnchorX:
                # move left
                newX = newAnchorX - pushable['width'] - 0.0001
            elif object['anchorY'] < newY and newY < newAnchorY:
                # move down
                newY = newAnchorY + 0.0001
            elif object['anchorY'] > newY + pushable['height'] and newY + pushable['height'] > newAnchorY:
                # move up
                newY = newAnchorY - pushable['height'] - 0.0001

            newPushableAnchorX = newX + (pushable['anchorX'] - pushable['x'])
            newPushableAnchorY = newY + (pushable['anchorY'] - pushable['y'])

            # if pushable can be moved to new location then move it and allow player to move.
            if self.checkLocation(pushable, newPushableAnchorX, newPushableAnchorY):
                self.setObjectLocationByAnchor(pushable, newPushableAnchorX, newPushableAnchorY)
                return True

        return validMove
