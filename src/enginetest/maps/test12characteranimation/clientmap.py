"""ClientMap for Engine Test Map."""

from engine.log import log
import engine.clientmap


class ClientMap(engine.clientmap.ClientMap):
    """Change player sprite's tile to a horse."""

    def blitTileObject(self, destImage, offset, tileObject):
        """Extend engine.clientmap.ClientMap.blitTileObject()

        If tileObject is the player sprite then change it's
        tile to a tile which has character data, in this case
        the horse is used.
        """
        if tileObject['type'] == "player":
            tileObject['tilesetName'] = "horse-golden"
            tileObject['tilesetTileNumber'] = 34
            tileObject['gid'] = self.findGid(tileObject['tilesetName'], tileObject['tilesetTileNumber'])
            # The horse tile is bigger than the wizard so we need to reset it's XY based on it's anchor point
            self.setObjectLocationByAnchor(tileObject, tileObject['anchorX'], tileObject['anchorY'])

        validUntil = super().blitTileObject(destImage, offset, tileObject)

        return validUntil
