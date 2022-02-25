"""ClientMap for Engine Test Map."""

from engine.log import log
import engine.log
import engine.clientmap


class ClientMap(engine.clientmap.ClientMap):
    """Log sprite data to screen."""

    def blitTileObject(self, destImage, offset, tileObject):
        """Extend engine.clientmap.ClientMap.blitTileObject()

        If tileObject is the player sprite then render a text
        log of the it to the to screen before the tile is
        rendered.
        """
        if tileObject['type'] == "player":
            textObject = {
                'x': 0, 'y': 32,
                'width': self['pixelWidth'], 'height': self['pixelHeight'],
                'text': {
                    'text': engine.log.dictToStr(tileObject),
                    'pixelsize': 12,
                    'vlaign': 'top',
                    'halign': 'left',
                    "color": "#ffffff",  # RGB
                    "fontfamily": 'Courier New',
                    "bgcolor": "#00000000",  # RGBA
                    "bgborderThickness": 0,
                    "antialiased": True
                    }
                }

            self.blitTextObject(destImage, offset, textObject)

        validUntil = super().blitTileObject(destImage, offset, tileObject)
        return validUntil
