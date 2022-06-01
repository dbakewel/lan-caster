"""Client for demo2 Game"""

import pygame
from pygame.locals import *

from engine.log import log
import engine.messages


class Messages(engine.messages.Messages):
    """Extends engine.messages.Messages"""

    def __init__(self):
        """Extends ___init__ and new flds and message types."""

        super().__init__()

        self['messageDefinitions']['step'].update({
            'bluePoints': 'int',
            'redPoints': 'int',
            'health': 'float',
            'endur': 'float',
            'timeRemaining': 'float'
            })
        self['messageDefinitions']['readyRequest'] = {}  # player has read help text and is ready to play
        self['messageDefinitions']['readyReply'] = {}  # server has reviced players ready message.
        self['messageDefinitions']['run'] = {}  # player has requested to run.
        self['messageDefinitions']['fire'] = {  # player has requested to fire.
            'fireDestX': 'int',
            'fireDestY': 'int'
            }
