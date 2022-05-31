"""Server for Demo Game"""

import sys
import engine.time as time
from engine.log import log
import engine.server
import engine.geometry as geo


class Server(engine.server.Server):
    """Extends engine.server.Server"""

    def __init__(self, args):
        """Extends __init__()

        Adds Attributes:

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

        # server will quit after this time.
        self['quitAfter'] = sys.float_info.max
        self['gameStartSec'] = 0
        self['mode'] = "waitingForPlayers"
        self['redPoints'] = 0
        self['bluePoints'] = 0

        self['GAMETIME'] = 60.0*10  # game leangth in seconds
        self['MAXHEALTH'] = 100.0
        self['HEALTHREGENSEC'] = 60.0 # seconds to regen full health from 0
        self['MAXENDUR'] = 3.0 # seconds
        self['ENDURREGENSEC'] = self['MAXENDUR']*5.0 # seconds to regen full run from 0
        self['RUNSPEED'] = 2.0  # multiplier of running vs. normal speed.

        log(f"Server __init__ complete. Server Attributes:{engine.log.dictToStr(self, 1)}", "VERBOSE")

    def msgReadyRequest(self, ip, port, ipport, msg):
        """msgReadyRequest()"""
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
        if self['mode'] == "waitingForPlayers":
            return

        if ipport in self['players']:
            sprite = self['players'][ipport]['sprite']
            if 'move' in sprite and self['players'][ipport]['endur'] > 0:
                sprite['move']['s'] *= self['RUNSPEED']
                sprite['move']['run'] = True

    def msgFire(self, ip, port, ipport, msg):
        if self['mode'] == "waitingForPlayers":
            return

        if ipport in self['players']:
            log("fire!")

    def addPlayer(self, ip, port, ipport, msg):
        """Extends addPlayer()"""

        super().addPlayer(ip, port, ipport, msg)
        sprite = self['players'][ipport]['sprite']
        self['players'][ipport].update({
            'ready': False,
            'lastReady': False,
            'health': self['MAXHEALTH'],
            'endur': self['MAXENDUR'],
            'startMapName': sprite['mapName'],
            'startAnchorX': sprite['anchorX'],
            'startAnchorY': sprite['anchorY'],
            'changed': True  # player changed and step message must be sent.
            })

        self.updateWaiting()

    def updateWaiting(self):
        totalPlayers = len(self['unassignedPlayerSprites']) + len(self['players'])
        ready = 0
        for ipport in self['players']:
            if self['players'][ipport]['ready'] == True:
                ready += 1

        if ready == totalPlayers:
            self['mode'] = "gameOn"
            self['gameStartSec'] = time.perf_counter()
            marqueeText = "GAME ON!!!\n\nClick to move."
            log("GAME ON: All players have joined.")
        elif len(self['unassignedPlayerSprites']) == 0:
            marqueeText = f"Waiting for {totalPlayers-ready} players to be ready."
        else:
            marqueeText = f"Waiting for {len(self['unassignedPlayerSprites'])} to players to join and {totalPlayers-ready} players to be ready."

        for playerNumber in self['playersByNum']:
            self.setPlayerMarqueeText(playerNumber, marqueeText)

    def getStepMsg(self, player):
        """Extends engine.getStepMsg()"""

        if self['mode'] == "gameOn":
            timeRemaining = self['GAMETIME'] - (time.perf_counter() - self['gameStartSec'])
        elif self['mode'] == 'gameOver':
            timeRemaining = 0.0
        else:
            timeRemaining = self['GAMETIME']

        msg = super().getStepMsg(player)
        msg.update({
            'health': player['health'],
            'endur': player['endur'],
            'redPoints': self['redPoints'],
            'bluePoints': self['bluePoints'],
            'timeRemaining': timeRemaining
            })

        return msg

    def stepServerStart(self):
        """Extends stepServerStart()"""

        super().stepServerStart()

        for playerNumber in self['playersByNum']:
            player = self['playersByNum'][playerNumber]

            if player['health'] <= 0:
                # if a players health is below 0 then respawn the player
                self.respawnPlayer(playerNumber)
            elif player['health'] < self['MAXHEALTH']:
                # regenerate health
                player['health'] += self['MAXHEALTH'] / (self['HEALTHREGENSEC'] * self['fps'])
                player['changed'] = True
                if player['health'] > self['MAXHEALTH']:
                    player['health'] = self['MAXHEALTH']

            if 'move' in player['sprite'] and 'run' in player['sprite']['move']:
                # if player is running then reduce endurance. if endurance == 0 then stop running
                player['endur'] -= 1.0/self['fps']
                player['changed'] = True
                if player['endur'] <= 0:
                    del player['sprite']['move']['run']
                    player['sprite']['move']['s'] /= self['RUNSPEED']
                    player['endur'] = -self['MAXENDUR']
            else:
                #regenerate endurance
                if player['endur'] < self['MAXENDUR']:
                    player['endur'] += self['MAXENDUR'] / (self['ENDURREGENSEC'] * self['fps'])
                    player['changed'] = True
                    if player['endur'] > self['MAXENDUR']:
                        player['endur'] = self['MAXENDUR']

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

    def respawnPlayer(self, playerNumber):
        """Move player back to where they started and reset health, endur, etc..."""

        player = self['playersByNum'][playerNumber]
        sprite = player['sprite']

        # give point to other team
        if sprite['prop-team'] == 'red':
            self['bluePoints'] += 1
        else:
            self['redPoints'] += 1

        # put held items back to where they were picked up.
        for item in ('weapon','key','idol'):
            if item in sprite:
                drop = sprite[item]
                destmap = self['maps'][drop['mapName']]
                destmap.dropHoldable(drop, item)

        # put player back to where they started.
        destMap = self['maps'][player['startMapName']]
        if sprite['mapName'] != player['startMapName']:
            map = self['maps'][sprite['mapName']]
            map.setObjectMap(sprite, destMap)
        destMap.setObjectLocationByAnchor(sprite, player['startAnchorX'], player['startAnchorY'])
        destMap.delMoveLinear(sprite)

        self.restoreStats(playerNumber)
        destMap.setSpriteSpeechText(sprite, "I died but I have been reborn!", time.perf_counter() + 8)

    def restoreStats(self, playerNumber):
        player = self['playersByNum'][playerNumber]
        player['health'] = self['MAXHEALTH']
        player['endur'] = self['MAXENDUR']

    def resetPlayerChanged(self, player):
        """Extends resetPlayerChanged()"""
        player['changed'] = False
        super().resetPlayerChanged(player)

    def getPlayerChanged(self, player):
        """Extends engine.getPlayerChanged() - Detect if player changed based on player['changed']"""

        if player['changed']:
            return True

        if player['lastStepMsgSent']+1 < time.perf_counter():
            # send a least one update per sec so player can see time increasing.
            return True

        return super().getPlayerChanged(player)