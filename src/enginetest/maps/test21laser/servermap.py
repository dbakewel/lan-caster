"""ServerMap for Engine Test Map."""
import random
import math

import engine.time as time
from engine.log import log
import engine.servermap
import engine.geometry as geo


class ServerMap(engine.servermap.ServerMap):
    """This servermap implements ray emitter and reflector mechanics.

    RAY EMITTER

    RAY REFLECTOR

    """

    def stepMapStartRayEmitter(self):
        """RAY MECHANIC: stepMapStart method

        Remove rays from sprite layer. They will be added again during the step.
        """
        for ray in self.findObject(name="ray", returnAll=True):
            self.removeObject(ray)

    def stepMapEndRayEmitter(self):
        """RAY MECHANIC: stepMapEnd method

        compute ray and monster hits.

        note, this is done at the end of the step in case reflectors are rotating.
        """
        # find ray emitters
        for emitter in self.findObject(name="rayemitter", returnAll=True):
            if not self.checkKeys(emitter, ['prop-rayDirection','prop-rayColor','prop-rayThickness']):
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
                 "lineThickness": emitter['prop-rayThickness'],
                 "name":"ray",
                 "polyline":polyline,
                 "x":emitter['x'],
                 "y":emitter['y']
                }
            self.checkObject(polyobject)
            self.addObject(polyobject)


    def rayTrace(self, x1, y1, r, exclude=False, maxRecurstion=10):
        """Create line segment from x,y in direction r.

        """
        if maxRecurstion == 0:
            return False

        reflextion = False
        x2,y2 = geo.project(x1,y1,r,self['pixelWidth']*self['pixelHeight'])

        for reflector in self.findObject(name="rayreflector", returnAll=True, exclude=exclude):
            rx1,ry1 = geo.project(reflector['anchorX'],reflector['anchorY'], reflector['rotation'],reflector['width']/2)
            rx2,ry2 = geo.project(reflector['anchorX'],reflector['anchorY'], reflector['rotation']+math.pi,reflector['width']/2)

            intersectionPoint = geo.intersectLines(x1,y1,x2,y2,rx1,ry1,rx2,ry2)

            if intersectionPoint:
                x2=intersectionPoint[0]
                y2=intersectionPoint[1]

                reflextionVector = geo.Vector2D(x2-x1,y2-y1).reflect(geo.Vector2D(rx2-rx1,ry2-ry1))
                maxRecurstion -= 1 
                reflextion = self.rayTrace(x2, y2, geo.angle(0, 0, reflextionVector.x, reflextionVector.y), exclude=reflector, maxRecurstion=maxRecurstion)

        if reflextion:
            polyline = [{"x":x1, "y":y1}] + reflextion
        else:
            polyline = [{"x":x1, "y":y1}, {"x":x2, "y":y2}]

        return polyline

            # find all intersection points between objects and ray

            # sort all intersections points from closest to x,y to farest

            # walk intersection points until a stop or a reflector is found.

            # create line segment

            # if reflector is found then trace the reflection

            # return line segment and any segments from reflection

    ########################################################
    # RAY REFLECTOR MECHANIC
    ########################################################

    def initRayReflector(self):
        """RAY REFLECTOR MECHANIC: init method.

        Set all reflectors to a random rotation to start.
        """
        for reflector in self.findObject(name="rayreflector", returnAll=True):
            reflector['startRotation'] = math.radians(random.randint(0, 179))
            reflector['rotation'] = reflector['startRotation']

    def stepSpriteStartRayReflector(self, sprite):
        """RAY REFLECTOR MECHANIC: stepSpriteStart method.

        Rotate reflector based on 10 second cycle.
        """
        if sprite['name'] == 'rayreflector':
            secondsPerHalfRotation = 10
            sprite['rotation'] = sprite['startRotation'] + math.pi * (time.perf_counter()/secondsPerHalfRotation % 1)

    def stepMapEndRayReflector(self):
        self.setMapChanged()  # reflectors rotate every step so map changes every step.