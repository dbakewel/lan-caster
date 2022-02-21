[ [ABOUT](README.md) | [SETUP and RUN](SETUP.md) | **CREATE A GAME** | [TUTORIALS](TUTORIALS.md) ]

# LAN-Caster - Create a Game (UNDER DEVELOPMENT)

This document explains how to create a new game in LAN-Caster. It covers basics of:
    File Organization
    Data Creation
    Extending LAN-Caster
    Server Step Logic
    Other Resources

## File Organization

Assume a new game is being created call "elmo". The game will have 
two maps: house, outside. For graphics a simple tielset image called basictiles.png
will be used.

Minimum file structure for elmo:
```
    lan-caster/
        elmo/
            docs/
            fonts/
            images/
                basictiles.png
            maps/
                house/
                    house.json
                outside/
                    outside.json
            tilesets/
                basictiles.json
```
  * only files that are added for elmo are shown.

A more fully filled out file structure for elmo adds more tilesets, extended game classes for server, servermap, client and clientmap, and extented servermap class for the house map:
```
    lan-caster/
        elmo/
            docs/
            fonts/
            images/
                basictiles.png
                othertiles.png
            maps/
                house/
                    house.json
                    servermap.py
                outside/
                    outside.json
            tilesets/
                basictiles.json
                othertiles.json
            client.py
            clientmap.py
            server.py
            servermap.py
```
  * only files that are added for elmo are shown.

## Data Creation in Tiled
LAN-Caster has been tested with data from Tiled 1.7.2
https://www.mapeditor.org/download.html

#### Supported Tiled Features
Map format:

  * Orientation: Orthogonal
  * Tile layer format: CSV
  * Tile render order: Right Down
  * Map size: Fixed
  * Save as type: JSON (.json)

Layer types: tile, object

Layer visibility is supported.

Tileset Type: Based on Tileset Image

For Tiled object (on object layers) the following are supported:

  * Attributes: name, type, x, y, width, height, gid
  * Object Types: rectangle, point, ellipse, tile, and text

Tile animations.

Custom properties in: maps, layers, objects, tilesets, and tiles.

#### Unsupported Tiled Features
Map and tileset types not listed above are not supported.

Layer types: image, group

For Tiled object (on object layers) the following are NOT supported:

  * Attributes: flip, rotation, id, visible
  * Object Types: polygon

Duplicate custom property names within the same element.

#### Other Filed Feature Support
Other features of of Tiled may have limited support or are
simply ignored by LAN-Caster.

## Extending LAN-Caster

The following files can be placed in the game folder. These should 
inherit from the corresponding file in the game engine:

  * client.py
  * clientmap.py
  * clienttileset.py
  * messages.py
  * server.py
  * servermap.py
  * tileset.py

The following files can be placed in the maps folder and will only apply
to that one map. Normally these should inherit from the corresponding file
in the game folder but they can also inherit directly from the game engine:

  * clientmap.py
  * servermap.py

## Server Step Logic

## Other Resources
