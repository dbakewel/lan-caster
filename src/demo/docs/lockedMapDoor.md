# Locked Map Door Mechanic

Implemented by: src/demo/maps/start/servermap.py

## Overview
The lockedMapDoor mechanic presents the player with a locked door. When the player first tries 
to use the door (assuming they don't have a key) then text appears to say the door is locked. 
When the player returns while holding the correct key (holding object) then the door graphic 
changes to opened and lets the user through.

## Requirements
Locked Mapdoor requires an object on the trigger layer with:
trigger['type'] == "lockedMapDoor".
trigger['prop-unlocks'] == <name of holdable object that unlocks door>

A layer with the graphic of only the locked door.
A layer with the graphic of only the unlocked door.

Locked Mapdoor also has all the same requirements of BOTH a PopUpText and MapDoor mechanic.

## Example Trigger Object
```
{   'anchorX': 336.0,
    'anchorY': 41.3,
    'height': 25.3333,
    'mapName': 'start',
    'name': '',
    'properties': {   'destMapName': 'end',
                      'destReference': 'door2',
                      'text': 'The door is locked.',
                      'textReference': 'door2LockedText',
                      'unlocks': 'green key'},
    'type': 'lockedMapDoor',
    'width': 30,
    'x': 321,
    'y': 28.6
}
```

## Functionality
If a sprite enters the Locked Mapdoor trigger, while NOT holding the object
that unlocks the door, then the lockedMapDoor behaves the same as popUpText.

The first time a sprite enters the lockedMapDoor trigger, while holding the object
that unlocks the door, then the 3 things happen:
1) lockedMapDoor has it's type changed to mapDoor. From this point on the trigger operates
as a mapDoor.
2) The layer that contains the closed door graphic is hidden
3) The layer with the open door graphic is shown.

## Limitations
In the implementation, the layers which are hidden and shown (door graphics)
are hard coded. This data could be moved to the trigger properties if a more
general implementation is needed.