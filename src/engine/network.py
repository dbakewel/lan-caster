"""Send/Receive Messages Over Network"""

import socket
import random
import engine.time as time
import re
import argparse
import msgpack

import engine.log
from engine.log import log


########################################################
# Network Socket (Send and Receive Messages)
########################################################

class Socket:
    """Socket Class

    Basic network communications class for reliable and unreliable
    send/recv of Messages. Based on UDP/IP sockets.
    """

    def __init__(self, messages, msgProcessor, sourceIP, sourcePort,
                 sourcePortSearch=False, destinationIP='127.0.0.1', destinationPort=20000):
        """Create and bind UDP socket.

        Args:
            messages (engine.messages.Messages object): Used for message validation.
            msgProcessor (class instance): Class instance that contains methods for
                msg types that will be received by recvReplyMsgs(). If a msg has
                type "joinRequest" then msgProcessor should have a method of the form
                "msgJoinRequest(self, ip, port, ipport, msg)".
            sourceIP (str): The IP address to bind to. This is the IP the socket will listen on. This
                must be 127.0.0.1 (locahost), 0.0.0.0 (all interfaces), or a valid IP address on the
                computer.
            sourcePort (int): The port to bind to.
            sourcePortSearch (bool): If true and sourcePort is not available then search for a
                port that is available.
            destinationIP (str): set the default IP to send messages to.
            destinationPort (int): set the default port to send messages to.

        Returns:
            Socket object.

        Raises:
            socket related exceptions.
        """

        self.messages = messages

        # Find all msg* methods in msgProcessor
        self.msgProcessor = msgProcessor
        self.msgProcessorMethods = [func for func in dir(self.msgProcessor) if callable(
            getattr(self.msgProcessor, func)) and func.startswith('msg')]
        log(
            f"Methods callable by recvReplyMsgs() when corresponding msg type received:\n{self.getAllMsgMethodsStr()}\n",
            "VERBOSE")

        self.sent = {}  # Number of messages sent to OS socket
        self.recv = {}  # Number of messages recv from OS socket
        self.sendRecvMessageCalls = 0  # Number of calls to sendRecvMessage
        self.sendRecvMessageResends = 0  # Number of resends made by sendRecvMessage
        self.sendRecvMessageTime = 0  # Total time in sendRecvMessage
        self.sendTypes = {}
        self.recvTypes = {}

        self.sendrecvDelay = 0.1

        self.sourceIP = sourceIP
        log("Creating socket with sourceIP=" + sourceIP + ", sourcePort=" + str(sourcePort), "VERBOSE")
        self.s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        if sourcePortSearch:
            portRange = 100  # try the source port provided and 100 ports above it until an available port is found.
        else:
            portRange = 1  # only try the sourcePort provided

        bind = False
        for i in range(portRange):
            try:
                self.s.bind((sourceIP, sourcePort + i))
                bind = True
                self.sourcePort = sourcePort + i
                break
            except Exception as e:
                pass

        if bind:
            log("Source Socket Binding Successful. Listening on " + formatIpPort(self.sourceIP, self.sourcePort))
        else:
            self.s.close()
            self.s = None
            log("Source Socket Binding Failed. The source port(s) may already be in use.", "FAILURE")
            raise

        self.s.settimeout(0)
        self.destinationIP = resolve(destinationIP)
        self.destinationPort = destinationPort
        self.bufferSize = 256000
        random.seed()
        self.msgID = random.randrange(0, 65000, 1)

    def __str__(self):
        return engine.log.objectToStr(self)

    def getAllMsgMethodsStr(self):
        '''return a multi-line string of all msg* methods both found and not found in msgProcessor'''
        missingMethods = []
        for m in self.messages['messageDefinitions'].keys():
            m = "msg" + m.capitalize()[:1] + m[1:]
            if m not in self.msgProcessorMethods:
                missingMethods.append(m)
        missingMethods.sort()

        output = f"{'msg* Methods Found':32}{'msg* Methods Not Found':32}\n"
        output += f"{'------------------------':32}{'------------------------':32}\n"
        for i in range(max(len(self.msgProcessorMethods), len(missingMethods))):
            found = ""
            notFound = ""
            if i < len(self.msgProcessorMethods):
                found = self.msgProcessorMethods[i]
            if i < len(missingMethods):
                notFound = missingMethods[i]
            output += f"{found:32}{notFound:32}\n"
        return output

    def settimeout(self, t):
        """Set the UDP socket timeout to t (float) secs.

        This is the length of time recvfrom() will block if not msg is already in
        the recv buffer.
        """
        self.s.settimeout(t)

    def setDelay(self, delay):
        """Set the default delay (float) in secs between msg send retries in sendRecvMessage()"""
        self.sendrecvDelay = delay

    def getStats(self):
        """ Return str of Socket stats. """
        output = "\n\n             ====== Network Stats ======"

        if self.sendRecvMessageCalls:
            output += \
                "\n     sendRecvMessage Calls: " + str(self.sendRecvMessageCalls) + \
                "\n   sendRecvMessage Resends: " + str(self.sendRecvMessageResends) + \
                "\n  Avg sendRecvMessage Time: " + \
                '%.6f' % (self.sendRecvMessageTime / self.sendRecvMessageCalls) + " secs."

        for ipport in self.sent.keys():
            output += "\n\n               === To/From: " + ipport + " ==="\
                "\n             Messages Sent: " + str(self.sent[ipport]) +\
                "\n             Messages Recv: " + str(self.recv[ipport])

            if ipport in self.sendTypes:
                output += "\n\n                Messages Sent by Type"
                for t, c in sorted(self.sendTypes[ipport].items(), key=lambda x: x[0]):
                    output += "\n" + '%26s' % (t) + ": " + str(c)

            if ipport in self.recvTypes:
                output += "\n\n                Messages Recv by Type"
                for t, c in sorted(self.recvTypes[ipport].items(), key=lambda x: x[0]):
                    output += "\n" + '%26s' % (t) + ": " + str(c)

            output += "\n"

        return output

    def setDestinationAddress(self, destinationIP, destinationPort):
        """
        Set default destination used by Socket send and recv functions when
        destination is not provided.

        Args:
            destinationIP (str)
            destinationPort (int)

        Raises:
            SocketException exception.
        """

        destinationIP = resolve(destinationIP)
        if not destinationIP or not isValidPort(destinationPort):
            raise SocketException("Bad IP or Port Provided.")

        self.destinationIP = destinationIP
        self.destinationPort = destinationPort

    def serialize(self, msg):
        return msgpack.packb(msg, use_bin_type=True)

    def deserialize(self, b):
        return msgpack.unpackb(b, raw=False)

    def sendMessage(self, msg, destinationIP=None, destinationPort=None, packedAndChecked=False):
        """Send a msg over the network.

        Sends msg to destinationIP:destinationPort and then returns immediately.
        sendMessage is considered asynchronous because it does not wait for a
        reply message and returns no value. Therefore there is no indication if
        msg will be received by the destination.

        msg must be a valid message (see Messages below). Raises
        SocketException exception if the msg does not have a valid format.

        If destinationIP or destinationPort is not provided then the default will
        be used (see setDestinationAddress()).

        If packedAndChecked is True then msg is assumed to already be serialized
        and no other checks will be done.

        Args:
            msg (dict): A valid message as defined in Messages object.
            destinationIP (str)
            destinationPort (int)
            packedAndChecked (bool)

        """

        if destinationIP is None:
            destinationIP = self.destinationIP
        destinationIP = resolve(destinationIP)

        if destinationPort is None:
            destinationPort = self.destinationPort

        if not packedAndChecked:
            if not self.messages.isValidMsg(msg):
                raise SocketException("Could not send because msg is not valid format.")
            if not isValidIP(destinationIP):
                raise SocketException("Could not send because destinationIP is not valid.")
            if not isValidPort(destinationPort):
                raise SocketException("Could not send because destinationPort is not valid format.")

            # Convert data from python objects to network binary format
            networkbytes = self.serialize(msg)
        else:
            networkbytes = msg

        log("Sending msg to " + destinationIP + ":" + str(destinationPort) +
            " len=" + str(len(networkbytes)) + " bytes " + str(msg), "DEBUG")
        self.s.sendto(networkbytes, (destinationIP, destinationPort))

        dest = formatIpPort(destinationIP, destinationPort)
        if dest in self.sent:
            self.sent[dest] += 1
        else:
            self.sent[dest] = 1

        if not packedAndChecked:
            msgtype = msg['type']
        else:
            msgtype = "Serialized"

        if dest not in self.sendTypes:
            self.sendTypes[dest] = {}
        if msgtype in self.sendTypes[dest]:
            self.sendTypes[dest][msgtype] += 1
        else:
            self.sendTypes[dest][msgtype] = 1

    def recvMessage(self):
        """
        Check the socket receive buffer and returns message, ip, and port only
        if a valid message is immediately ready to receive. recvMessage is
        considered asynchronous because it will not wait for a message to arrive
        before raising an exception.

        If the reply is an “Error” message then it will be returned just like
        any other message. No exception will be raised.

        If msg is not a valid message (see Messages below) then raises
        SocketException.

        Immediately raises SocketException if the receive buffer is empty.

        Note, the text above assumes the socket timeout is set to 0
        (non-blocking), which is the default in Socket.

        Returns:
            msg (dict): valid message type as defined in Messages object
            ip (str): The IP address that sent the message
            port (int): The Port number that sent the message

        """
        try:
            bytesAddressPair = self.s.recvfrom(self.bufferSize)
            # Convert data from network binary format to python objects
            msg = self.deserialize(bytesAddressPair[0])
            ip = bytesAddressPair[1][0]
            port = bytesAddressPair[1][1]
            log("Received msg from " + ip + ":" + str(port) + " len=" +
                str(len(bytesAddressPair[0])) + " bytes " + str(msg), "DEBUG")

            ipport = formatIpPort(ip, port)
            if ipport in self.recv:
                self.recv[ipport] += 1
            else:
                self.recv[ipport] = 1

            if ipport not in self.recvTypes:
                self.recvTypes[ipport] = {}
            if msg['type'] in self.recvTypes[ipport]:
                self.recvTypes[ipport][msg['type']] += 1
            else:
                self.recvTypes[ipport][msg['type']] = 1

        except (BlockingIOError, socket.timeout):
            # There was no data in the receive buffer.
            raise SocketException("Receive buffer empty.")
        except (ConnectionResetError):
            # Windows raises this when it gets back an ICMP destination unreachable packet
            log("The destination ip:port returned ICMP destination unreachable. Is the destination running?", "WARNING")
            raise SocketException(
                "The destination ip:port returned ICMP destination unreachable. Is the destination running?")

        if not self.messages.isValidMsg(msg):
            raise SocketException("Received message invalid format.")

        return msg, ip, port

    def sendRecvMessage(self, msg, destinationIP=None, destinationPort=None,
                        retries=10, delay=None, delayMultiplier=1.2):
        """
        Sends msg to destinationIP:destinationPort and then returns the reply.
        sendRecvMessage is considered synchronous because it will not return
        until and unless a reply is received. Programmers can this of this much
        like a normal function call.

        msg must be a valid message

        If destinationIP or destinationPort is not provided then the default will
        be used (see setDestinationAddress()).

        If the reply is an “Error” message then a SocketException exception
        will be raised.

        If no reply is received then the message will be sent again (retried) in
        case it was dropped by the network. If the maximum number of retries is
        reached then a SocketException exception will be raised.

        Args:
            msg (dict): A valid message as defined in Messages object.
            destinationIP (str)
            destinationPort (int)
            retries (int): The number of times to resend msg until reply
                is received.
            delay (float): How long to wait between each retry.
            delayMultiplier (float): How much longer or shorter to wait
                between each attempted retry.


        Raises:
            SocketException exception if the msg does not hae a valid format.
        """

        startTime = time.perf_counter()
        self.sendRecvMessageCalls += 1

        if destinationIP is None:
            destinationIP = self.destinationIP
        destinationIP = resolve(destinationIP)

        if destinationPort is None:
            destinationPort = self.destinationPort

        if delay:
            nextDelay = delay
        else:
            nextDelay = self.sendrecvDelay

        remaining = retries

        self.msgID = self.msgID + 1
        if self.msgID > 65000:
            self.msgID = 0

        msg['msgID'] = self.msgID

        gotReply = False
        sendMessage = 0
        while remaining != 0 and gotReply == False:
            if sendMessage <= time.perf_counter():
                self.sendMessage(msg, destinationIP, destinationPort)
                if sendMessage != 0:
                    self.sendRecvMessageResends += 1
                remaining = remaining - 1
                sendMessage = time.perf_counter() + nextDelay
                self.s.settimeout(nextDelay)
                nextDelay = nextDelay * delayMultiplier

            try:
                replyMsg, ip, port = self.recvMessage()
            except SocketException as e:
                # We didn't get anything from the buffer or it was an invalid message.
                ip = None

            if ip is not None:
                # if the message is the one we are looking for.
                if ip == destinationIP and port == destinationPort and \
                        isinstance(replyMsg, dict) and \
                        'msgID' in replyMsg and replyMsg['msgID'] == msg['msgID']:
                    gotReply = True

        self.s.settimeout(0)

        if not gotReply:
            log("Raising Exception SocketException because failed to get valid respose after " + str(retries) +
                " retries with delay = " + str(delay) + " and delayMultiplier = " + str(delayMultiplier), "VERBOSE")
            raise SocketException("Failed to get valid respose.")

        if replyMsg['type'] == "Error":
            log("Raising Exception SocketException because reply message, with correct msgID was of type Error.",
                "VERBOSE")
            raise SocketException("Received Error Message: " + replyMsg['result'])

        del replyMsg['msgID']

        self.sendRecvMessageTime += time.perf_counter() - startTime
        return replyMsg

    def recvReplyMsgs(self):
        """Process all messages in socket recv buffer.

        For each msg waiting to be received, invoke the corresponding callback
        method in the msgProcessor.

        e.g. if msg of type "joinRequest" is received then call:
            msgProcessor.msgJoinReploy(ip, port, ipport, msg)

        if the callback method returns a reply msg then send the
        reply msg back to the IP/Port that send us the message.
        """
        msgQ = []
        more = True
        while more:
            try:
                msgQ.append(self.recvMessage())
            except SocketException as e:
                # BUG this assumes this exception is only thrown if buffer is
                # empty but it is also thrown if an invalid msg is received.
                more = False
            except Exception as e:
                log(str(type(e)) + " " + str(e), "ERROR")
                more = False
        for msg, ip, port in msgQ:
            methodName = "msg" + msg['type'][:1].capitalize() + msg['type'][1:]
            if methodName not in self.msgProcessorMethods:
                log(f"Cannot process msg of type {msg['type']}. No {methodName} method is found in msgProcessor.", "WARNING")
                continue

            callbackFunc = getattr(self.msgProcessor, methodName, None)

            ipport = formatIpPort(ip, port)
            reply = callbackFunc(ip, port, ipport, msg)
            if reply:
                if 'msgID' in msg:
                    reply['msgID'] = msg['msgID']
                try:
                    self.sendMessage(reply, ip, port)
                except Exception as e:
                    log(str(e), "ERROR")


class SocketException(Exception):
    """Raised by the Socket class."""
    pass

########################################################
# Network Utility Functions
########################################################


def resolve(hostname):
    """Return an IP address for hostname."""
    if not isinstance(hostname, str):
        log("Hostname/IP is type " + str(type(hostname)) + " but must be type str: {hostname}", "ERROR")
    if isValidIP(hostname):
        return (hostname)
    ip = socket.gethostbyname(hostname)
    if isValidIP(ip):
        return (ip)
    else:
        log(f"Hostname cannot be resolved or IP bad format: {hostname} ({ip}).", "ERROR")
        return False


def isValidIP(ip):
    """ Returns True if ip is valid IP address, otherwise returns false. """
    if not isinstance(ip, str):
        return False
    if not re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', ip):
        return False
    return True

# Check IP address format as needed by argparse module.


def argParseCheckIPFormat(ip):
    """ Returns ip if ip is a valid IP address, otherwise raises argparse.ArgumentTypeError exception. """

    if not isValidIP(ip):
        raise argparse.ArgumentTypeError(ip)
    return ip


def isValidPort(p):
    """ Returns True if p is valid port number, otherwise returns false. """

    if not isinstance(p, int):
        log("Port is type " + str(type(p)) + " but must be type int.", "ERROR")
        return False
    if p < 1 or p > 65000:
        log("Port is out of valid range 0-65000: " + str(p), "ERROR")
        return False
    return True


def formatIpPort(ip, port):
    """ Formats ip and port into a single string. eg. 127.168.32.11:20012 """
    return str(ip) + ":" + str(port)


def getDefaultIP():
    # return the default ip of the host.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
