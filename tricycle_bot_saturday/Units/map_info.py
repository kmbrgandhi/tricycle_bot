import battlecode as bc
import random
import sys
import traceback

def get_initial_karbonite_locations(gc):
    deposit_locations = {}
    start_map = gc.starting_map(bc.Planet(0))
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(bc.Planet(0),x,y)
            karbonite_at = start_map.initial_karbonite_at(map_location)
            if karbonite_at > 0:
                deposit_locations[(x,y)] = karbonite_at
    return deposit_locations

# returns list of MapLocation that are impassable terrain
def get_impassable_terrain(gc,planet):
    impassable_terrain = []
    start_map = gc.starting_map(planet)
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(planet,x,y)   
            if not start_map.is_passable_terrain_at(map_location):
                impassable_terrain.append(map_location)
    return impassable_terrain

def is_next_to_terrain(gc,start_map,location):
    cardinal_directions = [bc.Direction.North, bc.Direction.East, bc.Direction.South, bc.Direction.West]
    for direction in cardinal_directions:
        next_location = location.add(direction)
        if not start_map.on_map(next_location) or not start_map.is_passable_terrain_at(next_location):
            return True
    return False
        

def get_locations_next_to_terrain(gc,planet):
    locations = []
    start_map = gc.starting_map(planet) 
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(planet,x,y)
            if not start_map.is_passable_terrain_at(map_location):
                continue
            elif is_next_to_terrain(gc,start_map,map_location):
                locations.append(map_location)
    return locations
