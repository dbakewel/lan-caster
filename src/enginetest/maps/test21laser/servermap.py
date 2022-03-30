"""ServerMap for Engine Test Map."""
import random
import math

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """RAY MECHANIC

    RayEmitter

    RayReflector
    """

    def stepSpriteStartRayEmitter(self, sprite):
        """RAY MECHANIC: Remove polyline that is ray from last step """
        if sprite['name']=="ray":
            self.removeObject(sprite)

    def stepMapEndRayEmitter(self):
        """RAY MECHANIC: compute ray beam and monster hits. """

        # find ray emitters
        for emitter in self.findObject(name="rayemitter", returnAll=True):
            if not self.checkKeys(emitter, ['prop-rayDirection','prop-rayColor']):
                continue

            polyline = self.rayTrace(emitter['x'], emitter['y'], emitter['prop-rayDirection'])

            # for each segment of ray, see if a monster intersects it.
                # change monster to scull

            # move polyline to correct coord system and add to map
            for p in polyline:
                p['x'] -= emitter['x']
                p['y'] -= emitter['y']
            polyobject = {
                 "lineColor": emitter['prop-rayColor'],
                 "lineThickness": 5,
                 "name":"ray",
                 "polyline":polyline,
                 "x":emitter['x'],
                 "y":emitter['y']
                }
            self.checkObject(polyobject)
            self.addObject(polyobject)


    def rayTrace(self, x1, y1, r):
        """Create line segment from x,y in direction r until something is intersected.

        """
        x2,y2 = geo.project(x1,y1,r,self['pixelWidth']*self['pixelHeight'])

        for reflector in self.findObject(name="rayreflector", returnAll=True):
            a = self.getRayReflectorAngle(reflector)
            rx1,ry1 = geo.project(reflector['anchorX'],reflector['anchorY'], a,reflector['width']/2)
            rx2,ry2 = geo.project(reflector['anchorX'],reflector['anchorY'], a+math.pi,reflector['width']/2)
            log(f" {round(rx1)}, {round(ry1)}, {round(rx2)}, {round(ry2)}, {round(a,3)}, {round(math.degrees(a),3)}")

            intersectionPoint = geo.intersectLines(x1,y1,x2,y2,rx1,ry1,rx2,ry2)

            if intersectionPoint:
                x2=intersectionPoint[0]
                y2=intersectionPoint[1]


        return [{
                 "x":x1,
                 "y":y1
                }, 
                {
                 "x":x2,
                 "y":y2
                }]

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
        for reflector in self.findObject(name="rayreflector", returnAll=True):
            if self['startReflectorGID'] == False:
                self['startReflectorGID'] = reflector['gid']
            reflector['gid'] = random.randint(0, 7) + self['startReflectorGID']

        self['nextReflectorRotateTime'] = time.perf_counter() + 1

    def stepMapStartRayReflector(self):
        if self['nextReflectorRotateTime'] < time.perf_counter():
            self['nextReflectorRotateTime'] = 0

    def stepSpriteStartRayReflector(self, sprite):
        if sprite['name'] == "rayreflector" and self['nextReflectorRotateTime'] == 0:
            sprite['gid'] += 1
            if sprite['gid'] > self['startReflectorGID'] + 7:
                sprite['gid'] = self['startReflectorGID']

    def stepMapEndRayReflector(self):
        if self['nextReflectorRotateTime'] == 0:
            self['nextReflectorRotateTime'] = time.perf_counter() + 1
            self.setMapChanged()

    def getRayReflectorAngle(self, reflector):
        """ Given a reflector object, return the angle of the reflector based on its GID """
        return (math.pi / 2.0 + (reflector['gid'] - self['startReflectorGID'])) * 0.392699