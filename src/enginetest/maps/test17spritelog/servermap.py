"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap


class ServerMap(engine.servermap.ServerMap):
    """TALK MECHANIC

        Adds a trigger with type == talk which
        sets speech text in the sprite.

        Uses Mechanics: speech text
    """

    def triggerTalk(self, trigger, sprite):
        """TALK MECHANIC: trigger method.

        Process triggers of type == talk that makes the sprite
        say whatever text is in the triggers whatToSay property.

        Trigger Properties:
            whatToSay: The text to add to sprite's speech text.
        """
        if not self.checkKeys(trigger, ["prop-whatToSay"]):
            log("Cannot process talk trigger.", "ERROR")
            return

        elif sprite['type'] == "player":
            self.setSpriteSpeechText(sprite, trigger['prop-whatToSay'])
