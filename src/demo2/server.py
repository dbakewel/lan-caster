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
        self['gameStartSec'] = False
        self['mode'] = "waitingForPlayers"
        self['redPoints'] = 0
        self['bluePoints'] = 0
        self['MAXHEALTH'] = 100.0
        self['HEALTHREGENSEC'] = 60.0 # seconds to regen full health from 0
        self['MAXENDUR'] = 3.0 # seconds
        self['ENDURREGENSEC'] = self['MAXENDUR']*5.0 # seconds to regen full run from 0
        self['RUNSPEED'] = 2.0  # multiplier of running vs. normal speed.

        log(f"Server __init__ complete. Server Attributes:{engine.log.dictToStr(self, 1)}", "VERBOSE")

    def msgPlayerMove(self, ip, port, ipport, msg):
        """Extends msgPlayerMove()

        ignore playerMove msgs until all players have joined game,
        self['mode'] == "gameOn".

        Once all players have joined game, if a player moves then
        remove their marqueeTest.
        """
        if self['mode'] != "gameOn":
            return

        # clear start marqueeText if player has moved and game is ongoing.
        if ipport in self['players']:
            self.delPlayerMarqueeText(self['players'][ipport]['playerNumber'])
        
        return super().msgPlayerMove(ip, port, ipport, msg)

    def msgPlayerAction(self, ip, port, ipport, msg):
        """Extends msgPlayerAction()

        ignore playerAction msgs until all players have joined game.
        """
        if self['mode'] != "gameOn":
            return

        return super().msgPlayerAction(ip, port, ipport, msg)

    def msgReadyRequest(self, ip, port, ipport, msg):
        """msgReadyRequest()"""

        if ipport in self['players'] and self['mode'] == "waitingForPlayers":
            self['players'][ipport]['ready'] = True
            self.updateWaiting()
        return {'type': 'readyReply'}

    def msgRun(self, ip, port, ipport, msg):
        if ipport in self['players'] and self['mode'] == "gameOn":
            sprite = self['players'][ipport]['sprite']
            if 'move' in sprite and self['players'][ipport]['endur'] > 0:
                sprite['move']['s'] *= self['RUNSPEED']
                sprite['move']['run'] = True

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

        msg = super().getStepMsg(player)
        msg.update({
            'health': player['health'],
            'endur': player['endur'],
            'redPoints': self['redPoints'],
            'bluePoints': self['bluePoints']
            })

        return msg

    def stepServerStart(self):
        """Extends stepServerStart()"""

        super().stepServerStart()

        # if game is in progress
        if self['mode'] == "gameOn":
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

        if playerNumber in self['playersByNum']:
            player = self['playersByNum'][playerNumber]
            sprite = player['sprite']

            # STILL NEED TO DROP ALL ITEMS BEFORE MOVING!!!

            destMap = self['maps'][player['startMapName']]
            if sprite['mapName'] != player['startMapName']:
                map = self['maps'][sprite['mapName']]
                map.setObjectMap(sprite, destMap)
            destMap.setObjectLocationByAnchor(sprite, player['startAnchorX'], player['startAnchorY'])
            destMap.delMoveLinear(sprite)

            player['health'] = self['MAXHEALTH']
            player['endur'] = self['MAXENDUR']

    def getPlayerChanged(self, player):
        """Extends engine.getPlayerChanged() - Detect if player changed based on player['changed']"""

        if player['changed']:
            player['changed'] = False
            return True
        return super().getPlayerChanged(player)