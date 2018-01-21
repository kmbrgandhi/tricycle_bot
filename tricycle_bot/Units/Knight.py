import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.attack as attack
import Units.variables as variables
import Units.clusters as clusters

order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]
knight_unit_priority = [1, 2, 0.5, 0.5, 2, 3, 3]
battle_radius = 9

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    gc = variables.gc
    planet = gc.planet()
    if planet == bc.Planet.Earth: 
        battle_locs = variables.earth_battle_locs
        diagonal = variables.earth_diagonal
    else: 
        battle_locs = variables.mars_battle_locs
        diagonal = variables.mars_diagonal

    assigned_knights = variables.assigned_knights
    direction_to_coord = variables.direction_to_coord
    precomputed_bfs = variables.precomputed_bfs
    bfs_fineness = variables.bfs_fineness
    info = variables.info

    my_team = variables.my_team
    enemy_team = variables.enemy_team
    # constants = variables.constants

    best_loc = None
    best_target = None
    location = unit.location

    if location.is_on_map(): 
        unit_loc = location.map_location()

        ## Movement 
        # If new knight assign to location 
        if unit.id not in assigned_knights: 
            if len(battle_locs) > 0: 
                best_loc = get_best_location(gc, unit, unit_loc, battle_locs, planet, diagonal) ## MapLocation
                assigned_knights[unit.id] = best_loc
                battle_locs[(best_loc.x,best_loc.y)].add_ally(unit.id)

            # else: 
            #     best_loc = move_away_from_factories(gc, unit_loc)
        else:
            best_loc = assigned_knights[unit.id] ## MapLocation

        ## Attack
        best_target = get_best_target(gc, unit, unit_loc, knight_unit_priority, enemy_team)

        ## Do shit
        if best_target is not None:  # checked if ready to attack in get best target
            # See if this is a new battle location
            target_loc = best_target.location.map_location()
            add_location = evaluate_battle_location(gc, target_loc, battle_locs)
            if add_location: 
                battle_locs[(target_loc.x,target_loc.y)] = clusters.Cluster(allies=set(),enemies=set([best_target.id]))

            # Attack
            gc.attack(unit.id, best_target.id)
        else:
            new_enemy = get_new_enemies(gc, unit, unit_loc, enemy_team)
            if new_enemy is not None: 
                enemy_loc = new_enemy.location.map_location()
                add_location = evaluate_battle_location(gc, enemy_loc, battle_locs)
                if add_location: 
                    battle_locs[(enemy_loc.x,enemy_loc.y)] = clusters.Cluster(allies=set(),enemies=set([new_enemy.id]))

        if best_loc is not None and gc.is_move_ready(unit.id): 
            best_dir = get_best_direction(gc, unit, unit_loc, best_loc, direction_to_coord, precomputed_bfs, bfs_fineness)
            if best_dir is not None: 
                gc.move_robot(unit.id, best_dir)

def get_best_location(gc, unit, unit_loc, battle_locs, planet, diagonal): 
    """
    Chooses the battle location this knight should aim for
    """
    most_urgent = None
    most_urgent_coeff = 0 ## 0 - 5

    for loc in battle_locs: 
        map_loc = bc.MapLocation(planet,loc[0],loc[1])
        distance_coeff = 1 - (float(unit_loc.distance_squared_to(map_loc))/diagonal)
        coeff = battle_locs[loc].urgency_coeff(gc)
        if coeff + distance_coeff > most_urgent_coeff:
            most_urgent_coeff = coeff + distance_coeff
            most_urgent = map_loc

    return most_urgent

def get_best_direction(gc, unit, unit_loc, target_loc, direction_to_coord, precomputed_bfs, bfs_fineness):
    start_coords = (unit_loc.x, unit_loc.y)
    target_coords_thirds = (int(target_loc.x/bfs_fineness), int(target_loc.y/bfs_fineness))
    shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
    options = sense_util.get_best_option(shape)
    for option in options: 
        if gc.can_move(unit.id, option):
            return option 
    return None

def get_best_target(gc, unit, location, priority_order, enemy_team, javelin=False):
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), enemy_team)
    if len(vuln_enemies)==0 or not gc.is_attack_ready(unit.id):
        return None
    best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order))
    return best_target

def get_new_enemies(gc, unit, unit_loc, enemy_team):
    new_enemies = gc.sense_nearby_units_by_team(unit_loc, int(unit.vision_range/2), enemy_team)
    if len(new_enemies)==0:
        return None
    return new_enemies[0]

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

def update_battles():
    """
    Remove locations & units that aren't valid anymore.
    """

    gc = variables.gc
    battle_locs = variables.battle_locations
    assigned_knights = variables.assigned_knights
    
    enemy_team = variables.enemy_team

    ## Locations
    remove = set()
    for loc_coords in battle_locs:
        found_enemy = battle_locs[loc_coords].update_enemies(gc, loc_coords, enemy_team)
        if not found_enemy:
            remove.add(loc_coords)

    for loc_coords in remove: 
        cluster = battle_locs[loc_coords]
        del battle_locs[loc_coords]
        for unit_id in cluster.allies: 
            del assigned_knights[unit_id]

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
        battle_locs[loc_coords].remove_ally(knight_id)
        del assigned_knights[knight_id]

