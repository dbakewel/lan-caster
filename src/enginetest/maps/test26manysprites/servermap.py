"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """This servermap tests servers performance."""

    def stepMapStartChase(self):
        """CHASE MECHANIC: stepMapStart method.

        Have the monster chast the player.
        """
        for sprite in self['sprites']:
            if sprite['type'] == "monster":
                if "move" not in sprite:
                    player = self.findObject(type="player")
                    self.setMoveLinear(sprite, player['anchorX'], player['anchorY'], 10)