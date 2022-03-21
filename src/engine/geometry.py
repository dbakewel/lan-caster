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


def objectContains(object, x, y, width=None, height=None):
    """ Returns True if x,y is inside object's rect else returns False.

    If width and height are provided then return True if any part of the 
    rect defined by x, y, width, height overlaps the object's rect.
    """
    if "ellipse" in object:
        pass  # not yet supported.
    elif "point" in object:
        if width is None or height is None:
            # if point object is same as point defined by x,y
            if x == object['x'] and y == object['y']:
                return True
        else: 
            # if point object is inside rect defined by x,y,width,height
            if x <= object['x'] and object['x'] <= x + wdith and \
                y <= object['y'] and object['y'] <= y + height:
                return True
    else:  # object is a rect. Tile objects ("gid") and text objects are also treated as rects.
        if width is None or height is None:
            # if rect object contains point defined by x,y
            if object['x'] <= x and x <= object['x'] + object['width'] and \
               object['y'] <= y and y <= object['y'] + object['height']:
                return True
        else:
            # if rect object overlaps rect defined by x,y,width,height
            if objectContains(object, x, y) or \
                objectContains(object, x+width, y) or \
                objectContains(object, x, y+height) or \
                objectContains(object, x+width, y+height) or \
                objectContains({'x': x, 'y': y, 'width': width, 'height': height}, object['x'], object['y']):
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
    '''
    Sort list of game objects by y and then x. Do sort in place but list is also returned in
    case it is needed.

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
