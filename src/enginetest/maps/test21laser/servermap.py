"""ServerMap for Engine Test Map."""
import random

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """RAY MECHANIC

    RayEmitter

    RayReflector

        
    """

    stepMapStartRayEmitter(self):
        """RAY MECHANIC: Remove any polylines that are rays from last step """

    stepMapEndRayEmitter(self):
        """RAY MECHANIC: compute ray beam and monster hits. """

        # find ray emitters

        # trace ray beam

        # for each segment of ray, see if a monster intersets it.
            # change monster to scull


    rayTrace(self, x, y, r):
        """Create line segment from x,y in direction r until something is intersected.

        """
            # find all intersection points between objects and ray

            # sort all intersections points from closest to x,y to farest

            # walk intersection points until a stop or a reflector is found.

            # create line segment

            # if reflector is found then trace the reflection

            # return line segment and any segments from reflection


    def initRayReflector(self):
        """RAY MECHANIC: init method.

        Set all reflectors to a random rotation to start.
        """
        self['startReflectorGID'] = False
        for reflector in self.findObject(name="reflector", returnAll=True):
            if self['startReflectorGID'] == False:
                self['startReflectorGID'] = reflector['gid']
            reflector['gid'] = random.randint(0, 7) + self['startReflectorGID']

        self['nextReflectorRotateTime'] = time.perf_counter() + 1

    def stepSpriteStartRayReflector(self, sprite):
        if sprite['name'] == "reflector" and self['nextReflectorRotateTime'] < time.perf_counter():
            sprite['gid'] += 1
            if sprite['gid'] > self['startReflectorGID'] + 7:
                sprite['gid'] = self['startReflectorGID']

    def stepMapEndRayReflector(self):
        if self['nextReflectorRotateTime'] < time.perf_counter():
            self['nextReflectorRotateTime'] = time.perf_counter() + 1
            self.setMapChanged()

    def getRayReflectorAngle(self, reflector):
        """ Given a reflector object, return the angle of the reflector based on its GID """
        return (reflector['gid'] - self['startReflectorGID']) * 22.5