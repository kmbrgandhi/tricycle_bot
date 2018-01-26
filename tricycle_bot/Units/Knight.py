import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.attack as attack
import Units.variables as variables

order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]
knight_unit_priority = [3, 2, 0.5, 0.5, 2, 3, 3]
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

    if location.is_on_map(): 
        # unit_loc = location.map_location()
        if unit.id not in unit_locations:
            loc = unit.location.map_location()
            unit_locations[unit.id] = (loc.x,loc.y)
        
        unit_loc = unit_locations[unit.id]

        ## Attack
        best_target = get_best_target(gc, unit, unit_loc, knight_unit_priority)

        ## Movement 
        # If new knight assign to location 
        if unit.id not in assigned_knights:
            assigned, best_loc = assign_to_quadrant(gc, unit, unit_loc)
            if not assigned: 
                nearby = gc.sense_nearby_units_by_team(bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1]), 8, variables.my_team)
                best_dir = sense_util.best_available_direction(gc,unit,nearby)  
        else: 
            best_loc = assigned_knights[unit.id]

        ## Do shit
        # Attack
        if best_target is not None and gc.can_attack(unit.id, best_target.id):  # checked if ready to attack in get best target 
            gc.attack(unit.id, best_target.id)
                
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

    best_quadrant = (None, None)
    best_coeff = -float('inf')

    for quadrant in quadrant_battles: 
        q_info = quadrant_battles[quadrant]
        coeff = q_info.urgency_coeff()
        # distance =  ADD DISTANCE COEFF TOO
        if coeff > best_coeff: 
            best_quadrant = quadrant 
            best_coeff = coeff

    if best_coeff > 0: 
        assigned_knights[unit.id] = quadrant_battles[best_quadrant].bottom_left
        return True, best_quadrant
    return False, None

def try_move_smartly(unit, coords1, coords2):
    if variables.gc.is_move_ready(unit.id):
        if int(coords1[0] / variables.bfs_fineness) == int(coords1[1] / variables.bfs_fineness) and int(coords2[0]/ variables.bfs_fineness)== int(coords2[1] / variables.bfs_fineness):#sense_util.distance_squared_between_maplocs(map_loc1, map_loc2) < (2 * variables.bfs_fineness ** 2)+1:
            map_loc1 = bc.MapLocation(variables.curr_planet, coords1[0], coords1[1])
            map_loc2 = bc.MapLocation(variables.curr_planet, coords2[0], coords2[1])
            d = map_loc1.direction_to(map_loc2)
        else:
            target_coords_thirds = (int(coords2[0] / variables.bfs_fineness), int(coords2[1] / variables.bfs_fineness))
            if (coords1, target_coords_thirds) in variables.precomputed_bfs:
                d = variables.precomputed_bfs[(coords1, target_coords_thirds)]
            else:
                map_loc1 = bc.MapLocation(variables.curr_planet, coords1[0], coords1[1])
                map_loc2 = bc.MapLocation(variables.curr_planet, coords2[0], coords2[1])
                d = map_loc1.direction_to(map_loc2)
        shape = variables.direction_to_coord[d]
        options = sense_util.get_best_option(shape)
        for option in options:
            if variables.gc.can_move(unit.id, option):
                variables.gc.move_robot(unit.id, option)
                ## CHANGE LOC IN NEW DATA STRUCTURE
                add_new_location(unit.id, coords1, option)
                break

def add_new_location(unit_id, old_coords, direction):
    unit_mov = variables.direction_to_coord[direction]
    new_coords = (old_coords[0]+unit_mov[0], old_coords[1]+unit_mov[1])
    variables.unit_locations[unit_id] = new_coords

    old_quadrant = (int(old_coords[0] / variables.quadrant_size), int(old_coords[1] / variables.quadrant_size))
    new_quadrant = (int(new_coords[0] / variables.quadrant_size), int(new_coords[1] / variables.quadrant_size))

    if old_quadrant != new_quadrant: 
        variables.quadrant_battle_locs[old_quadrant].remove_ally(unit_id)
        variables.quadrant_battle_locs[new_quadrant].add_ally(unit_id, "knight")


def get_best_target(gc, unit, loc_coords, priority_order, javelin=False):
    enemy_team = variables.enemy_team
    location = bc.MapLocation(variables.curr_planet,loc_coords[0],loc_coords[1])
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), enemy_team)
    if len(vuln_enemies)==0 or not gc.is_attack_ready(unit.id):
        return None
    best_target = max(vuln_enemies, key=lambda x: attack.coefficient_computation(gc, unit, x, location, priority_order))
    return best_target

def update_battles():
    """
    Remove locations & units that aren't valid anymore.
    """
    gc = variables.gc
    assigned_knights = variables.assigned_knights
    
    enemy_team = variables.enemy_team

    ## Units
    remove = set()
    for knight_id in assigned_knights:
        if knight_id not in variables.my_unit_ids:
            remove.add(knight_id)

    for knight_id in remove:
        del assigned_knights[knight_id]




