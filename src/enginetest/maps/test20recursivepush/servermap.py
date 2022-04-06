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

        Note, if two pushables start (from the map.json file) overlapping 
        then this will cause serious recursion problems since they start 
        in an invalid state.

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

        If the sprite impacts a pushable then move the pushable away from the
        sprite but only if moving the pushable would be a valid move. Note,
        this is using 'rect' based collision on the pushable.
        """

        # if the move is not valid then try to move a pushable out of the way.
        if not super().checkLocation(object, newAnchorX, newAnchorY):
            # if the object is moving between maps then do not try and push
            if self['name'] != object['mapName']:
                return False

            # if the object is not moving normally within a map (transport of some kind) then do not push
            if geo.distance(newAnchorX, newAnchorY, object['anchorX'], object['anchorY']) > 50:
                return False

            newObjectX = newAnchorX - (object['anchorX'] - object['x'])
            newObjectY = newAnchorY - (object['anchorY'] - object['y'])

            # try and find a pushable object that can be moved out of the way.
            pushables = self.findObject(
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
                exclude=object,
                returnAll=True)
            if len(pushables) == 0:
                return False

            newpushables = []
            for pushable in pushables:
                # find out what way to try and push pushable and compute new location.
                # Only directions are directly left, right, up, or down.
                newPushableX = pushable['x']
                newPushableY = pushable['y']

                if object['collisionType'] == 'anchor':
                    if object['anchorX'] < newPushableX and newPushableX < newAnchorX:
                        # move right
                        newPushableX = newAnchorX + 0.0001
                    elif object['anchorX'] > newPushableX + pushable['width'] and newPushableX + pushable['width'] > newAnchorX:
                        # move left
                        newPushableX = newAnchorX - pushable['width'] - 0.0001
                    elif object['anchorY'] < newPushableY and newPushableY < newAnchorY:
                        # move down
                        newPushableY = newAnchorY + 0.0001
                    elif object['anchorY'] > newPushableY + pushable['height'] and newPushableY + pushable['height'] > newAnchorY:
                        # move up
                        newPushableY = newAnchorY - pushable['height'] - 0.0001
                else:  # collisionType == 'rect'
                    if object['x'] + object['width'] < newPushableX and newPushableX < newObjectX + object['width']:
                        # move right
                        newPushableX = newObjectX + object['width'] + 0.0001
                    elif object['x'] > newPushableX + pushable['width'] and newPushableX + pushable['width'] > newObjectX:
                        # move left
                        newPushableX = newObjectX - pushable['width'] - 0.0001
                    elif object['y'] + object['height'] < newPushableY and newPushableY < newObjectY + object['height']:
                        # move down
                        newPushableY = newObjectY + object['height'] + 0.0001
                    elif object['y'] > newPushableY + pushable['height'] and newPushableY + pushable['height'] > newObjectY:
                        # move up
                        newPushableY = newObjectY - pushable['height'] - 0.0001

                newPushableAnchorX = newPushableX + (pushable['anchorX'] - pushable['x'])
                newPushableAnchorY = newPushableY + (pushable['anchorY'] - pushable['y'])

                # if pushable can be moved to new location then set it to be moved.
                if self.checkLocation(pushable, newPushableAnchorX, newPushableAnchorY):
                    newpushables.append((pushable, newPushableAnchorX, newPushableAnchorY))
                else:
                    return False  # the pushable cannot be moved.

            for pushable, newPushableAnchorX, newPushableAnchorY in newpushables:
                self.setObjectLocationByAnchor(pushable, newPushableAnchorX, newPushableAnchorY)

        return True
