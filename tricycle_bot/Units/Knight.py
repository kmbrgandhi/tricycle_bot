import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.clusters as clusters
import Units.attack as attack

order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]
knight_unit_priority = [1, 0.5, 2, 0.5, 2, 2, 3]
battle_radius = 9

def timestep(gc, unit, composition, battle_locs, assigned_knights, constants):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    best_loc = None
    best_target = None
    location = unit.location

    if location.is_on_map(): 
        unit_loc = location.map_location()

        ## Movement 
        # If new knight assign to location 
        if unit.id not in assigned_knights: 
            if len(battle_locs) > 0: 
                best_loc = get_best_location(gc, unit, unit_loc, battle_locs) ## MapLocation
                assigned_knights[unit.id] = best_loc
                battle_locs[(best_loc.x,best_loc.y)].add(unit.id)
            # else: 
            #     best_loc = move_away_from_factories(gc, unit_loc)
        else:
            best_loc = assigned_knights[unit.id] ## MapLocation

        ## Attack
        best_target = get_best_target(gc, unit, unit_loc, knight_unit_priority, constants)

        ## Do shit
        if best_target is not None:  # checked if ready to attack in get best target
            # See if this is a new battle location
            target_loc = best_target.location.map_location()
            add_location = evaluate_battle_location(gc, target_loc, battle_locs, constants)
            if add_location: 
                battle_locs[(target_loc.x,target_loc.y)] = set()

            # Attack
            gc.attack(unit.id, best_target.id)
        else:
            new_enemy = get_new_enemies(gc, unit, unit_loc, constants)
            if new_enemy is not None: 
                enemy_loc = new_enemy.location.map_location()
                add_location = evaluate_battle_location(gc, enemy_loc, battle_locs, constants)
                if add_location: 
                    battle_locs[(enemy_loc.x,enemy_loc.y)] = set()

        if best_loc is not None and gc.is_move_ready(unit.id): 
            best_dir = get_best_direction(gc, unit.id, unit_loc, best_loc)
            if best_dir is not None: 
                gc.move_robot(unit.id, best_dir)

def get_best_location(gc, unit, unit_loc, battle_locs): 
    """
    Chooses the battle location this knight should aim for
    """
    best = None
    best_coeff = -float('inf')

    for loc in battle_locs: 
        map_loc = bc.MapLocation(gc.planet(),loc[0],loc[1])
        distance = float(unit_loc.distance_squared_to(map_loc))
        quantity = len(battle_locs[loc])
        coeff = calculate_location_coefficient(distance, quantity)
        if coeff > best_coeff: 
            best = map_loc
            best_coeff = coeff

    return best

def calculate_location_coefficient(distance, quantity):
    dist_coeff = 1 - distance/100
    quantity_coeff = 1 - quantity/15

    return dist_coeff + quantity_coeff

def get_best_direction(gc, unit_id, unit_loc, target_loc):
    ideal_dir = unit_loc.direction_to(target_loc)

    if gc.can_move(unit_id, ideal_dir): 
        return ideal_dir
    else:
        shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
        directions = sense_util.get_best_option(shape)
        for d in directions: 
            if gc.can_move(unit_id, d): 
                return d

    return None

def get_best_target(gc, unit, location, priority_order, constants, javelin=False):
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), constants.enemy_team)
    if len(vuln_enemies)==0 or not gc.is_attack_ready(unit.id):
        return None
    best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order))
    return best_target

def get_new_enemies(gc, unit, unit_loc, constants):
    new_enemies = gc.sense_nearby_units_by_team(unit_loc, int(unit.vision_range/2), constants.enemy_team)
    if len(new_enemies)==0:
        return None
    return new_enemies[0]

def evaluate_battle_location(gc, loc, battle_locs, constants):
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

def update_battles(gc, battle_locs, assigned_knights, constants):
    """
    Remove locations & units that aren't valid anymore.
    """

    ## Locations
    remove = set()
    for loc_coords in battle_locs:
        loc = bc.MapLocation(gc.planet(),loc_coords[0],loc_coords[1])
        if gc.can_sense_location(loc): 
            found_enemy = False 
            locs_near = gc.all_locations_within(loc, battle_radius)
            for near in locs_near: 
                if gc.has_unit_at_location(near):
                    unit = gc.sense_unit_at_location(near)
                    if unit.team == constants.enemy_team:
                        found_enemy = True
                        break
            if not found_enemy: 
                remove.add(loc_coords)

    for loc_coords in remove: 
        units = battle_locs[loc_coords]
        del battle_locs[loc_coords]
        for unit in units: 
            del assigned_knights[unit]

    ## Units
    remove = set()
    for knight_id in assigned_knights:
        try:
            knight = gc.unit(knight_id)
        except:
            loc = assigned_knights[knight_id]
            remove.add((knight_id,(loc.x,loc.y)))

    for elem in remove:
        knight_id, loc_coords = elem
        battle_locs[loc_coords].remove(knight_id)
        del assigned_knights[knight_id]
