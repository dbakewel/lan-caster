[ [ABOUT](README.md) | [SETUP and RUN](SETUP.md) | **CREATE A GAME** | [TUTORIALS](TUTORIALS.md) | [CONTRIBUTING](CONTRIBUTING.md) ]

# LAN-Caster - Create a Game

Most information on creating a game is provided in the [tutorials](TUTORIALS.md) or in code comments.
This document covers only a few general topics.

## File Organization

A new game requires a folder to be added under the src/ folder. The new folder name will be the name of
the game (used with the -game command line argument). For example, assume a new game is being created call "elmo". 
The game will have two maps: house and outside. For graphics a simple tileset image called basictiles.png
will be used.

Minimum file structure for elmo:
```
    lan-caster/
        src/
            elmo/
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

A more fully filled out file structure for elmo adds more tilesets, extended game classes for server, servermap, client 
and clientmap, and extended servermap class for the house map. Also, a credits.md file
is added to give credit to the creator of the game and the creators of any assets (fonts and images). Finally a custom
font has been added.
```
    lan-caster/
        src/
            elmo/
                docs/
                    credits.md
                fonts/
                    coolfont.ttf
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
Tiled is used to create the map and tileset JSON files. LAN-Caster has been tested with data from Tiled 1.7.2
https://www.mapeditor.org/download.html. LAN-Caster only supports a subset of Tiled features as described below.

#### Supported Tiled Features
Map format and feature support:
  * Orientation: Orthogonal
  * Tile layer format: CSV
  * Tile render order: Right Down
  * Map size: Fixed
  * Save as type: JSON (.json)
  * Layer types: tile, object
  * Layer visibility

Tiled objects (on map object layers) support:
  * Attributes: name, type, x, y, width, height, gid
  * Object Types: rectangle, point, ellipse, tile, and text

Tileset format and features supported:
  * Tileset Type: Based on Tileset Image
  * Tile animations

Custom properties in: maps, layers, objects, tilesets, and tiles.

#### Unsupported Tiled Features
Map and tileset types not listed above are not supported.

Map Layer types: image, group

Tiled objects (on map object layers) do NOT support:
  * Attributes: flip, rotation, id, visible
  * Object Types: polygon

Duplicate custom property names within the same element are not supported.

#### Other Tiled Feature Support
Other features of of Tiled may have limited support or are simply ignored by LAN-Caster.

## Extending LAN-Caster

The following files can be placed in the game folder and will be used in place of the 
corresponding file from the engine folder. These should 
inherit from the corresponding file in the engine folder:

  * client.py
  * clientmap.py
  * clienttileset.py
  * messages.py
  * server.py
  * servermap.py
  * tileset.py

The following files can be placed in a map folder and will only apply
to that one map. These files will be used in place of the corresponding file from the game and engine
folders. Normally these files should inherit from the corresponding file
in the game folder but they can also inherit directly from the engine folder:

  * clientmap.py
  * servermap.py
