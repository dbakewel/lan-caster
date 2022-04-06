"""ServerMap for Engine Test Map."""

import math

from engine.log import log
import engine.servermap
import engine.time as time


class ServerMap(engine.servermap.ServerMap):
    """DELETE HOLDABLE AFTER MECHANIC

        If a holdable is dropped on the map then delete it
        from the game in 5 seconds unless it is picked up
        again. Also show a countdown in the holdable's
        label text.

        Uses Mechanics: holdable, label text
    """

    def dropHoldable(self, sprite):
        """DELETE HOLDABLE AFTER MECHANIC: Extend engine.servermap.ServerMap.dropHoldable()

        Sprite is dropping sprite['holding'] so this will start
        the delete countdown timer on holdable's trigger.

        Add 'delAfter' timer to holdable's trigger after it is
        dropped by the sprite.

        Add attributes to trigger: delAfter
        """
        # got holdable from sprite before dropping it.
        holdable = sprite['holding']

        # drop Holdable
        super().dropHoldable(sprite)

        #find trigger for the holdable that was just dropped and add timer.
        followers = self.getFollowers(holdable)
        for follower in followers:
            if 'holdableSprite' in follower and follower['holdableSprite'] == holdable:
                follower['delAfter'] = time.perf_counter() + 5
        
    def stepMapStartDelHoldableAfter(self):
        """DELETE HOLDABLE AFTER MECHANIC: stepMapStart method.

        Delete any triggers and corrisponding sprites that have a 
        delete countdown (delAfter) timer that is in the past.

        Also update label text of any sprites that are have
        triggers that are counting down.
        """
        for trigger in self['triggers']:
            if 'holdableSprite' in trigger and 'delAfter' in trigger:
                if trigger['delAfter'] < time.perf_counter():
                    self.removeFollower(trigger['holdableSprite'], trigger)
                    self.removeObjectFromAllLayers(trigger['holdableSprite'])
                    self.removeObjectFromAllLayers(trigger)
                else:
                    self.setSpriteLabelText(trigger['holdableSprite'], str(math.ceil(trigger['delAfter'] - time.perf_counter())))
