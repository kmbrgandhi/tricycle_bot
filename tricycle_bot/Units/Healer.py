import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.variables as variables
import Units.explore as explore
import Units.Ranger as Ranger

import time
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
    # print('HEALER ID: ', unit.id)

    if variables.collective_healer_time > 0.02:
        # print('simple')
        timestep_simple(unit)
    else:
        timestep_complex(unit)    

def timestep_complex(unit):
    gc = variables.gc  

    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    bfs_array = variables.bfs_array
    enemy_team = variables.enemy_team
    my_team = variables.my_team

    assigned_healers = variables.assigned_healers              ## healer id: (cluster, best_healer_loc)
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets

    quadrant_battles = variables.quadrant_battle_locs
    if variables.curr_planet == bc.Planet.Earth:
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    unit_locations = variables.unit_locations

    best_dir = None
    best_loc = None
    best_heal_target = None
    best_overcharge_target = None
    heal = False
    overcharge = False
    location = unit.location

    if location.is_on_map():
        #print(location.map_location())
        ## Add new ones to unit_locations, else just get the location
        if unit.id not in unit_locations:
            loc = unit.location.map_location()
            unit_locations[unit.id] = (loc.x,loc.y)
            f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
            quadrant_battles[f_f_quad].add_ally(unit.id, "healer")

        unit_loc = unit_locations[unit.id]

        ## Assign role
        if unit.id not in assigned_overcharge and unit.id not in assigned_healers:
            overcharge_to_total = 1
            total = len(assigned_healers) + len(assigned_overcharge)
            if total > 0: overcharge_to_total = len(assigned_overcharge) / total
            # Assign to overcharge if there are targets and ratio is good
            if variables.research.get_level(variables.unit_types["healer"]) == 3 and overcharge_to_total < 0.2 and len(overcharge_targets) > 0:
                best_overcharge_target = gc.unit(overcharge_targets.pop())
                assigned_overcharge[unit.id] = best_overcharge_target
            if gc.is_heal_ready(unit.id): 
                best_heal_target = get_best_target(gc, unit, unit_loc, my_team)
                if best_heal_target is not None:
                    heal = True
            assigned, best_loc = assign_to_quadrant(gc, unit, unit_loc)
            if not assigned:
                unit_loc_map = bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1])
                best_dir = Ranger.run_towards_init_loc_new(gc, unit, unit_loc_map, variables.direction_to_coord)

        ## Overcharge
        if unit.id in assigned_overcharge:
            ally = assigned_overcharge[unit.id]
            if gc.can_overcharge(unit.id, ally.id):
                overcharge = True
                best_overcharge_target = ally
        if best_heal_target is None and gc.is_heal_ready(unit.id):
            best_heal_target = get_best_target(gc, unit, unit_loc, my_team)
            if best_heal_target is not None:
                heal = True

        ## Movement
        # If sees enemies close enough then tries to move away from them
        loc = bc.MapLocation(variables.curr_planet, unit_loc[0], unit_loc[1])
        enemies = gc.sense_nearby_units_by_team(loc, unit.vision_range, enemy_team)
        if len(enemies) > 0:
            enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(loc))
            enemy_loc = enemies[0].location.map_location()
            battle_quadrant = (int(enemy_loc.x/5), int(enemy_loc.y/5))
            if battle_quadrant not in variables.next_turn_battle_locs: 
                variables.next_turn_battle_locs[battle_quadrant] = (enemy_loc, 1)
            best_dir = dir_away_from_enemy(gc, unit, loc, enemy_loc)
        elif variables.curr_round > 650: 
            best_dir = Ranger.move_to_rocket(gc, unit, loc, variables.direction_to_coord, variables.bfs_array)
        # Otherwise, goes to locations in need of healers
        else:
            if unit.id in assigned_overcharge:
                ally = assigned_overcharge[unit.id]
                best_loc_map = ally.location.map_location()
                best_loc = (best_loc_map.x, best_loc_map.y)
            elif unit.id in assigned_healers:
                best_loc = assigned_healers[unit.id][1]

        ## Do shit
        #print(best_dir)
        #print(best_loc)
        if best_overcharge_target is not None:
            if overcharge and gc.is_overcharge_ready(unit.id):
                gc.overcharge(unit.id, best_overcharge_target.id)
                overcharged_unit = gc.unit(best_overcharge_target.id)
                if overcharged_unit.unit_type == variables.unit_types["ranger"]:
                    Ranger.timestep(overcharged_unit)
        if best_heal_target is not None:
            if heal and gc.can_heal(unit.id, best_heal_target.id):
                gc.heal(unit.id, best_heal_target.id)
        if best_dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id,best_dir):
            gc.move_robot(unit.id, best_dir)
            add_new_location(unit.id, unit_loc, best_dir)
        elif best_loc is not None and gc.is_move_ready(unit.id) and unit_loc != best_loc:
            try_move_smartly(unit, unit_loc, best_loc)


def timestep_simple(unit):
    gc = variables.gc

    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    bfs_array = variables.bfs_array
    enemy_team = variables.enemy_team
    my_team = variables.my_team

    assigned_healers = variables.assigned_healers              ## healer id: (cluster, best_healer_loc)
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets

    quadrant_battles = variables.quadrant_battle_locs
    if variables.curr_planet == bc.Planet.Earth:
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    unit_locations = variables.unit_locations

    best_loc = None
    best_heal_target = None
    location = unit.location

    if location.is_on_map():
        ## Track location
        if unit.id not in unit_locations:
            loc = unit.location.map_location()
            unit_locations[unit.id] = (loc.x,loc.y)
            f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
            quadrant_battles[f_f_quad].add_ally(unit.id, "healer")

        unit_loc = unit_locations[unit.id]

        ## Assign
        if unit.id not in assigned_healers: 
            for quadrant in quadrant_battles: 
                q_info = quadrant_battles[quadrant]
                if q_info.in_battle[0]: 
                    healer_loc = choose_healer_loc(q_info, unit_loc)
                    if healer_loc is not None: 
                        assigned_healers[unit.id] = (quadrant, healer_loc)
                        best_loc = healer_loc

        ## Heal
        if gc.is_heal_ready(unit.id): 
            best_heal_target = get_best_target(gc, unit, unit_loc, my_team)

        ## Do stuff 
        if best_heal_target is not None and gc.can_heal(unit.id, best_heal_target.id):
            gc.heal(unit.id, best_heal_target.id)
        if best_loc is not None and gc.is_move_ready(unit.id) and unit_loc != best_loc:
            try_move_smartly(unit, unit_loc, best_loc)


def assign_to_quadrant(gc, unit, unit_loc):
    """
    Assigns knight to a quadrant in need of help.
    """
    quadrant_battles = variables.quadrant_battle_locs
    assigned_healers = variables.assigned_healers

    quadrants = [x for x in quadrant_battles]
    quadrants = sorted(quadrants, key=lambda x: quadrant_battles[x].urgency_coeff("healer"), reverse=True)

    for quadrant in quadrants: 
        q_info = quadrant_battles[quadrant]
        if q_info.urgency_coeff("healer") > 0:
            healer_loc = choose_healer_loc(q_info, unit_loc)
            if healer_loc is not None: 
                assigned_healers[unit.id] = (quadrant, healer_loc)
                q_info.assigned_healers[unit.id] = healer_loc
                return True, healer_loc
        else: 
            break
    return False, None

def choose_healer_loc(q_info, unit_loc):
    possible_healer_locs = q_info.healer_locs
    if len(possible_healer_locs) > 0:
        for healer_loc in possible_healer_locs: 
            if is_accessible(unit_loc, healer_loc): 
                # q_info.healer_locs.remove(healer_loc)
                return healer_loc
    else: 
        return q_info.target_loc

def is_accessible(unit_loc, target_loc): 
    bfs_array = variables.bfs_array
    our_coords_val = Ranger.get_coord_value(unit_loc)
    target_coords_val = Ranger.get_coord_value(target_loc)
    if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
        return True 
    return False

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

# def get_best_target_opt(gc, unit, coords, my_team, quadrant_size): 
#     assigned_healers = variables.assigned_healers

#     quadrant = (int(coords[0]/quadrant_size),int(coords[1]/quadrant_size))

#     if unit.id in assigned_healers: 
#         assignment = assigned_healers[unit.id]
#         quadrant_loc = (int(assignment[1][0]/quadrant_size), int(assignment[1][1]/quadrant_size))
#         assigned_quadrant = assignment[0]
#         if quadrant == quadrant_loc: 
#             q_info1 = variables.quadrant_battle_locs[quadrant_loc]
#             q_info2 = variables.quadrant_battle_locs[assigned_quadrant]
#             fighters = q_info1.fighters() | q_info2.fighters()
#             allies = q_info1.all_allies() | q_info2.all_allies()
#         else: 
#             q_info = variables.quadrant_battle_locs[quadrant]
#             fighters = q_info.fighters() 
#             allies = q_info.all_allies()

#         if len(fighters) > 0: 
#             allies = []
#             for ally_id in allies: 
#                 ally_loc = variables.unit_locations[ally_id]
#                 distance = sense_util.distance_squared_between_coords(coords, ally_loc)
#                 if distance < 30: # heal range = 30
#                     ally = gc.unit(ally_id)
#                     allies.append((ally, ally.health/ally.max_health))
#             if len(allies) > 0:
#                 allies = sorted(allies, key=lambda x: x[1])
#                 return allies[0]
#     return None

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
    variables.overcharge_targets = set()
    quadrant_battles = variables.quadrant_battle_locs

    if variables.curr_planet == bc.Planet.Earth:
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    ## Remove dead healers from assigned healers OR healers with expired locations
    remove = set()
    for healer_id in assigned_healers:
        f_f_quad, loc = assigned_healers[healer_id]
        if healer_id not in variables.my_unit_ids:
            remove.add((healer_id, f_f_quad))
        else:
            healer_coeff = quadrant_battles[f_f_quad].urgency_coeff_without_add_units("healer")
            if healer_coeff == 0:
                remove.add((healer_id,f_f_quad))

    for healer_id, f_f_quad in remove:
        if healer_id in assigned_healers:
            del assigned_healers[healer_id]
        q_info = quadrant_battles[f_f_quad]
        if healer_id in q_info.assigned_healers: 
            del q_info.assigned_healers[healer_id]

    # ## Remove dead healers from assigned overcharge
    # remove = set()
    # for healer_id in assigned_overcharge:
    #     if healer_id not in variables.my_unit_ids:
    #         remove.add(healer_id)

    # for healer_id in remove:
    #     del assigned_overcharge[healer_id]

    # ## Remove dead overcharge targets
    # remove = set()
    # for ally_id in overcharge_targets:
    #     if ally_id not in variables.my_unit_ids:
    #         remove.add(ally_id)

    # for ally_id in remove:
    #     overcharge_targets.remove(ally_id)






"""
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
    # print('HEALER ID: ', unit.id)
    gc = variables.gc

    composition = variables.info
    direction_to_coord = variables.direction_to_coord
    bfs_array = variables.bfs_array
    enemy_team = variables.enemy_team
    my_team = variables.my_team

    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    overcharge_targets = variables.overcharge_targets

    quadrant_battles = variables.quadrant_battle_locs
    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

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
            f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
            quadrant_battles[f_f_quad].add_ally(unit.id, "healer")

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
                # print('assigned? ', assigned)
                # print('assigned loc: ', best_loc)
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
                best_loc_map = ally.location.map_location()
                best_loc = (best_loc_map.x, best_loc_map.y)

            elif unit.id in assigned_healers:
                best_loc = assigned_healers[unit.id]

            #     print('already had a loc: ', best_loc)
            # else:
            #     print('UH OH')


        # # Special movement if already within healing range of the best location
        # if best_loc is not None and sense_util.distance_squared_between_coords(unit_loc, best_loc) < unit.attack_range()/2:
        #     best_loc = None ## Change this
        #     print('oopz too close')

        ## Do shit
        if best_target is not None:
            if overcharge and gc.is_overcharge_ready(unit.id):
                gc.overcharge(unit.id, best_target.id)
                overcharged_unit = gc.unit(best_target.id)
                if overcharged_unit.unit_type == variables.unit_types["ranger"]:
                    print(overcharged_unit.location.map_location())
                    Ranger.timestep(overcharged_unit)
            if heal and gc.is_heal_ready(unit.id):
                gc.heal(unit.id, best_target.id)
        if best_dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id,best_dir): 
            gc.move_robot(unit.id, best_dir)
            add_new_location(unit.id, unit_loc, best_dir)
        elif best_loc is not None and gc.is_move_ready(unit.id) and unit_loc != best_loc:
            try_move_smartly(unit, unit_loc, best_loc)

def assign_to_quadrant(gc, unit, unit_loc):
    quadrant_battles = variables.quadrant_battle_locs
    assigned_healers = variables.assigned_healers

    best_quadrant = (None, None)
    best_coeff = -float('inf')

    for quadrant in quadrant_battles: 
        q_info = quadrant_battles[quadrant]
        coeff = q_info.urgency_coeff("healer")
        # distance =  ADD DISTANCE COEFF TOO
        if coeff > best_coeff and q_info.healer_loc is not None: 
            best_quadrant = quadrant 
            best_coeff = coeff

    if best_coeff > 0: 
        assigned_healers[unit.id] = quadrant_battles[best_quadrant].healer_loc
        return True, assigned_healers[unit.id]
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
    gc = variables.gc
    assigned_healers = variables.assigned_healers
    assigned_overcharge = variables.assigned_overcharge
    variables.overcharge_targets = set([])
    overcharge_targets = variables.overcharge_targets
    quadrant_battles = variables.quadrant_battle_locs

    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    ## Remove dead healers from assigned healers OR healers with expired locations
    remove = set()
    for healer_id in assigned_healers:
        if healer_id not in variables.my_unit_ids: 
            remove.add(healer_id)
        else: 
            loc = assigned_healers[healer_id]
            f_f_quad = (int(loc[0] / quadrant_size), int(loc[1] / quadrant_size))
            healer_coeff = quadrant_battles[f_f_quad].urgency_coeff("healer")
            if healer_coeff == 0: 
                remove.add(healer_id)

    for healer_id in remove: 
        if healer_id in assigned_healers: 
            del assigned_healers[healer_id]

    # ## Remove dead healers from assigned overcharge
    # remove = set()
    # for healer_id in assigned_overcharge:
    #     if healer_id not in variables.my_unit_ids:
    #         remove.add(healer_id)

    # for healer_id in remove:
    #     del assigned_overcharge[healer_id]

    # ## Remove dead overcharge targets 
    # remove = set()
    # for ally_id in overcharge_targets: 
    #     if ally_id not in variables.my_unit_ids:
    #         remove.add(ally_id)

    # for ally_id in remove:
    #     overcharge_targets.remove(ally_id)

"""


