"""ServerMap implements game mechanics."""

from engine.log import log
import engine.map
import engine.geometry as geo
import engine.time as time
import engine.stepmap
import engine.server


class ServerMap(engine.stepmap.StepMap):
    """The ServerMap implements several basic game mechanics.

    MOVE LINEAR MECHANIC
        Move a sprite along a linear path at a consent speed.
        Stops the sprite if it reaches the destination or
        any further movement would be invalid.

    MAPDOOR MECHANIC
        A mapDoor trigger can relocate a sprite to a new location
        on the same or different map.

    HOLDABLE MECHANIC
        Allows a sprite to request (using ACTION MECHANIC) to pickup
        and drop other sprites of type == holdable.

        Uses Mechanics: action, player action text

    ACTION MECHANIC
        Allows a sprite to request to perform some action during
        the next step. This request is only valid for one step.
        The action mechanic does nothing on it own. Other game 
        mechanics can consume the action and perform some function.

    SPEECH TEXT MECHANIC
        Used by other game mechanics to show text above a 
        sprite. Speech text only last one step or until
        a specific time after which it is removed.

    LABEL TEXT MECHANIC
        Used by other game mechanics to show text below a 
        sprite. Label text remains until changed.

    PLAYER ACTION TEXT MECHANIC
        Used by other game mechanics to display available action
        to a player. (what will probably happen if player hits
        the action button.) This is removed at the start of 
        each step and can only be set once per step (other 
        attempts to set will be ignored.)

    PLAYER MARQUEE TEXT MECHANIC
        Used by other game mechanics to display marquee text
        to a player. Marquee text remains until changed.

    """

    ########################################################
    # MOVE LINEAR MECHANIC
    ########################################################

    def stepMoveLinear(self, sprite):
        """MOVE LINEAR MECHANIC: stepMove method.

        If the sprite is moving then move it towards it's destination. If it
        can't move any longer (all movement would be invalid) or it has reached 
        it's destination then stop the sprite.

        Add attributes to sprite: direction
        """
        
        # if sprite is moving
        if "moveDestX" in sprite and "moveDestY" in sprite and "moveSpeed" in sprite:

            # convert pixels per second to pixels per step
            stepSpeed = sprite['moveSpeed'] / engine.server.SERVER['fps']

            # compute a new angle in radians which moves directly towards destination
            # sprite['direction'] is stored and never removed so client will know the last
            # direction the sprite was facing.
            sprite['direction'] = geo.angle(
                sprite['anchorX'],
                sprite['anchorY'],
                sprite['moveDestX'],
                sprite['moveDestY'])

            # compute a new anchor x,y which moves directly towards destination for this step
            newAnchorX, newAnchorY = geo.project(
                sprite['anchorX'],
                sprite['anchorY'],
                sprite['direction'],
                stepSpeed
                )

            # movement is only allowed if it is inbounds.
            inBounds = False

            # if sprite can move directly towards destination
            if self.checkMove(sprite, newAnchorX, newAnchorY):
                inBounds = True
            # elif sprite is moving along X then try to stay at the same Y and move along only along X
            elif newAnchorX != sprite['anchorX'] and self.checkMove(sprite, newAnchorX, sprite['anchorY']):
                newAnchorY = sprite['anchorY']
                inBounds = True
            # elif sprite is moving along Y then try to stay at the same X and move along only along Y
            elif newAnchorY != sprite['anchorY'] and self.checkMove(sprite, sprite['anchorX'], newAnchorY):
                newAnchorX = sprite['anchorX']
                inBounds = True

            if inBounds:
                if geo.distance(sprite['anchorX'], sprite['anchorY'], newAnchorX, newAnchorY) < 0.1:
                    # if sprite is only going to move less than 0.1 pixel then stop it.
                    self.delSpriteDest(sprite)
                elif geo.distance(newAnchorX, newAnchorY, sprite['moveDestX'], sprite['moveDestY']) < stepSpeed:
                    # if sprite is close to destination then stop it.
                    self.delSpriteDest(sprite)

                # move sprite to new location
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)
            else:
                # sprite cannot move.
                self.delSpriteDest(sprite)

    def checkMove(self, object, x, y):
        """MOVE LINEAR MECHANIC: Check if a location for an object is valid.

        Determines is (x, y) would be a valid anchor point for object while
        taking several things into account, including map size, inBounds layer, 
        and outOfBounds layer.

        Priority of evaluation is as follows:
        1) if (x, y) is not on the map then it is NOT inbounds.
        2) if (x, y) is inside an object on the inBounds layer then it IS inbounds.
        3) if (x, y) is inside an object on the outOfBounds layer then it is NOT inbounds.
        4) else it IS inbounds.

        Args:
            object (dict): A Tiled object.
            x (float): x coordiate to check if valid
            y (float): y coordiate to check if valid

        Returns:
            bool: True if an anchor point of (x, y) would be a valid for object, else False
        """

        # if move player move checking has been turned off then allow all moves for players
        if object['type'] == 'player' and not engine.server.SERVER['playerMoveCheck']:
            return True

        if geo.objectContains({"x": 0, "y": 0, "width": self['pixelWidth'], "height": self['pixelHeight']}, x, y) and \
                (geo.objectsContains(self['inBounds'], x, y) or (not geo.objectsContains(self['outOfBounds'], x, y))):
            return True
        return False

    def setSpriteDest(self, sprite, moveDestX, moveDestY, moveSpeed):
        """MOVE LINEAR MECHANIC: Set sprites destination and speed.

        Add attributes to sprite: moveDestX, moveDestY, moveSpeed
        """
        sprite['moveDestX'] = moveDestX
        sprite['moveDestY'] = moveDestY
        sprite['moveSpeed'] = moveSpeed

    def delSpriteDest(self, sprite):
        """MOVE LINEAR MECHANIC: Stop Sprite

        Remove attributes from sprite: moveDestX, moveDestY, moveSpeed
        """
        if "moveDestX" in sprite:
            del sprite['moveDestX']
        if "moveDestY" in sprite:
            del sprite['moveDestY']
        if "moveSpeed" in sprite:
            del sprite['moveSpeed']

    ########################################################
    # MAPDOOR MECHANIC
    ########################################################

    def initMapDoor(self):
        """MAPDOOR MECHANIC: init method.

        Set the priority of mapDoor trigger to 1 (very high).
        This ensures a sprite goes through the mapDoor first
        and other triggers are stopped after the sprite moves.
        """
        self.addStepMethodPriority("trigger", "triggerMapDoor", 1)

    def triggerMapDoor(self, trigger, sprite):
        """MAPDOOR MECHANIC: trigger method

        Relocate sprite based on trigger properties.

        Trigger Properties:
            destMapName: The map to move the player to. If missing then
                do not change map.
            destReference: The name of an object on the destination map
                reference layer. This is the location the sprite will be
                moved to.

        If the sprite is relocated then this method returns True which
        stops other triggers from being processed for this sprite during 
        the rest of this step. This makes sense since the sprite is no 
        longer in the same location.

        Returns:
            True: if sprite was moved.
            None: if sprite did not move.
        """

        if not self.checkKeys(trigger, ["prop-destReference"]):
            log("Cannot process mapDoor trigger.", "ERROR")
            return

        # find destination based on object named trigger['prop-destReference'] on
        # layer "reference" of map trigger['prop-destMapName']. If trigger['prop-destMapName']
        # then we stay on the same map.
        if "prop-destMapName" in trigger:
            if trigger['prop-destMapName'] in engine.server.SERVER['maps']:
                destMap = engine.server.SERVER['maps'][trigger['prop-destMapName']]
            else:
                log(
                    f"MapDoor destMapName does not exist! trigger['prop-destMapName'] == {trigger['prop-destMapName']}",
                    "FAILURE")
                exit()
        else:
            destMap = self
        dest = self.findObject(name=trigger['prop-destReference'], objectList=destMap['reference'])
        if dest:
            self.setObjectMap(sprite, destMap)
            destMap.setObjectLocationByAnchor(sprite, dest['anchorX'], dest['anchorY'])
            destMap.delSpriteDest(sprite)
            return True  # stop the processing of other triggers since sprite has moved.
        else:
            log(
                f"Trigger destination not found = {trigger['prop-destMapName']} - {trigger['prop-destReference']}",
                "ERROR")

    ########################################################
    # HOLDABLE MECHANIC
    ########################################################

    def initHoldable(self):
        """HOLDABLE MECHANIC: init method.

        holdable sprites need to be included in Tiled data on
        the sprites layer. This methods copies (by reference) 
        sprites of type == "holdable" to the triggers layer. They
        are them on BOTH layers at the same time.
        """
        
        for holdable in self.findObject(type="holdable", returnAll=True):
            self.addObject(holdable, objectList=self['triggers'])

        self.addStepMethodPriority("trigger", "triggerHoldable", 10)
        self.addStepMethodPriority("stepSpriteEnd", "stepSpriteEndHoldable", 89)

    def triggerHoldable(self, holdable, sprite):
        """HOLDABLE MECHANIC: trigger method.

        The sprite's anchor is inside the trigger.

        if the sprite is not holding anything now then: 
            1) pick up holdable if the sprite has requested an action else
            2) tell the sprite the pick up action is possible.
        """
        if "holding" not in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.setHoldable(holdable, sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Pick Up {holdable['name']}")

    def stepSpriteEndHoldable(self, sprite):
        """HOLDABLE MECHANIC: stepSpriteEnd method.

        Drop holdable if sprite has holding and action is requested by user.
        """
        
        if "holding" in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite) # consume sprite action
                self.delHoldable(sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Drop {sprite['holding']['name']}")

    def setHoldable(self, holdable, sprite):
        """HOLDABLE MECHANIC: sprite picks up holdable.

        Add attributes to sprite: holding
        """
        self.removeObjectFromAllLayers(holdable)
        sprite['holding'] = holdable

    def delHoldable(self, sprite):
        """HOLDABLE MECHANIC: sprite drops holding at sprite's location.

        Remove attributes from sprite: holding
        """
        dropping = sprite['holding']
        del sprite['holding']

        # put the dropped item at the feet of the sprite that was holding it.
        self.setObjectLocationByAnchor(dropping, sprite['anchorX'], sprite['anchorY'])
        self.delSpriteDest(dropping)
        self.addObject(dropping, objectList=self['sprites'])
        # add holdable type object back as a trigger so it can be picked up again.
        self.addObject(dropping, objectList=self['triggers'])

    ########################################################
    # ACTION MECHANIC
    ########################################################

    def initAction(self):
        """ACTION MECHANIC: init method.

        Set priority of stepSpriteEndAction to be very low so all other
        code has a chance to consume an action before it is removed.
        """
        self.addStepMethodPriority("stepSpriteEnd", "stepSpriteEndAction", 90)

    def stepSpriteEndAction(self, sprite):
        """ACTION MECHANIC: stepSpriteEnd method.

        If an action was requested but no step method was able to consume
        the action then simply delete the action (consume action it but do nothing).
        """
        self.delSpriteAction(sprite)

    def setSpriteAction(self, sprite):
        """ACTION MECHANIC: flag sprite that it should perform one action.
        
        This is normally set in a player sprite after the server
        receives a playerAction message from client. Other game
        mechanics can look for an action request and perform
        some action based on this.

        This should be set before a steps starts or very early
        in a step since it will be removed at the end of the step
        and all step code should have a chance to see the action 
        has been requested.

        Add attributes to sprite: action
        """
        sprite['action'] = True

    def delSpriteAction(self, sprite):
        """ACTION MECHANIC: clear sprite flag from sprite.

        This should be called whenever some code does something
        because of the action (the action is consumed). It 
        should also be called at the end of the step is nothing
        could consume the action since action requests only 
        last one step.

        Remove attributes to sprite: action
        """
        if "action" in sprite:
            del sprite['action']

    ########################################################
    # SPEECH TEXT MECHANIC
    ########################################################

    def stepSpriteStartSpeechText(self, sprite):
        """SPEECH TEXT MECHANIC: Remove speechText from sprite if it has timed out."""

        if "speechTextDelAfter" not in sprite or (
                "speechTextDelAfter" in sprite and sprite['speechTextDelAfter'] < time.perf_counter()):
            self.delSpriteSpeechText(sprite)

    def setSpriteSpeechText(self, sprite, speechText, speechTextDelAfter=0):
        """SPEECH TEXT MECHANIC: add speechText to sprite.

        Add attributes to sprite: 
            speechText
            speechTextDelAfter (optional)

        Args:
            speechText (str): The text the sprite is speaking.
            speechTextDelAfter (float): time after which speechText will be
                removed. Default is to remove at start of next step. 
        """
        old = False
        if "speachText" in sprite:
            old = sprite['speechText']

        self.delSpriteSpeechText(sprite)
        sprite['speechText'] = speechText
        if speechTextDelAfter > 0:
            sprite['speechTextDelAfter'] = speechTextDelAfter

        if old != sprite['speechText']:
            self.setMapChanged()

    def delSpriteSpeechText(self, sprite):
        """SPEECH TEXT MECHANIC: remove speechText from sprite.

        Remove attributes to sprite: speechText, speechTextDelAfter
        """
        if "speechText" in sprite:
            del sprite['speechText']
        if "speechTextDelAfter" in sprite:
            del sprite['speechTextDelAfter']

    ########################################################
    # LABEL TEXT MECHANIC
    ########################################################

    def setSpriteLabelText(self, sprite, labelText):
        """LABEL TEXT MECHANIC: add labelText to sprite.

        Adds attributes to sprite: labelText
        """
        if 'labelText' not in sprite or labelText != sprite['labelText']:
            sprite['labelText'] = labelText
            self.setMapChanged()

    def delSpriteLabelText(self, sprite):
        """LABEL TEXT MECHANIC: remove labelText from sprite.

        Remove attributes to sprite: labelText
        """
        if 'labelText' in sprite:
            del sprite['labelText']
            self.setMapChanged()

    ########################################################
    # PLAYER ACTION TEXT MECHANIC
    ########################################################

    def stepSpriteStartActionText(self, sprite):
        """PLAYER ACTION TEXT MECHANIC: delete action text from player linked to sprite.

        Each step the actions available may change so start each
        step by removing all action text. The first game mechanic
        that finds an action that could be performed can set a
        new action text.
        """
        self.delSpriteActionText(sprite)

    def setSpriteActionText(self, sprite, actionText):
        """PLAYER ACTION TEXT MECHANIC: add action text to player linked to sprite.

        Note, this will only work if sprite action text has not
        already been set during this step.
        """

        if sprite['type'] == "player" and "playerNumber" in sprite:
            engine.server.SERVER.setPlayerActionText(sprite['playerNumber'], actionText)

    def delSpriteActionText(self, sprite):
        """PLAYER ACTION TEXT MECHANIC: remove action text from player linked to sprite."""
        if sprite['type'] == "player" and "playerNumber" in sprite:
            engine.server.SERVER.delPlayerActionText(sprite['playerNumber'])

    ########################################################
    # PLAYER MARQUEE TEXT MECHANIC
    ########################################################

    def setSpriteMarqueeText(self, sprite, marqueeText):
        """PLAYER MARQUEE TEXT MECHANIC: add marquee text to player linked to sprite."""

        # if this is a sprite for a player that has joined the game.
        if sprite['type'] == "player" and "playerNumber" in sprite:
            engine.server.SERVER.setPlayerMarqueeText(sprite['playerNumber'], marqueeText)

    def delSpriteMarqueeText(self, sprite):
        """PLAYER MARQUEE TEXT MECHANIC: remove marquee text from player linked to sprite."""

        if sprite['type'] == "player" and "playerNumber" in sprite:
            engine.server.SERVER.delPlayerMarqueeText(sprite['playerNumber'])
