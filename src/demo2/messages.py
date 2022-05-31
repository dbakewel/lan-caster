"""Client for Demo Game"""

import pygame
from pygame.locals import *

from engine.log import log
import engine.messages


class Messages(engine.messages.Messages):
    """Extends engine.messages"""

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
        self['messageDefinitions']['readyRequest'] = {}
        self['messageDefinitions']['readyReply'] = {}
        self['messageDefinitions']['run'] = {}
        self['messageDefinitions']['fire'] = {}