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
        (only if a valid location) on the same or different map.

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
        if 'move' in sprite and sprite['move']['type'] == 'Linear':
            moveDestX = sprite['move']['x']
            moveDestY = sprite['move']['y']
            moveSpeed = sprite['move']['s']
            slide = sprite['move']['sl']

            # convert pixels per second to pixels per step
            startStepSpeed = stepSpeed = moveSpeed / engine.server.SERVER['fps']

            # compute a new angle in radians which moves directly towards destination
            # sprite['direction'] is stored and never removed so client will know the last
            # direction the sprite was facing.
            sprite['direction'] = geo.angle(
                sprite['anchorX'],
                sprite['anchorY'],
                moveDestX,
                moveDestY)

            # while the location is not valid and we are trying to move at least 0.01 pixel.
            inBounds = False
            while not inBounds and stepSpeed > 0:
                # if we can get to the dest this step then just go there.
                if stepSpeed > geo.distance(sprite['anchorX'], sprite['anchorY'],
                                            moveDestX, moveDestY):
                    newAnchorX = moveDestX
                    newAnchorY = moveDestY
                else:
                    # compute a new anchor x,y which moves directly towards destination
                    newAnchorX, newAnchorY = geo.project(
                        sprite['anchorX'],
                        sprite['anchorY'],
                        sprite['direction'],
                        stepSpeed
                        )

                # if we are out of bounds then slow down and try again. Mabye not going as far will be in bounds.
                inBounds = self.checkLocation(sprite, newAnchorX, newAnchorY)
                if not inBounds:
                    stepSpeed -= startStepSpeed * 0.9

            # if we cannot move directly then try sliding (if enabled).
            if not inBounds and slide:
                # reset speed since it was probably reduced above.
                stepSpeed = startStepSpeed

                if moveDestX > sprite['anchorX']:
                    newAnchorX = sprite['anchorX'] + min(stepSpeed, moveDestX - sprite['anchorX'])
                    if newAnchorX > moveDestX:
                        newAnchorX = moveDestX
                elif moveDestX < sprite['anchorX']:
                    newAnchorX = sprite['anchorX'] - min(stepSpeed, sprite['anchorX'] - moveDestX)
                    if newAnchorX < moveDestX:
                        newAnchorX = moveDestX
                else:
                    newAnchorX = moveDestX

                if moveDestY > sprite['anchorY']:
                    newAnchorY = sprite['anchorY'] + min(stepSpeed, moveDestY - sprite['anchorY'])
                    if newAnchorY > moveDestY:
                        newAnchorY = moveDestY
                elif moveDestY < sprite['anchorY']:
                    newAnchorY = sprite['anchorY'] - min(stepSpeed, sprite['anchorY'] - moveDestY)
                    if newAnchorY < moveDestY:
                        newAnchorY = moveDestY
                else:
                    newAnchorY = sprite['anchorY']

                # if sprite is moving along X then try to stay at the same Y and move along only along X
                if newAnchorX != moveDestX and self.checkLocation(sprite, newAnchorX, sprite['anchorY']):
                    newAnchorY = sprite['anchorY']
                    inBounds = True
                # elif sprite is moving along Y then try to stay at the same X and move along only along Y
                elif newAnchorY != sprite['anchorY'] and self.checkLocation(sprite, sprite['anchorX'], newAnchorY):
                    newAnchorX = sprite['anchorX']
                    inBounds = True

            if inBounds:
                """
                if sprite reached the destination or sprite is only going to move less than 0.01 pixel then
                    stop it after this move.
                """
                if (moveDestX == newAnchorX and moveDestY == newAnchorY) or \
                        geo.distance(sprite['anchorX'], sprite['anchorY'], newAnchorX, newAnchorY) < 0.04:
                    self.delMoveLinear(sprite)

                # move sprite to new location
                self.setObjectLocationByAnchor(sprite, newAnchorX, newAnchorY)
            else:
                # sprite cannot move.
                self.delMoveLinear(sprite)

    def setMoveLinear(self, sprite, moveDestX, moveDestY, moveSpeed, slide=True):
        """MOVE LINEAR MECHANIC: Set sprites destination and speed.

        Add attributes to sprite: move
        """
        sprite['move'] = {'type': 'Linear', 'x': moveDestX, 'y': moveDestY, 's': moveSpeed, 'sl': slide}
        self.setMapChanged()

    def delMoveLinear(self, sprite):
        """MOVE LINEAR MECHANIC: Stop Sprite

        Remove attributes from sprite: move
        """
        if 'move' in sprite and sprite['move']['type'] == 'Linear':
            del sprite['move']
            self.setMapChanged()

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

        Note, sprite will only be moved if destination is valid based
        on calling checkLocation().

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
                log(f"MapDoor destMapName does not exist! {trigger['prop-destMapName']}", "FAILURE")
                exit()
        else:
            destMap = self
        dest = destMap.findObject(name=trigger['prop-destReference'], objectList=destMap['reference'])
        if dest:
            # if dest location is a valid location for sprite.
            if destMap.checkLocation(sprite, dest['anchorX'], dest['anchorY']):
                self.setObjectMap(sprite, destMap)
                destMap.setObjectLocationByAnchor(sprite, dest['anchorX'], dest['anchorY'])
                destMap.delMoveLinear(sprite)
                return True  # stop the processing of other triggers since sprite has moved.
            else:
                log(f"Trigger destination failed checkLocation.", "VERBOSE")
        else:
            log(f"Trigger destination not found. {trigger['prop-destReference']}", "ERROR")

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
            self.addHoldableTrigger(holdable)

        self.addStepMethodPriority("trigger", "triggerHoldable", 10)
        self.addStepMethodPriority("stepMapEnd", "stepMapEndHoldable", 89)

    def triggerHoldable(self, holdableTrigger, sprite):
        """HOLDABLE MECHANIC: trigger method.

        The sprite's anchor is inside the trigger.

        if the sprite is not holding anything now then:
            1) pick up holdable if the sprite has requested an action else
            2) tell the sprite the pick up action is possible.
        """
        if "holding" not in sprite:
            if "action" in sprite:
                self.delSpriteAction(sprite)
                self.pickupHoldable(holdableTrigger, sprite)
            else:
                self.setSpriteActionText(sprite, f"Available Action: Pick Up {holdableTrigger['holdableSprite']['name']}")

    def stepMapEndHoldable(self):
        """HOLDABLE MECHANIC: stepMapEnd method.

        Drop holdable if sprite has holding and action is requested by user.
        """
        for sprite in self['sprites']:
            if "holding" in sprite:
                if "action" in sprite:
                    self.delSpriteAction(sprite)  # consume sprite action
                    self.dropHoldable(sprite)
                else:
                    self.setSpriteActionText(sprite, f"Available Action: Drop {sprite['holding']['name']}")

    def pickupHoldable(self, holdableTrigger, sprite):
        """HOLDABLE MECHANIC: sprite picks up holdable.

        Add attributes to sprite: holding
        """
        holdable = holdableTrigger['holdableSprite']
        self.removeFollower(holdable,holdableTrigger)
        self.removeObjectFromAllLayers(holdableTrigger)
        self.removeObjectFromAllLayers(holdable)
        sprite['holding'] = holdable

    def dropHoldable(self, sprite):
        """HOLDABLE MECHANIC: sprite drops holding at sprite's location.

        Remove attributes from sprite: holding
        """
        holdable = sprite['holding']
        del sprite['holding']

        # put the dropped item at the feet of the sprite that was holding it.
        self.setObjectLocationByAnchor(holdable, sprite['anchorX'], sprite['anchorY'])
        self.delMoveLinear(holdable)
        self.addObject(holdable, objectList=self['sprites'])
        self.addHoldableTrigger(holdable)

    def addHoldableTrigger(self, holdable):
        """HOLDABLE MECHANIC: copy holdable sprite and make it a trigger."""
        
        # shallow copy holdable (sprite)
        holdableTrigger = holdable.copy()

        # change collisionType to 'rect' so sprites can collide with the trigger.
        holdableTrigger['collisionType'] = 'rect'

        # set doNotTrigger to be a list with just holdable. If this is not
        # not done then holdable (sprite) will collide with trigger each
        # step and set of the trigger each step. This stops that from
        # happening.
        holdableTrigger['doNotTrigger'] = [holdable]

        # Save a reference in the trigger for the sprite that this trigger
        # will pick up.
        holdableTrigger['holdableSprite'] = holdable

        # add trigger to the triggers layer.
        self.addObject(holdableTrigger, objectList=self['triggers'])

        # set trigger to follow sprite. If the sprites moves then
        # so will the trigger.
        self.addFollower(holdable, holdableTrigger)

    ########################################################
    # ACTION MECHANIC
    ########################################################

    def initAction(self):
        """ACTION MECHANIC: init method.

        Set priority of stepMapEndAction to be very low so all other
        code has a chance to consume an action before it is removed.
        """
        self.addStepMethodPriority("stepMapEnd", "stepMapEndAction", 90)

    def stepMapEndAction(self):
        """ACTION MECHANIC: stepMapEnd method.

        If an action was requested but no step method was able to consume
        the action then simply delete the action (consume action it but do nothing).
        """
        for sprite in self['sprites']:
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

    def stepMapStartSpeechText(self):
        """SPEECH TEXT MECHANIC: Remove speechText from sprite if it has timed out."""
        for sprite in self['sprites']:
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

    def stepMapStartActionText(self):
        """PLAYER ACTION TEXT MECHANIC: delete action text from player linked to sprite.

        Each step the actions available may change so start each
        step by removing all action text. The first game mechanic
        that finds an action that could be performed can set a
        new action text.
        """
        for sprite in self['sprites']:
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
