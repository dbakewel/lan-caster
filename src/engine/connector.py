"""Connector Server"""

import signal
import engine.time as time
import random
import os

from engine.log import log
import engine.log
import engine.messages
import engine.network


def quit(signal=None, frame=None):
    """Quit the connector process.

    Designed to be used with the signal module to catch and shutdown when user hits Ctrl-C
    but can also be called by other code to shutdown gracefully.

    Args:
        signal (int): Signal number.
        frame : stack frame

    Returns:
        Does not return. Exits python.
    """
    log("Quiting", "INFO")
    exit()


class Connector(dict):
    """The Connector Class.

    The Connector can be used to allow game servers and clients to connect
    without having to know each other's IP addresses. Rather a simple
    serverName is used.

    The Connector class is responsible for:
        1) Opening the socket;
        2) Maintaining a list of server connection info;
        3) Processing msgs from server and clients so they can find each other.

    To make the connector work, the connector must be run on a host that is
    accessible by the game server and all clients and must use a known name.
    For example, the connector must be run on a internet accessible host
    and use a DNS name such as "lan-caster.net". Once the connector is running
    the follow steps can take place:
        1) Server sends addServer message to connector. This provides the server
           information to the connector and also create a UDP punch through so
           the connector can send data back to there server. The server needs
           to send additional addServer messages at a regular interval (e.g. 10s) to
           keep the UDP punch through active and to stop the connector from
           removing the server information based on a timeout.
        2) Each client can now send a getConnetInfo msg to the connector. The
           connector will combine the server and client ips into a connectInfo
           msg and send it to both the server and client.
        3) When the server receives a connectInfo message it will send a
           UDP punch through to the client so client msgs can reach the server.
        4) When the client receives a connectInfo message it will send a
           joinRequest to the server using each server IP until one connects.
        5) When all users have joined the game, the server can send a
           delServer msg to the connector.
    """

    def __init__(self, connectorIP, connectorPort):
        """Init the connector: set up data, open socket."""
        self['MAX_SERVERS'] = 100
        self['SERVER_TIMEOUT'] = 30

        self['serverlist'] = {}

        messages = engine.messages.Messages()

        # set up networking
        try:
            self['socket'] = engine.network.Socket(
                messages,
                msgProcessor=self,
                sourceIP=connectorIP,
                sourcePort=connectorPort
                )

        except Exception as e:
            log(str(e), "FAILURE")
            quit()

    def __str__(self):
        return engine.log.objectToStr(self)

    ########################################################
    # MAIN LOOP
    ########################################################

    def run(self):
        '''Main connector loop.

        Runs once every second.
        '''
        while True:
            # process messages from servers and clients (recvReplyMsgs calls msg<msgType> for each msg received)
            self['socket'].recvReplyMsgs()
            self.checkTimeouts()
            time.sleep(sec=1)

    def checkTimeouts(self):
        """Remove any serverName from self['serverlist'] that have timed out.

        Note, servers need to keep sending addServer messages on a regular
        interval if they want the connector to keep their entry in the
        server list.
        """
        currentTime = time.perf_counter()
        for serverName in list(self['serverlist'].keys()):
            if self['serverlist'][serverName]['timeout'] < currentTime:
                log(f"Deleting server named '{serverName}' based on timeout:")
                log(self['serverlist'][serverName])
                del self['serverlist'][serverName]

    ########################################################
    # Network Message Processing
    ########################################################

    def msgAddServer(self, ip, port, ipport, msg):
        """Add serverName from self['serverlist'].

        This message would normally be sent by a server so that
        clients can request connectInfo for the server.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        Returns:
            dict: A serverAdded msg if the serverName was added else
                returns an Error msg.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if msg['serverName'] not in self['serverlist']:
            if self['MAX_SERVERS'] > len(self['serverlist']):
                self['serverlist'][msg['serverName']] = {
                    'timeout': time.perf_counter() + self['SERVER_TIMEOUT'],
                    'serverPrivateIP': msg['serverPrivateIP'],
                    'serverPrivatePort': msg['serverPrivatePort'],
                    'serverPublicIP': ip,
                    'serverPublicPort': port,
                    }
                log(f"Added server named '{msg['serverName']}':")
                log(self['serverlist'][msg['serverName']])
                return {'type': 'serverAdded'}
            else:
                return {'type': 'Error', 'result': f"Max servers already registered."}
        else:
            server = self['serverlist'][msg['serverName']]
            if server['serverPublicIP'] == ip and server['serverPublicPort'] == port:
                server['timeout'] = time.perf_counter() + self['SERVER_TIMEOUT']
                log(f"Updated timeout for server named '{msg['serverName']}':")
                log(self['serverlist'][msg['serverName']])
                return {'type': 'serverAdded'}
            else:
                return {'type': 'Error', 'result': f"A server with that name is already registered. Choose a different name."}

    def msgDelServer(self, ip, port, ipport, msg):
        """Remove serverName from self['serverlist'].

        This message would normally be sent by a server that no
        longer wants clients to join it's game.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        Returns:
            dict: A serverDeleted msg if the serverName was removed else
                returns an Error msg.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if msg['serverName'] in self['serverlist']:
            server = self['serverlist'][msg['serverName']]
            if server['serverPublicIP'] == ip and server['serverPublicPort'] == port:
                log(f"Deleting server named '{msg['serverName']}' based on delServer msg:")
                log(self['serverlist'][msg['serverName']])
                del self['serverlist'][msg['serverName']]
                return {'type': 'serverDeleted'}
            else:
                return {'type': 'Error', 'result': f"Permission Denied."}
        else:
            return {'type': 'Error', 'result': f"Server is not registered."}

    def msgGetConnetInfo(self, ip, port, ipport, msg):
        """Process msg of type getConnectInfo.

        This message would normally be sent by a client that knows the
        server name they wish to connect to but need the connection info
        (ip addresses) so they can connect.

        The connect info is sent back to the client but it is also sent
        to the server since the server may need to use the info to send
        a udpPunchThrough msg that will allow the client to talk to the
        server.

        This method is designed to be called from self['socket'].recvReplyMsgs().
        self['socket'].recvReplyMsgs() will call this method when it receives a
        msg of the corresponding type.

        Args:
            ip (str): IP Address of sender.
            port (int): Port number of sender.
            ipport (str): IP Address and Port of sender in format "ip:port".
            msg (dict): The message which was received.

        Returns:
            dict: A connectInfo msg if the serverName is in self['severlist'] else
                returns an Error msg. Regardless, this msg will be sent back to the
                client.

        See Also:
            Message format in engine.messages.Messages['messageDefinitions']
            engine.socket.recvReplyMsgs()
        """
        if msg['serverName'] in self['serverlist']:
            server = self['serverlist'][msg['serverName']]
            reply = {
                'type': 'connectInfo',
                'serverName': msg['serverName'],
                'clientPrivateIP': msg['clientPrivateIP'],
                'clientPrivatePort': msg['clientPrivatePort'],
                'serverPrivateIP': server['serverPrivateIP'],
                'serverPrivatePort': server['serverPrivatePort'],
                'clientPublicIP': ip,
                'clientPublicPort': port,
                'serverPublicIP': server['serverPublicIP'],
                'serverPublicPort': server['serverPublicPort']
                }

            # send connectInfo to server.
            self['socket'].sendMessage(
                reply,
                destinationIP=server['serverPublicIP'],
                destinationPort=server['serverPublicPort']
                )

            # send connectInfo to client
            return reply
        else:
            return {'type': 'Error', 'result': f"Server is not registered."}
