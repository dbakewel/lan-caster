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

    FLAT REFLECTOR

    CIRCLE REFLECTOR (all code is part of the RAY EMITTER raytrace() method.)

    """

    def initRayEmitter(self):
        """RAY MECHANIC: init method

        Find GID of skull using tileObject on reference layer
        """
        self['skullObject'] = self.findObject(name='skull', objectList=self['reference'])

    def stepMapStartRayEmitter(self):
        """RAY MECHANIC: stepMapStart method

        Remove rays from sprite layer. They will be added back at the end of the step.
        """
        for ray in self.findObject(name="ray", returnAll=True):
            self.removeObject(ray)

    def stepMapEndRayEmitter(self):
        """RAY MECHANIC: stepMapEnd method

        compute ray and monster hits.
        """
        # find ray emitters
        for emitter in self.findObject(name="rayemitter", returnAll=True):
            if not self.checkKeys(emitter, ['prop-rayDirection', 'prop-rayColor', 'prop-rayThickness']):
                continue

            polyline = self.rayTrace(emitter['x'], emitter['y'], emitter['prop-rayDirection'])
            if not polyline:
                continue

            # convert polyline from map origin to emitter/polyobject (x,y) origin
            for p in polyline:
                p['x'] -= emitter['x']
                p['y'] -= emitter['y']

            polyobject = {
                "collisionType" : 'line',
                "lineColor": emitter['prop-rayColor'],
                "lineThickness": emitter['prop-rayThickness'],
                "name": "ray",
                "polyline": polyline,
                "x": emitter['x'],
                "y": emitter['y']
                }

            # kill (change name and tile) any raytargets that collide with the ray.
            for sprite in self.findObject(name='raytarget', returnAll=True):
                # we need to call collides() (rather than using colloidesWith in findObject()) because
                # we want to use collisionType='circle' for raytargets rather than their default of 'anchor'.
                if geo.collidesFast(polyobject, 'line', sprite, 'circle'):
                    for attribute in ('name', 'gid', 'tilesetName', 'tilesetTileNumber'):
                        sprite[attribute] = self['skullObject'][attribute]

            self.checkObject(polyobject)
            self.addObject(polyobject)

    def rayTrace(self, x1, y1, r, exclude=False, maxRecurstion=10):
        """RAY MECHANIC: Create a polyline from x,y in direction r.

        Takes collisions and reflectors into account.

        Returns a polyline dict of the form:
            [{"x":x1, "y":y1},{"x":x2, "y":y2},...]
        where all values are ralative to map orgin. To use in a polyline Object
        values must be converted so all points are relative to object x,y.
        """
        if maxRecurstion == 0:
            return False

        reflextion = False
        x2, y2 = geo.project(x1, y1, r, self['pixelWidth'] * self['pixelHeight'])

        """
        intersections is an array of tules that contain points of intersection between the ray
        and other game objects. Form (x, y, distance from (x1,y1) to (x,y), type, object )
        """
        intersections = []

        # find all intersections with outOfBounds
        for o in self['outOfBounds']:
            ipts = geo.intersectLineRect(x1, y1, x2, y2, o['x'], o['y'], o['width'], o['height'])
            if ipts:
                for i in range(len(ipts)):
                    intersections.append(ipts[i] + (geo.distance(x1, y1, ipts[i][0], ipts[i][1]), "stop", o))

        # find all intersections with map edges
        for l in (
                (0, 0, self['pixelWidth'], 0),  # top
                (0, 0, 0, self['pixelHeight']),  # left
                (self['pixelWidth'], 0, self['pixelWidth'], self['pixelHeight']),  # right
                (0, self['pixelHeight'], self['pixelWidth'], self['pixelHeight'])  # bottom
                ):
            ipt = geo.intersectLineLine(x1, y1, x2, y2, l[0], l[1], l[2], l[3],)
            if ipt:
                intersections.append(ipt + (geo.distance(x1, y1, ipt[0], ipt[1]), "stop", None))

        # find all intersections with sprites (based on collisionType) with special code for reflectors.
        for o in self.findObject(returnAll=True, exclude=exclude):
            if o['name'] == 'flatreflector':
                rx1, ry1 = geo.project(o['anchorX'], o['anchorY'], o['rotation'], o['width'] / 2)
                rx2, ry2 = geo.project(o['anchorX'], o['anchorY'], o['rotation'] + math.pi, o['width'] / 2)
                ipt = geo.intersectLineLine(x1, y1, x2, y2, rx1, ry1, rx2, ry2)
                if ipt:
                    intersections.append(ipt + (geo.distance(x1, y1, ipt[0], ipt[1]), "flatreflector", o))
            elif o['name'] == 'circlereflector':
                ipts = geo.intersectLineCircle(x1, y1, x2, y2, o['anchorX'], o['anchorY'], o['width'] / 2)
                if ipts:
                    if len(ipts) == 2:  # if ray did not start inside o and did not simply hit tangent to it.
                        for i in range(len(ipts)):
                            intersections.append(ipts[i] +
                                                 (geo.distance(x1, y1, ipts[i][0], ipts[i][1]), "circlereflector", o))
            elif o['collisionType'] == 'rect':
                ipts = geo.intersectLineRect(x1, y1, x2, y2, o['x'], o['y'], o['width'], o['height'])
                if ipts:
                    if len(ipts) == 2:  # if ray did not start inside o
                        for i in range(len(ipts)):
                            intersections.append(ipts[i] + (geo.distance(x1, y1, ipts[i][0], ipts[i][1]), "stop", o))

        # sort intersections by the distance from the x1,y1 (i.e. the start of the ray)
        intersections.sort(key=lambda ipt: ipt[2])

        # trace the ray from it's start until it hits something that stops or reflects it.
        for ipt in intersections:
            if ipt[3] == "stop":
                # hit something that is hard stop, such as map edge or sprite with collisionType ray can pass through.
                break
            elif ipt[3] == "flatreflector" or ipt[3] == "circlereflector":
                # compute reflection angle and make recursive call
                o = ipt[4]
                if ipt[3] == "flatreflector":
                    rx1, ry1 = geo.project(o['anchorX'], o['anchorY'], o['rotation'], o['width'] / 2)
                    rx2, ry2 = geo.project(o['anchorX'], o['anchorY'], o['rotation'] + math.pi, o['width'] / 2)
                    reflextionVector = geo.Vector2D(ipt[0] - x1, ipt[1] - y1).reflect(
                        geo.Vector2D(rx2 - rx1, ry2 - ry1))
                elif ipt[3] == "circlereflector":
                    reflextionVector = geo.Vector2D(ipt[0] - x1, ipt[1] - y1).reflect(
                        geo.Vector2D(o['anchorX'] - ipt[0], o['anchorY'] - ipt[1]).ortho())
                maxRecurstion -= 1
                reflextion = self.rayTrace(ipt[0], ipt[1], geo.angle(0, 0, reflextionVector.x, reflextionVector.y),
                                           exclude=o, maxRecurstion=maxRecurstion)
                break

        x2 = ipt[0]
        y2 = ipt[1]

        if reflextion:
            polyline = [{"x": x1, "y": y1}] + reflextion
        else:
            polyline = [{"x": x1, "y": y1}, {"x": x2, "y": y2}]

        return polyline

    ########################################################
    # FLAT REFLECTOR MECHANIC
    ########################################################

    def initFlatReflector(self):
        """FLAT REFLECTOR MECHANIC: init method.

        Set reflector half circle rotation speed in seconds
        Set all reflectors to a random rotation to start.
        """
        self['rayReflectorRotationSpeed'] = 20  # seconds for half rotation
        for flatreflector in self.findObject(name="flatreflector", returnAll=True):
            flatreflector['startRotation'] = math.radians(random.randint(0, 179))
            self.setFlatReflectorRotation(flatreflector)

    def stepMapStartFlatReflector(self):
        """FLAT REFLECTOR MECHANIC: stepMapStart method.

        Rotate reflector based on secondsPerHalfRotation second cycle.
        """
        for sprite in self.findObject(name='flatreflector', returnAll=True):
            self.setFlatReflectorRotation(sprite)
            self.setMapChanged()

    def dropHoldable(self, sprite):
        """FLAT REFLECTOR MECHANIC: extend EXTEND HOLDABLE MECHANIC

        reset reflextor start position when dropped so it picks up where
        it was when it was picked up.
        """
        if sprite['holding']['name'] == "flatreflector":
            sprite['holding']['startRotation'] = sprite['holding']['rotation'] - math.pi * (time.perf_counter()/self['rayReflectorRotationSpeed'] % 1)
            self.setFlatReflectorRotation(sprite['holding'])

        super().dropHoldable(sprite)

    def setFlatReflectorRotation(self, flatreflector):
        """FLAT REFLECTOR MECHANIC: set rotation of flat reflector."""
        flatreflector['rotation'] = flatreflector['startRotation'] + math.pi * \
            (time.perf_counter() / self['rayReflectorRotationSpeed'] % 1)

    ########################################################
    # PUSH MECHANIC (Only init part)
    ########################################################
    def initPush(self):
        """PUSH MECHANIC: init method.

        Copy (by reference) all pushable sprites to the outOfBounds layer.

        Note, only part of pushable code included here so there are some objects 
        with collisionType == rect in this test map.
        """
        for pushable in self.findObject(type="pushable", returnAll=True):
            pushable['collisionType'] = "rect"
