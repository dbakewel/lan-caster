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


def sleep(sec=False, until=False):
    """Function does not return until a specified time has passed.

    one of 'sec' or 'until' must be provided. 'sec' will
    use the OS sleep function while 'until' will busy 
    wait for greater accuracy.

    Args:
        sec (float): seconds to sleep.
        until (float): time to sleep until
    """
    if sec:
        time.sleep(sec)

    if until:
        global DELTA
        while time.perf_counter() + DELTA < until:
            pass
