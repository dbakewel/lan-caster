"""ServerMap for Engine Test Map."""

import math

from engine.log import log
import engine.servermap
import engine.time as time


class ServerMap(engine.servermap.ServerMap):
    """DELETE TIMER MECHANIC

        If a holdable to dropped on the map then delete it
        from the game in 5 seconds unless it is picked up
        again. Also show a countdown in the holdable's
        label text.

        Uses Mechanics: holdable, label text
    """

    def setHoldable(self, holdable, sprite):
        """DELETE TIMER MECHANIC: Extend engine.servermap.ServerMap.setHoldable()

        Remove delAfter timer if it exists. This stops the
        delete countdown timer from a sprite when it is
        picked up.

        Removes attributes from sprite: delAfter
        """
        if 'delAfter' in holdable:
            del holdable['delAfter']
        super().setHoldable(holdable, sprite)

    def delHoldable(self, sprite):
        """DELETE TIMER MECHANIC: Extend engine.servermap.ServerMap.delHoldable()

        Add delAfter timer to holdable that sprite is holding.
        Sprite is dropping sprite['holding'] so this will start
        the delete countdown timer on holdable.

        Add attributes to sprite: delAfter
        """
        sprite['holding']['delAfter'] = time.perf_counter() + 5
        super().delHoldable(sprite)

    def stepSpriteStartDelAfter(self, sprite):
        """DELETE TIMER MECHANIC: stepSpriteStart method.

        Delete any sprites that have a delete countdown (delAfter)
        timer that is in the past.

        Also update label text of any sprites that are counting
        down.
        """
        if 'delAfter' in sprite:
            if sprite['delAfter'] < time.perf_counter():
                self.removeObjectFromAllLayers(sprite)
            else:
                self.setSpriteLabelText(sprite, str(math.ceil(sprite['delAfter'] - time.perf_counter())))
