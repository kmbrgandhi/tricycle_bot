import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.variables as variables
import Units.clusters as clusters

import numpy as np

battle_radius = 9

def timestep(unit):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Healer:
        return

    gc = variables.gc
    planet = gc.planet()
    if planet == bc.Planet.Earth: 
        battle_locs = variables.earth_battles
        diagonal = variables.earth_diagonal
    else: 
        battle_locs = variables.mars_battles
        diagonal = variables.mars_diagonal

    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    precomputed_bfs = variables.precomputed_bfs
    bfs_fineness = variables.bfs_fineness
    enemy_team = variables.enemy_team
    my_team = variables.my_team
    directions = variables.directions

    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    healer_target_locs = variables.healer_target_locs
    overcharge_targets = variables.overcharge_targets

    best_dir = None
    best_loc = None
    best_target = None
    heal = False
    overcharge = False
    location = unit.location

    if location.is_on_map():
        unit_loc = location.map_location()

        ## Assign role 
        if unit.id not in assigned_overcharge and unit.id not in assigned_healers:
            overcharge_to_total = 1
            total = len(assigned_healers) + len(assigned_overcharge)
            if total > 0: overcharge_to_total = len(assigned_overcharge) / total
            # Assign to overcharge if there are targets and ratio is good
            if variables.research.get_level(bc.UnitType.Healer) == 3 and overcharge_to_total < 0.2 and len(overcharge_targets) > 0: 
                best_target = gc.unit(overcharge_targets.pop())
                assigned_overcharge[unit.id] = best_target
            # Assign to best healer target or target location
            else: 
                best_target = get_best_target(gc, unit, unit_loc, my_team)
                if best_target is not None: 
                    target_loc = best_target.location.map_location()
                    heal = True
                    add_healer_target(gc, target_loc)
                    assigned_healers[unit.id] = target_loc
                elif len(healer_target_locs) > 0:
                    best_loc = get_best_target_loc(gc, unit, unit_loc, healer_target_locs, planet, diagonal) ## MapLocation
                    assigned_healers[unit.id] = best_loc

        ## Overcharge  
        if unit.id in assigned_overcharge:
            ally = assigned_overcharge[unit.id]
            if gc.can_overcharge(unit.id, ally.id):
                overcharge = True
                best_target = ally
        elif not overcharge and best_target is None: 
            best_target = get_best_target(gc, unit, unit_loc, my_team)
            if best_target is not None: 
                target_loc = best_target.location.map_location()
                heal = True
                add_healer_target(gc, target_loc)

        ## Movement
        # If sees enemies close enough then tries to move away from them 
        enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, enemy_team)
        if len(enemies) > 0: 
            enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))
            enemy_loc = enemies[0].location.map_location()
            best_dir = dir_away_from_enemy(gc, unit, unit_loc, enemy_loc)
            add_location = evaluate_battle_location(gc, enemy_loc, battle_locs)
            if add_location: 
                battle_locs[(enemy_loc.x,enemy_loc.y)] = clusters.Cluster(allies=set(),enemies=set([enemies[0].id]))

        # Otherwise, goes to battle locations where they are in need of healers
        else: 
            if unit.id in assigned_overcharge: 
                ally = assigned_overcharge[unit.id]
                best_loc = ally.location.map_location()
            elif unit.id in assigned_healers: 
                best_loc = assigned_healers[unit.id]
            elif len(healer_target_locs) > 0: 
                best_loc = get_best_target_loc(gc, unit, unit_loc, healer_target_locs, planet, diagonal) ## MapLocation
                assigned_healers[unit.id] = best_loc

            # elif len(battle_locs) > 0: 
            #     best_loc = get_best_location(gc, unit, unit_loc, battle_locs, planet, diagonal)

            else: 
                best_dir = get_explore_dir(gc, unit, unit_loc, directions)


        ## Do shit
        if best_target is not None:
            if overcharge and gc.is_overcharge_ready(unit.id):
                gc.overcharge(unit.id, best_target.id)
            if heal and gc.is_heal_ready(unit.id):
                gc.heal(unit.id, best_target.id)
        if best_dir is not None and gc.is_move_ready(unit.id): 
            gc.move_robot(unit.id, best_dir)
        elif best_loc is not None and gc.is_move_ready(unit.id):
            #print('GETTING BEST DIRECTION')
            #print(best_loc)
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

def get_explore_dir(gc, unit, location, directions):
    # function to get a direction to explore by picking locations that are within some distance that are
    # not visible to the team yet, and going towards them.
    dir = None
    close_locations = [x for x in gc.all_locations_within(location, 150) if
                       not gc.can_sense_location(x)]
    if len(close_locations) > 0:
        dir = sense_util.best_available_direction_visibility(gc, unit, close_locations)
    else:
        dir = random.choice(directions)
    if gc.can_move(unit.id, dir):
        return dir
    return None

def get_best_target_loc(gc, unit, unit_loc, battle_locs, planet, diagonal):
    best = None
    best_coeff = -float('inf')
    for loc in battle_locs: 
        map_loc = bc.MapLocation(planet,loc[0],loc[1])
        distance_coeff = (1 - (float(unit_loc.distance_squared_to(map_loc))/diagonal))
        if distance_coeff > best_coeff: 
            best_coeff = distance_coeff
            best = map_loc
    return best

def add_healer_target(gc, target_loc): 
    healer_target_locs = variables.healer_target_locs
    assigned_healers = variables.assigned_healers
    valid = True

    locs_near = gc.all_locations_within(target_loc, variables.healer_radius)
    for near in locs_near:
        near_coords = (near.x, near.y)
        if near_coords in healer_target_locs: 
            valid = False
            break
    if valid: 
        healer_target_locs.add((target_loc.x, target_loc.y))

def get_best_location(gc, unit, unit_loc, battle_locs, planet, diagonal): 
    """
    Chooses the battle location this knight should aim for
    """
    most_urgent = None
    most_urgent_coeff = 0 ## 0 - 5

    for loc in battle_locs: 
        map_loc = bc.MapLocation(planet,loc[0],loc[1])
        distance_coeff = 2*(1 - (float(unit_loc.distance_squared_to(map_loc))/diagonal))
        coeff = battle_locs[loc].urgent
        if coeff + distance_coeff > most_urgent_coeff:
            most_urgent_coeff = coeff + distance_coeff
            most_urgent = map_loc

    return most_urgent

def check_radius_squares_factories(gc, unit, radius=1):
    is_factory = False
    for nearby_loc in gc.all_locations_within(unit.location.map_location(), radius):
        if gc.can_sense_location(nearby_loc) and gc.has_unit_at_location(nearby_loc) and gc.sense_unit_at_location(nearby_loc).unit_type == bc.UnitType.Factory:
            return True
    return False

def get_best_direction(gc, unit_id, unit_loc, target_loc, direction_to_coord, precomputed_bfs, bfs_fineness):
    start_coords = (unit_loc.x, unit_loc.y)
    target_coords_thirds = (int(target_loc.x/bfs_fineness), int(target_loc.y/bfs_fineness))
    if (start_coords, target_coords_thirds) in precomputed_bfs:
        shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
        options = sense_util.get_best_option(shape)
        for option in options: 
            if gc.can_move(unit_id, option):
                return option 
    return None


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
    valid = True
    locs_near = gc.all_locations_within(loc, battle_radius)
    for near in locs_near:
        near_coords = (near.x, near.y)
        if near_coords in battle_locs: 
            valid = False
    
    return valid

def update_healers():
    """
    Remove dead healers from healer dict and overcharge dict.
    If healer target loc has no allied units then remove from dictionary.
    Checks overcharge targets are still alive. 
    """
    gc = variables.gc
    target_locs = variables.healer_target_locs
    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets
    planet = gc.planet()
    my_team = variables.my_team

    ## Remove dead healers from assigned healers OR healers with expired locations
    remove = set()
    for healer_id in assigned_healers:
        try: 
            healer = gc.unit(healer_id)
            loc = assigned_healers[healer_id]
            if gc.can_sense_location(loc):
                allies = gc.sense_nearby_units_by_team(loc, 4, my_team)
                if len(allies) == 0: 
                    remove.add(healer_id)
                    if (loc.x,loc.y) in target_locs: 
                        target_locs.remove((loc.x,loc.y))
        except:
            remove.add(healer_id)

    for healer_id in remove: 
        if healer_id in assigned_healers: 
            del assigned_healers[healer_id]

    ## Remove dead healers from assigned overcharge
    remove = set()
    for healer_id in assigned_overcharge:
        try:
            healer = gc.unit(healer_id)
        except:
            remove.add(healer_id)

    for healer_id in remove:
        del assigned_overcharge[healer_id]

    ## Remove dead overcharge targets 
    remove = set()
    for ally_id in overcharge_targets: 
        try: 
            ally = gc.unit(ally_id)
        except:
            remove.add(ally_id)

    for ally_id in remove:
        overcharge_targets.remove(ally_id)




