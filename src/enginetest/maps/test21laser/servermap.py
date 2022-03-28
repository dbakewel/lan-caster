"""ServerMap for Engine Test Map."""
import random

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """LASER MECHANIC

        
    """


    """MIRROR MECHANIC

        
    """

    def initMirror(self):
        """LASER MECHANIC: init method.

        Set all mirrors to a random rotation to start.
        """
        self['startMirrorGID'] = False
        for mirror in self.findObject(name="mirror", returnAll=True):
            if self['startMirrorGID'] == False:
                self['startMirrorGID'] = mirror['gid']
            mirror['gid'] = random.randint(0, 7) + self['startMirrorGID']

        self['nextMirrorRotateTime'] = time.perf_counter() + 1

    def mirrorAngle(self, mirror):
        """ Given a mirror object, return the angle of the mirror based on its GID """
        return (mirror['gid'] - self['startMirrorGID']) * 22.5

    def stepSpriteStartMirror(self, sprite):
        if sprite['name'] == "mirror" and self['nextMirrorRotateTime'] < time.perf_counter():
            sprite['gid'] += 1
            if sprite['gid'] > self['startMirrorGID'] + 7:
                sprite['gid'] = self['startMirrorGID']

    def stepMapEndMirror(self):
        if self['nextMirrorRotateTime'] < time.perf_counter():
            self['nextMirrorRotateTime'] = time.perf_counter() + 1
            self.setMapChanged()