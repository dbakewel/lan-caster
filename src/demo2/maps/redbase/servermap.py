"""ServerMap for demo2 Game redbase map"""

from engine.log import log
import demo2.servermap
import engine.server
import engine.time as time


class ServerMap(demo2.servermap.ServerMap):
    """Extends demo2.servermap.ServerMap"""

    def stepMapStartIdolCaptured(self):
        """if a player is in their base with the other teams idol then
        give 10 points and put idol back. (this code is red base specific)
        """

        for sprite in self['sprites']:
            if sprite['type'] == 'player' and 'idol' in sprite and sprite['prop-team'] == 'red' and sprite['idol']['prop-team'] == 'blue':
                otherbase = engine.server.SERVER['maps']['bluebase']
                otherbase.dropHoldable(sprite, 'idol')
                self.setSpriteSpeechText(sprite, "Blue Idol Captured! 10 Points for Red.", time.perf_counter() + 8)
                engine.server.SERVER['redPoints'] += 10
