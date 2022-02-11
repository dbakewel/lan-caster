"""Logging Module

Prints messages to command line window in a standard format.
"""

import inspect
import os
from datetime import datetime
import pprint

# global printing of debug and verbose log level messages on/off
LOGDEBUG = False
LOGVERBOSE = False

# global printing to logfile on/off
LOGFILE = False


def setLogLevel(debug=False, verbose=False):
    """Set the log levels that will be printed.

    Turn DEBUG and VERBOSE printing on or off. Both are off by default.
    Note, debug = True will set verbose = True.
    """

    global LOGDEBUG, LOGVERBOSE

    LOGDEBUG = debug
    if LOGDEBUG == True:
        verbose = True
    LOGVERBOSE = verbose
    log("DEBUG logging = " + str(LOGDEBUG) + ". VERBOSE logging = " + str(LOGVERBOSE), "INFO")


def setLogFile(filename=False):
    """Turn writing to file on or off. Off by default."""

    global LOGFILE

    LOGFILE = filename
    log("LOGFILE set to " + str(LOGFILE), "INFO")


def log(msg, level="INFO", depth=3):
    """Print msg to standard output.

    format: LogLevel Time Function: msg

    level should be one of DEBUG, VERBOSE, INFO, WARNING, ERROR, or FAILURE.
    Use log level as follows:
        DEBUG: Very detailed information, such as network messages.
        VERBOSE: Detailed information about normal function of program.
        INFO: Information about the normal functioning of the program. (default log level).
        WARNING: Something unexpected happened but normal program flow can continue.
        ERROR: Can not continue as planned.
        FAILURE: program will need to quit or initialize.

    Args:
        msg (str): The log message to print
        level (str): Log level of the msg. DEBUG and VERBOSE will only be printed if
            turned on using setLog Level.
        depth (int): When logging objects, this is the depth of nested objects to print.


    """

    global LOGDEBUG, LOGVERBOSE, LOGFILE

    if level == "DEBUG" and LOGDEBUG == False:
        return

    if level == "VERBOSE" and LOGVERBOSE == False:
        return

    try:
        # Get the execution frame of the calling function and use it to determine the calling filename and function name
        # This will fail if called from a python interactive shell.
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        filename = os.path.basename(module.__file__)
        modulename = module.__name__
        function = frame[0].f_code.co_name
        if function != '<module>':
            function = function + '()'
    except Exception as e:
        modulename = '-'
        filename = '-'
        function = '-'

    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    # format msg to be human readable
    if(isinstance(msg, dict)):
        msg = dictToStr(msg, depth)
    else:
        msg = str(msg)

    output = level + ' ' + str(time) + ' ' + str(modulename) + '.' + str(function) + ': ' + msg

    print(output)

    if LOGFILE:
        with open(LOGFILE, "a+") as f:
            f.write(output + "\n")


def dictToStr(object, depth=3):
    """return a human readable string version of a Dictionary object."""
    return '\n' + pprint.pformat(object, indent=4, width=80, depth=depth, sort_dicts=True)


def objectToDict(o):
    """return a Dictionary version of a python object with all methods and private attributes removed."""
    contents = {}
    for a in dir(o):
        if not a.startswith('__') and str(type(getattr(o, a))) != "<class 'method'>":
            contents[a] = getattr(o, a)
    return contents


def objectToStr(o, depth=3):
    """return a readable string version of a python object with all methods and private attributes removed."""
    return dictToStr(objectToDict(o), depth=depth)
