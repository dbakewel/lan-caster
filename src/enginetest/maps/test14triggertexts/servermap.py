"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """TEXT MECHANIC

        Adds triggers that can add/remove all kinds of text
        for the sprite and player.

        Uses Mechanics: player action test, player speech text
            label text, marquee text.
    """

    def triggerAddText(self, trigger, sprite):
        """TEXT MECHANIC: trigger method

        Add sprite or player text.

        Trigger Properties:
            prop-text: The text to set.
            prop-textType: The type of text to set: speech,
                action, label, marquee
        """
        if not self.checkKeys(trigger, ["prop-text", "prop-textType"]):
            log("Cannot process addText trigger because a trigger property is missing.", "ERROR")
            return

        if trigger['prop-textType'] == "speech":
            self.setSpriteSpeechText(sprite, trigger["prop-text"])
            # Note, speechText is removed at the start of every step (see engine.servermap.stepMapStartSpeechText())
        elif trigger['prop-textType'] == "action":
            self.setSpriteActionText(sprite, trigger["prop-text"])
            # Action text can only be set once per step. The next line will be ignored.
            self.setSpriteActionText(sprite, "SHOULD NOT SEE THIS!!!")
            # Note, actionText is removed at the start of every step (see engine.servermap.stepMapStartActionText())
        elif trigger['prop-textType'] == "label":
            self.setSpriteLabelText(sprite, trigger["prop-text"])
            # Label changes last until something else changes them.
        elif trigger['prop-textType'] == "marquee":
            self.setSpriteMarqueeText(sprite, trigger["prop-text"])
            # Marquee changes last until something else changes them.
        else:
            log(f"addText trigger has unsupported textType property: {trigger['prop-textType']}", "WARNING")

    def triggerRemoveMarqueeText(self, trigger, sprite):
        """TEXT MECHANIC: trigger method.

        Remove Marquee Text from player
        """
        self.delSpriteMarqueeText(sprite)
