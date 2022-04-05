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
            2) gameOn: All players have joined and game.
            3) gameOver: Game objective is complete.

        self['quitAfter'] which tells the server when to quit. Set
            when mode == gameOver so players will have time to see the
            game has been won before everything quits.
        """

        super().__init__(args)

        # server will quit after this time.
        self['quitAfter'] = sys.float_info.max

        self['mode'] = "waitingForPlayers"

        # set the collision type of end game object to circle
        end = self['maps']['end']
        endGame = end.findObject(name="endGame", objectList=end['reference'])
        endGame['collisionType'] = 'circle'

        log(f"Server __init__ complete. Server Attributes:{engine.log.dictToStr(self, 1)}", "VERBOSE")

    def msgPlayerMove(self, ip, port, ipport, msg):
        """Extends msgPlaeryMove()

        ignore playerMove msgs until all players have joined game,
        self['mode'] == "gameOn".

        Once all players have joined game, if a player moves then
        remove their marqueeTest.
        """
        if self['mode'] == "waitingForPlayers":
            return

        # clear start marqueeText if player has moved and game is ongoing.
        if self['mode'] == "gameOn" and ipport in self['players']:
            self.delPlayerMarqueeText(self['players'][ipport]['playerNumber'])

        return super().msgPlayerMove(ip, port, ipport, msg)

    def msgPlayerAction(self, ip, port, ipport, msg):
        """Extends msgPlayerAction()

        ignore playerAction msgs until all players have joined game.
        """
        if self['mode'] == "waitingForPlayers":
            return

        return super().msgPlayerAction(ip, port, ipport, msg)

    def addPlayer(self, ip, port, ipport, msg):
        """Extends addPlayer()

        Show game opening marqueeTest until all players have joined the
        game and then set mode to "gameOn" and change the marqueeTest.
        """
        super().addPlayer(ip, port, ipport, msg)

        if self['mode'] == "waitingForPlayers":
            marqueeText = "All players must gather in the stone circle to win."
            if len(self['unassignedPlayerSprites']) == 0:
                self['mode'] = "gameOn"
                marqueeText += " Game On! Click to move."
            else:
                marqueeText += f" Waiting for {len(self['unassignedPlayerSprites'])} more players to join."
            for playerNumber in self['playersByNum']:
                self.setPlayerMarqueeText(playerNumber, marqueeText)

            if self['mode'] == "gameOn":
                self['gameStartSec'] = time.perf_counter()
                log("GAME ON: All players have joined.")

    def stepServerStart(self):
        """Extends stepServerStart()

        If the mode is gameOn then evaluate if all
        players have made it to the stone circle. If they have then
        change mode to gameOver and set the timer to shutdown the
        server.

        If the mode is gameOver then check if the quitAfter is in the
        past. If it is then tell clients the server is quiting and
        then quit the server process.
        """
        super().stepServerStart()

        # check for game won
        # if all players have joined game
        if self['mode'] == "gameOn":
            end = self['maps']['end']
            endGame = end.findObject(name="endGame", objectList=end['reference'])
            playersIn = end.findObject(collidesWith=endGame, type='player', returnAll=True)
            # if all players have made it to the end.
            if len(playersIn) == len(self['players']):
                self['mode'] = "gameOver"
                secsToWin = round(time.perf_counter() - self['gameStartSec'])
                self['quitAfter'] = time.perf_counter() + 30
                log("GAME OVER: Quiting in 30 seconds")
                for playerNumber in self['playersByNum']:
                    self.setPlayerMarqueeText(playerNumber,
                                              f"Game Won! Good teamwork everyone. You took {secsToWin} secs to win.")

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
