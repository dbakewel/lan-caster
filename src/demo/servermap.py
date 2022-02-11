"""ServerMap for Demo Game"""

import random

import engine.time as time
from engine.log import log
import engine.geometry as geo
import engine.servermap


class ServerMap(engine.servermap.ServerMap):
    """Extends engine.servermap.ServerMap

    This class implements mechanics:

    BOMB AREA MECHANIC
        Allow players to blow up the rocks blocking the mapDoor that
        links the middle of the start map to the middle of the 
        under map. There are two bomb areas, one at the 'top' of
        the mapDoor on the start map and one on the 'bottom' of
        the mapDoor on the under map.

        This mechanic requires very specific set up in Tiled of
        layers and objects on both the start and under map.

        Uses Mechanics: action, speech text, player action text,
            holdable, layer visibility.

    THROW AREA MECHANIC
        Allow sprites of type == holdable to be thrown. If a 
        sprite is holding a holdable and the sprite is in a
        trigger of type == throwArea then the holdable can
        be thrown using an action. The direction and distance
        to throw is defined by the throwArea properties and
        the throw speed is pre-defined in code.

        Uses Mechanics: action, player action text, speech text,
            holdable.

    SPEED MULTIPLIER MECHANIC
        Change the sprite's moveSpeed while inside a trigger of 
        type == speedMultiplier. This is used in the demo game
        to implement the slowing down of the player while
        walking through mud.

        Uses Mechanics: move linear

    CHICKEN MECHANIC
        Animates the chickens movement and makes them talk.

        Uses Mechanics: move linear, speech text, throw area

    RESPAWN POINT MECHANIC
        While a sprite is inside a trigger of type == saveRespawnPoint
        save the location of the player inside the sprite. The sprite
        can be sent back to this location at a later time. 
        The idea is to save the last safe point the sprite was 
        at. If the sprite is killed then it can be respawned back to 
        this point.

    """

    ########################################################
    # BOMB AREA MECHANIC
    ########################################################

    def initBombArea(self):
        """BOMB AREA MECHANIC: init method.

        Only if on the start and under map:
            Remove and store the map doors and inBounds objects that 
            are covered by rocks. These will get put back when the bomb 
            is set off in triggerBombArea()

        Note, this is hard coded to the two bomb areas in the game.
        """

        if self['name'] == "start" or self['name'] == "under":
            self['bombLadder1MapDoor'] = self.findObject(name="ladder1MapDoor", objectList=self['triggers'])
            self.removeObject(self['bombLadder1MapDoor'], objectList=self['triggers'])
            self['bombLadder1InBounds'] = self.findObject(name="ladder1InBounds", objectList=self['inBounds'])
            self.removeObject(self['bombLadder1InBounds'], objectList=self['inBounds'])

    def triggerBombArea(self, bombArea, sprite):
        """BOMB AREA MECHANIC: trigger method.

        Manage setting off the bomb. Requires player to request
        and action, be holding the bomb, and be inside the bombArea
        trigger.

        Also, show action and speech text if we are not currently
        setting off the bomb.

        This is hard coded to the two bomb area in the game.
        """
        # if we are holding a bomb in a bombArea then set it off.

        if "holding" in sprite and sprite['holding']['name'] == "bomb":
            if "action" in sprite:
                self.delSpriteAction(sprite)
                del sprite['holding']  # remove bomb and delete it from game completely

                # find maps at top and bottom of ladder.
                start = engine.server.SERVER['maps']['start']
                under = engine.server.SERVER['maps']['under']

                # update start map to after the bomb has gone off.
                start.setLayerVisablitybyName("rockOnStairs", False)
                start.setLayerVisablitybyName("rockOnStairs2", False)
                start.setLayerVisablitybyName("rockOffStairs", True)
                start.addObject(start['bombLadder1MapDoor'], objectList=start['triggers'])
                start.addObject(start['bombLadder1InBounds'], objectList=start['inBounds'])

                # update under map to after the bomb has gone off.
                under.setLayerVisablitybyName("rockOnStairs", False)
                under.setLayerVisablitybyName("rockOffStairs", True)
                under.addObject(under['bombLadder1MapDoor'], objectList=under['triggers'])
                under.addObject(under['bombLadder1InBounds'], objectList=under['inBounds'])
            else:
                self.setSpriteActionText(sprite, f"Available Action: Set off {sprite['holding']['name']}.")
        elif sprite['type'] == "player":  # if sprite is a player
            # if the rock has not been blown up yet.
            start = engine.server.SERVER['maps']['start']
            if start.getLayerVisablitybyName("rockOnStairs"):
                self.setSpriteSpeechText(sprite, f"Hmmm I wonder if I could blow this up?")
            else:
                self.setSpriteSpeechText(sprite, f"That done blow up good!")

    ########################################################
    # THROW AREA MECHANIC
    ########################################################

    def initThrowArea(self):
        """THROW AREA MECHANIC: init method."""
        self['THROWSPEED'] = 360

    def triggerThrowArea(self, throwArea, sprite):
        """THROW AREA MECHANIC: trigger method.

        If the sprite is holding a holdable and has requested
        an action then drop holdable and set it moving as 
        defined by the throwArea properties.

        Trigger Properties:
            deltaX: The holdable's X destination relative to the sprite.
            deltaY:The holdable's Y destination relative to the sprite.
        """
        # if we are holding anything while in a throwArea then throw it.

        if not self.checkKeys(throwArea, ["prop-deltaX", "prop-deltaY"]):
            log("Cannot process throwArea trigger.", "ERROR")
            return

        if "holding" in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                throwable = sprite['holding']
                self.delHoldable(sprite)  # drop throwable on the ground.
                self.setSpriteDest(
                    throwable,
                    throwable['anchorX'] + throwArea['prop-deltaX'],
                    throwable['anchorY'] + throwArea['prop-deltaY'],
                    self['THROWSPEED']
                    )
            else:
                self.setSpriteActionText(sprite, f"Available Action: Throw {sprite['holding']['name']}")
        elif sprite['type'] == "player":
            self.setSpriteSpeechText(sprite, f"I could throw something from here.")

    def checkMove(self, object, x, y):
        """THROW AREA MECHANIC: Extend MOVE LINEAR MECHANIC checkMove().

        Allow things that have bee thrown to go out of bounds so they 
        can be thrown over water. The way the throw zones are set up in
        the demo game ensures that objects can't be thrown off the map
        or other places they should not be thrown.
        """
        
        if "moveSpeed" in object and object['moveSpeed'] == self['THROWSPEED']:
            return True

        return super().checkMove(object, x, y)

    ########################################################
    # SPEED MULTIPLIER MECHANIC
    ########################################################

    def triggerSpeedMultiplier(self, trigger, sprite):
        """SPEED MULTIPLIER MECHANIC: trigger method.
        
        Change the sprite's moveSpeed based on speedMultiplier
        trigger property. This trigger will fire before stepMove
        methods are called so it will take effect this step.

        Trigger Properties:
            speedMultiplier: float value to multiply the sprite's
                moveSpeed by.

        Adds attributes to sprite: speedMultiNormalSpeed
        """
        if not self.checkKeys(trigger, ['prop-speedMultiplier']):
            log("Cannot process speedMultiplier trigger.", "ERROR")
            return

        # if sprite is moving.
        if "moveSpeed" in sprite:
            sprite['speedMultiNormalSpeed'] = sprite['moveSpeed']
            sprite['moveSpeed'] *= trigger['prop-speedMultiplier']

    def stepSpriteEndSpeedMultiplier(self, sprite):
        """SPEED MULTIPLIER MECHANIC: stepSpriteEnd method.

        This will run after stepMove methods. Restore the sprite's
        moveSpeed back to what it was.

        Removes attributes from sprite: speedMultiNormalSpeed
        """
        if "speedMultiNormalSpeed" in sprite:
            if "moveSpeed" in sprite:
                sprite['moveSpeed'] = sprite['speedMultiNormalSpeed']
            del sprite['speedMultiNormalSpeed']

    ########################################################
    # CHICKEN MECHANIC
    ########################################################

    def initChichen(self):
        """CHICKEN MECHANIC: init method."""
        self['CHICKENSPEED'] = 10

    def stepSpriteStartChicken(self, sprite):
        """CHICKEN MECHANIC: stepSpriteStart method.

        Have the chicken move towards the closest player, but
        stop before getting to close. Note, if a chicken is
        being thrown then we need to wait until it lands
        before starting it moving again.

        Also make chicken say random things at random times.
        """
        if sprite['name'] == "chicken":
            # if this chicken is not being thrown right now then have it walk to closest player.
            # we know something is being thrown because it's moveSpeed will be self['THROWSPEED']
            if ("moveSpeed" not in sprite or (
                    "moveSpeed" in sprite and sprite['moveSpeed'] != self['THROWSPEED'])):
                player = False
                playerDistance = 0
                # find the closet player.
                for p in self.findObject(type="player", returnAll=True):
                    pDis = geo.distance(sprite['anchorX'], sprite['anchorY'], p['anchorX'], p['anchorY'])
                    if pDis < playerDistance or player == False:
                        player = p
                        playerDistance = pDis
                if player and playerDistance > 50:
                    self.setSpriteDest(sprite, player['anchorX'], player['anchorY'], self['CHICKENSPEED'])
                else:
                    self.delSpriteDest(sprite)

            if random.randint(0, 5000) == 0:
                # chicken sounds from https://www.chickensandmore.com/chicken-sounds/
                text = random.choice((
                    "cluck cluck",
                    "Life is good, I'm having a good time.",
                    "Take cover I think I see a hawk!",
                    "buk, buk, buk, ba-gawk"
                    ))
                self.setSpriteSpeechText(sprite, text, time.perf_counter() + 2)

    ########################################################
    # RESPAWN POINT MECHANIC
    ########################################################

    def setSpriteLocationByRespawnPoint(self, sprite):
        """RESPAWN POINT MECHANIC: Move sprite to respawn point.
        
        Move sprite to respawn point if one was previously stored.
        This may move the sprite to a different map.

        If no respawn point was previously stored in the sprite then 
        do nothing and log a warning.
        """

        if "respawnX" in sprite:
            destMap = self
            if sprite['respawnMapName'] != self['name']:
                destMap = engine.server.SERVER['maps'][sprite['respawnMapName']]
                self.setObjectMap(sprite, destMap)
            destMap.setObjectLocationByAnchor(sprite, sprite['respawnX'], sprite['respawnY'])
            destMap.delSpriteDest(sprite)
        else:
            # else this sprite never went through a respawn point. Perhaps it is something the player carried into over
            # the respawn area. Let's hope it's OK to leave it where it is.
            log("Tried to respawn a sprite that does not have a respawn point.", "WARNING")

    def triggerSaveRespawnPoint(self, trigger, sprite):
        """RESPAWN POINT MECHANIC: trigger method.

        Save the sprite's current location as the its respawn point. 
        """
        self.setRespawnPoint(sprite)

    def setRespawnPoint(self, sprite):
        """RESPAWN POINT MECHANIC: set the sprites respawn point to it's current location.

        Remember sprites location so the sprite can be put back to this
        location later.

        Adds attributes to sprite: respawnMapName, respawnX, respawnY
        """

        sprite['respawnMapName'] = sprite['mapName']
        sprite['respawnX'] = sprite['anchorX']
        sprite['respawnY'] = sprite['anchorY']

    def delRespawnPoint(self, sprite):
        """RESPAWN POINT MECHANIC: remove the sprites respawn point.

        Removes attributes from sprite: respawnMapName, respawnX, respawnY
        """
        if "respawnMapName" in sprite:
            del sprite['respawnMapName']
        if "respawnX" in sprite:
            del sprite['respawnX']
        if "respawnY" in sprite:
            del sprite['respawnY']