"""ServerMap for Demo Game Start Map"""

from engine.log import log
import demo.servermap


class ServerMap(demo.servermap.ServerMap):
    """Extends demo.servermap.ServerMap

    This class implements mechanics:

    LOCKED MAPDOOR MECHANIC
        The locked mapDoor mechanic will change type to
        a mapDoor trigger when the sprite is holding a
        holdable with a specific name. It will optionally
        also hide and show a layer so the graphic can
        change from a locked door to an unlocked door.

        While the door is still locked, speechtext is
        displayed to give player hide on what is needed
        to unlock the door.

        Uses Mechanics: holdable, mapDoor, player speech text
    """

    ########################################################
    # LOCKED MAPDOOR MECHANIC
    ########################################################

    def triggerLockedMapDoor(self, trigger, sprite):
        """LOCKED MAPDOOR MECHANIC: trigger method.

        Trigger Properties:
            unlocks: The name of a holdable that will unlock the door.
            lockedText: The speech text for the sprite to say while
                the door is locked.
            hidelayer: The name of the layer to hide when
                door is unlocked. (optional)
            showlayer:The name of the layer to show when
                door is unlocked. (optional)
        """

        if not self.checkKeys(trigger, ["prop-unlocks", "prop-lockedText"]):
            log("Cannot process lockedMapDoor trigger.", "ERROR")
            return

        # if the sprite is holding the correct thing to unlock the door.
        if "holding" in sprite and sprite['holding']['name'] == trigger['prop-unlocks']:

            # unlock door (change type to mapDoor)
            # sprite will most likely trigger the mapDoor on the next step.
            trigger['type'] = "mapDoor"

            # hide door locked layer and show unlocked door layer.
            if "prop-hideLayer" in trigger:
                self.setLayerVisablitybyName(trigger['prop-hideLayer'], False)
            if "prop-showLayer" in trigger:
                self.setLayerVisablitybyName(trigger['prop-showLayer'], True)
        elif sprite['type'] == "player":
            self.setSpriteSpeechText(sprite, trigger['prop-lockedText'])
