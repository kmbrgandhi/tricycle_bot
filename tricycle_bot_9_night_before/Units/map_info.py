import battlecode as bc
import random
import sys
import traceback

"""
def get_initial_karbonite_locations(gc):
    deposit_locations = {}
    start_map = gc.starting_map(bc.Planet(0))
    initial_coords = []

    for initial_unit in start_map.initial_units:
        if initial_unit.team == bc.my_team:
            initial_unit_location = initial_unit.location.map_location()
            initial_coords.append((initial_unit_location.x,initial_unit_location.y))

    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(variables.earth,x,y)
            karbonite_at = start_map.initial_karbonite_at(map_location)
            karbonite_coord = (x,y)

            if karbonite_at > 0:
                target_coords_val = Ranger.get_coord_value(karbonite_coord)
                for initial_coord in initial_coords:
                    our_coords_val = Ranger.get_coord_value(initial_coord)
                    if variables.bfs_array[our_coords_val, target_coords_val] != float('inf'):
                        deposit_locations[(x,y)] = karbonite_at

    return deposit_locations
"""
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
