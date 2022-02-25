"""Load Game Modules and Data"""

import os
import importlib

from engine.log import log


def loadModule(moduleName, game, mapName=False):
    '''Return most specific module for moduleName.

    Search for module from most to least specific: maps, game, and engine folder, in that order.
    Map folder will only be search if mapName is provided.

    For example, loadModule("servermap", game="demo", mapName="start")
    will search in the following order and return the first one found:
        1) demo/maps/start/servermap.py
        2) demo/servermap.py
        3) engine/servermap.py

    Args:
        moduleName (str): The module name
        game (str): The game name (game folder name)
        mapName (str): The name of the map: <game>/maps/<mapName>/
    '''

    fortext = ""
    if mapName:
        fortext = f"Map {mapName}: "

    if game and mapName and os.path.isfile(f"src/{game}/maps/{mapName}/{moduleName}.py"):
        log(f"{fortext}Importing {game}.maps.{mapName}.{moduleName}", "VERBOSE")
        module = importlib.import_module(f"{game}.maps.{mapName}.{moduleName}")
    elif game and os.path.isfile(f"src/{game}/{moduleName}.py"):
        log(f"{fortext}Importing {game}.{moduleName}", "VERBOSE")
        module = importlib.import_module(f"{game}.{moduleName}")
    elif os.path.isfile(f"src/engine/{moduleName}.py"):
        log(f"{fortext}Importing engine.{moduleName}", "VERBOSE")
        module = importlib.import_module(f"engine.{moduleName}")
    else:
        log(f"{fortext}Module name {moduleName} not found.", "FAILURE")
        exit()

    return module


def loadTilesets(game, loadImages):
    '''Load game tilesets.

    This functions loads all Tiled tilesets for a game.

    Args:
        game (str): The game name (game folder name). Tilesets will
            be loaded from <game>/tilesets/
        loadImages (bool): If loadImages is True then also loads
            tileset images.

    Returns:
        dict: dictionary of tileset objects, with the key being the tileset name:
            {'tileset1name': tileset1object, 'tileset2name': tileset2object, ....}
    '''

    if loadImages:
        module = loadModule("clienttileset", game=game)
    else:
        module = loadModule("tileset", game=game)

    tilesetsDir = f"src/{game}/tilesets"
    tilesets = {}
    listing = os.listdir(tilesetsDir)
    for tilesetFile in listing:
        if loadImages:
            ts = module.ClientTileset(tilesetsDir + "/" + tilesetFile)
        else:
            ts = module.Tileset(tilesetsDir + "/" + tilesetFile)
        tilesets[ts['name']] = ts
    return tilesets


def loadMaps(tilesets, game, maptype):
    '''Load game maps.

    This functions loads all Tiled maps for a game.

    All map objects will be either type ServerMap or ClientMap. For each map, the most specific
    module will be found for by looking first in the map folder for servermap.py or
    clientmap.py, then the game folder, and then the engine folder. Therefore, each map
    could use a different module.

    Args:
        game (str): The game name (game folder name). Maps will
            be loaded from <game>/maps/
        maptype (str): Must be either "ServerMap" or "ClientMap".

    Returns:
        dict: dictionary of map objects, with the key being the map name:
        {'map1name': map1object, 'map2name': map2object, ....}


    '''

    if maptype == "ServerMap":
        moduleName = "servermap"
    elif maptype == "ClientMap":
        moduleName = "clientmap"
    else:
        log(f"maptype == {maptype} is not supported. maptype must be 'ServerMap' or 'ClientMap'.", "FAILURE")
        exit()

    mapsDir = f"src/{game}/maps"
    maps = {}
    listing = os.listdir(mapsDir)
    for mapName in listing:
        module = loadModule(moduleName, game=game, mapName=mapName)

        if maptype == "ServerMap":
            mapObj = module.ServerMap(tilesets, mapsDir + "/" + mapName)
        else:
            mapObj = module.ClientMap(tilesets, mapsDir + "/" + mapName)

        maps[mapObj['name']] = mapObj

    return maps
