"""Client for Demo Game"""

import pygame
from pygame.locals import *
import math

from engine.log import log
import engine.client


class Client(engine.client.Client):
    """Extends engine.client"""

    def __init__(self, args):
        """Extends ___init__ and updates text defaults."""

        super().__init__(args)

        self['MARQUEETEXT'].update({
            "pixelsize": 24,
            "bgborderThickness": 8,
            "bgroundCorners": 10,
            })

        self['ready'] = False

        self['help'] = """Blue vs. Red Team Challenge

LMB=Move   R=Rum   F=Fire Space=Pick Up 

WINNING: You win if your team has the most points when the time runs out. 1 point each time a player on the other team dies. 10 points each time the other team’s idol arrives at your base.

WALKING and RUNNING: Click Left Mouse Button (LMB) where you want to walk to. Press R to run while moving. Stop running by using the LMB again. Running requires endurance. Endurance recharges while not running. If endurance reaches 0 it will take longer to recharge.

ITEMS: A player can hold one weapon, one key, and one idol at the same time. Use Space to pick up items. Items cannot be dropped but keys vanish once used and the idol is returned when you carry it into your base. All items are returned to where you found them when you die.

WEAPONS: Press F to fire weapon at most once per second. The bow fires long distances and does heavy damage. The throwing stars spread out but only cover a short distance. The wand sends out a very fast beam that can pass through all obstacles.

HEALTH: Your health is reduced if you are hit by weapons or come into contact with players from the other team. Monsters and traps can also cause damage. Health slowly regenerates. If you die, you and all items are returned to their starting points.

PRESS ANY KEY WHEN READY :)"""

    def updateInterface(self):
        """Extend updateInterface()"""
        
        super().updateInterface()

        # find the map that the server wants us to render.
        map = self['maps'][self['step']['mapName']]

        if self['ready'] == False:
            """ Render help text to screen. """
            text = self['MARQUEETEXT'].copy()
            text.update({
                'text': self['help'],
                "pixelsize": 16
                })
            textObject = {
                'x': self['screen'].get_width() * 0.2,
                'y': self['screen'].get_height() * 0.2,
                'width': self['screen'].get_width() * 0.6,
                'height': self['screen'].get_height() * 0.6,
                'text': text,
                }
        else:
            # render score board to screen.
            text = self['MARQUEETEXT'].copy()
            text.update({
                'text': f"Time={math.floor(self['step']['timeRemaining']/60.0)}:{str(math.floor(self['step']['timeRemaining']%60.0)).rjust(2, '0')} Blue={self['step']['bluePoints']}  Red={self['step']['redPoints']}  Health={round(self['step']['health'])}  Endurance={round(self['step']['endur'],1)}",
                'pixelsize': 24,
                'valign': 'top',
                "bgborderThickness": 4,
                "bgroundCorners": 4,
                })
            textObject = {
                'x': 0, 
                'y': -4,
                'width': self['screen'].get_width(), 
                'height': self['screen'].get_height(),
                'text': text
            }
        map.blitTextObject(self['screen'], (0, 0), textObject, mapRelative=False)


    def processEvent(self, event):
        """Extend engine.processEvent()"""
        if self['ready'] == False:
            if event.type == QUIT:
                quit()
            elif event.type == pygame.TEXTINPUT:
                self['socket'].sendRecvMessage({'type': 'readyRequest'})
                self['ready'] = True
                log("Player Ready.")
        else:
            if event.type == pygame.TEXTINPUT:
                if event.text == 'r':
                    self['socket'].sendMessage({'type': 'run'})
                elif event.text == 'f':
                    self['socket'].sendMessage({'type': 'fire'})
                else:
                    super().processEvent(event)
            else:
                super().processEvent(event)
