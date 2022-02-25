[ [ABOUT](README.md) | [SETUP and RUN](SETUP.md) | [CREATE A GAME](CREATE.md) | **TUTORIALS** | [CONTRIBUTING](CONTRIBUTING.md) ]

# LAN-Caster - Tutorials (UNDER DEVELOPMENT)

The following videos provide an overview of how to use LAN-Caster to build your own game.

### Videos to add:

* Engine Overview
```
General purpose, enhancement, and limitations of the engine
What the engine can do (see enginetest)
How the engine can be expanded (see demo)
architecture: 
  Input data (Tiled): maps and tilesets
  server and clients
    server side(game logic, steps and mechanics), 
    clients/players side (input and display), 
  LAN networking
```

* How to write a game with LAN-Caster
```
Design
  Game Concept and Story
  Game Mechanics
  Engine Enhancements and Limitations
  Details: Game and Maps

Implementation
  file structure and loaders
  Maps and Tilesets
  launcher
  adding code
  build for testing (back doors and test suites)
  incremental improvement

Watch the other videos for detailed examples
```

* Engine Maps and Tilesets
```
Tiled
map requirements
layer types
tilesets
tile layers
object layers
well defined (known or special) layers
  sprites
  anchor points vs x y
layer order (using black layer to help)
```

* Engine Client and ClientMap Class
```
designed to be a single instance class
map and tileset and clienttileset classes
clientmap class (blitting and validUntil)
limitation (what parts of Tiled are not supported)
```

* Engine Server Class
```
designed to be a single instance class
init
main loop
  message processing
  step processing
  sending steps
  loop timing (fps)
```

* Engine ServerMap Class (stepping and game mechanics)
```
servermap class
  init
  step processing (start, sprites, end)
  testing game engine mechanics with test-engine
  engine mechanics
  ACTIONS
    client user input and action message, set action in sprite
    dispacther, 
    pickup, 
    use, 
    drop
  ACTIONTEXT 
    following through to display by client
  TRIGGERS
    dispacther
    mapDoor
    popUpText
  MOVE
    client user input, set dest message

LABELTEXT
SPEACHTEXT
```

* Demo overview
```
  file strucutre, subclassing and loaders review

  Maps and Tileset data

  Tangent: General vs. Hardcoded Design Decisions

  Demo Server
    stepEnd

  Demo Client
    open and ending text (user interface overlay)

```

* Demo game mechanics
```
  
  Making General vs. Hardcoded Design Decisions

  Demo ServerMap
    Chicken, 
    Throw, 
    SpeedMultiplier (mud), 
    Bomb,
    RespawnPoint mechanics (designed to work between maps but demo does not use that feature)

  Start Map ServerMap
    lockedMapDoor

  Under Map ServerMap
    Saw
    Use of Respawn points
    StopSaw

  Under Map ClientMap
    Darkness

  End Map ServerMap
    Lever
    Magic Wand


```
