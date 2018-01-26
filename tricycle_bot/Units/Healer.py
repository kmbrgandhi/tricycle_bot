import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.variables as variables
import Units.explore as explore
import Units.Ranger as Ranger


import numpy as np

if variables.curr_planet==bc.Planet.Earth:
    passable_locations = variables.passable_locations_earth
else:
    passable_locations = variables.passable_locations_mars

battle_radius = 9

def timestep(unit):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Healer:
        return

    gc = variables.gc

    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    bfs_dict = variables.bfs_dict
    bfs_fineness = variables.bfs_fineness
    enemy_team = variables.enemy_team
    my_team = variables.my_team

    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets

    unit_locations = variables.unit_locations

    best_dir = None
    best_loc = None
    best_target = None
    heal = False
    overcharge = False
    location = unit.location

    if location.is_on_map():
        ## Add new ones to unit_locations, else just get the location
        if unit.id not in unit_locations:
            loc = unit.location.map_location()
            unit_locations[unit.id] = (loc.x,loc.y)

        unit_loc = unit_locations[unit.id]

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
                    heal = True
                assigned, best_loc = assign_to_quadrant(gc, unit, unit_loc)
                if not assigned: 
                    nearby = gc.sense_nearby_units_by_team(bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1]), 8, variables.my_team)
                    best_dir = sense_util.best_available_direction(gc,unit,nearby)  

        ## Overcharge  
        if unit.id in assigned_overcharge:
            ally = assigned_overcharge[unit.id]
            if gc.can_overcharge(unit.id, ally.id):
                overcharge = True
                best_target = ally
        elif not overcharge and best_target is None: 
            best_target = get_best_target(gc, unit, unit_loc, my_team)
            if best_target is not None: 
                heal = True

        ## Movement
        # If sees enemies close enough then tries to move away from them 
        loc = bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1])
        enemies = gc.sense_nearby_units_by_team(loc, unit.vision_range, enemy_team)
        if len(enemies) > 0: 
            enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(loc))
            enemy_loc = enemies[0].location.map_location()
            best_dir = dir_away_from_enemy(gc, unit, loc, enemy_loc)

        # Otherwise, goes to locations in need of healers
        else: 
            if unit.id in assigned_overcharge: 
                ally = assigned_overcharge[unit.id]
                best_loc = ally.location.map_location()
            elif unit.id in assigned_healers: 
                best_loc = assigned_healers[unit.id]
            else: 
                best_dir = get_explore_dir(gc, unit, loc, variables.directions)

        # Special movement if already within healing range of the best location
        if best_loc is not None and sense_util.distance_squared_between_coords(unit_loc, best_loc) < unit.attack_range():
            best_loc = None ## Change this

        ## Do shit
        if best_target is not None:
            if overcharge and gc.is_overcharge_ready(unit.id):
                gc.overcharge(unit.id, best_target.id)
            if heal and gc.is_heal_ready(unit.id):
                gc.heal(unit.id, best_target.id)
        if best_dir is not None and gc.is_move_ready(unit.id): 
            gc.move_robot(unit.id, best_dir)
            add_new_location(unit.id, unit_loc, best_dir)
        elif best_loc is not None and gc.is_move_ready(unit.id) and unit_loc != best_loc:
            try_move_smartly(unit, unit_loc, best_loc)

def assign_to_quadrant(gc, unit, unit_loc): 
    """
    Assigns knight to a quadrant in need of help. 
    """
    quadrant_battles = variables.quadrant_battle_locs
    assigned_healers = variables.assigned_healers

    best_quadrant = (None, None)
    best_coeff = -float('inf')

    for quadrant in quadrant_battles: 
        q_info = quadrant_battles[quadrant]
        coeff = q_info.urgency_coeff(healer=True)
        # distance =  ADD DISTANCE COEFF TOO
        if coeff > best_coeff: 
            best_quadrant = quadrant 
            best_coeff = coeff

    if best_coeff > 0: 
        assigned_healers[unit.id] = quadrant_battles[best_quadrant].bottom_left
        return True, best_quadrant
    return False, None

def try_move_smartly(unit, map_loc1, map_loc2):
	if variables.gc.is_move_ready(unit.id):
		our_coords = map_loc1
		target_coords = map_loc2
		explore.add_bfs(variables.bfs_dict, target_coords, passable_locations)
		#target_coords_thirds = (int(map_loc2.x / variables.bfs_fineness), int(map_loc2.y / variables.bfs_fineness))
		if (our_coords, target_coords) in variables.bfs_dict:
			best_dirs = Ranger.use_dist_bfs(our_coords, target_coords, variables.bfs_dict)
			choice_of_dir = random.choice(best_dirs)
			shape = variables.direction_to_coord[choice_of_dir]
			options = sense_util.get_best_option(shape)
			for option in options:
				if variables.gc.can_move(unit.id, option):
					variables.gc.move_robot(unit.id, option)
					## CHANGE LOC IN NEW DATA STRUCTURE
					add_new_location(unit.id, our_coords, option)
					break

def add_new_location(unit_id, old_coords, direction):
    unit_mov = variables.direction_to_coord[direction]
    new_coords = (old_coords[0]+unit_mov[0], old_coords[1]+unit_mov[1])
    variables.unit_locations[unit_id] = new_coords

    old_quadrant = (int(old_coords[0] / variables.quadrant_size), int(old_coords[1] / variables.quadrant_size))
    new_quadrant = (int(new_coords[0] / variables.quadrant_size), int(new_coords[1] / variables.quadrant_size))

    if old_quadrant != new_quadrant: 
        variables.quadrant_battle_locs[old_quadrant].remove_ally(unit_id)
        variables.quadrant_battle_locs[new_quadrant].add_ally(unit_id, "healer")

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

def get_best_direction(gc, unit_id, unit_loc, target_loc, direction_to_coord, bfs_dict, bfs_fineness):
    start_coords = (unit_loc.x, unit_loc.y)
    target_coords = (target_loc.x, target_loc.y)
    explore.add_bfs(bfs_dict, target_coords, passable_locations)
    #target_coords_thirds = (int(target_loc.x/bfs_fineness), int(target_loc.y/bfs_fineness))
    if (start_coords, target_coords) in bfs_dict:
        best_dirs = Ranger.use_dist_bfs(start_coords, target_coords, bfs_dict)
        choice_of_dir = random.choice(best_dirs)
        shape = direction_to_coord[choice_of_dir]
        options = sense_util.get_best_option(shape)
        for option in options:
            if gc.can_move(unit_id, option):
                return option
        return variables.directions[8]
    return None


def get_best_target(gc, unit, coords, my_team):
    ## Attempt to heal nearby units
    loc = bc.MapLocation(variables.curr_planet, coords[0], coords[1])
    nearby = gc.sense_nearby_units_by_team(loc, unit.ability_range()-1, my_team)
    if len(nearby) > 0: 
        nearby = sorted(nearby, key=lambda x: x.health/x.max_health)
        for ally in nearby: 
            if gc.can_heal(unit.id, ally.id) and ally.health < ally.max_health: 
                return ally
    return None

def get_dangerous_allies(gc, loc, radius, team):
    DANGEROUS = [bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage]
    allies = gc.sense_nearby_units_by_team(loc, radius, team)
    dangerous_allies = 0
    for ally in allies: 
        if ally.unit_type in DANGEROUS: 
            dangerous_allies += 1

    return dangerous_allies

def update_healers():
    """
    Remove dead healers from healer dict and overcharge dict.
    If healer target loc has no allied units then remove from dictionary.
    Checks overcharge targets are still alive. 
    """
    gc = variables.gc
    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets

    ## Remove dead healers from assigned healers OR healers with expired locations
    remove = set()
    for healer_id in assigned_healers:
        if healer_id not in variables.my_unit_ids: 
            remove.add(healer_id)

    for healer_id in remove: 
        if healer_id in assigned_healers: 
            del assigned_healers[healer_id]

    ## Remove dead healers from assigned overcharge
    remove = set()
    for healer_id in assigned_overcharge:
        if healer_id not in variables.my_unit_ids:
            remove.add(healer_id)

    for healer_id in remove:
        del assigned_overcharge[healer_id]

    ## Remove dead overcharge targets 
    remove = set()
    for ally_id in overcharge_targets: 
        if ally_id not in variables.my_unit_ids:
            remove.add(ally_id)

    for ally_id in remove:
        overcharge_targets.remove(ally_id)




