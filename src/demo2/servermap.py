"""ServerMap for Demo Game"""

import random

import engine.time as time
from engine.log import log
import engine.geometry as geo
import engine.servermap


class ServerMap(engine.servermap.ServerMap):
    """Extends engine.servermap.ServerMap"""

    def initWeapon(self):
        for s in self.findObject(type="weapon", returnAll=True):
            self.addTriggerToSprite(s)

    def triggerWeapon(self, trigger, sprite):
        # if sprite is a player without a weapon then pick up weapon.
        if sprite['type'] == 'player' and 'weapon' not in sprite:
            sprite['weapon'] = trigger['sprite']
            self.removeFollower(trigger['sprite'], trigger)
            self.removeObjectFromAllLayers(trigger)
            self.removeObjectFromAllLayers(trigger['sprite'])

    def initKey(self):
        for s in self.findObject(type="key", returnAll=True):
            self.addTriggerToSprite(s)

    def triggerKey(self, trigger, sprite):
        # if sprite is a player without a weapon then pick up weapon.
        if sprite['type'] == 'player' and 'key' not in sprite:
            sprite['key'] = trigger['sprite']
            self.removeFollower(trigger['sprite'], trigger)
            self.removeObjectFromAllLayers(trigger)
            self.removeObjectFromAllLayers(trigger['sprite'])

    def initIdle(self):
        for s in self.findObject(type="idle", returnAll=True):
            self.addTriggerToSprite(s)

    def triggerIdle(self, trigger, sprite):
        # if sprite is a player without a weapon then pick up weapon.
        if sprite['type'] == 'player' and 'idle' not in sprite and sprite['prop-team'] != trigger['prop-team']:
            sprite['idle'] = trigger['sprite']
            self.removeFollower(trigger['sprite'], trigger)
            self.removeObjectFromAllLayers(trigger)
            self.removeObjectFromAllLayers(trigger['sprite'])

    def addTriggerToSprite(self, sprite):
        trigger = sprite.copy()
        trigger['collisionType'] = 'rect'
        trigger['doNotTrigger'] = [sprite]
        trigger['sprite'] = sprite
        self.addObject(trigger, objectList=self['triggers'])
        self.addFollower(sprite, trigger)