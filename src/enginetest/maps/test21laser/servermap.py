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

    def stepSpriteStartRayEmitter(self, sprite):
        """RAY MECHANIC: stepSpriteStart method

        Remove rays from sprite layer. They will be added again during the step.
        """
        if sprite['name']=="ray":
            self.removeObject(sprite)

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
        """Create line segment from x,y in direction r until something is intersected.

        """
        if maxRecurstion == 0:
            return False

        reflextion = False
        x2,y2 = geo.project(x1,y1,r,self['pixelWidth']*self['pixelHeight'])

        for reflector in self.findObject(name="rayreflector", returnAll=True, exclude=exclude):
            a = self.getRayReflectorAngle(reflector)
            rx1,ry1 = geo.project(reflector['anchorX'],reflector['anchorY'], a,reflector['width']/2)
            rx2,ry2 = geo.project(reflector['anchorX'],reflector['anchorY'], a+math.pi,reflector['width']/2)

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
            reflector['tilesetTileNumber'] = random.randint(0, 7)
            reflector['gid'] = self.findGid(reflector['tilesetName'], reflector['tilesetTileNumber'])

        self['nextReflectorRotateTime'] = time.perf_counter() + 1

    def stepMapStartRayReflector(self):
        """RAY REFLECTOR MECHANIC: stepMapStart method.

        Determine if it is time to rotate the reflectors.
        """
        if self['nextReflectorRotateTime'] < time.perf_counter():
            self['nextReflectorRotateTime'] = 0 # time has expired and reflextors should rotate.

    def stepSpriteStartRayReflector(self, sprite):
        """RAY REFLECTOR MECHANIC: stepSpriteStart method.

        If sprite is a reflector then rotate if it is time to do so.
        """
        if sprite['name'] == "rayreflector" and self['nextReflectorRotateTime'] == 0:
            sprite['tilesetTileNumber'] += 1
            if sprite['tilesetTileNumber'] > 7:
                sprite['tilesetTileNumber'] = 0
            sprite['gid'] = self.findGid(sprite['tilesetName'], sprite['tilesetTileNumber'])

    def stepMapEndRayReflector(self):
        """RAY REFLECTOR MECHANIC: stepMapEnd method.

        If reflectors were just rotated then set a new timeout for the next rotation.
        """
        if self['nextReflectorRotateTime'] == 0:
            self['nextReflectorRotateTime'] = time.perf_counter() + 1  # set next reflector rotation time.
            self.setMapChanged()

    def getRayReflectorAngle(self, reflector):
        """RAY REFLECTOR MECHANIC: init method.

        Given a reflector object, return the angle of the reflector.
        """
        return math.pi / 2.0 + reflector['tilesetTileNumber'] * 0.392699  # pi / 8 = 0.392699