"""Geometry Utility Functions.

This module provides several using geometry functions that can be used
with Tiled objects and object lists.

Note, all angles below are in radians, starting a 3 oclock and increasing clockwise.
You can convert between degrees and radians in your code as follows:

    import math
    r = math.radians(d)
    d = math.degrees(r)
"""

import math

from engine.log import log

##############################################
# BASIC GEOMETRY
##############################################


def angle(x1, y1, x2, y2):
    """ Returns angle from (x1,y1) and (x2,y2) in radians. """
    delta_x = x2 - x1
    delta_y = y2 - y1
    a = math.atan2(delta_y, delta_x)
    # atan2 return between -pi and pi. We want between 0 and 2pi with 0 degrees at 3 oclock
    return normalizeAngle(a)


def normalizeAngle(a):
    """ Returns angle a in the normalized range of 0 - 2pi. Angle a must be in radians. """
    while a < 0:
        a += math.pi * 2
    while a >= math.pi * 2:
        a -= math.pi * 2
    return a


def project(x, y, rad, dis):
    """
    Returns point (x',y') where angle from (x,y) to (x',y')
    is rad and distance from (x,y) to (x',y') is dis.
    """

    xp = x + dis * math.cos(rad)
    yp = y + dis * math.sin(rad)

    return xp, yp


def distance(x1, y1, x2, y2):
    """ Returns distance between (x1,y1) and (x2,y2) """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


##############################################
# GAME ENGINE SPECIFIC GEOMETRY
##############################################

def angleLabel(a):
    """ Returns the label ('Up', 'Down', 'Left', 'Right') of angle a """
    if a < math.pi / 4:
        label = 'Right'
    elif a < math.pi - math.pi / 4:
        label = 'Down'
    elif a < math.pi + math.pi / 4:
        label = 'Left'
    elif a < math.pi * 2 - math.pi / 4:
        label = 'Up'
    else:
        label = 'Right'
    return label


def sortRightDown(listOfGameObs, maxWidth, useAnchor=True):
    '''Sort list of game objects by y and then x.

    Do sort in place but list is also returned in case it is needed.

    Schwartzian Transform is used to speed up sort.
    https://gawron.sdsu.edu/compling/course_core/python_intro/intro_lecture_files/fastpython.html#setgetdel
    '''

    if useAnchor:  # use the anchor point to sort by
        listOfGameObs[:] = [(maxWidth * o['anchorY'] + o['anchorX'], o) for o in listOfGameObs]
    else:  # use middle of object rect to sort by
        listOfGameObs[:] = [(maxWidth * (o['y'] + o['height'] / 2) + o['x'] + o['width'] / 2, o) for o in listOfGameObs]
    listOfGameObs.sort(key=lambda x: x[0])
    listOfGameObs[:] = [o for (k, o) in listOfGameObs]

    return listOfGameObs

##############################################
# COLLISIONS
##############################################

def collides(o1, o2, overlap='partial', o1CollisionType=False, o2CollisionType=False):
    """Returns True if o1 overlaps o2 else returns False.

    Valid collisionType values are 'none', 'anchor', 'line', rect', and circle.

    Args:
        o1, o2 (dict): These are game objects which must contain at least: x, y, width, 
            height, anchoX, anchorY, and collisionType.
        overlap (str): overlap must be one of 'partial' or 'full'.
            If overlap == 'partial' then collides() returns True if any part of o1
            and o2 overlap. If overlap == 'full' the collides only returns True if
            o2 fully overlaps o1 (i.e. o1 is fully inside o2).
        o1CollisionType (bool, str): If False then use o1['collisionType']. If str
            then use o1CollisionType in place of o1['collisionType'].
        o2CollisionType (bool, str): If False then use o2['collisionType']. If str
            then use o2CollisionType in place of o2['collisionType'].
    Returns:
        Boolean.
    """
    if not o1CollisionType:
        o1CollisionType = o1['collisionType']
    if not o2CollisionType:
        o2CollisionType = o2['collisionType']

    if o1CollisionType == 'line' and o2CollisionType == 'line':
        log("line/line collisions not yet supported.", "WARNING")
        return False

    # do we need to reverse o1 and o2?
    if o2CollisionType == 'anchor' or \
            o1CollisionType == 'rect' and o2CollisionType == 'line' or \
            o1CollisionType == 'circle' and o2CollisionType == 'line' or \
            o1CollisionType == 'circle' and o2CollisionType == 'rect':
        o1, o2 = o2, o1
        o1CollisionType, o2CollisionType = o2CollisionType, o1CollisionType

    for o,ct in ((o1,o1CollisionType),(o2,o2CollisionType)):
        if ct == 'line' and 'polyline' not in o and 'polygon' not in o:
                log("collision type line requires polyline or polygon object.", "ERROR")
                return False
        if ct == 'circle' and o['width'] != o['height']:
                log("collision type circle assumes width == height which it does not.", "WARNING")
                return False

    return collidesFast(o1, o1CollisionType, o2, o2CollisionType, overlap)

def collidesFast(o1, o1CollisionType, o2, o2CollisionType, overlap='partial'):
    """Fast version of collides() with no error checking.

    Valid collisionType values are 'none', 'anchor', 'line', rect', and circle.

    If collisionType == 'line' then object must contain a polyline or polygon.

    The only supported collisionType combinations are:
        o1CollisionType     o1CollisionType
        ---------------     ---------------
        anchor              rect
        anchor              circle
        line                rect
        line                circle
        rect                rect
        rect                circle
        circle              circle
        All other combinations will return false.

    Args:
        o1, o2 (dict): These are game objects which must contain at least: x, y, width, 
            height, anchoX, anchorY.
        o1CollisionType, o2CollisionType (str): collisionType for o1 and o2
        overlap (str): overlap must be one of 'partial' or 'full'.
            If overlap == 'partial' then collides() returns True if any part of o1
            and o2 overlap. If overlap == 'full' the collides only returns True if
            o2 fully overlaps o1 (i.e. o1 is fully inside o2).
    Returns:
        Boolean.
    """

    if o1CollisionType == 'anchor' and o2CollisionType == 'rect':
        if o2['x'] <= o1['anchorX'] and o1['anchorX'] <= o2['x'] + o2['width'] and \
            o2['y'] <= o1['anchorY'] and o1['anchorY'] <= o2['y'] + o2['height']:
            return True

    elif o1CollisionType == 'anchor' and o2CollisionType == 'circle':
        if distance(o1['anchorX'],o1['anchorY'],o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) <= o2['width']/2:
            return True

    elif o1CollisionType == 'line' and o2CollisionType == 'rect':
        if 'polyline' in o1:
            lpts = o1['polyline']
        else:
            lpts = o1['polygon']
        if overlap=='partial':
            # if one of the points in the poly is inside the rect.
            for i in range(0,len(lpts)):
                if collidesFast({'anchorX': o1['x']+lpts[i]['x'], 'anchorY':o1['y']+lpts[i]['y']},'anchor', o2, 'rect'):
                    return True
            # if one of the line segments from line intersects rect.
            for i in range(1,len(lpts)):
                if intersectLineRect(
                    o1['x']+lpts[i-1]['x'], o1['y']+lpts[i-1]['y'], 
                    o1['x']+lpts[i]['x'], o1['y']+lpts[i]['y'], 
                    o2['x'], o2['y'], o2['width'], o2['height']):
                    return True
            # check last leg of polygon
            if 'polygon' in o1:
                if intersectLineRect(
                    o1['x']+lpts[0]['x'], o1['y']+lpts[0]['y'], 
                    o1['x']+lpts[len(lpts)-1]['x'], o1['y']+lpts[len(lpts)-1]['y'], 
                    o2['x'], o2['y'], o2['width'], o2['height']):
                    return True
        else:
            # if all of the points in the poly are inside the rect.
            for i in range(0,len(lpts)):
                if not collidesFast({'anchorX': o1['x']+lpts[i]['x'], 'anchorY':o1['y']+lpts[i]['y']},'anchor',o2,'rect'):
                    return False
            return True

    elif o1CollisionType == 'line' and o2CollisionType == 'circle':
        if 'polyline' in o1:
            lpts = o1['polyline']
        else:
            lpts = o1['polygon']
        if overlap=='partial':
            # if one of the points in the poly is inside the circle.
            for i in range(0,len(lpts)):
                if distance(o1['x']+lpts[0]['x'], o1['y']+lpts[0]['y'],
                        o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) <= o2['width']/2:
                    return True
            # if one of the line segments from line intersects circle.
            for i in range(1,len(lpts)):
                if intersectLineCircle(
                    o1['x']+lpts[i-1]['x'], o1['y']+lpts[i-1]['y'], 
                    o1['x']+lpts[i]['x'], o1['y']+lpts[i]['y'], 
                    o2['x'] + o2['width']/2,o2['y'] + o2['height']/2, o2['width']/2):
                    return True
            # check last leg of polygon
            if 'polygon' in o1:
                if intersectLineCircle(
                    o1['x']+lpts[0]['x'], o1['y']+lpts[0]['y'], 
                    o1['x']+lpts[len(lpts)-1]['x'], o1['y']+lpts[len(lpts)-1]['y'], 
                    o2['x'] + o2['width']/2,o2['y'] + o2['height']/2, o2['width']/2):
                    return True
        else:
            # if all of the points in the poly are inside the circle.
            for i in range(0,len(lpts)):
                if not distance(o1['x']+lpts[0]['x'], o1['y']+lpts[0]['y'],
                        o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) <= o2['width']/2:
                    return False
            return True

    elif o1CollisionType == 'rect' and o2CollisionType == 'rect':
        if overlap=='partial':
            if not o1['x']+o1['width'] < o2['x'] and \
                not o1['y']+o1['height'] < o2['y'] and \
                not o1['x'] > o2['x']+o2['width'] and \
                not o1['y'] > o2['y']+o2['height']:
                    return True
        else:  # o1 must be fully inside o2
            for pt in ((o1['x'], o1['y']),
                (o1['x'], o1['y']+o1['height']),
                (o1['x']+o1['width'], o1['y']),
                (o1['x']+o1['width'], o1['y']+o1['height'])):
                if not (o2['x'] <= pt[0] and pt[0] <= o2['x'] + o2['width'] and \
                    o2['y'] <= pt[1] and pt[1] <= o2['y'] + o2['height']):
                    return False
            return True

    elif o1CollisionType == 'rect' and o2CollisionType == 'circle':
        # first check rect/rect collision.
        if collidesFast(o1, 'rect',o2, 'rect',overlap=overlap):
            # quick check if rect anchor is inside circle
            if overlap=='partial':
                if collidesFast(o1, 'anchor',o2, 'circle'):
                    return True
                # now check if a line from the rect intersects circle.
                for line in ((o1['x'], o1['y'], o1['x']+o1['width'], o1['y']),
                    (o1['x'], o1['y'], o1['x'], o1['y']+o1['height']),
                    (o1['x']+o1['width'], o1['y'], o1['x']+o1['width'], o1['y']+o1['height']),
                    (o1['x'], o1['y']+o1['height'], o1['x']+o1['width'], o1['y']+o1['height'])):
                    if intersectLineCircle(line[0], line[1], line[2], line[3], \
                            o2['x'] + o2['width']/2,o2['y'] + o2['height']/2, o2['width']/2):
                        return True
            else:  # o1 must be fully inside o2
                # if all 4 rect points are inside circle.
                for pt in ((o1['x'], o1['y']),
                    (o1['x'], o1['y']+o1['height']),
                    (o1['x']+o1['width'], o1['y']),
                    (o1['x']+o1['width'], o1['y']+o1['height'])):
                    if not distance(pt[0],pt[1],o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) <= o2['width']/2:
                        return False
                return True

    elif o1CollisionType == 'circle' and o2CollisionType == 'circle':
        if overlap=='partial':
            if distance(o1['x'] + o1['width']/2,o1['y'] + o1['height']/2, \
                o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) < o1['width']/2 + o2['width']/2:
                return True
        else:
            if distance(o1['x'] + o1['width']/2,o1['y'] + o1['height']/2, \
                o2['x'] + o2['width']/2,o2['y'] + o2['height']/2) + o1['width']/2 < o2['width']/2:
                return True

    return False


##############################################
# INTERSECTIONS
##############################################


def intersectLineLine(x1, y1, x2, y2, x3, y3, x4, y4):
    '''Returns intersection point between line segments or None

    Returns intersection point between line segment ((x1,y1), (x2,y2)) and
    line segment ((x3,y3), (x4,y4)). If line segments do not intersect then
    return None.

    Based on code from https://gist.github.com/kylemcdonald/6132fc1c29fd3767691442ba4bc84018
    '''
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0:  # parallel
        return None
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    if ua < 0 or ua > 1:  # out of range
        return None
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    if ub < 0 or ub > 1:  # out of range
        return None
    x = x1 + ua * (x2 - x1)
    y = y1 + ua * (y2 - y1)
    return (x, y)


def intersectLineRect(x1, y1, x2, y2, rx, ry, rwidth, rheight):
    '''Returns list of intersection points between line segment and Rect or None

    Returns intersection point between line segment ((x1,y1), (x2,y2)) and
    rect (rx, ry, rwidth, rheight). If line segment does not intersect then
    return None.
    '''
    ipoints = []
    for pt in [(rx, ry, rx + rwidth, ry),
               (rx, ry, rx, ry + rheight),
               (rx + rwidth, ry, rx + rwidth, ry + rheight),
               (rx, ry + rheight, rx + rwidth, ry + rheight)]:
        ipt = intersectLineLine(x1, y1, x2, y2, pt[0], pt[1], pt[2], pt[3])
        if ipt:
            ipoints.append(ipt)

    if len(ipoints) == 0:
        return None
    return ipoints


def sgn(x):
    """Utily function used by other geometry functions"""
    if x < 0:
        return -1
    return 1


def intersectLineCircle(x1, y1, x2, y2, cx, cy, cradius):
    """Returns intersection point(s) between a line and circle, or None

    Return list of intersection points between line segment (x1,y1) and
    (x2,y2) circle centered at (cx,cy) with radius cradius, or None if line
    segment is entirely inside or outside circle.

    Based on http://mathworld.wolfram.com/Circle-LineIntersection.html
    """

    # move points so circle is at origin (0,0)
    x1 -= cx
    x2 -= cx
    y1 -= cy
    y2 -= cy

    # Does infinite line intersect circle
    dx = x2 - x1
    dy = y2 - y1
    dr = math.sqrt(dx**2 + dy**2)
    D = x1 * y2 - x2 * y1
    delta = (cradius * cradius) * dr**2 - D**2
    # delta < 0 -> no intersection
    # delta == 0 -> tangent (one point of intersection)
    # delta > 0 -> intersection (two points)
    if delta < 0:
        return None

    # now we know that the line to infinity intersects the circle.
    # but we need to figure out if the line segment touches or not
    # and if so what the points are.

    # compute intersection points (will be the same if delta==0)
    ix1 = (D * dy + sgn(dy) * dx * math.sqrt(delta)) / dr**2
    ix2 = (D * dy - sgn(dy) * dx * math.sqrt(delta)) / dr**2

    iy1 = (-1 * D * dx + abs(dy) * math.sqrt(delta)) / dr**2
    iy2 = (-1 * D * dx - abs(dy) * math.sqrt(delta)) / dr**2

    ipoints = []
    # only need to check if the x is on the line, since y will give same result.
    # note, this can result in no points if line segment is fully inside the circle.
    if (x1 < ix1 and ix1 < x2) or (x1 > ix1 and ix1 > x2):
        ipoints.append((ix1 + cx, iy1 + cy))
    if (x1 < ix2 and ix2 < x2) or (x1 > ix2 and ix2 > x2):
        ipoints.append((ix2 + cx, iy2 + cy))

    if len(ipoints) == 0:
        return None
    if delta == 0 and len(ipoints) == 2:
        # remove one of the duplicate points.
        ipoints.pop()

    return ipoints

def intersectRectRect(r1x, r1y, r1width, r1height, r2x, r2y, r2width, r2height):
    log("Not yet supported.", "WARNING")

def intersectRectCircle(rx, ry, rwidth, rheight, cx, cy, cradius):
    log("Not yet supported.", "WARNING")

def intersectCircleCircle(c1x, c1y, c1radius, c2x, c2y, c2radius):
    log("Not yet supported.", "WARNING")

##############################################
# VECTOR
##############################################


class Vector2D:
    """A two-dimensional vector with Cartesian coordinates.

    Based on https://scipython.com/book2/chapter-4-the-core-python-language-ii/examples/a-2d-vector-class/
    """

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):
        """Human-readable string representation of the vector."""
        return repr((round(self.x, 4), round(self.y, 4)))
        # return '{:g}i + {:g}j'.format(self.x, self.y)

    def __repr__(self):
        """Unambiguous string representation of the vector."""
        return repr((self.x, self.y))

    def dot(self, other):
        """The scalar (dot) product of self and other. Both must be vectors."""

        if not isinstance(other, Vector2D):
            raise TypeError('Can only take dot product of two Vector2D objects')
        return self.x * other.x + self.y * other.y
    # Alias the __matmul__ method to dot so we can use a @ b as well as a.dot(b).
    __matmul__ = dot

    def __sub__(self, other):
        """Vector subtraction."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """Vector addition."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        """Multiplication of a vector by a scalar."""

        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector2D(self.x * scalar, self.y * scalar)
        raise NotImplementedError('Can only multiply Vector2D by a scalar')

    def __rmul__(self, scalar):
        """Reflected multiplication so vector * scalar also works."""
        return self.__mul__(scalar)

    def __neg__(self):
        """Negation of the vector (invert through origin.)"""
        return Vector2D(-self.x, -self.y)

    def __truediv__(self, scalar):
        """True division of the vector by a scalar."""
        return Vector2D(self.x / scalar, self.y / scalar)

    def __mod__(self, scalar):
        """One way to implement modulus operation: for each component."""
        return Vector2D(self.x % scalar, self.y % scalar)

    def __abs__(self):
        """Absolute value (magnitude) of the vector. i.e. ||self|| """
        return math.sqrt(self.x**2 + self.y**2)

    def distance_to(self, other):
        """The distance between vectors self and other."""
        return abs(self - other)

    def to_polar(self):
        """Return the vector's components in polar coordinates."""
        return self.__abs__(), math.atan2(self.y, self.x)

    def project(self, other):
        """Return a vector that is the vector projected onto other.

        https://matthew-brett.github.io/teaching/vector_projection.html
        """
        return ((self @ other) / abs(other)**2) * other

    def unit(self):
        """Return a unit vector of the vector."""
        return self / abs(self)

    def ortho(self):
        """Return a vector that is orthogonal."""
        return Vector2D(self.y, -self.x)

    def reflect(self, other):
        """Return a vector that is reflected off other.

        Unlike other reflect code. The vector being reflected starts
        being pointed at other. The returned vector points away
        from other.

        https://bluebill.net/vector_reflection.html
        """
        normal = other.ortho().unit()
        return self - 2 * (self @ normal) * normal

##############################################
# TESTS
##############################################

if __name__ == '__main__':
    #v1 = Vector2D(2, 5/3)
    #v2 = Vector2D(3, -1.5)

    #v1 = Vector2D(0, 1)
    #v2 = Vector2D(0, 1)

    v1 = Vector2D(10, 10)
    v2 = Vector2D(1, 2)

    print('v1 = ', v1)
    print('repr(v2) = ', repr(v2))
    print('v1 + v2 = ', v1 + v2)
    print('v1 - v2 = ', v1 - v2)
    print('abs(v2 - v1) = ', abs(v2 - v1))
    print('-v2 = ', -v2)
    print('v1 * 3 = ', v1 * 3)
    print('7 * v2 = ', 7 * v1)
    print('v2 / 2.5 = ', v2 / 2.5)
    print('v1 % 1 = ', v1 % 1)
    print('v1.dot(v2) = v1 @ v2 = ', v1 @ v2)
    print('v1.distance_to(v2) = ', v1.distance_to(v2))
    print('v1 as polar vector, (r, theta) =', v1.to_polar())
    print('v1 project onto v2 = ', v1.project(v2))
    print('v2 project onto v1 = ', v2.project(v1))
    print('v1 unit vector = ', v1.unit())
    print('v2 unit vector = ', v2.unit())
    print('v1 ortho vector = ', v1.ortho())
    print('v2 ortho vector = ', v2.ortho())
    print('v1 refect off v2 = ', v1.reflect(v2))
