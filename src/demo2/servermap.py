"""ServerMap for Demo Game"""

import random

import engine.time as time
from engine.log import log
import engine.geometry as geo
import engine.servermap
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """Extends engine.servermap.ServerMap"""

    ########################################################
    # BRAWL MECHANIC
    ########################################################

    def stepMapEndBrawl(self):
        """If two players (or player and monster) overlap then they fight, reducing players health."""

        # player fighting player
        for i in range(len(self['sprites'])):
            if self['sprites'][i]['type'] == 'player':
                player = self['sprites'][i]
                for j in range(i+1, len(self['sprites'])):
                    other = self['sprites'][j]
                    if other['type'] == 'player' and player['prop-team'] != other['prop-team']:
                        # do a fast collision checked based on the width and anchor points.
                        distance =  geo.distance(
                            player['anchorX'], player['anchorY'],
                            other['anchorX'], other['anchorY'],
                        )
                        if distance < (player['width']/2 + other['width']/2):
                            engine.server.SERVER['playersByNum'][player['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(player,"Fight!!!")
                            engine.server.SERVER['playersByNum'][other['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(other,"Fight!!!")
                            

        # player fighting monster
        for i in range(len(self['sprites'])):
            if self['sprites'][i]['type'] == 'player':
                player = self['sprites'][i]
                for j in range(len(self['sprites'])):
                    if self['sprites'][j]['type'] == 'monster':
                        other = self['sprites'][j]
                        # do a fast collision checked based on the width and anchor points.
                        distance =  geo.distance(
                            player['anchorX'], player['anchorY'],
                            other['anchorX'], other['anchorY'],
                        )
                        if distance < (player['width']/2 + other['width']/2):
                            engine.server.SERVER['playersByNum'][player['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(player,"Fight!!!")
                            self.setSpriteSpeechText(other,"Kill!!!")

    ########################################################
    # MONSTER MECHANIC
    ########################################################

    def initMonster(self):
        """MONSTER MECHANIC: init method."""
        self['MONSTERSPEED'] = 50

    def stepMapStartMonster(self):
        """MONSTER MECHANIC: stepMapStart method.

        Have the monster move towards the closest player.
        Also make monster say random things at random times.
        """
        for sprite in self['sprites']:
            if sprite['type'] == "monster":
                player = False
                playerDistance = 0
                # find the closet player.
                for p in self['sprites']:
                    if p['type'] == 'player':
                        pDis = geo.distance(sprite['anchorX'], sprite['anchorY'], p['anchorX'], p['anchorY'])
                        if pDis < playerDistance or player == False:
                            player = p
                            playerDistance = pDis
                if player:
                    self.setMoveLinear(sprite, player['anchorX'], player['anchorY'], self['MONSTERSPEED'])

                if random.randint(0, 5000) == 0:
                    text = random.choice((
                        "kill kill kill",
                        "I want to suck your blood.",
                        "BRAINS!!!",
                        "agggggg"
                        ))
                    self.setSpriteSpeechText(sprite, text, time.perf_counter() + 2)

    ########################################################
    # LAVA MECHANIC
    ########################################################

    def triggerLava(self, trigger, sprite):
        """LAVA MECHANIC: trigger method."""
        engine.server.SERVER['playersByNum'][sprite['playerNumber']]['health'] -= 2
        self.setSpriteSpeechText(sprite,"LAVA!!!")

    ########################################################
    # HOLDABLE MECHANIC (override engine.servermap)
    ########################################################

    def triggerHoldable(self, holdableTrigger, sprite):
        """OVERRIDE engine.triggerHoldable"""

        if holdableTrigger['prop-holdable-type'] == 'idol' and holdableTrigger['prop-team'] == sprite['prop-team']:
            if 'canNextPray' in sprite and sprite['canNextPray'] < time.perf_counter():
                del sprite['canNextPray']
            if 'canNextPray' not in sprite:
                if "action" in sprite:
                    self.delSpriteAction(sprite)
                    engine.server.SERVER.restoreStats(sprite['playerNumber'])
                    self.setSpriteSpeechText(sprite, "I am restored!", time.perf_counter() + 8)
                    sprite['canNextPray'] = time.perf_counter() + 60
                else:
                    self.setSpriteActionText(sprite, f"Available Action: Pray to Idol")

        elif sprite['type'] == 'player' and holdableTrigger['prop-holdable-type'] not in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.pickupHoldable(holdableTrigger, sprite)

                if holdableTrigger['prop-holdable-type'] == 'idol':
                    self.setSpriteSpeechText(sprite, "I must return this idol to my base!", time.perf_counter() + 8)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Pick Up {holdableTrigger['holdableSprite']['name']}")

    def stepMapEndHoldable(self):
        """OVERRIDE engine.stepMapEndHoldable()

        do not allow dropping
        """
        pass

    def pickupHoldable(self, holdableTrigger, sprite):
        """OVERRIDE pickup to one of weapon, key, or idol"""
        holdable = holdableTrigger['holdableSprite']
        self.removeFollower(holdable,holdableTrigger)
        self.removeObjectFromAllLayers(holdableTrigger)
        self.removeObjectFromAllLayers(holdable)
        sprite[holdableTrigger['prop-holdable-type']] = holdable

    def dropHoldable(self, sprite, key):
        """OVERRIDE drop back where items started"""
        holdable = sprite[key]
        del sprite[key]

        # put the dropped item back where it came from.
        destmap = engine.server.SERVER['maps'][holdable['mapName']]
        destmap.addObject(holdable)
        destmap.addHoldableTrigger(holdable)

