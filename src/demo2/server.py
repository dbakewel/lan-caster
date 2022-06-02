"""Server for demo2 Game"""

import sys
import random

import engine.time as time
from engine.log import log
import engine.server
import engine.geometry as geo


class Server(engine.server.Server):
    """Extends engine.server.Server"""

    def __init__(self, args):
        """Extends __init__()

        Adds Attributes: (incomplete list but these are the important ones)

        self['mode'] which contains one of three values:
            1) waitingForPlayers: Game has not started.
                - Waiting for all players to Join AND
                - Waiting for all players to send "ready" msg.
            2) gameOn: All players have joined and game.
            3) gameOver: Game objective is complete.

        self['quitAfter'] which tells the server when to quit. Set
            when mode == gameOver so players will have time to see the
            game has been won before everything quits.
        """

        super().__init__(args)
        """Set up game data, default values, and set objects on maps"""

        # server will quit after this time.
        self['quitAfter'] = sys.float_info.max
        self['gameStartSec'] = 0
        self['mode'] = "waitingForPlayers"
        self['redPoints'] = 0
        self['bluePoints'] = 0

        self['GAMETIME'] = 60.0 * 10  # game leangth in seconds
        self['MAXHEALTH'] = 100.0
        self['HEALTHREGENSEC'] = 60.0  # seconds to regen full health from 0
        self['MAXENDUR'] = 3.0  # seconds
        self['ENDURREGENSEC'] = self['MAXENDUR'] * 5.0  # seconds to regen full run from 0
        self['RUNSPEED'] = 2.0  # multiplier of running vs. normal speed.

        self.setCollsion()
        self.randomizeWeapons()
        self.createDoors()
        self.createKeys()

        log(f"Server __init__ complete. Server Attributes:{engine.log.dictToStr(self, 1)}", "VERBOSE")

    def setCollsion(self):
        """Change collision type of monsters and players to be circle.
        also, players only collide with outOfBounds layer while moving"""
        for mapName in self['maps']:
            map = self['maps'][mapName]
            for o in map['sprites']:
                if o['type'] == 'player':
                    o['collisionType'] = 'circle'
                    o['checkLocationOn'] = ['outOfBounds']
                elif o['type'] == 'monster':
                    o['collisionType'] = 'circle'

    def randomizeWeapons(self):
        """Move weapons from the hidden map to random weaponlocaion points. Then set them up as holdables"""
        # find all weapons
        weapons = []
        map = self['maps']['hidden']
        for holdable in map['reference']:
            if holdable['type'] == 'holdable' and holdable['prop-holdable-type'] == 'weapon':
                weapons.append(holdable)

        # remove weapons from current locations. (Don't really need to this since
        # the hidden map is used but doing it to be very clean)
        for weapon in weapons:
            map.removeObjectFromAllLayers(weapon)

        # find all weapon location and shuffle the list
        weaponLocations = []
        for mapName in self['maps']:
            map = self['maps'][mapName]
            for o in map['reference']:
                if o['name'] == 'weaponLocation':
                    weaponLocations.append(o)
        random.shuffle(weaponLocations)

        # put weapons in new locations and set up as holdables.
        for weapon in weapons:
            location = weaponLocations.pop()
            map = self['maps'][location['mapName']]
            map.addObject(weapon)
            map.setObjectLocationByAnchor(weapon, location['anchorX'], location['anchorY'])
            map.addHoldableTrigger(weapon)

    def createDoors(self):
        """ Create doors. Doors are created from rects on the triggers layer of type == 'lockedDoor' """

        lockNumbers = random.sample(range(10, 99), 20)

        doorTiles = []
        map = self['maps']['hidden']
        for doorTile in map['reference']:
            if doorTile['name'] == 'doorTile':
                doorTiles.append(doorTile)

        self['lockedDoors'] = []
        # find all doors
        for mapName in self['maps']:
            map = self['maps'][mapName]
            for doorTrigger in map['triggers']:
                if doorTrigger['type'] == 'lockedDoor':
                    self['lockedDoors'].append(doorTrigger)
                    doorTrigger['lockNumber'] = lockNumbers.pop()

                    doorCopy = doorTrigger.copy()
                    doorCopy['fillColor'] = "#008800"
                    # Add to outOfBounds so it blocks players
                    map.addObject(doorCopy, map['outOfBounds'])
                    # Add to spries adn color it so players can see it
                    map.addObject(doorCopy)

                    # grow trigger so players can step on it even with doorCopy on outOfBounds layer.
                    doorTrigger['x'] -= 10
                    doorTrigger['y'] -= 10
                    doorTrigger['width'] += 20
                    doorTrigger['height'] += 20

                    # add doorTile icon graphic
                    doorTile = doorTiles[random.randrange(0, len(doorTiles))]
                    door = doorTile.copy()
                    map.addObject(door)
                    # add 0.1 so tile render on top of door rect on sprite layer.
                    map.setObjectLocationByAnchor(door, doorCopy['anchorX'] + 0.1, doorCopy['anchorY'] + 0.1)
                    doorTrigger['doNotTrigger'] = [doorCopy, door]

    def createKeys(self):
        """Create a key for each door and put them in keylocaions."""

        # find of keyTiles
        keyTiles = []
        map = self['maps']['hidden']
        for keyTile in map['reference']:
            if keyTile['name'] == 'keyTile':
                keyTiles.append(keyTile)

        # find all key locations and shuffle the list
        keyLocations = []
        for mapName in self['maps']:
            map = self['maps'][mapName]
            for o in map['reference']:
                if o['name'] == 'keyLocation':
                    keyLocations.append(o)
        random.shuffle(keyLocations)

        # create a key for each lockedDoor
        for door in self['lockedDoors']:
            keyLocation = keyLocations.pop()
            map = self['maps'][keyLocation['mapName']]
            keyTile = keyTiles[random.randrange(0, len(keyTiles))]
            key = keyTile.copy()
            key['lockNumber'] = door['lockNumber']
            key['name'] = f"Key {door['lockNumber']}"
            map.addObject(key)
            map.setObjectLocationByAnchor(key, keyLocation['anchorX'], keyLocation['anchorY'])
            map.addHoldableTrigger(key)

    ########################################################
    # Networking - GAME MESSAGES
    ########################################################

    def msgReadyRequest(self, ip, port, ipport, msg):
        """msgReadyRequest()

        Record player is ready and call updateWaiting() which will start game if all players are ready.
        """
        if self['mode'] != "waitingForPlayers":
            return

        if ipport in self['players']:
            self['players'][ipport]['ready'] = True
            self.updateWaiting()
        return {'type': 'readyReply'}

    def msgPlayerMove(self, ip, port, ipport, msg):
        """Extends msgPlayerMove()

        ignore playerMove msgs until all players have joined game,
        self['mode'] == "gameOn".

        Once all players have joined game, if a player moves then
        remove their marqueeTest.
        """
        if self['mode'] == "waitingForPlayers":
            return
        elif self['mode'] == 'gameOn' and ipport in self['players']:
            # clear start marqueeText if player has moved and game is ongoing.
            self.delPlayerMarqueeText(self['players'][ipport]['playerNumber'])

        return super().msgPlayerMove(ip, port, ipport, msg)

    def msgPlayerAction(self, ip, port, ipport, msg):
        """Extends msgPlayerAction()

        ignore playerAction msgs until all players have joined game.
        """
        if self['mode'] == "waitingForPlayers":
            return

        return super().msgPlayerAction(ip, port, ipport, msg)

    def msgRun(self, ip, port, ipport, msg):
        """Increase players speed. Player must already be moving and have an endur value > 0"""

        if self['mode'] == "waitingForPlayers":
            return

        if ipport in self['players']:
            sprite = self['players'][ipport]['sprite']
            if 'move' in sprite and self['players'][ipport]['endur'] > 0:
                sprite['move']['s'] *= self['RUNSPEED']
                sprite['move']['run'] = True

    def msgFire(self, ip, port, ipport, msg):
        """Fire players weapon, player must have a weapon and not have fired it for 1 second"""

        if self['mode'] == "waitingForPlayers":
            return

        if ipport in self['players']:
            player = self['players'][ipport]
            sprite = player['sprite']
            map = self['maps'][sprite['mapName']]

            # player must have weapon and can only fire once per second
            if 'weapon' not in sprite or player['lastFired'] > time.perf_counter() - 1:
                return

            # ensure player is not firing at themselves
            if geo.distance(sprite['anchorX'], sprite['anchorY'], msg['fireDestX'], msg['fireDestY']) < sprite['width']:
                return

            angle = geo.angle(sprite['anchorX'], sprite['anchorY'], msg['fireDestX'], msg['fireDestY'])

            if sprite['prop-team'] == 'blue':
                color = "#4444ff"
            else:
                color = "#ff4444"

            if sprite['weapon']['name'] == "Bow":
                map.createArrow(sprite['anchorX'], sprite['anchorY'], angle, sprite['width'], color)
            elif sprite['weapon']['name'].startswith("Throwing "):
                map.createStars(sprite['anchorX'], sprite['anchorY'], angle, sprite['width'], color)
            elif sprite['weapon']['name'] == "Magic Wand":
                map.createRay(sprite['anchorX'], sprite['anchorY'], angle, sprite['width'], color)
            else:
                log(f"Unrecognized weapon type: {sprite['weapon']['name']}", ERROR)

            player['lastFired'] = time.perf_counter()

    ########################################################
    # Networking - STEP MESSAGES
    ########################################################

    def getStepMsg(self, player):
        """Extends engine.getStepMsg()

        Adds game specific data based on game mode (self['mode']).
        """

        msg = super().getStepMsg(player)

        # Add game specific data to step message
        if self['mode'] == "gameOn":
            timeRemaining = self['GAMETIME'] - (time.perf_counter() - self['gameStartSec'])
        elif self['mode'] == 'gameOver':
            timeRemaining = 0.0
        else:
            timeRemaining = self['GAMETIME']
        msg.update({
            'health': player['health'],
            'endur': player['endur'],
            'redPoints': self['redPoints'],
            'bluePoints': self['bluePoints'],
            'timeRemaining': timeRemaining
            })

        if self['mode'] == "waitingForPlayers":
            if 'actionText' in msg:
                del msg['actionText']
        else:
            # add to or create action text
            addonActionText = ""
            if 'weapon' in player['sprite']:
                addonActionText = addonActionText + "    Fire (f)"
            if player['endur'] > 0:
                addonActionText = addonActionText + "    Run (r)"
            if addonActionText != "":
                if 'actionText' in msg:
                    msg['actionText'] = msg['actionText'] + addonActionText
                else:
                    msg['actionText'] = addonActionText.lstrip()

        return msg

    ########################################################
    # GAME LOGIC
    ########################################################

    def stepServer(self):
        """OVERRIDE stepServer()

        Take the game one "step" forward in time. Unlike engine.server.Server.stepServer()
        this function steps every map on every step, not just maps with players. This allows
        monsters to chase players through map doors.
        """
        self.stepServerStart()

        for mapName in self['maps']:
            self['maps'][mapName].stepMap()

        self.stepServerEnd()

    def updateWaiting(self):
        """Detect if all players are ready and switch mode to gameOn. Update players as each player becomes ready."""

        # count how many players are ready.
        totalPlayers = len(self['unassignedPlayerSprites']) + len(self['players'])
        ready = 0
        for ipport in self['players']:
            if self['players'][ipport]['ready'] == True:
                ready += 1

        # if all players are ready.
        if ready == totalPlayers:
            self['mode'] = "gameOn"
            self['gameStartSec'] = time.perf_counter()
            marqueeText = "GAME ON!!!\n\nClick to move."
            log("GAME ON: All players have joined.")
        elif len(self['unassignedPlayerSprites']) == 0:
            # all players have  joined but not all ready.
            marqueeText = f"Waiting for {totalPlayers-ready} players to be ready."
        else:
            # waiting for players to both join and be ready.
            marqueeText = f"Waiting for {len(self['unassignedPlayerSprites'])} to players to join and {totalPlayers-ready} players to be ready."

        for playerNumber in self['playersByNum']:
            self.setPlayerMarqueeText(playerNumber, marqueeText)

    def stepServerStart(self):
        """Extends stepServerStart()"""

        super().stepServerStart()

        # check stats of players
        for playerNumber in self['playersByNum']:
            player = self['playersByNum'][playerNumber]

            if player['health'] <= 0:
                # Player died. respawn the player
                self.respawnPlayer(playerNumber)
            elif player['health'] < self['MAXHEALTH']:
                # regenerate health
                player['health'] += self['MAXHEALTH'] / (self['HEALTHREGENSEC'] * self['fps'])
                player['changed'] = True
                if player['health'] > self['MAXHEALTH']:
                    player['health'] = self['MAXHEALTH']

            if 'move' in player['sprite'] and 'run' in player['sprite']['move']:
                # if player is running then reduce endurance.
                player['endur'] -= 1.0 / self['fps']
                player['changed'] = True
                # if player ran endurance to 0 then stop running and set endurance to negative number.
                if player['endur'] <= 0:
                    del player['sprite']['move']['run']
                    player['sprite']['move']['s'] /= self['RUNSPEED']
                    player['endur'] = -self['MAXENDUR']
            else:
                # regenerate endurance
                if player['endur'] < self['MAXENDUR']:
                    player['endur'] += self['MAXENDUR'] / (self['ENDURREGENSEC'] * self['fps'])
                    player['changed'] = True
                    if player['endur'] > self['MAXENDUR']:
                        player['endur'] = self['MAXENDUR']

        # check if the game has ended
        if self['mode'] == "gameOn":
            timeRemaining = self['GAMETIME'] - (time.perf_counter() - self['gameStartSec'])
            if timeRemaining < 0:
                self['mode'] = 'gameOver'
                self['quitAfter'] = time.perf_counter() + 30
                log("GAME OVER: Quiting in 30 seconds")

                if self['redPoints'] > self['bluePoints']:
                    winnerText = "RED WINS!"
                elif self['redPoints'] == self['bluePoints']:
                    winnerText = "IT'S A TIE!"
                else:
                    winnerText = "BLUE WINS!"
                for playerNumber in self['playersByNum']:
                    self.setPlayerMarqueeText(playerNumber,
                                              f"Game Over\n\nBlue={self['bluePoints']}  Red={self['redPoints']}\n\n{winnerText}")

        # check if it is time for server to quit
        if self['quitAfter'] < time.perf_counter():
            log("Sending quitting msg to all clients.")
            for ipport in self['players']:
                self['socket'].sendMessage(
                    msg={'type': 'quitting'},
                    destinationIP=self['players'][ipport]['ip'],
                    destinationPort=self['players'][ipport]['port']
                    )
            engine.server.quit()

    ########################################################
    # PLAYER
    ########################################################

    def addPlayer(self, ip, port, ipport, msg):
        """Extends addPlayer() and adds game specific data"""

        super().addPlayer(ip, port, ipport, msg)

        sprite = self['players'][ipport]['sprite']
        self['players'][ipport].update({
            'ready': False,
            # Next 3 lines are to remember where player started
            'startMapName': sprite['mapName'],
            'startAnchorX': sprite['anchorX'],
            'startAnchorY': sprite['anchorY'],
            'lastFired': 0  # time (in sec) that player last fired weapon.
            })
        self.restoreStats(sprite['playerNumber'])
        self.updateWaiting()

    def respawnPlayer(self, playerNumber):
        """Move player, and all held items, back to where they started and restore player health, endur, etc..."""

        player = self['playersByNum'][playerNumber]
        sprite = player['sprite']

        # give point to other team
        if sprite['prop-team'] == 'red':
            self['bluePoints'] += 1
        else:
            self['redPoints'] += 1

        # put held items back to where they were picked up.
        for item in ('weapon', 'key', 'idol'):
            if item in sprite:
                drop = sprite[item]
                destmap = self['maps'][drop['mapName']]
                destmap.dropHoldable(sprite, item)

        # put player back to where they started.
        destMap = self['maps'][player['startMapName']]
        if sprite['mapName'] != player['startMapName']:
            map = self['maps'][sprite['mapName']]
            map.setObjectMap(sprite, destMap)
        destMap.setObjectLocationByAnchor(sprite, player['startAnchorX'], player['startAnchorY'])
        destMap.delMoveLinear(sprite)

        self.restoreStats(playerNumber)
        destMap.setSpriteSpeechText(sprite, "I died but I have been reborn!", time.perf_counter() + 4)

    def restoreStats(self, playerNumber):
        """ Set player health and endurance to max"""
        player = self['playersByNum'][playerNumber]
        player['health'] = self['MAXHEALTH']
        player['endur'] = self['MAXENDUR']
        player['changed'] = True  # player changed and step message must be sent.

    def resetPlayerChanged(self, player):
        """Extends resetPlayerChanged()"""

        player['changed'] = False
        super().resetPlayerChanged(player)

    def getPlayerChanged(self, player):
        """Extends getPlayerChanged()

        Detect if player changed based on player['changed']

        Also says player has change if player has not been send a step message
        in 1 second. This makes sure player can see time changing every second.
        """

        if player['changed']:
            return True

        if player['lastStepMsgSent'] + 1 < time.perf_counter():
            # send a least one update per sec so player can see time increasing.
            return True

        return super().getPlayerChanged(player)
