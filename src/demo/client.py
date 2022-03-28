"""Client for Demo Game"""

import pygame
from pygame.locals import *

from engine.log import log
import engine.client


class Client(engine.client.Client):
    """Extends engine.client"""

    def __init__(self, args):
        """Extends ___init__ and updates text defaults."""

        super().__init__(args)

        self['MARQUEETEXT'].update({
            'pixelsize': 36,
            "fontfamily": "Old London",
            "color": "#1d232b",
            "bgcolor": "#fafacd",
            "bgbordercolor": "#47361e",
            "bgborderThickness": 6,
            "bgroundCorners": 12
            })

        log(f"Client __init__ complete. Client Attributes:{engine.log.dictToStr(self, 1)}", "VERBOSE")
