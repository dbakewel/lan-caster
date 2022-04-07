"""Map Step Processor"""
from engine.log import log
import engine.map
import engine.geometry as geo
import engine.time as time
import engine.server


class StepMap(engine.map.Map):
    '''Class which implements stepping the game forward in time.

    The StepMap class is responsible for calling the game logic, located
    in sub-classes, which takes the game forward one step in time. It
    does this by finding methods that match the naming format and then
    calling those methods in a very specific order during each step.
    Using the various methods name formats, a sub-class can implement
    many different game mechanics.

    The method name formats StepMap looks for are as follows. Except
    for init<MechanicName>() the methods are called in this order
    during each step:

        0) init<MechanicName>(): Called only once when the map is loaded.

        1) stepMapStart<MechanicName>(): Called once at the start of each step.

        2) trigger<MechanicName>(trigger, sprite): Called for every trigger
            and sprite combination where the sprite anchor point is inside
            the trigger, with two exceptions:
                1) if the trigger and sprite are the same object;
                2) if the sprite is in trigger['doNotTrigger'] array.

        3) stepMove<MechanicName>(sprite): Called for every object
            on the sprite layer which contains:
                sprite['move']['type'] == '<MechanicName>'

        4) stepMapEnd<MechanicName>(): Called once at the end of each step.

    <MechanicName> is replaced with the name of the game mechanic
    being implemented.

    Besides implementing the step methods above, a game mechanic
    may need to extend, override, or implement other methods.
    See examples of implementing game mechanics in engine.servermap and
    the various servermap sub-classes of the enginetest and demo games.

    The Server normally only calls the engine.stepmap.StepMap.StepMap()
    method if at least one player is on the map. So game logic stops for
    maps with no players.

    Also, the Server class normally calls stepServerStart() before the
    maps process thier steps and calls stepServerEnd() after
    all maps have processed their steps.
    See engine.server.Server.stepServer() for details.
    '''

    def __init__(self, tilesets, mapDir):
        """Extents engine.map.Map.__init__()

        Finds and calls the init<MechanicName>() methods.
        Finds all methods that match each step method type format.
        Sorts all methods by type and priority.
        """

        super().__init__(tilesets, mapDir)

        self['stepsProcessed'] = 0
        self['stepProcessingTime'] = 0

        self['stepMethodTypes'] = (
            "stepMapStart",
            "trigger",
            "stepMove",
            "stepMapEnd")

        self['stepMethodPriority'] = {}
        for stepMethodType in self['stepMethodTypes']:
            self['stepMethodPriority'][stepMethodType] = {'default': 50}

        self['stepMethods'] = {}

        # Find and call init* methods in this instance (methods could be from this class or a subclass)
        # Note, one important job of init methods is to add to
        # self['stepMethodPriority'] before the step methods are found and sorted
        # below.
        self['initMethods'] = sorted([func for func in dir(self) if callable(getattr(self, func))
                                      and func.startswith("init") and len(func) > len("init")])
        for initMethodName in self['initMethods']:
            initMethod = getattr(self, initMethodName, None)
            initMethod()

        # find step methods in this instance and sort by type and priority
        for stepMethodType in self['stepMethodTypes']:
            self['stepMethods'][stepMethodType] = [func for func in dir(self) if callable(
                getattr(self, func)) and func.startswith(stepMethodType)]
            # if stepMethod is not in priority list then add it with the default priority
            for methodName in self['stepMethods'][stepMethodType]:
                if methodName not in self['stepMethodPriority'][stepMethodType]:
                    self['stepMethodPriority'][stepMethodType][methodName] = self['stepMethodPriority'][stepMethodType]['default']
            self['stepMethods'][stepMethodType].sort(
                key=lambda methodName: self['stepMethodPriority'][stepMethodType][methodName])

        log(f"Map '{self['name']}' Methods:\n{self.getAllMethodsStr()}", "VERBOSE")

    def getAllMethodsStr(self):
        '''Return a multi-line human readable string of all map init*, step*, and trigger* methods.'''

        allMethods = sorted([func for func in dir(self) if callable(getattr(self, func))
                             and not func.startswith("__")])

        stepMethodsStr = ""

        for i in range(len(self['stepMethodTypes'])):
            methodType = f"{self['stepMethodTypes'][i]}*"
            if "Move" in self['stepMethodTypes'][i]:
                methodType += "(sprite)"
            elif self['stepMethodTypes'][i].startswith("trigger"):
                methodType += "(trigger, sprite)"
            else:
                methodType += "()"
            stepMethodsStr += f"{methodType:32}"
        stepMethodsStr += "\n"
        for i in range(len(self['stepMethodTypes'])):
            stepMethodsStr += f"{'------------------------':32}"
        stepMethodsStr += "\n"

        j = 0
        keepGoing = True
        while keepGoing:
            keepGoing = False
            for i in range(len(self['stepMethodTypes'])):
                methodName = ""
                if j < len(self['stepMethods'][self['stepMethodTypes'][i]]):
                    methodName = self['stepMethods'][self['stepMethodTypes'][i]][j]
                    allMethods.remove(methodName)
                    methodName += f"/{self['stepMethodPriority'][self['stepMethodTypes'][i]][methodName]}"
                    keepGoing = True
                stepMethodsStr += f"{methodName:32}"
            stepMethodsStr += "\n"
            j += 1

        initMethods = []
        getMethods = []
        setMethods = []
        delMethods = []
        otherMethods = []
        for method in allMethods:
            if method.startswith('init'):
                initMethods.append(method)
            elif method.startswith('get'):
                getMethods.append(method)
            elif method.startswith('set'):
                setMethods.append(method)
            elif method.startswith('del'):
                delMethods.append(method)
            else:
                otherMethods.append(method)

        otherMethodsStr = f"\n{'init*':32}{'get*':32}{'set*':32}{'del*':32}{'other':32}\n"
        otherMethodsStr += f"{'------------------------':32}{'------------------------':32}{'------------------------':32}{'------------------------':32}{'------------------------':32}\n"
        for i in range(max(len(initMethods), len(getMethods), len(setMethods), len(otherMethods))):
            if i < len(initMethods):
                otherMethodsStr += f"{initMethods[i]:32}"
            else:
                otherMethodsStr += f"{'':32}"
            if i < len(getMethods):
                otherMethodsStr += f"{getMethods[i]:32}"
            else:
                otherMethodsStr += f"{'':32}"
            if i < len(setMethods):
                otherMethodsStr += f"{setMethods[i]:32}"
            else:
                otherMethodsStr += f"{'':32}"
            if i < len(delMethods):
                otherMethodsStr += f"{delMethods[i]:32}"
            else:
                otherMethodsStr += f"{'':32}"
            if i < len(otherMethods):
                otherMethodsStr += f"{otherMethods[i]:32}"
            else:
                otherMethodsStr += f"{'':32}"
            otherMethodsStr += '\n'

        return otherMethodsStr + "\n" + stepMethodsStr

    def addStepMethodPriority(self, stepMethodType, stepMethodName, priority):
        """Set the priority of a step method.

        This is normally used by subclass init* methods to prioritize step
        methods before finding and sorting them.

        Args:
            stepMethodType (str): One of self['stepMethodPriority']
            stepMethodName (str): A method name that starts with stepMethodType
            priority (int): The priority of stepMethodName.Lower number is
                higher priority.
        """
        if stepMethodType not in self['stepMethodPriority']:
            log(f"{stepMethodType} is not a valid stepMethodType.", "WARNING")
            return
        self['stepMethodPriority'][stepMethodType][stepMethodName] = priority

    def getStatsAvgMs(self):
        """Returns the avg ms to process each stepMap for this map."""
        if self['stepsProcessed'] == 0:
            return 0.0
        return  (self['stepProcessingTime']/self['stepsProcessed']) * 1000

    ########################################################
    # STEP DISPATCHER (Order of steps matters!)
    ########################################################

    def stepMap(self):
        """Move the map forward one step in time"""

        startTime = time.perf_counter()

        # call all self.stepMapStart*() methods
        for methodName in self['stepMethods']['stepMapStart']:
            method = getattr(self, methodName, None)
            method()

        # for each sprite, find all triggers sprite is inside and call
        # corresponding trigger* method.
        for sprite in self['sprites']:
            self.stepTriggers(sprite)

        # call all selfstepMove*(sprite) methods for each sprite
        # with a corresponding sprite['move']['type']
        for methodName in self['stepMethods']['stepMove']:
            method = getattr(self, methodName, None)
            for sprite in self['sprites']:
                if 'move' in sprite and sprite['move']['type'] == methodName[8:]:
                    method(sprite)

        # call all self.stepMapEnd*() methods
        for methodName in self['stepMethods']['stepMapEnd']:
            method = getattr(self, methodName, None)
            method()

        self['stepsProcessed'] += 1
        self['stepProcessingTime'] += (time.perf_counter()-startTime)

    def stepTriggers(self, sprite):
        """Process all triggers for a sprite.

        Find all triggers (objects on the trigger layer) that contain this
        sprite's anchor and call the corresponding trigger* method.

        The search excludes the sprite itself from the search
        since objects may be on the sprite and trigger layer at the
        same time.

        A trigger may optionally contain an array of sprite references.
        Sprites in that list will not set off the trigger:
        e.g. trigger['doNotTrigger'] = [sprite1, sprite2, ...]

        Args:
            sprite (dict): Tiled object from the sprite layer.
        """

        # get a list of all triggers that the sprite is colliding with.
        # The next line was removed and replaced with the lines below to increase performance.
        #triggers = self.findObject(collidesWith=sprite,objectList=self['triggers'],returnAll=True,exclude=sprite)
        triggers = []
        for t in self['triggers']:
            # using collidesFast() assumes t objects have collision types of rect or circle. Others will return False
            if t != sprite and geo.collidesFast(sprite,sprite['collisionType'], t, t['collisionType']):
                triggers.append(t)

        # remove any triggers that do not have trigger* methods to call.
        # log warning since this should not happen.
        for trigger in triggers:
            triggerMehodName = self.getTriggerMethodName(trigger)
            # if trigger is not in priority list then log error and remove it
            if triggerMehodName not in self['stepMethodPriority']['trigger']:
                log(
                    f"ServerMap does not have method named {triggerMehodName} for trigger type {trigger['type']}.",
                    "ERROR")
                triggers.remove(trigger)

        # sort trigger method names by priority (lower first)
        triggers.sort(key=lambda trigger: self['stepMethodPriority']['trigger'][self.getTriggerMethodName(trigger)])

        # call each triggers method. e.g. trigger['type'] == 'mapDoor' will call triggerMapDoor(trigger, sprite)
        for trigger in triggers:
            # if the sprite is in the trigger's doNotTrigger list then do nothing.
            if 'doNotTrigger' in trigger and sprite in trigger['doNotTrigger']:
                continue
            triggerMethod = getattr(self, self.getTriggerMethodName(trigger), None)
            stopOtherTriggers = triggerMethod(trigger, sprite)
            if stopOtherTriggers:
                break  # do not process any more triggers for this sprite on this step.

    def getTriggerMethodName(self, trigger):
        """Convert a trigger type  to method

        eg. trigger['type'] == "mapDoor" would return "triggerMapDoor"

        Args:
            trigger (dict): Tiled object that is on this maps trigger layer.

        Returns:
            str: The name of the method used to process the trigger.
        """
        return "trigger" + trigger['type'][:1].capitalize() + trigger['type'][1:]
