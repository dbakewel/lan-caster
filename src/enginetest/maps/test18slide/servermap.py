"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap
import engine.geometry as geo
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """SLIDE MECHANIC

        A slide forces sprites to move in a specific direction and speed.
        Note, a sprite that is sliding can move while in an outOfBounds area.

        Uses Mechanics: move
    """

    def initSlide(self):
        """SLIDE MECHANIC: init method.

        Slide trigger needs to occur after other triggers
        that change speed and direction since we want to force
        the sprite to move as dictated by the slide.
        """
        self.addStepMethodPriority("trigger", "triggerSlide", 99)

    def triggerSlide(self, trigger, sprite):
        """SLIDE MECHANIC: trigger method.

        Set the sprites direction and speed to match the slide triggers
        properties: slideDirection, slideSpeed

        Note, slideDirection is in radians.
        """
        if not self.checkKeys(trigger, ["prop-slideDirection", "prop-slideSpeed"]):
            log("Cannot process slide trigger.", "ERROR")
            return

        # Set the destination slightly further away (1.001) then the sprite will get in one step.
        # This ensures the sprite will make a full speed move this step.
        moveDestX, moveDestY = geo.project(
            sprite['anchorX'],
            sprite['anchorY'],
            trigger["prop-slideDirection"],
            trigger["prop-slideSpeed"] / engine.server.SERVER['fps'] * 1.001
            )
        self.setMoveLinear(sprite, moveDestX, moveDestY, trigger["prop-slideSpeed"])

        # mark sprite as sliding so we know it should be allowed to move inside outOfBounds areas.
        sprite["sliding"] = True

    def checkLocation(self, object, newAnchorX, newAnchorY):
        """SLIDE MECHANIC: Extend MOVE LINEAR MECHANIC checkLocation().

        If an object is sliding then allow it to move. The slide setup must
        ensure the sprite does not move to an invalid location.
        """

        if "sliding" in object:
            return True

        return super().checkLocation(object, newAnchorX, newAnchorY)

    def stepMapEndSlide(self):
        """SLIDE MECHANIC: remove sliding marker from sprite.

        Remove the sprite sliding marker now the step is over. It will
        get added again during the next step is the sprite is still inside
        a slide trigger.
        """
        for sprite in self['sprites']:
            if "sliding" in sprite:
                del sprite["sliding"]
