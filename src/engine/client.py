"""Game Client"""

import signal
import engine.time as time

import pygame
from pygame.locals import *

import engine.log
from engine.log import log

import engine.network
import engine.loaders


def quit(signal=None, frame=None):
    """Quit the client process.

    Designed to be used with the signal module to catch and shutdown when user hits Ctrl-C
    but can also be called by other code to shutdown gracefully.

    Args:
        signal (int): Signal number.
        frame : stack frame

    Returns:
        Does not return. Exits python.
    """

    # If the socket has been created then print network stats.
    try:
        log(engine.client.CLIENT['socket'].getStats())
    except BaseException:
        pass

    global profiler
    if profiler:
        profiler.stop()
        profiler.print()

    log("Quiting", "INFO")
    exit()


class Client(dict):
    """The Client Class.

    The Client class is responsible for:
        1) Opening the game interface window;
        2) Requesting that the server allow the player to join the game;
        3) Collecting user input and sending it to the server over the network;
        4) Receiving updates from the server and rendering them to the screen.
        5) Performing any screen updates and animations that that are not
           related to game logic, such as tile and character animations.

    Client attributes are stored in dictionary form (self['attribute_name'] rather
    than self.attribute_name). All attributes can be seen by turning on -verbose
    and looking in the output of the client.

    The Client class is designed to be a singleton (only one instance) and stores
    a reference to itself in the module global variable engine.client.CLIENT. Any game
    code that is part of the client can access the Client instance using:
        import engine.client
        engine.client.CLIENT...

    The Client class is intended to be sub-classed and extended by the game.

    To sub-class, add a client.py file under the game folder:
        src/<game name>/client.py

    In the sub-classed client.py inherit from engine.client as follows:
        import engine.client
        class Client(engine.client.Client):

    See src/demo/client.py for an example.
    """

    def __init__(self, args):
        """Init the Client class.

        Set up the Client data, open client network ip:port, join the server,
        open the game window, load Tiled data (maps and tilesets)
        """

        # enable SIGINT so quit() will be called on Cntl-C
        global CLIENT
        CLIENT = self
        signal.signal(signal.SIGINT, quit)

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
        self['playerDisplayName'] = args.playerDisplayName
        self['connectName'] = args.connectName
        self['connectorHostName'] = args.connectorHostName
        self['connectorPort'] = args.connectorPort
        self['serverIP'] = args.serverIP
        self['serverPort'] = args.serverPort
        self['clientIP'] = args.clientIP
        self['clientPort'] = args.clientPort
        self['windowWidth'] = args.windowWidth
        self['windowHeight'] = args.windowHeight
        self['fps'] = args.fps
        self['busySec'] = args.busySec

        # actionText defaults that differ from DEFAULTTEXT
        self['ACTIONTEXT'] = {
            "halign": "center",
            "valign": "bottom"
            }

        # marqueeText defaults that differ from DEFAULTTEXT
        self['MARQUEETEXT'] = {
            "halign": "center",
            "valign": "center"
            }

        self['testMode'] = False  # True if server is in testMode. Server provides this in joinReply message.

        # Set up network, send joinRequest msg to server, and wait for joinReply to be sent back from server.

        log(f"Client Default IP: {engine.network.getDefaultIP()}")

        if self['connectName']:
            self['clientIP'] = '0.0.0.0'  # ignore clinetIP if we are going to request server address from connector.
        try:
            self['socket'] = engine.network.Socket(
                messages=engine.loaders.loadModule("messages", game=self['game']).Messages(),
                msgProcessor=self,
                sourceIP=self['clientIP'],
                sourcePort=self['clientPort'],
                sourcePortSearch=True
                )
        except Exception as e:
            log(str(e), "FAILURE")
            quit()

        self['clientPort'] = self['socket'].sourcePort  # may have changed to a different available port.
        joinReply = False
        if self['connectName']:
            # talk to connector for connetinfo msg
            log(f"Asking connector for '{self['connectName']}' connection details.")
            connectorReply = False
            try:
                connectorReply = self['socket'].sendRecvMessage({
                    'type': 'getConnetInfo',
                    'serverName': self['connectName'],
                    'clientPrivateIP': engine.network.getDefaultIP(),
                    'clientPrivatePort': self['socket'].sourcePort
                    },
                    destinationIP=self['connectorHostName'],
                    destinationPort=self['connectorPort'],
                    retries=3, delay=3, delayMultiplier=1)
            except engine.network.SocketException as e:
                log(e)
                quit()

            if connectorReply['serverPublicIP'] == connectorReply['clientPublicIP'] and connectorReply['serverPrivateIP'] == connectorReply['clientPrivateIP']:
                # try route to localhost first (same computer)
                self['serverIP'] = '127.0.0.1'
                self['serverPort'] = connectorReply['serverPrivatePort']
                joinReply = self.joinServer()
            if not joinReply and connectorReply['serverPublicIP'] == connectorReply['clientPublicIP']:
                # try route over Local Area Network (LAN) second
                self['serverIP'] = connectorReply['serverPrivateIP']
                self['serverPort'] = connectorReply['serverPrivatePort']
                joinReply = self.joinServer()
            if not joinReply:
                self['serverIP'] = connectorReply['serverPublicIP']
                self['serverPort'] = connectorReply['serverPublicPort']

        if not joinReply:
            joinReply = self.joinServer()
            if not joinReply:
                log("Could not connect to server. Is server running?")
                quit()

        self['playerNumber'] = joinReply['playerNumber']

        # set the time so client engine.time.perf_counter() will return secs in sync (very close) to server.
        time.set(joinReply['serverSec'])

        self['testMode'] = joinReply['testMode']
        if(self['testMode']):
            log("Server running in TEST MODE.")

        log("Join server was successful.")

        self['serverIpport'] = engine.network.formatIpPort(self['serverIP'], self['serverPort'])
        self['step'] = False  # Currently displayed step. Empty until we get first step msg from server. = {}
        self['mapOffset'] = (0, 0)

        # Note, we must init pygame before we load tileset data.
        pygame.init()
        pygame.mixer.quit()  # Turn all sound off.
        pygame.display.set_caption(f"{self['game']} - {self['playerDisplayName']}")  # Set the title of the window
        self['screen'] = pygame.display.set_mode((self['windowWidth'], self['windowHeight']),
                                                 pygame.RESIZABLE)  # open the window
        self['screenValidUntil'] = 0  # invalid and needs to be rendered.

        self['tilesets'] = engine.loaders.loadTilesets(
            game=self['game'],
            loadImages=True  # Client needs images so it can render screen.
            )

        self['maps'] = engine.loaders.loadMaps(
            tilesets=self['tilesets'],
            game=self['game'],
            maptype="ClientMap"
            )

        log("Loading tilesets and maps was successful.")

    def joinServer(self):
        """Send a joinRequest msg to the server and wait for a reply.

        Returns:
            dict or False: A joinReply msg if the player was added else returns False.
        """
        try:
            log(f"Sending joinRequest to server at {self['serverIP']}:{self['serverPort']}")
            self['socket'].setDestinationAddress(self['serverIP'], self['serverPort'])
            joinReply = self['socket'].sendRecvMessage({
                'type': 'joinRequest',
                'game': self['game'],
                'playerDisplayName': self['playerDisplayName']
                },
                retries=5, delay=1, delayMultiplier=1)
            if joinReply['type'] != "joinReply":
                log(f"Expected joinReply message but got {joinReply['type']}, quiting!", "FAILURE")
                quit()
            return joinReply
        except engine.network.SocketException as e:
            log(e)
            return False

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # Main Loop
    ########################################################

    def run(self):
        '''Main client loop.

        This loop is controlled to run once every 1/fps seconds.
        Every loop it received msgs from the server, updates the screen, and
        processes user input events. It also prints server busy messages on
        a regular interval.
        '''

        startAt = time.perf_counter()
        nextStatusAt = startAt + self['busySec']
        sleepTime = 0
        nextStepAt = startAt + (1.0 / self['fps'])
        while True:
            # process messages from server (recvReplyMsgs calls msg<msgType> for each msg received)
            self['socket'].recvReplyMsgs()

            # update the screen so player can see data that server sent
            self.updateScreen()

            # process any user input and send it to the server as required.
            self.processEvents()

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
                log("Client running slower than " + str(self['fps']) + " fps.", "VERBOSE")

            nextStepAt = time.perf_counter() + (1.0 / self['fps'])

    ########################################################
    # NETWORK MESSAGE PROCESSING
    ########################################################

    def msgStep(self, ip, port, ipport, msg):
        """Process msg of type step.

        Store step msg and invalidate the screen timer.

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
        if ipport != self['serverIpport']:
            log(f"Msg received but not from server! Msg from ({ipport}).", "WARNING")
            return
        self['step'] = msg  # store the new step
        self['screenValidUntil'] = 0  # flag that we need to redraw the screen.

    def msgQuitting(self, ip, port, ipport, msg):
        """Process msg of type quitting.

        Call the quit() function if the message was from the server.

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
        if ipport != self['serverIpport']:
            log(f"Msg received but not from server! Msg from ({ipport}).", "WARNING")
            return
        log("Received quitting msg from server.")
        quit()

    def msgUdpPunchThrough(self, ip, port, ipport, msg):
        """Process msg of type udpPunchTrough.

        Ignore this message. The server only sent it to client so server's NAT
        would allow client to send messages to server.
        """
        pass

    ########################################################
    # SCREEN DRAWING
    ########################################################

    def updateScreen(self):
        """Update the window.

        Only update window if step data has been received from the
        server and the screen valid timer is in the past.
        """
        if self['step'] and self['screenValidUntil'] < time.perf_counter():
            # find the map that the server wants us to render.
            map = self['maps'][self['step']['mapName']]

            # update layer visibility from the server step message.
            map.setLayerVisablityMask(self['step']['layerVisabilityMask'])

            # compute the best map offset given the players position
            self['mapOffset'] = self.setMapOffset(map)

            # draw the map.
            self['screenValidUntil'] = map.blitMap(self['screen'], self['mapOffset'], self['step']['sprites'])

            # add on any items not specific to the map.
            self.updateInterface()

            # tell pygame to actually display changes to user.
            pygame.display.update()

    def setMapOffset(self, map):
        """Return an offset for displaying the map.

        The offset needs to ensure the map is centered
        in the window (if map is smaller than the window) and ensure the player is
        on a visible part of the map (if map is bigger than the window).

        Assumes step data has been sent from server.

        Args:
        map : engine.map.Map
            The map the player is on.

        Returns:
            (mapOffsetX, mapOffsetY) (int, int): a list of two ints.
        """
        mapOffsetX = 0
        mapOffsetY = 0

        if map['pixelWidth'] < self['screen'].get_width():
            mapOffsetX = round((self['screen'].get_width() - map['pixelWidth']) / 2)
        if map['pixelHeight'] < self['screen'].get_height():
            mapOffsetY = round((self['screen'].get_height() - map['pixelHeight']) / 2)

        if map['pixelWidth'] > self['screen'].get_width() or map['pixelHeight'] > self['screen'].get_height():
            # find the player.
            for sprite in self['step']['sprites']:
                if "playerNumber" in sprite and self['playerNumber'] == sprite['playerNumber']:
                    break

            if map['pixelWidth'] > self['screen'].get_width():
                mapOffsetX = self['screen'].get_width() / 2 - sprite['anchorX']
                if mapOffsetX > 0:
                    mapOffsetX = 0
                if map['pixelWidth'] + mapOffsetX < self['screen'].get_width():
                    mapOffsetX = self['screen'].get_width() - map['pixelWidth']

            if map['pixelHeight'] > self['screen'].get_height():
                mapOffsetY = self['screen'].get_height() / 2 - sprite['anchorY']
                if mapOffsetY > 0:
                    mapOffsetY = 0
                if map['pixelHeight'] + mapOffsetY < self['screen'].get_height():
                    mapOffsetY = self['screen'].get_height() - map['pixelHeight']

        mapOffsetX = round(mapOffsetX)
        mapOffsetY = round(mapOffsetY)
        return((mapOffsetX, mapOffsetY))

    def updateInterface(self):
        """Render User Interface to Window.

        Render any non-map items, such as player specific data or gui elements.
        These are rendered relative to the screen, not the map. (e.g. bottom
        of screen, not bottom of map)
        """

        if "actionText" in self['step']:
            self.blitActionText(self['step']['actionText'])

        if 'marqueeText' in self['step']:
            self.blitMarqueeText(self['step']['marqueeText'])

        if(self['testMode']):
            self.blitTestText()

    def blitActionText(self, actionText):
        """ Render actionText to screen. """
        text = self['ACTIONTEXT'].copy()
        text['text'] = actionText + " (spacebar)"
        textObject = {
            'x': 0,
            'y': 0,
            'width': self['screen'].get_width(),
            'height': self['screen'].get_height(),
            'text': text
            }

        # find the map that the server wants us to render.
        map = self['maps'][self['step']['mapName']]
        map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)

    def blitMarqueeText(self, marqueeText):
        """ Render marqueeText to screen. """
        text = self['MARQUEETEXT'].copy()
        text['text'] = marqueeText
        textObject = {
            'x': self['screen'].get_width() / 4,
            'y': self['screen'].get_height() / 4,
            'width': self['screen'].get_width() / 2,
            'height': self['screen'].get_height() / 2,
            'text': text
            }

        # find the map that the server wants us to render.
        map = self['maps'][self['step']['mapName']]
        map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)

    def blitTestText(self):
        """ Render test mode text to screen. """
        textObject = {
            'x': 0, 'y': 0,
            'width': self['screen'].get_width(), 'height': self['screen'].get_height(),
            'text': {
                'text': "TEST MODE: F1=Toggle_Player_Move_Checking F2/F3=Jump_Map RMB=Jump_Location",
                'pixelsize': 14,
                'vlaign': 'top',
                'halign': 'center',
                "color": "#00ff00",
                "fontfamily": 'Courier New',
                "bgcolor": "#000000",
                "bgbordercolor": "#000000",
                "bgborderThickness": 0,
                "bgroundCorners": 0,
                "antialiased": True
                }
            }

        # find the map that the server wants us to render.
        map = self['maps'][self['step']['mapName']]
        map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)

        textObject['text']['valign'] = "bottom"
        textObject['text']['halign'] = "right"
        textObject['text']['text'] = "Map: " + self['step']['mapName']
        map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)

        for sprite in self['step']['sprites']:
            if "playerNumber" in sprite and self['playerNumber'] == sprite['playerNumber']:
                textObject['text']['valign'] = "bottom"
                textObject['text']['halign'] = "left"
                textObject['text']['text'] = f"Player Anchor: ({round(sprite['anchorX'],4)}, {round(sprite['anchorY'],4)})"
                map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)
                break

    ########################################################
    # USER INPUT HANDLING
    ########################################################

    def processEvents(self):
        """ Process User Input.

        Get and process input events from user, such as keyboard,
        mouse, and window events.
        """
        for event in pygame.event.get():
            self.processEvent(event)

    def processEvent(self, event):
        """Process an input event.

        Most input events will result in a msg being sent to the server.
        """
        if event.type == QUIT:
            quit()
        elif event.type == VIDEORESIZE:
            self['screenValidUntil'] = 0
        elif event.type == pygame.TEXTINPUT:
            if event.text == ' ':
                self['socket'].sendMessage({'type': 'playerAction'})
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F1:
                self['socket'].sendMessage({'type': 'testTogglePlayerMoveChecking'})
            elif event.key == pygame.K_F2:
                self['socket'].sendMessage({'type': 'testPlayerPreviousMap'})
            elif event.key == pygame.K_F3:
                self['socket'].sendMessage({'type': 'testPlayerNextMap'})
        elif event.type == pygame.MOUSEBUTTONDOWN:
            btn1, btn2, btn3 = pygame.mouse.get_pressed(num_buttons=3)
            moveDestX, moveDestY = pygame.mouse.get_pos()
            moveDestX -= self['mapOffset'][0]
            moveDestY -= self['mapOffset'][1]
            msgType = 'playerMove'
            if btn3:
                msgType = 'testPlayerJump'
            self['socket'].sendMessage({'type': msgType, 'moveDestX': moveDestX, 'moveDestY': moveDestY})
