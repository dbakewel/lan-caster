"""Game Server."""

import signal
import engine.time as time
import random
import os

from engine.log import log
import engine.log
import engine.network
import engine.loaders


def quit(signal=None, frame=None):
    """Quit the server process.

    Designed to be used with the signal module to catch and shutdown when user hits Ctrl-C
    but can also be called by other code to shutdown gracefully.

    Args:
        signal (int): Signal number.
        frame : stack frame

    Returns:
        Does not return. Exits python.
    """

    # If the socket has been created then print network stats.
    global SERVER

    try:
        log(SERVER['socket'].getStats(), "VERBOSE")
    except BaseException:
        pass

    #try:
    str="\n\n          ==== Average Map Step Time ====\n"
    for mapName in SERVER['maps']:
        str += f"\n    {mapName:>20} {round(SERVER['maps'][mapName].getStatsAvgMs(),2)} ms"
    log(str + "\n", "VERBOSE")
    #except BaseException:
    # #   pass

    global profiler
    if profiler:
        profiler.stop()
        profiler.print()

    log("Quiting", "INFO")
    exit()


class Server(dict):
    """The Server Class.

    The Server class is responsible for:
        1) Opening the game network interface and allowing players to
           join the game;
        2) Initiating game logic: step maps forward, global game logic
           such as detect end game;
        3) Send updated map data to players for the map they are on;
        4) Receiving messages from players and storing the data for
           processing by the step logic.
        5) Receive and process test and connector messages if those
           features are turned on.

    Server attributes are stored in dictionary form (self['attribute_name'] rather
    than self.attribute_name). All attributes can be seen by turning on -verbose
    and looking in the output of the server.

    The Server class is designed to be a singleton (only one instance) and stores
    a reference to itself in the module global variable engine.server.SERVER. Any game
    code that is part of the server can access the Server instance using:
        import engine.server
        engine.server.SERVER...

    The Server class is intended to be sub-classed and extended by the game.

    To sub-class, add a server.py file under the game folder:
        src/<your_game_name>/server.py

    In the sub-classed server.py inherit from engine.server as follows:
        import engine.server
        class Server(engine.server.Server):

    See src/demo/server.py for an example.
    """

    def __init__(self, args):
        """Init the Server class.

        Set up the Server data, open server network ip:port, register with
        connector (if required), load Tiled data (maps and tilesets),
        and find player start locations.

        Args:
            args: output from argparse. see startserver.py
        """
        global SERVER
        SERVER = self

        # enable SIGINT so quit() will be called on Cntl-C
        signal.signal(signal.SIGINT, quit)

        random.seed()

        # enable profiler if -profile was given on command line.
        global profiler
        profiler = False
        if args.profile:
            try:
                from pyinstrument import Profiler
            except BaseException:
                log("Python package missing for -profile option. Install with something similar to:\n py -3 -m pip install pyinstrument", "FAILURE")
                exit()
            profiler = Profiler()
            profiler.start()

        self['game'] = args.game
        self['registerName'] = args.registerName
        self['connectorHostName'] = args.connectorHostName
        self['connectorPort'] = args.connectorPort
        self['serverIP'] = args.serverIP
        self['serverPort'] = args.serverPort
        self['fps'] = args.fps
        self['testMode'] = args.testMode
        self['busySec'] = args.busySec

        self['playerMoveCheck'] = True
        self['CONNECTOR_KEEP_ALIVE'] = 10  # send a keepalive to connector every 10 secs until all players have joined.

        if(self['testMode']):
            log("Server running in TEST MODE.")

        self['players'] = {}  # dict of players indexed by their ipport (eg. '192.168.3.4:20013')
        self['playersByNum'] = {}  # same as above but indexed by playerNumber
        self['gameStartSec'] = 0  # time.perf_counter() that the game started (send in step msgs)

        # set up networking
        log(f"Server Default IP: {engine.network.getDefaultIP()}")

        if self['registerName']:
            self['serverIP'] = '0.0.0.0'  # ignore serverIP arg if we are going to register with connector.

        try:
            self['socket'] = engine.network.Socket(
                messages=engine.loaders.loadModule("messages", game=self['game']).Messages(),
                msgProcessor=self,
                sourceIP=self['serverIP'],
                sourcePort=self['serverPort']
                )
        except Exception as e:
            log(str(e), "FAILURE")
            quit()

        if self['registerName']:
            try:
                log(f"Adding server to connector as '{self['registerName']}'.")
                reply = self['socket'].sendRecvMessage(
                    self.getAddServerMsg(),
                    destinationIP=self['connectorHostName'],
                    destinationPort=self['connectorPort'],
                    retries=10, delay=5, delayMultiplier=1)
                if reply['type'] == "serverAdded":
                    log(f"Server added to connector as {self['registerName']}.")
                    self.sendAddServerAfter = time.perf_counter() + self['CONNECTOR_KEEP_ALIVE']
                else:
                    log(msg['result'], "FAILURE")
                    quit()
            except Exception as e:
                log(str(e), "FAILURE")
                log("Is connector running?")
                quit()

        self['tilesets'] = engine.loaders.loadTilesets(
            game=self['game'],
            loadImages=False  # Server does not need to render images so save memory and don't load them.
            )

        self['maps'] = engine.loaders.loadMaps(
            tilesets=self['tilesets'],
            game=self['game'],
            maptype="ServerMap"
            )

        log("Loading tilesets and maps was successful.")

        # find player starting locations. Number of locations determines how many players can play game.
        self['unassignedPlayerSprites'] = []  # List of player sprites that have not been assigned to any client yet.
        for m in self['maps']:
            for player in self['maps'][m]['sprites']:
                if player['type'] == "player":
                    self['unassignedPlayerSprites'].append((player, self['maps'][m]['name']))
        # ensure players are assigned random player sprites even if they join in the same order.
        random.shuffle(self['unassignedPlayerSprites'])

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # MAIN LOOP
    ########################################################

    def run(self):
        """Main server loop.

        This loop is controlled to run once every 1/fps seconds.
        Every loop it received msgs from players, takes one step forward in time,
        sends updated step messages to players, and keeps the connector data
        current (if required). It also prints server busy messages on a regular
        interval.
        """

        startAt = time.perf_counter()
        nextStatusAt = startAt + self['busySec']
        sleepTime = 0
        nextStepAt = startAt + (1.0 / self['fps'])
        while True:
            # process messages from server (recvReplyMsgs calls msg<msgType> for each msg received)
            self['socket'].recvReplyMsgs()

            # Run the game logic to move everything forward one step
            self.stepServer()

            # Send updates to players for maps that have changed during the step
            self.sendStepMsgs()

            # send keep alive messages to connector
            self.sendConnectorKeepAlive()

            # wait until next step should start.
            ptime = time.perf_counter()
            if ptime < nextStepAt:
                sleepTime += nextStepAt - ptime

                if ptime > nextStatusAt:
                    # log the amount of time we are busy vs. waiting for the next step.
                    log(f"Status: busy == {int(100-(sleepTime/(ptime-startAt)*100))}%")
                    startAt = ptime
                    nextStatusAt = startAt + self['busySec']
                    sleepTime = 0
                time.sleep(until=nextStepAt)
            else:
                log("Server running slower than " + str(self['fps']) + " fps.", "VERBOSE")

            nextStepAt = time.perf_counter() + (1.0 / self['fps'])

    ########################################################
    # Networking - GAME MESSAGES
    ########################################################

    def msgJoinRequest(self, ip, port, ipport, msg):
        """Process msg of type joinRequest.

        If the game is not full then add the
        add the new player to the game.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        Returns:
            dict: A joinReply msg if the player was added to the game else an Error msg.
                Regardless, this msg will be sent back to the client.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """

        # if player has already joined then just send them back OK.
        if ipport in self['players']:
            result = "OK"
            log("Player at " + ipport + " sent joinRequest again.")
        elif msg['game'] != self['game']:
            result = f"Client and Server are not running the same game: client->{msg['game']}, server->{self['game']}"
            log("Player at " + ipport + " tried to join wrong game.")
        else:
            if len(self['unassignedPlayerSprites']) == 0:
                result = "Game is full. No more players can join."
                log("Player from " + ipport + " tried to join full game.")
            else:
                # add the client to the game.
                self.addPlayer(ip, port, ipport, msg)
                result = "OK"

        if result == "OK":
            # if using connector and all players have joined we can delServer from connector
            if self['registerName'] and len(self['unassignedPlayerSprites']) == 0:
                self['socket'].sendMessage(
                    {
                        'type': 'delServer',
                        'serverName': self['registerName']
                        },
                    destinationIP=self['connectorHostName'],
                    destinationPort=self['connectorPort']
                    )

            # send the new client back their player number
            return {
                'type': "joinReply",
                'playerNumber': self['players'][ipport]['sprite']['playerNumber'],
                'serverSec': time.perf_counter(),
                'testMode': self['testMode']
                }
        else:
            return {'type': 'Error', 'result': result}

    def msgPlayerMove(self, ip, port, ipport, msg):
        """Process msg of type playerMove.

        Sets the destination and speed in the player sprite.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            sprite = self['players'][ipport]['sprite']
            map = self['maps'][sprite['mapName']]
            map.setMoveLinear(sprite, msg['moveDestX'], msg['moveDestY'], self['players'][ipport]['moveSpeed'])

    def msgPlayerAction(self, ip, port, ipport, msg):
        """Process msg of type playerAction.

        Sets the sprite action so the sprite's
        action will be processed (or discarded if not action is available) during
        the next step.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            sprite = self['players'][ipport]['sprite']
            map = self['maps'][sprite['mapName']]
            map.setSpriteAction(sprite)

    ########################################################
    # Networking - TEST MESSAGES
    ########################################################

    def msgTestPlayerJump(self, ip, port, ipport, msg):
        """Process msg of type playerJump.

        If the server is in test mode then
        change the player location to the DestX, DestY in the msg.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            if self['testMode']:
                sprite = self['players'][ipport]['sprite']
                map = self['maps'][sprite['mapName']]
                map.setObjectLocationByAnchor(sprite, msg['moveDestX'], msg['moveDestY'])
                map.delMoveLinear(sprite)
                log(f"TEST: Player Jumped: {self['players'][ipport]['sprite']['labelText']} {ipport}")

    def msgTestTogglePlayerMoveChecking(self, ip, port, ipport, msg):
        """Process msg of type playerMoveChecking.

        If in test mode, toggles the boolean
        state of self['playerMoveCheck']. When False, players will be able move in
        areas that are normally out of bounds

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            if self['testMode']:
                self['playerMoveCheck'] = not self['playerMoveCheck']
                if self['playerMoveCheck']:
                    log(f"TEST: playerMoveCheck turned ON by {self['players'][ipport]['sprite']['labelText']} {ipport}")
                else:
                    log(f"TEST: playerMoveCheck turned OFF by {self['players'][ipport]['sprite']['labelText']} {ipport}")

    def msgTestPlayerPreviousMap(self, ip, port, ipport, msg):
        """Process msg of type playerNextMap.

        If in test mode, moves the player
        to previous map (based on map names sorted alphabetically).

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            if self['testMode']:
                sprite = self['players'][ipport]['sprite']
                mapNames = []
                for mapName in self['maps'].keys():
                    mapNames.append(mapName)
                mapNames.sort
                destMapName = mapNames[len(mapNames) - 1]
                for i in range(len(mapNames)):
                    if mapNames[i] == sprite['mapName']:
                        break
                    destMapName = mapNames[i]
                map = self['maps'][sprite['mapName']]
                destMap = self['maps'][destMapName]
                map.setObjectMap(sprite, destMap)
                # make sure player is still inside the map bounds.
                # This can be a problem is player jumped to smaller map.
                if sprite['anchorX'] > destMap['pixelWidth'] or sprite['anchorY'] > destMap['pixelHeight']:
                    destMap.setObjectLocationByAnchor(sprite, destMap['pixelWidth'] / 2, destMap['pixelHeight'] / 2)
                destMap.delMoveLinear(sprite)
                log(f"TEST: Player Changed Maps: {self['players'][ipport]['sprite']['labelText']} {ipport}")

    def msgTestPlayerNextMap(self, ip, port, ipport, msg):
        """Process msg of type playerNextMap.

        If in test mode, moves the player
        to next map (based on map names sorted alphabetically).

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if ipport in self['players']:  # if this is a player who has already joined the game
            if self['testMode']:
                sprite = self['players'][ipport]['sprite']
                mapNames = []
                for mapName in self['maps'].keys():
                    mapNames.append(mapName)
                mapNames.sort
                destMapName = mapNames[0]
                for i in range(len(mapNames)):
                    if mapNames[i] == sprite['mapName'] and i != len(mapNames) - 1:
                        destMapName = mapNames[i + 1]
                        break
                map = self['maps'][sprite['mapName']]
                destMap = self['maps'][destMapName]
                map.setObjectMap(sprite, destMap)
                # make sure player is still inside the map bounds.
                # This can be a problem is player jumped to smaller map.
                if sprite['anchorX'] > destMap['pixelWidth'] or sprite['anchorY'] > destMap['pixelHeight']:
                    destMap.setObjectLocationByAnchor(sprite, destMap['pixelWidth'] / 2, destMap['pixelHeight'] / 2)
                destMap.delMoveLinear(sprite)
                log(f"TEST: Player Changed Maps: {self['players'][ipport]['sprite']['labelText']} {ipport}")

    ########################################################
    # Networking - CONNECTOR MESSAGES
    ########################################################

    def msgConnectInfo(self, ip, port, ipport, msg):
        """Process msg of type connectInfo.

        If server is using connector
        (self['registerName'] != False) then send a udpPunchThrough to the
        client public ip/port. Do this even if it looks like client and
        and server are on the same LAN or same host. It does not matter
        if this msg reaches the client, only that it opens the server's
        LAN NAT so msgs are allowed from the client to the server.
        The client can then find the best path (localhost/lan/wan) to
        reach the server.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if self['registerName']:
            log(f"Sending udpPunchThrough to {msg['clientPublicIP']}:{msg['clientPublicPort']}")
            self['socket'].sendMessage(
                {'type': 'udpPunchThrough'},
                destinationIP=msg['clientPublicIP'],
                destinationPort=msg['clientPublicPort']
                )

    def msgServerAdded(self, ip, port, ipport, msg):
        """Process msg of type serverAdded.

        These are sent from the connector in reply
        to addServer msgs sent by self.sendConnectorKeepAlive(). These msgs can be
        safety ignored.
        """
        pass

    def msgServerDeleted(self, ip, port, ipport, msg):
        """Process msg of type serverDeleted.

        These are sent from the connector in reply
        to delServer msgs sent by self.msgJoinRequest(). These msgs can be
        safety ignored.
        """
        pass

    def sendConnectorKeepAlive(self):
        """Keep server data in connector from timing out.

        If we are using the connector (self['registerName'] != False) then
        send addServer msgs to the connector at a regular interval until
        all players have joined the game. This will ensure the connector
        does not remove this server data based the connectors timeout. This
        also keeps the UDP punch through in the server's LAN NAT open so
        the connector can send msgs.

        This method should be called regularly (in main loop) after the
        addServer msgs has been accepted by the connector.
        """
        if self['registerName'] and len(self['unassignedPlayerSprites']) != 0:
            if self.sendAddServerAfter < time.perf_counter():
                self['socket'].sendMessage(
                    self.getAddServerMsg(),
                    destinationIP=self['connectorHostName'],
                    destinationPort=self['connectorPort']
                    )
                self.sendAddServerAfter = time.perf_counter() + self['CONNECTOR_KEEP_ALIVE']

    def getAddServerMsg(self):
        """Creates an addServer msg that can be sent to the connector.

        Returns:
            dict: A correctly filled out addServer msg.
        """
        return {
            'type': 'addServer',
            'serverName': self['registerName'],
            'serverPrivateIP': engine.network.getDefaultIP(),
            'serverPrivatePort': self['serverPort']
            }

    ########################################################
    # Networking - STEP MESSAGES
    ########################################################

    def sendStepMsgs(self):
        """Send step msgs.

        Send a step msg to each player, but only if the map the
        player is on has changed or the player has changed.
        """
        for ipport in self['players']:
            player = self['players'][ipport]
            map = self['maps'][player['sprite']['mapName']]
            if map.changed or self.getPlayerChanged(player):
                self['socket'].sendMessage(
                    self.getStepMsg(player),
                    destinationIP=self['players'][ipport]['ip'],
                    destinationPort=self['players'][ipport]['port']
                    )
                player['lastStepMsgSent'] = time.perf_counter()
            # reset the change detection on player.
            self.resetPlayerChanged(self['players'][ipport])

        # reset the change detection on all maps
        for mapName in self['maps']:
            self['maps'][mapName].setMapChanged(False)

    def getStepMsg(self, player):
        """Creates a step msg that can be sent to a player.

        Args:
            player (dict): A player from self['players']

        Returns:
            dict: A correctly filled out step msg.
        """
        map = self['maps'][player['sprite']['mapName']]
        msg = {
            'type': 'step',
            'gameSec': time.perf_counter() - self['gameStartSec'],
            'mapName': map['name'],
            'layerVisabilityMask': map.getLayerVisablityMask(),
            'sprites': map['sprites']
            }

        if player['actionText']:
            msg['actionText'] = player['actionText']

        if player['marqueeText']:
            msg['marqueeText'] = player['marqueeText']

        return msg

    ########################################################
    # GAME LOGIC
    ########################################################

    def stepServer(self):
        """Take the game one "step" forward in time.

        This should be called once every 1/fps seconds by the main server loop.
        Three tasks are performed:
            1) call self.stepServerStart()
            2) call map.stepMap() for each map that has at least one player on it.
               Perform these calls in order of maps names sorted alphabetically.
            3) call self.stepServerEnd()
        """
        self.stepServerStart()

        # Run map.stepMap() for any maps that have players on them. We do not bother
        # to process maps that do not currently contain players.

        # find mapNames that have at least one player on them.
        mapNames = []
        for ipport in self['players']:
            mapNames.append(self['players'][ipport]['sprite']['mapName'])

        # set() removes duplicates and sorted() ensures we process maps in the same order each time.
        mapNames = sorted(set(mapNames))

        # call stepMap for each map with at least one player
        for mapName in mapNames:
            self['maps'][mapName].stepMap()

        self.stepServerEnd()

    def stepServerStart(self):
        """Server logic for the start of a step.

        Placeholder that can be overridden in sub-classes to perform any game
        logic for the start of a step. This is any logic that is not map
        specific and is called before any map step processing is performed.
        """
        pass

    def stepServerEnd(self):
        """Server logic for the end of a step.

        Placeholder that can be overridden in sub-classes to perform any game
        logic for the end of a step. This is any logic that is not map
        specific and is called after all map step processing is performed.
        """
        pass

    ########################################################
    # PLAYER
    ########################################################

    def addPlayer(self, ip, port, ipport, msg):
        """Add a client as a new player. Assumes client is not already a player (not yet in self['players']).
        Also, assumes there are still still players in self['unassignedPlayerSprites']

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.
        """

        # add the client to the game.
        sprite, mapName = self['unassignedPlayerSprites'].pop()

        # add player data to sprite
        sprite['playerNumber'] = len(self['unassignedPlayerSprites']) + 1
        sprite['mapName'] = mapName
        # add playerDisplaName to sprite as "labelText" so client can display it.
        sprite['labelText'] = msg['playerDisplayName']

        self['players'][ipport] = {
            'ip': ip,
            'port': port,
            'moveSpeed': 120,  # default move speed in pixels per second.
            'sprite': sprite,
            'playerNumber': sprite['playerNumber'],
            'actionText': False,  # set to false if not in use, rather than removing.
            'lastActionText': False,
            'marqueeText': False,
            'lastMarqueeText': False,  # set to false if not in use, rather than removing.
            'lastStepMsgSent': 0
            }
        # Also add player to self['playersByNum'] with the playerNumber so we can look up either way.
        self['playersByNum'][sprite['playerNumber']] = self['players'][ipport]

        # The sprite labelText changed so the map needs to be sent to all players
        self['maps'][mapName].setMapChanged()

        log(f"Player named {msg['playerDisplayName']} from {ipport} joined the game.")

    def setPlayerActionText(self, playerNumber, actionText):
        """Update the player's actionText to actionText.

        Args:
            playerNumber (int): A player's playerNumber
            actionText (str): A string to display to the user in the action text box.
        """
        if playerNumber in self['playersByNum']:
            player = self['playersByNum'][playerNumber]
            # actionText can only be set once after a call to delPlayerActionText
            if not player['actionText']:
                player['actionText'] = actionText

    def delPlayerActionText(self, playerNumber):
        """Update the player so they do not have any actionText.

        Args:
            playerNumber (int): A players playerNumber
        """
        if playerNumber in self['playersByNum']:
            self['playersByNum'][playerNumber]['actionText'] = False

    def setPlayerMarqueeText(self, playerNumber, marqueeText):
        """Update the player's marqueeText to marqueeText.

        Args:
            playerNumber (int): A player's playerNumber
            marqueeText (str): A string to display to the user in the marquee text box.
        """
        if playerNumber in self['playersByNum']:
            self['playersByNum'][playerNumber]['marqueeText'] = marqueeText

    def delPlayerMarqueeText(self, playerNumber):
        """Update the player so they do not have any marqueeText.

        Args:
            playerNumber (int): A players playerNumber
        """
        if playerNumber in self['playersByNum']:
            self['playersByNum'][playerNumber]['marqueeText'] = False

    def resetPlayerChanged(self, player):
        """Update player so calls to self.getPlayerChanged will return False until the player is changed again.

        Args:
            player (dict): A player from self['players']
        """
        player['lastActionText'] = player['actionText']
        player['lastMarqueeText'] = player['marqueeText']

    def getPlayerChanged(self, player):
        """Return True if player has changed since last call to self.resetPlayerChanged() else returns False.

        Args:
            player (dict): A player from self['players']

        Returns:
            boolean
        """
        if player['lastActionText'] != player['actionText'] or player['lastMarqueeText'] != player['marqueeText']:
            return True
        return False
