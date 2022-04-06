"""ServerMap for Demo Game End Map"""

from engine.log import log
import demo.servermap
import engine.server
import engine.geometry as geo


class ServerMap(demo.servermap.ServerMap):
    """Extends demo.servermap.ServerMap

    This class implements mechanics:

    MAGIC AREA MECHANIC
        Allow players to trigger the lever mechanic if they
        are standing in a magic area and are holding the
        magic want holdable.

        Uses Mechanics: action, lever, holdable,
            player action text, player speech text

    LEVER MECHANIC
        The lever mechanic show/hides bridges on maps start
        and end. It also add/removes inbounds objects to
        allow/stop sprites from crossing bridges.

        This mechanic requires very specific set up in Tiled of
        layers and objects on both the start and end map.

        Uses Mechanics: action, layer visibility,
            player action text
    """

    ########################################################
    # MAGIC AREA MECHANIC
    ########################################################

    def triggerMagicArea(self, magicArea, sprite):
        """MAGIC AREA MECHANIC: trigger method

        If sprite is holding magic want and requested an action
        then trigger the lever.

        Also show speech and action text.
        """
        if "holding" in sprite and sprite['holding']['name'] == "magic wand":
            self.setSpriteActionText(sprite, f"Available Action: Cast spell with {sprite['holding']['name']}.")
            if "action" in sprite:
                self.triggerLever(self.findObject(name="lever"), sprite)
        else:
            self.setSpriteSpeechText(
                sprite, f"This place seems magical but I feel like I need something to help cast a spell.")

    ########################################################
    # LEVER MECHANIC
    ########################################################

    def initLever(self):
        """LEVER MECHANIC: init method.

        Lever sprite needs to be trigger so copy
        sprite to trigger layer. Details on this
        method are in engine.servermap.ServerMap.addHoldableTrigger()
        """
        lever = self.findObject(type="lever")
        leverTrigger = lever.copy()
        leverTrigger['collisionType'] = 'rect'
        leverTrigger['doNotTrigger'] = [lever]
        self.addObject(leverTrigger, objectList=self['triggers'])
        self.addFollower(lever, leverTrigger)

    def triggerLever(self, trigger, sprite):
        """LEVER MECHANIC: trigger method.

        Move the lever one step to the right and show/hide
        layers to the correct bridge appears/disappears. Objects
        on the inBounds layer must also be added/removed.

        This mechanic requires very specific set up in Tiled of
        layers and objects on both the start and end map.
        """
        if trigger['name'] == "lever":
            lever = trigger
            self.setSpriteActionText(sprite, f"Available Action: Heave {sprite['name']}")
            if "action" in sprite:
                self.delSpriteAction(sprite)
                start = engine.server.SERVER['maps']['start']

                # hard coding of gids is specific to this map and it's assignment of gids.
                # add 1 to levers gid and make sure it stays in range 381-383
                lever['gid'] += 1  # move lever one step to the right
                if lever['gid'] == 384:  # if lever is out of range then
                    lever['gid'] = 381  # move lever back to left

                if lever['gid'] == 381:  # if lever is on left then:
                    self.setLayerVisablitybyName("bridge1", True)
                    start.setLayerVisablitybyName("bridge2", False)
                    self.setLayerVisablitybyName("bridge3", False)
                    self.removeObject(
                        self.findObject(name="bridge3InBounds", objectList=self['inBounds']),
                        objectList=self['inBounds'])
                    b1ib = self.findObject(name="bridge1InBounds", objectList=self['reference'])
                    self.addObject(b1ib, objectList=self['inBounds'])
                    b1ib['collisionType'] = 'rect'
                elif lever['gid'] == 382:  # if lever is in center then:
                    self.setLayerVisablitybyName("bridge1", False)
                    start.setLayerVisablitybyName("bridge2", True)
                    self.setLayerVisablitybyName("bridge3", False)
                    self.removeObject(
                        self.findObject(name="bridge1InBounds", objectList=self['inBounds']),
                        objectList=self['inBounds'])
                    b2ib = start.findObject(name="bridge2InBounds", objectList=start['reference'])
                    start.addObject(b2ib, objectList=start['inBounds'])
                    b2ib['collisionType'] = 'rect'
                elif lever['gid'] == 383:  # if lever is on right then:
                    self.setLayerVisablitybyName("bridge1", False)
                    start.setLayerVisablitybyName("bridge2", False)
                    self.setLayerVisablitybyName("bridge3", True)

                    b2ib = start.findObject(name="bridge2InBounds", objectList=start['inBounds'])
                    # The very first time we use the lever there will not be bridge2InBounds in
                    # the inBounds so we need to check to see if we found anything.
                    if b2ib:
                        start.removeObject(b2ib, objectList=start['inBounds'])
                    b3ib = self.findObject(name="bridge3InBounds", objectList=self['reference'])
                    self.addObject(b3ib, objectList=self['inBounds'])
                    b3ib['collisionType'] = 'rect'
