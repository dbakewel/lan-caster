"""Game Time

This module replaces the python built in time module and
adds a DELTA offset to the perf_counter function. This is
used by the client to sync it's time with the server. 
With this, the client can evaluate time outs set by the
server.
"""

import time

DELTA = 0


def set(serverTime):
    """Sets DELTA to add to time to sync with serverTime.

    Args:
        serverTime (float): server time in seconds.
    """
    global DELTA
    DELTA = serverTime - time.perf_counter()


def perf_counter():
    """Returns float of current time in seconds.

    This is is not clock time and is only relative to itself.

    Returns:
        counter (float): time in seconds.
    """
    global DELTA
    return time.perf_counter() + DELTA


def sleep(sec):
    """Function does not return until sec seconds have passed.

    Args:
        sec (float): seconds to sleep.
    """
    time.sleep(sec)
