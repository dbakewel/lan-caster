"""Extends Demo ClientMap to add darkness and light circles for under map."""

import pygame
from pygame.locals import *
import math
import sys

from engine.log import log
import engine.clientmap
import engine.geometry as geo


class ClientMap(engine.clientmap.ClientMap):
    """Extends demo.clientmap.ClientMap"""

    def blitObject(self, destImage, offset, object):
        """FLAT REFLECTOR MECHANIC: Extend blitObject to render flat reflectors."""

        if object['name'] == "flatreflector":
            validUntil = sys.float_info.max
            rx1, ry1 = geo.project(object['anchorX'], object['anchorY'], object['rotation'], object['width'] / 2)
            rx2, ry2 = geo.project(object['anchorX'], object['anchorY'],
                                   object['rotation'] + math.pi, object['width'] / 2)
            pygame.draw.line(
                destImage,
                "#FFD700",
                (rx1 + offset[0],
                 ry1 + offset[1]),
                (rx2 + offset[0],
                 ry2 + offset[1]),
                width=2)
            return validUntil
        else:
            return super().blitObject(destImage, offset, object)

    def blitPolyObject(self, destImage, offset, polyObject,
                       lineColor=(0, 0, 0, 255), lineThickness=1):
        """FLAT REFLECTOR MECHANIC: Extend blitPolyObject and add use of color and line thickness in polyObject."""

        if 'lineColor' in polyObject:
            lineColor = polyObject['lineColor']
        if 'lineThickness' in polyObject:
            lineThickness = polyObject['lineThickness']

        return super().blitPolyObject(destImage, offset, polyObject, lineColor, lineThickness)
