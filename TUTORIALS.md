[ [ABOUT](README.md) | [SETUP and RUN](SETUP.md) | [CREATE A GAME](CREATE.md) | **TUTORIALS** | [CONTRIBUTING](CONTRIBUTING.md) ]

# LAN-Caster - Tutorials

The following links and videos provide an overview of how to use LAN-Caster to build your own game. More will be added as content is created.

## Python Basics

To write a game with LAN-Caster, you should have a basic familiarity with python 3. The links below will help:

* [Python for Java Programmers (YouTube 1:00:00)](https://www.youtube.com/watch?v=xLovcfIugy8)
* [Python Introductions](https://docs.python-guide.org/intro/learning/)
* Important Python types: [dict](https://docs.python.org/3/tutorial/datastructures.html#dictionaries), [str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str), [int and float](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex).
* Other important python skills: [default arguments](https://www.geeksforgeeks.org/default-arguments-in-python/) and [exceptions](https://docs.python.org/3/tutorial/errors.html). 

## [LAN-Caster Game Engine Overview](https://youtu.be/jUvnkdJJ1os)
* What is LAN-Caster?
* Where to get it: https://github.com/dbakewel/lan-caster
* File Organization
* Running the Demo
* Architecture:
  * Input data (Tiled): Maps and Tilesets
  * Processes
  * Server: game logic, steps, and mechanics
  * Clients (aka players): input and display 
  * Networking
* How to make your own game?

## [How to write a game with LAN-Caster](https://youtu.be/S1vMXXxbLMw)
* Design
  * Game Concept and Story
  * Game Mechanics
  * Engine Enhancements and Limitations
  * Tilesets, Maps, and Code
  * Working in a Team

* Implementation
  * File Structure and Revision Control
  * Maps and Tilesets
  * Launcher
  * Adding Code
  * Testing (-verbose, -profile, -test)
  * Incremental Improvement

## [Tilesets in LAN-Caster](https://youtu.be/Ays2itJTVPY)
* Tiled Tilesets 
* Images (png) files
  * Where to find and how to give credit.
  * How to make your own
* Create Tileset file
* Animated tiles
* Character tiles
* Anchor point
* Using Tiles on a Map:
  * Tile layers
  * Tile objects

## [Maps in LAN-Caster](https://youtu.be/W3ni7JxcZiI)
* Tiled Maps
* Map Requirements
* Tilesets
* Adding External Tilesets
Layers Types:
  * Tile Layers
  * Object Layers
  * Well Defined (known or special) Layers
    * sprites
    * triggers
    * inbounds
    * outofBounds
    * reference
* Layer Order (using black layer to help)
* Object Anchor Points vs. (x, y)
* Properties

## [LAN-Caster Client Code Overview](https://youtu.be/ccoLowFDico)
* startclient.py
* Client Class
  * init()
  * run()
    * Message Processing
    * Update Screen
    * User Input Event Processing
    * Loop Timing
* ClientMap Class (intro to map rendering)
* Subclassing

## [LAN-Caster Server Code Overview](https://youtu.be/6rHjjfqX-YY)
* startserver.py
* Server Class
  * init()
  * run()
    * Message Processing
    * Step Processing
    * Send Steps
    * Loop Timing
* ServerMap Class (intro to mechanics)
* Subclassing

## [LAN-Caster Server Stepping](https://youtu.be/vB2HY1xLVAg)
* StepMap Class
* Server Stepping
* Step Methods used for Game Mechanics
  * initMechanicName(): Called only once when the map is loaded.
  * stepMapStartMechanicName(): Called once at the start of each step.
  * triggerMechanicName(trigger, sprite): Called for every trigger/sprite collision
  * stepMoveMechanicName(sprite): Called for every sprite that is moving
  * stepMapEndMechanicName(): Called once at the end of each step.
* -verbose server startup messages

# Videos to be added...

## LAN-Caster engineTest Explanation (part 1)
* Player Sprites
* Move Linear Mechanic (also, intro to collisions)
* MapDoor Mechanic
* Holdable Mechanic
* Rendering (layers, shapes, map size)
* Text Styles
* Tile Animation and Character Tiles

## LAN-Caster engineTest Explanation (part 2)
* Triggers and Layer Visibility
* Ways to show text
* Extending a Mechanic
  * PortKey Mechanic
  * Timer Mechanic
* Sprite Dictionary
* Advanced Tests

## LAN-Caster Demo Game Overview

## LAN-Caster Demo Game Mechanics

## Tiled Properties in LAN-Caster

## Collisions in LAN-Caster

## How To Add User Inputs to LAN-Caster

## How To Add Interface Elements to LAN-Caster