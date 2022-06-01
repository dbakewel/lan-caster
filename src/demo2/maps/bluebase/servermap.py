"""ServerMap for demo2 Game bluebase map"""

from engine.log import log
import demo2.servermap
import engine.server
import engine.time as time


class ServerMap(demo2.servermap.ServerMap):
    """Extends demo2.servermap.ServerMap"""

    def stepMapStartIdolCaptured(self):
        """if a player is in their base with the other teams idol then
        give 10 points and put idol back. (this code is blue base specific)
        """

        for sprite in self['sprites']:
            if sprite['type'] == 'player' and 'idol' in sprite and sprite['prop-team'] == 'blue' and sprite['idol']['prop-team'] == 'red':
                otherbase = engine.server.SERVER['maps']['redbase']
                otherbase.dropHoldable(sprite, 'idol')
                self.setSpriteSpeechText(sprite, "Red Idol Captured! 10 Points for Blue.", time.perf_counter() + 8)
                engine.server.SERVER['bluePoints'] += 10
