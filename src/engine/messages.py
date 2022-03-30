"""
Message Definition and Validation
"""

import engine.log
from engine.log import log


class Messages(dict):
    """Messages Class

    Messages defines and can validate what information can be sent over the network
    between the server and clients.

    Every message is a python dict type with at least a type attribute (i.e. field) and a
    string value.

    For example: { 'type': 'playerMove'}

    messageDefinitions below defines valid types and additional fields that must be included and
    can optionally be included based on type.

    Optional fields end in '_o' which marks the field as optional. The '_o' should not
    appear in the actual message, it is just a marker that the field is optional.
    For example, a joinRequest message with optional gameData field would be:

    {'type': 'joinRequest', 'game': 'Demo', 'playerDisplayName': 'Bob', 'gameData': ['some', 'data']}

    All fields have a defined type in the form of <type> or [<type>, min, max].
    <type> can be expressed as multiple acceptable types as (<type>,<type>,...)

    For fields of type 'str', min and max are the min length and max length of the string.
    """

    def __init__(self):
        """Define valid messages"""

        self['messageDefinitions'] = {
            # valid msg types and a dict their of required/optional msg fields (optional end with _o)
            # note, all msgs require their type to be included: eg. {'type': 'quitting'}
            'joinRequest': {
                'game': ['str', 1, 32],
                'playerDisplayName': ['str', 1, 16]
                },
            'joinReply': {
                'playerNumber': 'int',
                'serverSec': 'float',
                'testMode': 'bool'
                },
            'quitting': {},
            'playerMove': {
                'moveDestX': 'int',
                'moveDestY': 'int'
                },
            'playerAction': {},
            'step': {
                'gameSec': 'float',
                'mapName': ['str', 1, 32],
                'layerVisabilityMask': 'int',
                'sprites': 'list',
                'actionText_o': ['str', 1, 256],
                'marqueeText_o': ['str', 1, 512]
                },
            'Error': {
                'result': 'str'
                },

            # msgs used only for test mode
            'testTogglePlayerMoveChecking': {},
            'testPlayerPreviousMap': {},
            'testPlayerNextMap': {},
            'testPlayerJump': {
                'moveDestX': 'int',
                'moveDestY': 'int'
                },

            # msgs used only for connection setup through the connector.
            'addServer': {
                'serverName': ['str', 8, 64],
                'serverPrivateIP': ['str', 7, 15],
                'serverPrivatePort': 'int'
                },
            'serverAdded': {},
            'delServer': {
                'serverName': ['str', 8, 64]
                },
            'serverDeleted': {},
            'getConnetInfo': {
                'serverName': ['str', 8, 64],
                'clientPrivateIP': ['str', 7, 15],
                'clientPrivatePort': 'int'
                },
            'connectInfo': {
                'serverName': ['str', 8, 64],
                'clientPrivateIP': ['str', 7, 15],
                'clientPrivatePort': 'int',
                'serverPrivateIP': ['str', 7, 15],
                'serverPrivatePort': 'int',
                'clientPublicIP': ['str', 7, 15],
                'clientPublicPort': 'int',
                'serverPublicIP': ['str', 7, 15],
                'serverPublicPort': 'int'
                },
            'udpPunchThrough': {}
            }

    def __str__(self):
        return engine.log.objectToStr(self)

    def isValidMsg(self, msg):
        """ Returns True if msg is a valid message as defined by messageDefinitions, otherwise returns False. """

        if not isinstance(msg, dict):
            log("Msg is type " + str(type(msg)) + " but must be dict type: " + str(msg), "ERROR")
            return False
        if not 'type' in msg:
            log("Msg does not contain 'type' key: " + str(msg), "ERROR")
            return False

        unvalidedFields = list(msg.keys())
        # type is validated below as part of loop so does not need specific validation.
        unvalidedFields.remove('type')
        # msgId and replyData are always optional and have no specific format. So they are always valid if present.
        if 'msgID' in unvalidedFields:
            unvalidedFields.remove('msgID')
        if 'replyData' in unvalidedFields:
            unvalidedFields.remove('replyData')

        for msgtype, msgspec in self['messageDefinitions'].items():
            if msgtype == msg['type']:
                for fld, fldspec in msgspec.items():
                    if fld.endswith('_o'):
                        # remove magic suffix marking field as optional
                        fld = fld.rstrip('_o')
                        if fld not in msg:
                            # optional field is not present, which is valid.
                            continue
                    elif fld not in msg:
                        log("Msg does not contain required '" + fld + "' key: " + str(msg), "ERROR")
                        return False
                    if isinstance(fldspec, list):
                        if not isinstance(msg[fld], eval(fldspec[0])):
                            log("Msg '" + fld + "' key has value of type " + str(type(msg[fld])) +
                                " but expected " + fldspec[0] + ": " + str(msg), "ERROR")
                            return False
                        if fldspec[0] is 'str':
                            if len(msg[fld]) < fldspec[1] or len(msg[fld]) > fldspec[2]:
                                log("Msg '" + fld + "' key has a string value " + str(msg[fld]) +
                                    " with length out of range [" + str(fldspec[1]) + "," +
                                    str(fldspec[2]) + "] : " + str(msg), "ERROR")
                                return False
                        elif msg[fld] < fldspec[1] or msg[fld] > fldspec[2]:
                            log("Msg '" + fld + "' key has a value " + str(msg[fld]) +
                                " which is out of range [" + str(fldspec[1]) + "," +
                                str(fldspec[2]) + "] : " + str(msg), "ERROR")
                            return False
                    else:
                        if not isinstance(msg[fld], eval(fldspec)):
                            log("Msg '" + fld + "' key has value of type " + str(type(msg[fld])) +
                                " but expected " + fldspec + ": " + str(msg), "ERROR")
                            return False
                    unvalidedFields.remove(fld)
                # All fields defined for message type have now been examined and are valid
                if len(unvalidedFields):
                    # message has fields it should not have.
                    log("Msg contains field(s) " + str(unvalidedFields) +
                        " which is not defined for message type " + msg['type'] + ": " + str(msg), "ERROR")
                    for fld in unvalidedFields:
                        if fld.endswith('_o'):
                            log("Optional message fields should not include '_o' suffix in field name.", "WARNING")
                            break
                    return False
                else:
                    # message is valid and has no extra fields.
                    return True
        log("Msg 'type' key has value '" + str(msg['type']) + "' which is not known: " + str(msg), "ERROR")
        return False
