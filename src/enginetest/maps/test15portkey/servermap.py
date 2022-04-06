"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap


class ServerMap(engine.servermap.ServerMap):
    """PORTKEY MECHANIC

        A portkey is like a mapDoor but is a visible sprite
        and requires the player to request an action before
        they will go through the mapDoor.

        Uses Mechanics: action, mapdoor, payer action text
    """

    def initPortkey(self):
        """PORTKEY MECHANIC: init method.

        Portkey sprites need to be triggers so copy
        sprites to trigger layer. Details on this
        method are in engine.servermap.ServerMap.addHoldableTrigger()
        """
        for portkey in self.findObject(type="portkey", returnAll=True):
            portkeyTrigger = portkey.copy()
            portkeyTrigger['collisionType'] = 'rect'
            portkeyTrigger['doNotTrigger'] = [portkey]
            self.addObject(portkeyTrigger, objectList=self['triggers'])
            self.addFollower(portkey, portkeyTrigger)

    def triggerPortkey(self, portkey, sprite):
        """PORTKEY MECHANIC: trigger method.

        Portkey acts as a mapdoor but also requires a
        user to request an action. Requires the same
        properties as a mapdoor.
        """
        if "action" in sprite:
            self.delSpriteAction(sprite)
            self.triggerMapDoor(portkey, sprite)  # assume portkey has the properties required by a mapDoor trigger
        else:
            self.setSpriteActionText(sprite, f"Available Action: Touch {portkey['name']}")
