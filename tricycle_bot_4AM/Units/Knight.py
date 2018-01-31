import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.attack as attack
import Units.variables as variables

import Units.Ranger as Ranger

order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]
knight_unit_priority = [1, 3, 3, 2, 3, 2, 2]
battle_radius = 9

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    gc = variables.gc

    assigned_knights = variables.assigned_knights
    quadrant_battles = variables.quadrant_battle_locs
    unit_locations = variables.unit_locations
    
    info = variables.info

    my_team = variables.my_team
    enemy_team = variables.enemy_team
    directions = variables.directions

    best_loc = None ## (x,y)
    best_dir = None
    best_target = None
    location = unit.location

    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    if location.is_on_map(): 
        if unit.id not in unit_locations:
            loc = unit.location.map_location()
            unit_locations[unit.id] = (loc.x,loc.y)
            f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
            quadrant_battles[f_f_quad].add_ally(unit.id, "knight")
            variables.knight_attacks[unit.id] = 0
        
        unit_loc = unit_locations[unit.id]

        ## Movement 
        # If new knight assign to location 
        if unit.id not in assigned_knights:
            assigned, best_loc = assign_to_quadrant(gc, unit, unit_loc)
            if not assigned:
                unit_loc_map = bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1])
                best_dir = Ranger.run_towards_init_loc_new(gc, unit, unit_loc_map, variables.direction_to_coord)
                #nearby = gc.sense_nearby_units_by_team(bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1]), 8, variables.my_team)
                #best_dir = sense_util.best_available_direction(gc,unit,nearby)
        else: 
            best_loc = assigned_knights[unit.id]

        ## Attack based on if in quadrant 
        if best_loc is not None: 
            curr_quadrant = (int(unit_loc[0] / quadrant_size), int(unit_loc[1] / quadrant_size))
            best_loc_quadrant = (int(best_loc[0] / quadrant_size), int(best_loc[1] / quadrant_size))

            ## If in best quadrant already, then get best_loc towards the target
            if curr_quadrant == best_loc_quadrant: 
                best_target, best_loc = get_best_target_in_quadrant(gc, unit, unit_loc, knight_unit_priority)

            else:
                best_target = get_best_target(gc, unit, unit_loc, knight_unit_priority)

        ## Do shit
        # Attack
        if best_target is not None and gc.can_attack(unit.id, best_target.id):  # checked if ready to attack in get best target 
            gc.attack(unit.id, best_target.id)
            variables.knight_attacks[unit.id] += 1
                
        # Move
        if best_loc is not None and gc.is_move_ready(unit.id) and unit_loc != best_loc: 
            try_move_smartly(unit, unit_loc, best_loc)
        elif best_dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, best_dir):
            gc.move_robot(unit.id, best_dir)
            add_new_location(unit.id, unit_loc, best_dir)

def assign_to_quadrant(gc, unit, unit_loc): 
    """
    Assigns knight to a quadrant in need of help. 
    """
    quadrant_battles = variables.quadrant_battle_locs
    assigned_knights = variables.assigned_knights

    if variables.curr_planet == bc.Planet.Earth: 
        diagonal = (variables.earth_diagonal)
    else:
        diagonal = (variables.mars_diagonal)

    best_quadrant = (None, None)
    best_coeff = -float('inf')

    for quadrant in quadrant_battles: 
        q_info = quadrant_battles[quadrant]
        if q_info.target_loc is not None: 
            coeff = q_info.urgency_coeff("knight")
            bfs_array = variables.bfs_array
            our_coords_val = Ranger.get_coord_value(unit_loc)
            target_coords_val = Ranger.get_coord_value(q_info.target_loc)
            if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
                distance = bfs_array[our_coords_val, target_coords_val]
                coeff += 3*(1 - distance/diagonal)
                if coeff > best_coeff: 
                    best_quadrant = quadrant 
                    best_coeff = coeff

    if best_coeff > 0: 
        assigned_knights[unit.id] = quadrant_battles[best_quadrant].target_loc
        return True, assigned_knights[unit.id]
    return False, None

def try_move_smartly(unit, map_loc1, map_loc2):
    if variables.gc.is_move_ready(unit.id):
        our_coords = map_loc1
        target_coords = map_loc2
        bfs_array = variables.bfs_array
        our_coords_val = Ranger.get_coord_value(our_coords)
        target_coords_val = Ranger.get_coord_value(target_coords)
        if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
            best_dirs = Ranger.use_dist_bfs(our_coords, target_coords, bfs_array)
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
    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    unit_mov = variables.direction_to_coord[direction]
    new_coords = (old_coords[0]+unit_mov[0], old_coords[1]+unit_mov[1])
    variables.unit_locations[unit_id] = new_coords

    old_quadrant = (int(old_coords[0] / quadrant_size), int(old_coords[1] / quadrant_size))
    new_quadrant = (int(new_coords[0] / quadrant_size), int(new_coords[1] / quadrant_size))

    if old_quadrant != new_quadrant: 
        variables.quadrant_battle_locs[old_quadrant].remove_ally(unit_id)
        variables.quadrant_battle_locs[new_quadrant].add_ally(unit_id, "knight")


def get_best_target(gc, unit, loc_coords, priority_order, javelin=False):
    assigned_knights = variables.assigned_knights

    enemy_team = variables.enemy_team
    location = bc.MapLocation(variables.curr_planet,loc_coords[0],loc_coords[1])
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), enemy_team)
    if len(vuln_enemies)==0 or not gc.is_attack_ready(unit.id):
        return None
    best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order))
    
    ## Make this the new target loc
    if not variables.knight_rush: 
        best_target_loc = best_target.location.map_location()
        assigned_knights[unit.id] = (best_target_loc.x, best_target_loc.y)
    return best_target

def get_best_target_in_quadrant(gc, unit, loc_coords, priority_order): 
    """
    Returns best_target, best_loc to move towards. 
    """
    quadrant_battles = variables.quadrant_battle_locs
    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    enemy_team = variables.enemy_team
    location = bc.MapLocation(variables.curr_planet,loc_coords[0],loc_coords[1])
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), enemy_team)
    # If there is a vuln enemy but can't attack then don't move
    if len(vuln_enemies) > 0:
        if not gc.is_attack_ready(unit.id):
            return (None, None)
        else: 
            best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order))
            return (best_target, None)
    # If there are no vuln enemies then look at vision range and choose to move towards nearby enemies
    else: 
        # vuln_enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, enemy_team)
        # if len(vuln_enemies) > 0: 
        #     best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order, far=True))
        #     best_loc = (best_target.location.map_location().x, best_target.location.map_location().y)
        #     return (None, best_loc)
        # return (None, None)
        quadrant = (int(loc_coords[0]/quadrant_size), int(loc_coords[1]/quadrant_size))
        q_info = quadrant_battles[quadrant]
        if len(q_info.enemy_locs) > 0:
            for loc in q_info.enemy_locs: 
                if is_accessible(loc_coords, loc): 
                    return (None, loc)
        return (None, q_info.target_loc)

def is_accessible(unit_loc, target_loc): 
    bfs_array = variables.bfs_array
    our_coords_val = Ranger.get_coord_value(unit_loc)
    target_coords_val = Ranger.get_coord_value(target_loc)
    if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
        return True 
    return False

def update_battles():
    """
    Remove locations & units that aren't valid anymore.
    """
    assigned_knights = variables.assigned_knights
    quadrant_battles = variables.quadrant_battle_locs
    knight_attacks = variables.knight_attacks

    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size
    
    ## Units
    remove_assigned = set()
    remove = set()
    for knight_id in knight_attacks:
        if knight_id not in assigned_knights and knight_id not in variables.my_unit_ids:
            remove.add(knight_id)
        elif knight_id in assigned_knights and knight_id not in variables.my_unit_ids:
            remove_assigned.add(knight_id)
            remove.add(knight_id)
        else: 
            loc = assigned_knights[knight_id]
            f_f_quad = (int(loc[0] / quadrant_size), int(loc[1] / quadrant_size))
            knight_coeff = quadrant_battles[f_f_quad].urgency_coeff("knight")
            if knight_coeff == 0: 
                remove_assigned.add(knight_id)

    for knight_id in remove_assigned: 
        del assigned_knights[knight_id]

    knights_dead_no_attack = 0
    total_dead_knights = 0
    for knight_id in remove:
        num_times_attacked = knight_attacks[knight_id]
        if num_times_attacked == 0: 
            knights_dead_no_attack += 1
        total_dead_knights += 1
        del knight_attacks[knight_id]

    if total_dead_knights == 0: 
        variables.died_without_attacking = 0
    else: 
        variables.died_without_attacking = knights_dead_no_attack / total_dead_knights


