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
        self['ready'] = False

    def updateInterface(self):
        """Extend updateInterface()"""
        
        super().updateInterface()

        map = self['maps'][self['step']['mapName']]
        if self['ready'] == False:
            """ Render help text to screen. """
            text = self['MARQUEETEXT'].copy()
            text['text'] = "This is help text.\n\nPress space when ready. :)"
            textObject = {
                'x': self['screen'].get_width() * 0.2,
                'y': self['screen'].get_height() * 0.2,
                'width': self['screen'].get_width() * 0.6,
                'height': self['screen'].get_height() * 0.6,
                'text': text
                }

            # find the map that the server wants us to render.
            
            map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)
        else:
            textObject = {
            'x': 0, 'y': 0,
            'width': self['screen'].get_width(), 'height': self['screen'].get_height(),
            'text': {
                'text': f"Points: Blue = {self['step']['bluePoints']}  Red = {self['step']['redPoints']}  Health = {round(self['step']['health'])}  Endurance = {round(self['step']['endur'],1)}",
                'pixelsize': 24,
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


    def processEvent(self, event):
        """Extend engine.processEvent()"""
        if self['ready'] == False:
            if event.type == QUIT:
                quit()
            elif event.type == pygame.TEXTINPUT:
                if event.text == ' ':
                    self['socket'].sendRecvMessage({'type': 'readyRequest'})
                    self['ready'] = True
                    log("Player Ready.")
        else:
            if event.type == pygame.TEXTINPUT:
                if event.text == 'r':
                    self['socket'].sendMessage({'type': 'run'})
            else:
                super().processEvent(event)
