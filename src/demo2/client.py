"""Client for demo2 Game"""

import pygame
from pygame.locals import *
import math

from engine.log import log
import engine.client


class Client(engine.client.Client):
    """Extends engine.client.Client"""

    def __init__(self, args):
        """Extends ___init__

        updates text defaults and has help text.
        """

        super().__init__(args)

        self['MARQUEETEXT'].update({
            "pixelsize": 24,
            "bgborderThickness": 8,
            "bgroundCorners": 10,
            "bgcolor": "#00000080",
            "bgbordercolor": "#00000080"
            })

        self['ACTIONTEXT'].update({
            "bgcolor": "#00000080",
            "bgbordercolor": "#00000080"
            })

        self['ready'] = False

        self['help'] = """Blue vs. Red Team Challenge (BETA VERSION)

LMB=Walk   R=Run   F=Fire   Space=Pick Up

WINNING: You win if your team has the most points when the time runs out. Your team gets points when:

Player on the other team dies (1 pt)
Player on your team opens a door (3 pts)
Other team’s idol arrives at your base (10 pts)

WALKING and RUNNING: Click Left Mouse Button (LMB) to walk. Press R while walking to run. Running requires endurance. Endurance recharges while not running. If endurance reaches 0 it will take longer to recharge.

ITEMS: A player can hold one weapon, one key, and one idol at the same time. Use Space to pick up items. Items cannot be dropped but keys vanish once used and the idol is returned when it is carried into your base.

WEAPONS: Press F to fire weapon at most once per second. The bow fires long distances and does heavy damage. Throwing weapons spread out but only cover a short distance. The wand sends out a very fast beam that can pass through all obstacles.

HEALTH: Your health is reduced if you are hit by weapons or come into contact with players from the other team, monsters or traps. Health slowly regenerates. If you die, you and all items are returned to their starting points. Praying to your idol (max once per minute) will restore your health and endurance.

PRESS ANY KEY WHEN READY :)"""

    def updateInterface(self):
        """Extend updateInterface()

        add help text during pre-game and scoreboard once player is ready.
        """

        # find the map that the server wants us to render.
        map = self['maps'][self['step']['mapName']]

        if self['ready'] == False:
            # don't display marqueeText unless player is ready
            if 'marqueeText' in self['step']:
                del self['step']['marqueeText']

            """ Render help text to screen. """
            text = self['MARQUEETEXT'].copy()
            text.update({
                'text': self['help'],
                "pixelsize": 16,
                "bgcolor": "#000000",
                "bgbordercolor": "#00ff00",
                "bgborderThickness": 4
                })
            textObject = {
                'x': self['screen'].get_width() * 0.1,
                'y': self['screen'].get_height() * 0.1,
                'width': self['screen'].get_width() * 0.8,
                'height': self['screen'].get_height() * 0.8,
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

        super().updateInterface()

    def processEvent(self, event):
        """Extend processEvent()

        Add game specific events for:
            ready (any key) and quit during the pre-game
            fire (f) and run (r) during game. Pass all other events to super()
        """
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
                    fireDestX, fireDestY = pygame.mouse.get_pos()
                    fireDestX -= self['mapOffset'][0]
                    fireDestY -= self['mapOffset'][1]
                    self['socket'].sendMessage({
                        'type': 'fire',
                        'fireDestX': fireDestX,
                        'fireDestY': fireDestY
                        })
                else:
                    super().processEvent(event)
            else:
                super().processEvent(event)
