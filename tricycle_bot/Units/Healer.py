import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.variables as variables

import numpy as np

battle_radius = 9

def timestep(unit):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Healer:
        return

    gc = variables.gc
    battle_locs = variables.battle_locations
    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    precomputed_bfs = variables.precomputed_bfs
    bfs_fineness = variables.bfs_fineness
    enemy_team = variables.enemy_team
    my_team = variables.my_team

    best_dir = None
    best_loc = None
    best_target = None
    location = unit.location
    if location.is_on_map():
        unit_loc = location.map_location()

        ## Movement
        # If sees enemies close enough then tries to move away from them 
        enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, enemy_team)
        if len(enemies) > 0: 
            enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))
            enemy_loc = enemies[0].location.map_location()
            best_dir = dir_away_from_enemy(gc, unit, unit_loc, enemy_loc)
            add_location = evaluate_battle_location(gc, enemy_loc, battle_locs)
            if add_location: 
                battle_locs[(enemy_loc.x,enemy_loc.y)] = set()

        # Otherwise, goes to battle locations where they are in need of healers
        elif len(battle_locs) > 0: 
            best_loc = get_best_location(gc, unit, unit_loc, battle_locs)
            #print('best loc: ', best_loc)
        ## Healing
        best_target = get_best_target(gc, unit, unit_loc, my_team)

        ## Do shit
        if best_target is not None and gc.is_heal_ready(unit.id):
            gc.heal(unit.id, best_target.id)
        if best_dir is not None and gc.is_move_ready(unit.id): 
            gc.move_robot(unit.id, best_dir)
        elif best_dir is None and best_loc is not None and gc.is_move_ready(unit.id):
            best_dir = get_best_direction(gc, unit.id, unit_loc, best_loc, direction_to_coord, precomputed_bfs, bfs_fineness)
            if best_dir is not None: 
                gc.move_robot(unit.id, best_dir)

def dir_away_from_enemy(gc, unit, unit_loc, enemy_loc):
    ideal_dir_from_enemy = enemy_loc.direction_to(unit_loc)

    if gc.can_move(unit.id, ideal_dir_from_enemy):
        return ideal_dir_from_enemy
    else:
        shape = [enemy_loc.x - unit_loc.x, enemy_loc.y - unit_loc.y]
        directions = sense_util.get_best_option(shape)
        for d in directions: 
            if gc.can_move(unit.id, d): 
                return d
    return None

def get_best_location(gc, unit, unit_loc, battle_locs): 
    """
    Chooses the battle location this knight should aim for
    """
    best = None
    best_coeff = -float('inf')

    for loc in battle_locs: 
        map_loc = bc.MapLocation(gc.planet(),loc[0],loc[1])
        distance = float(unit_loc.distance_squared_to(map_loc))
        units = battle_locs[loc]
        coeff = calculate_location_coefficient(gc, distance, units)
        if coeff > best_coeff: 
            best = map_loc
            best_coeff = coeff

    return best

def calculate_location_coefficient(gc, distance, units):
    dist_coeff = 1 - distance/100
    health_coeff = 0

    for unit_id in units: 
        unit = gc.unit(unit_id)
        health_coeff += unit.max_health / unit.health

    if len(units) > 0: health_coeff = health_coeff/len(units)

    return dist_coeff + health_coeff

def get_best_direction(gc, unit_id, unit_loc, target_loc, direction_to_coord, precomputed_bfs, bfs_fineness):
    start_coords = (unit_loc.x, unit_loc.y)
    target_coords_thirds = (int(target_loc.x/bfs_fineness), int(target_loc.y/bfs_fineness))
    shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
    options = sense_util.get_best_option(shape)
    for option in options: 
        if gc.can_move(unit_id, option):
            return option 
    return None

# def get_best_direction(gc, unit_id, unit_loc, target_loc):
#     ideal_dir = unit_loc.direction_to(target_loc)

#     if gc.can_move(unit_id, ideal_dir): 
#         return ideal_dir
#     else:
#         shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
#         directions = sense_util.get_best_option(shape)
#         for d in directions: 
#             if gc.can_move(unit_id, d): 
#                 return d
#     return None

def get_best_target(gc, unit, unit_loc, my_team):
    ## Attempt to heal nearby units
    nearby = gc.sense_nearby_units_by_team(unit_loc, unit.ability_range()-1, my_team)
    if len(nearby) > 0: 
        nearby = sorted(nearby, key=lambda x: x.health/x.max_health)
        for ally in nearby: 
            if gc.can_heal(unit.id, ally.id): 
                return ally
    return None

def evaluate_battle_location(gc, loc, battle_locs):
    """
    Chooses whether or not to add this enemy's location as a new battle location.
    """
    # units_near = gc.sense_nearby_units_by_team(loc, battle_radius, constants.enemy_team)
    valid = True
    locs_near = gc.all_locations_within(loc, battle_radius)
    for near in locs_near:
        near_coords = (near.x, near.y)
        if near_coords in battle_locs: 
            valid = False
    
    return valid