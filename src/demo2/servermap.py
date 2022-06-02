"""ServerMap for demo2 Game"""

import random
import math

import engine.time as time
from engine.log import log
import engine.geometry as geo
import engine.servermap
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """Extends engine.servermap.ServerMap"""

    ########################################################
    # LOCKED DOOR MECHANIC (setup done in server init() since it has to be done game wide)
    ########################################################

    def triggerLockedDoor(self, trigger, sprite):
        """LOCKED DOOR MECHANIC: trigger method."""

        if sprite['type'] == 'player':
            # If the player has a key that unlocks the door
            if 'key' in sprite and sprite['key']['lockNumber'] == trigger['lockNumber']:
                #remove door trigger
                self.removeObject(trigger, self['triggers'])
                # remove copy of door from other layers
                for o in trigger['doNotTrigger']:
                    self.removeObjectFromAllLayers(o)
                # remove key from game
                del sprite['key']

                # give points to team that opened door
                if sprite['prop-team'] == 'blue':
                    engine.server.SERVER['bluePoints'] += 3
                else:
                    engine.server.SERVER['redPoints'] += 3
                self.setSpriteSpeechText(sprite, f"3 points for {sprite['prop-team']}!", time.perf_counter() + 4)
            else:
                self.setSpriteSpeechText(sprite, f"This door needs key {trigger['lockNumber']}")

    ########################################################
    # WEAPONS MECHANIC
    ########################################################
    def initWeapons(self):
        """Set weapon tunable values"""

        self['ARROWRANGE'] = 10000
        self['ARROWDAMAGE'] = 40
        self['ARROWSPEED'] = 600

        self['STARRANGE'] = 400
        self['STARDAMAGE'] = 10
        self['STARSPEED'] = 300
        self['STARCOUNT'] = 5
        self['STARSPRED'] = math.pi / 4 / self['STARCOUNT']

        self['RAYRANGE'] = 200
        self['RAYDAMAGE'] = 1  # per step
        self['RAYSECS'] = 0.5  # secs ray lasts for

    def stepMapStartWeapons(self):
        """Inflict damage from weapons"""

        for s1 in self['sprites']:
            if s1['type'] == 'arrow' or s1['type'] == 'star':
                # if arrow or star has stopped moving then remove it from game
                if 'move' not in s1:
                    # if s1 has stopped then remove it.
                    self.removeObject(s1)
                else:
                    # determine if s1 hit a player
                    for s2 in self['sprites']:
                        if s2['type'] == 'player':
                            # do a fast collision checked based on the width and anchor points.
                            distance = geo.distance(
                                s1['anchorX'], s1['anchorY'],
                                s2['anchorX'], s2['anchorY'],
                                )
                            if distance < s2['width'] / 2:
                                self.removeObject(s1)
                                if s1['type'] == 'arrow':
                                    engine.server.SERVER['playersByNum'][s2['playerNumber']]['health'] -= self['ARROWDAMAGE']
                                elif s1['type'] == 'star':
                                    engine.server.SERVER['playersByNum'][s2['playerNumber']]['health'] -= self['STARDAMAGE']

            elif s1['type'] == 'ray':
                # is is time to remove ray?
                if s1['delAfter'] < time.perf_counter():
                    # if s1 has timed out then remove it.
                    self.removeObject(s1)
                else:
                    # determine if s1 hit a player
                    for s2 in self['sprites']:
                        if s2['type'] == 'player':
                            if geo.intersectLineCircle(
                                s1['x'] + s1['polyline'][0]['x'], 
                                s1['y'] + s1['polyline'][0]['y'], 
                                s1['x'] + s1['polyline'][1]['x'], 
                                s1['y'] + s1['polyline'][1]['y'],
                                s2['anchorX'], s2['anchorY'], s2['width']/2):
                                engine.server.SERVER['playersByNum'][s2['playerNumber']]['health'] -= self['RAYDAMAGE']


    def createArrow(self, x,y,angle,startDistance,color):
        """Add an arrow to the map"""
        anchorX, anchorY = geo.project(x,y,angle,startDistance)
        endX, endY = geo.project(anchorX,anchorY,angle-math.pi,12)

        arrow = {
            "lineColor": color,
            "lineThickness": 1,
             "polyline":[
                    {
                     "x":0,
                     "y":0
                    }, 
                    {
                     "x":endX - anchorX,
                     "y":endY - anchorY
                    }],
             "type":"arrow",
             "x":anchorX,
             "y":anchorY,
             "checkLocationOn": ['outOfBounds'] # only consider outOfBounds layer
            }
        self.checkObject(arrow)
        self.addObject(arrow)
        moveDestX, moveDestY = geo.project(anchorX,anchorY,angle,self['ARROWRANGE'])
        self.setMoveLinear(arrow, moveDestX, moveDestY, self['ARROWSPEED'], slide=False, easeIn=False)

    def createStars(self, x,y,angle,startDistance,color):
        """Add a throwing stars to the game"""
        angle = angle - (self['STARSPRED'] * self['STARCOUNT'] / 2)
        for i in range(self['STARCOUNT']):
            anchorX, anchorY = geo.project(x,y,angle,startDistance)
            star = {
                "ellipse":True,
                "borderColor": color,
                "borderThickness": 1,
                "type":"star",
                "anchorX": anchorX,
                "anchorY": anchorY,
                "width": 5.0,
                "height": 5.0,
                "x":anchorX-2.5,
                "y":anchorY-2.5,
                "checkLocationOn": ['outOfBounds'] # only consider outOfBounds layer
                }
            self.checkObject(star)
            self.addObject(star)
            moveDestX, moveDestY = geo.project(anchorX,anchorY,angle,self['STARRANGE'])
            self.setMoveLinear(star, moveDestX, moveDestY, self['STARSPEED'], slide=False, easeIn=False)

            angle += self['STARSPRED']

    def createRay(self, x,y,angle,startDistance,color):
        """Add ray to the game"""
        x1, y1 = geo.project(x,y,angle,startDistance)
        x2, y2 = geo.project(x1,y1,angle,self['RAYRANGE'])

        arrow = {
            "lineColor": color,
            "lineThickness": 4,
            "polyline":[
                    {
                     "x":0,
                     "y":0
                    }, 
                    {
                     "x":x2 - x1,
                     "y":y2 - y1
                    }],
             "type":"ray",
             "x":x1,
             "y":y1,
             "delAfter": time.perf_counter() + self['RAYSECS']
            }
        self.checkObject(arrow)
        self.addObject(arrow)

    ########################################################
    # BRAWL MECHANIC
    ########################################################

    def stepMapEndBrawl(self):
        """If two players (or player and monster) overlap then they fight, reducing both players health."""

        # player fighting player
        for i in range(len(self['sprites'])):
            if self['sprites'][i]['type'] == 'player':
                player = self['sprites'][i]
                for j in range(i + 1, len(self['sprites'])):
                    other = self['sprites'][j]
                    if other['type'] == 'player' and player['prop-team'] != other['prop-team']:
                        # do a fast collision check based on the width and anchor points.
                        distance = geo.distance(
                            player['anchorX'], player['anchorY'],
                            other['anchorX'], other['anchorY'],
                            )
                        if distance < (player['width'] / 2 + other['width'] / 2):
                            engine.server.SERVER['playersByNum'][player['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(player, "Fight!!!")
                            engine.server.SERVER['playersByNum'][other['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(other, "Fight!!!")

        # player fighting monster
        for i in range(len(self['sprites'])):
            if self['sprites'][i]['type'] == 'player':
                player = self['sprites'][i]
                for j in range(len(self['sprites'])):
                    if self['sprites'][j]['type'] == 'monster':
                        other = self['sprites'][j]
                        # do a fast collision check based on the width and anchor points.
                        distance = geo.distance(
                            player['anchorX'], player['anchorY'],
                            other['anchorX'], other['anchorY'],
                            )
                        if distance < (player['width'] / 2 + other['width'] / 2)*1.1:  # 1.1 required since monsters cannot overlap other sprites
                            engine.server.SERVER['playersByNum'][player['playerNumber']]['health'] -= 1
                            self.setSpriteSpeechText(player, "Fight!!!")
                            self.setSpriteSpeechText(other, "Kill!!!")

    ########################################################
    # MONSTER MOVE MECHANIC
    ########################################################

    def initMonster(self):
        """MONSTER MOVE MECHANIC: init method."""
        self['MONSTERSPEED'] = 50

    def stepMapStartMonster(self):
        """MONSTER MOVE MECHANIC: stepMapStart method.

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

                # at random times, have monster say things.
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

        if sprite['type'] != 'player':
            return

        engine.server.SERVER['playersByNum'][sprite['playerNumber']]['health'] -= 2
        self.setSpriteSpeechText(sprite, "LAVA!!!")

    ########################################################
    # HOLDABLE MECHANIC (override engine.servermap)
    ########################################################

    def triggerHoldable(self, holdableTrigger, sprite):
        """OVERRIDE engine.triggerHoldable

        Add support for holding 3 different holdables, one of each: weapon, key, and idol.
        """

        if sprite['type'] != 'player':
            return

        if holdableTrigger['prop-holdable-type'] == 'idol' and holdableTrigger['prop-team'] == sprite['prop-team']:
            # action to pray to players own idol
            if 'canNextPray' in sprite and sprite['canNextPray'] < time.perf_counter():
                del sprite['canNextPray']
            if 'canNextPray' not in sprite:
                if "action" in sprite:
                    self.delSpriteAction(sprite)
                    engine.server.SERVER.restoreStats(sprite['playerNumber'])
                    self.setSpriteSpeechText(sprite, "I am restored!", time.perf_counter() + 4)
                    sprite['canNextPray'] = time.perf_counter() + 60
                else:
                    self.setSpriteActionText(sprite, f"Pray to Idol (space)")

        elif holdableTrigger['prop-holdable-type'] not in sprite:
            # pick up weapon, key, or other teams idol.
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.pickupHoldable(holdableTrigger, sprite)

                if holdableTrigger['prop-holdable-type'] == 'idol':
                    self.setSpriteSpeechText(sprite, "I must return this idol to my base!", time.perf_counter() + 8)
            else:
                self.setSpriteActionText(sprite, f"Pick Up {holdableTrigger['holdableSprite']['name']} (space)")

    def stepMapEndHoldable(self):
        """OVERRIDE engine.stepMapEndHoldable()

        do not allow dropping
        """
        pass

    def pickupHoldable(self, holdableTrigger, sprite):
        """OVERRIDE. pickup to one of weapon, key, or idol"""
        holdable = holdableTrigger['holdableSprite']
        self.removeFollower(holdable, holdableTrigger)
        self.removeObjectFromAllLayers(holdableTrigger)
        self.removeObjectFromAllLayers(holdable)
        # each holdable has a property saying if it is a key, weapon, or idol in 'prop-holdable-type'
        sprite[holdableTrigger['prop-holdable-type']] = holdable

    def dropHoldable(self, sprite, key):
        """OVERRIDE. Drop back where items were picked up as opposed to where the player is now.

        key variable is one of key, idol, or weapon
        """
        holdable = sprite[key]
        del sprite[key]

        # put the dropped item back where it came from.
        destmap = engine.server.SERVER['maps'][holdable['mapName']]
        destmap.addObject(holdable)
        destmap.addHoldableTrigger(holdable)
