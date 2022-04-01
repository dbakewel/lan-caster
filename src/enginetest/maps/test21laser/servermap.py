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

    CIRCLE REFLECTOR

    """
    def initRayEmitter(self):
        """RAY MECHANIC: init method

        Find GID of skull using tileObject on reference layer
        """
        self['skullObject'] = self.findObject(name='skull', objectList=self['reference'])

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
            if not polyline:
                continue

            # kill (change name and tile) any raytargets that intersect the ray.
            # for each segment of ray, see if a raytarget intersects it.
            for i in range(1,len(polyline)):
                for sprite in self.findObject(name='raytarget', returnAll=True):
                    if geo.intersectLineRect(polyline[i-1]['x'],polyline[i-1]['y'], polyline[i]['x'],polyline[i]['y'], 
                        sprite['x'],sprite['y'], sprite['width'], sprite['height']):
                        for att in ('name','gid','tilesetName','tilesetTileNumber'):
                            sprite[att] = self['skullObject'][att]

            # convert polyline from map origin to emitter/polyobject (x,y) origin
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
        """Create a polyline from x,y in direction r.

        Takes collisions and reflectors into account.

        Returns a polyline dict of the form:
            [{"x":x1, "y":y1},{"x":x2, "y":y2},...]
        where all values are ralative to map orgin. To use in a polyline Object
        values must be converted so all points are relative to object x,y.
        """
        if maxRecurstion == 0:
            return False

        reflextion = False
        x2,y2 = geo.project(x1,y1,r,self['pixelWidth']*self['pixelHeight'])

        # determine how many inBounds objects ray starts inside of.
        obs = self.findObject(x=x1,y=y1, objectList=self['inBounds'], returnAll=True)
        inBoundsCount = len(obs)
        # determine how many outOfBounds objects ray starts inside of.
        obs = self.findObject(x=x1,y=y1, objectList=self['outOfBounds'], returnAll=True)
        outOfBoundsCount = len(obs)

        """
        intersections is an array of tules that contain points of intersection between the ray 
        and other game objects. Form (x, y, distance from (x1,y1) to (x,y), type, enter/exit, object )
        """
        intersections = []
        # find all intersections with inBounds
        for o in self['inBounds']:
            ipts = geo.intersectLineRect(x1,y1, x2, y2, o['x'],o['y'], o['width'], o['height'])
            if ipts:
                for i in range(len(ipts)):
                    ipts[i] = ipts[i] + (geo.distance(x1,y1,ipts[i][0],ipts[i][1]),)
                # if ray did not start inside o
                if len(ipts) == 2:
                    if ipts[0][2] < ipts[1][2]:
                        intersections.append(ipts[0] + ("inBounds","enter",o))
                        intersections.append(ipts[1] + ("inBounds","exit",o))
                    else:
                        intersections.append(ipts[1] + ("inBounds","enter",o))
                        intersections.append(ipts[0] + ("inBounds","exit",o))
                else:
                    intersections.append(ipts[0] + ("inBounds","exit",o))

        # find all intersections with outOfBounds
        for o in self['outOfBounds']:
            ipts = geo.intersectLineRect(x1,y1, x2, y2, o['x'],o['y'], o['width'], o['height'])
            if ipts:
                for i in range(len(ipts)):
                    ipts[i] = ipts[i] + (geo.distance(x1,y1,ipts[i][0],ipts[i][1]),)
                # if ray did not start inside o
                if len(ipts) == 2:
                    if ipts[0][2] < ipts[1][2]:
                        intersections.append(ipts[0] + ("outOfBounds","enter",o))
                        intersections.append(ipts[1] + ("outOfBounds","exit",o))
                    else:
                        intersections.append(ipts[1] + ("outOfBounds","enter",o))
                        intersections.append(ipts[0] + ("outOfBounds","exit",o))
                else:
                    intersections.append(ipts[0] + ("outOfBounds","exit",o))

        # find all intersections with map edges
        for l in (
            (0,0,self['pixelWidth'],0), # top
            (0,0,0,self['pixelHeight']),  # left
            (self['pixelWidth'],0,self['pixelWidth'],self['pixelHeight']),  # right
            (0,self['pixelHeight'],self['pixelWidth'],self['pixelHeight'])  # bottom
            ):
            ipt = geo.intersectLines(x1,y1, x2, y2, l[0],l[1],l[2],l[3],)
            if ipt:
                ipt = ipt + (geo.distance(x1,y1,ipt[0],ipt[1]),)
                intersections.append(ipt + ("stop",None,None))

        # find all intersections with sprites (based on collisionType) including reflectors.
        for o in self.findObject(returnAll=True, exclude=exclude):
            if o['name'] == 'flatreflector':
                rx1,ry1 = geo.project(o['anchorX'],o['anchorY'], o['rotation'],o['width']/2)
                rx2,ry2 = geo.project(o['anchorX'],o['anchorY'], o['rotation']+math.pi,o['width']/2)

                ipt = geo.intersectLines(x1,y1, x2, y2, rx1,ry1,rx2,ry2)
                if ipt:
                    ipt = ipt + (geo.distance(x1,y1,ipt[0],ipt[1]),)
                    intersections.append(ipt + ("flatreflector",None,o))
            elif o['name'] == 'circlereflector':
                ipts = geo.intersectLineCircle(x1, y1, x2, y2,o['anchorX'],o['anchorY'], o['width']/2)
                if ipts:
                    for i in range(len(ipts)):
                        ipts[i] = ipts[i] + (geo.distance(x1,y1,ipts[i][0],ipts[i][1]),)
                    # if ray did not start inside o and did not simply hit tangent to it.
                    if len(ipts) == 2:
                        if ipts[0][2] < ipts[1][2]:
                            intersections.append(ipts[0] + ("circlereflector",None,o))
                        else:
                            intersections.append(ipts[1] + ("circlereflector",None,o))
            elif o['collisionType'] == 'rect':
                ipts = geo.intersectLineRect(x1,y1, x2, y2, o['x'],o['y'], o['width'], o['height'])
                if ipts:
                    for i in range(len(ipts)):
                        ipts[i] = ipts[i] + (geo.distance(x1,y1,ipts[i][0],ipts[i][1]),)
                    # if ray did not start inside o
                    if len(ipts) == 2:
                        if ipts[0][2] < ipts[1][2]:
                            intersections.append(ipts[0] + ("stop",None,o))
                        else:
                            intersections.append(ipts[1] + ("stop",None,o))

        # sort intersections by the distance from the x1,y1 (i.e. the start of the ray)
        intersections.sort(key=lambda ipt: ipt[2])

        # trace the ray from it's start until it hits something that stops or reflects it.
        for ipt in intersections:
            if ipt[3] == "stop":
                # hit something that is hard stop, such as map edge or sprite with collisionType ray can pass through.
                break
            elif ipt[3] == "inBounds":
                if ipt[4] == "enter":
                    inBoundsCount +=1
                else:
                    inBoundsCount -=1
                    if inBoundsCount == 0 and outOfBoundsCount != 0:
                        # exited an inbound rect while also inside an outOfBounds rect.
                        break
            elif ipt[3] == "outOfBounds":
                if ipt[4] == "enter":
                    outOfBoundsCount +=1
                    if inBoundsCount == 0:
                        # hit an outOfBounds that is not covered by an inBounds.
                        break
                else:
                    outOfBoundsCount -=1
            elif ipt[3] == "flatreflector" or ipt[3] == "circlereflector":
                o = ipt[5]
                if ipt[3] == "flatreflector":
                    rx1,ry1 = geo.project(o['anchorX'],o['anchorY'], o['rotation'],o['width']/2)
                    rx2,ry2 = geo.project(o['anchorX'],o['anchorY'], o['rotation']+math.pi,o['width']/2)
                    reflextionVector = geo.Vector2D(ipt[0]-x1,ipt[1]-y1).reflect(geo.Vector2D(rx2-rx1,ry2-ry1))
                elif ipt[3] == "circlereflector":
                    reflextionVector = geo.Vector2D(ipt[0]-x1,ipt[1]-y1).reflect(
                        geo.Vector2D(o['anchorX']-ipt[0],o['anchorY']-ipt[1]).ortho() )
                maxRecurstion -= 1 
                reflextion = self.rayTrace(ipt[0], ipt[1], geo.angle(0, 0, reflextionVector.x, reflextionVector.y), exclude=o, maxRecurstion=maxRecurstion)
                break

        x2 = ipt[0]
        y2 = ipt[1]

        if reflextion:
            polyline = [{"x":x1, "y":y1}] + reflextion
        else:
            polyline = [{"x":x1, "y":y1}, {"x":x2, "y":y2}]

        return polyline

    ########################################################
    # FLAT REFLECTOR MECHANIC
    ########################################################

    def initRayReflector(self):
        """FLAT REFLECTOR MECHANIC: init method.

        Set reflector half circle rotation speed in seconds
        Set all reflectors to a random rotation to start.
        """
        self['rayReflectorRotationSpeed'] = 20
        for reflector in self.findObject(name="flatreflector", returnAll=True):
            reflector['startRotation'] = math.radians(random.randint(0, 179))
            reflector['rotation'] = reflector['startRotation']

    def stepSpriteStartRayReflector(self, sprite):
        """FLAT REFLECTOR MECHANIC: stepSpriteStart method.

        Rotate reflector based on secondsPerHalfRotation second cycle.
        """
        if sprite['name'] == 'flatreflector':
            sprite['rotation'] = sprite['startRotation'] + math.pi * (time.perf_counter()/self['rayReflectorRotationSpeed'] % 1)

    def stepMapEndRayReflector(self):
        self.setMapChanged()  # reflectors rotate every step so map changes every step.

    def delHoldable(self, sprite):
        """FLAT REFLECTOR EXTEND HOLDABLE MECHANIC: reset reflextor start position when dropped so it picks up where it was when it was picked up."""

        if sprite['holding']['name'] == "flatreflector":
            sprite['holding']['startRotation'] = sprite['holding']['rotation'] - math.pi * (time.perf_counter()/self['rayReflectorRotationSpeed'] % 1)

        super().delHoldable(sprite)

    ########################################################
    # FLAT REFLECTOR MECHANIC
    ########################################################
    def initPush(self):
        """PUSH MECHANIC: init method.

        Copy (by reference) all pushable sprites to the outOfBounds layer.

        Note, only part of pushable code included here so there are some objects with collisionType == rect.
        """
        for pushable in self.findObject(type="pushable", returnAll=True):
            pushable['collisionType'] = "rect"