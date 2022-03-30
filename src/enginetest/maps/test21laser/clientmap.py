"""Extends Demo ClientMap to add darkness and light circles for under map."""

import pygame
from pygame.locals import *

from engine.log import log
import engine.clientmap


class ClientMap(engine.clientmap.ClientMap):
    """Extends demo.clientmap.ClientMap

    This class makes the map render polylines with color and thickness provided
    in the poly object.
    """

    def blitPolyObject(self, destImage, offset, polyObject,
                       lineColor=(0, 0, 0, 255), lineThickness=1):
        """Extend blitPolyObject and add use of color in polyObject."""

        if 'lineColor' in polyObject:
            lineColor = polyObject['lineColor']
        if 'lineThickness' in polyObject:
            lineThickness = polyObject['lineThickness']

        return super().blitPolyObject(destImage, offset, polyObject, lineColor, lineThickness)