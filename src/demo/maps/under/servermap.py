"""ServerMap for Demo Game Under Map"""

import random
from engine.log import log
import demo.servermap
import engine.time as time


class ServerMap(demo.servermap.ServerMap):
    """Extends demo.servermap.ServerMap

    This class implements mechanics:

    SAW 
        This mechanic slides a saw horizontally and if a sprite
        is hit by the saw then they are sent to their respawn 
        point.

        Uses Mechanics: move linear, respawn point, speed multiplier
            player speech text

    STOP SAW
        Allows a stopSaw trigger to stop a saw based on the saw
        name. While a sprite is on a stop saw trigger then the
        associated saw will stop moving.

        Uses Mechanics: saw, move Linear

    """

    ########################################################
    # SAW MECHANIC
    ########################################################

    def initSaws(self):
        """SAW: init method.

        copy (by reference) all sprites of type == saw from the 
        sprite layer to the trigger layer. Type "saw" will act 
        as both a sprite and a trigger. Note, when we move the 
        sprite the trigger will also move, because it is the
        same object.
        """

        for saw in self.findObject(type="saw", returnAll=True):
            if not self.checkKeys(saw, ["prop-maxX", "prop-minX", "prop-speed"]):
                log("Cannot init saw because it is missing require properties.", "ERROR")
                # change the saw type so it will not do anything any more.
                saw['type'] = "sawBroken"
            else:
                self.addObject(saw, objectList=self['triggers'])

    def stepSpriteStartSaw(self, sprite):
        """SAW: stepSpriteStart method.

        If saw has stopped then start it moving again 
        but in the reverse direction.
        """

        if sprite['type'] == "saw":
            if "moveDestX" not in sprite:
                # change direction sprite will go the next time is stops.
                sprite['prop-speed'] *= -1
                if sprite['prop-speed'] > 0:
                    self.setSpriteDest(
                        sprite,
                        sprite['prop-maxX'],
                        sprite['anchorY'],
                        sprite['prop-speed'])
                else:
                    self.setSpriteDest(
                        sprite,
                        sprite['prop-minX'],
                        sprite['anchorY'],
                        sprite['prop-speed'] * -1)

    def triggerSaw(self, trigger, sprite):
        """SAW: trigger method.

        The sprite has been hit by a saw. Move the sprite back
        to it's respawun point. This assumes sprite has been 
        through a respawn point. The game design up to the saw
        should ensure sprite has a respawn point assigned.

        Also have the sprite say an expletive.
        """

        self.setSpriteLocationByRespawnPoint(sprite)

        # That saw probably hurt so sprite should say something.
        text = random.choice((
            "ARRRH!",
            "*&^@%", 
            "Bad Idea!",
            "Good thing I have public health care."
            ))
        self.setSpriteSpeechText(sprite, text, time.perf_counter() + 1)  # show text for only 1 sec.

    def triggerSpeedMultiplier(self, trigger, sprite):
        """SAW: Extend trigger method from speedMultiplier Mechanic.
        
        Filter out saws so they do not have their speed changed.
        """
        if sprite['type'] != "saw":
            super().triggerSpeedMultiplier(trigger, sprite)

    ########################################################
    # STOP SAW MECHANIC
    ########################################################

    def setStopSawDest(self, sprite):
        """STOP SAW: Stop Saw from moving this step.

        Assumes sprite is a saw.

        Add attributes to sprite: stopSawDestX, stopSawDestY, stopSawSpeed
        """
        if "moveDestX" in sprite:
            sprite['stopSawDestX'] = sprite['moveDestX']
            sprite['stopSawDestY'] = sprite['moveDestY']
            sprite['stopSawSpeed'] = sprite['moveSpeed']

    def delStopSawDest(self, sprite):
        """STOP SAW: Remove Stop Saw data from sprite.

        Assumes sprite is a saw.

        Remove attributes from sprite: stopSawDestX, stopSawDestY, stopSawSpeed
        """
        if "stopSawDestX" in sprite:
            del sprite['stopSawDestX']
            del sprite['stopSawDestY']
            del sprite['stopSawSpeed']

    def triggerStopSaw(self, trigger, sprite):
        """STOP SAW: trigger method.

        Stop a saw before the stepMove methods are
        called during this step.

        Trigger Properties:
            sawName: The name of the saw sprite that this
                trigger stops the movement of.
        """

        if not self.checkKeys(trigger, ['prop-sawName']):
            log("Cannot process stopSaw trigger.", "ERROR")
            return

        # find saw that trigger stops
        saw = self.findObject(name=trigger['prop-sawName'])
        self.setStopSawDest(saw)
        self.delSpriteDest(saw)

    def stepSpriteEndStopSaw(self, sprite):
        """STOP SAW: stepSpriteEnd

        If a saw was stopped earlier in the step then set it moving
        again now that we are past stepMove methods.
        """
        if sprite['type'] == "saw" and "stopSawDestX" in sprite:
            self.setSpriteDest(sprite, sprite['stopSawDestX'], sprite['stopSawDestY'], sprite['stopSawSpeed'])
            self.delStopSawDest(sprite)
