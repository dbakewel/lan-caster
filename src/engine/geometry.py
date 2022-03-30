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


def objectContains(object, x, y, width=0, height=0):
    """ Returns True if rect defined by x, y, width, height overlaps object's rect else returns False.

    Note, a rect with width=0 and height==0 is a point.
    """

    if width == 0 and height == 0:
        # if object's rect contains point defined by x,y
        if object['x'] <= x and x <= object['x'] + object['width'] and \
           object['y'] <= y and y <= object['y'] + object['height']:
            return True
    else:
        # if object's rect overlaps rect defined by x, y, width, height
        if objectContains({'x': x, 'y': y, 'width': width, 'height': height}, object['x'], object['y']) or \
                objectContains(object, x, y) or \
                objectContains(object, x + width, y) or \
                objectContains(object, x, y + height) or \
                objectContains(object, x + width, y + height):
            return True

    return False


def angleLable(a):
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


def normalizeAngle(a):
    """ Returns angle a in the normalized range of 0 - 2pi. Angle a must be in radians. """
    while a < 0:
        a += math.pi * 2
    while a >= math.pi * 2:
        a -= math.pi * 2
    return a


def angle(x1, y1, x2, y2):
    """ Returns angle from (x1,y1) and (x2,y2) in radians. """
    delta_x = x2 - x1
    delta_y = y2 - y1
    a = math.atan2(delta_y, delta_x)
    # atan2 return between -pi and pi. We want between 0 and 2pi with 0 degrees at 3 oclock
    return normalizeAngle(a)


def distance(x1, y1, x2, y2):
    """ Returns distance between (x1,y1) and (x2,y2) """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def project(x, y, rad, dis):
    """
    Returns point (x',y') where angle from (x,y) to (x',y')
    is rad and distance from (x,y) to (x',y') is dis.
    """

    xp = x + dis * math.cos(rad)
    yp = y + dis * math.sin(rad)

    return xp, yp


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

def intersectLines(x1,y1, x2,y2, x3,y3, x4,y4):
    '''Returns intersection point between line segments or None
    Returns intersection point between line segment ((x1,y1), (x2,y2)) and 
    line segment ((x3,y3), (x4,y4)). If line segments do not intersect then 
    return None.
    Based on code from https://gist.github.com/kylemcdonald/6132fc1c29fd3767691442ba4bc84018
    '''
    denom = (y4-y3)*(x2-x1) - (x4-x3)*(y2-y1)
    if denom == 0: # parallel
        return None
    ua = ((x4-x3)*(y1-y3) - (y4-y3)*(x1-x3)) / denom
    if ua < 0 or ua > 1: # out of range
        return None
    ub = ((x2-x1)*(y1-y3) - (y2-y1)*(x1-x3)) / denom
    if ub < 0 or ub > 1: # out of range
        return None
    x = x1 + ua * (x2-x1)
    y = y1 + ua * (y2-y1)
    return (x,y)

class Vector2D:
    """A two-dimensional vector with Cartesian coordinates.

    Based on https://scipython.com/book2/chapter-4-the-core-python-language-ii/examples/a-2d-vector-class/
    """

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):
        """Human-readable string representation of the vector."""
        return repr((round(self.x,4), round(self.y,4)))
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
            return Vector2D(self.x*scalar, self.y*scalar)
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
        return ((self @ other)/abs(other)**2)*other

    def unit(self):
        """Return a unit vector of the vector."""
        return self / abs(self)

    def ortho(self):
        """Return a vector that is orthogonal."""
        return Vector2D(self.y, -self.x)

    def reflect(self, other):
        """Return a vector that is reflected off other

        https://bluebill.net/vector_reflection.html
        """
        normal = other.ortho().unit()
        return self - 2 * (self @ normal) * normal


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
    print('v1.distance_to(v2) = ',v1.distance_to(v2))
    print('v1 as polar vector, (r, theta) =', v1.to_polar())
    print('v1 project onto v2 = ', v1.project(v2))
    print('v2 project onto v1 = ', v2.project(v1))
    print('v1 unit vector = ', v1.unit())
    print('v2 unit vector = ', v2.unit())
    print('v1 ortho vector = ', v1.ortho())
    print('v2 ortho vector = ', v2.ortho())
    print('v1 refect off v2 = ', v1.reflect(v2))