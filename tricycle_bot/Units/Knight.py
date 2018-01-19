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
    Remove locations that aren't valid anymore.
    """
    remove = set()
    for loc_coords in battle_locs:
        loc = bc.MapLocation(bc.Planet.Earth,loc_coords[0],loc_coords[1])
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

    # if unit.id not in seen_knights_ids and location.is_on_map(): 
    #     unit_loc = location.map_location()
    #     ## Clustering: if has a goal location keep moving there
    #     if unit.id in knight_to_cluster: 
    #         try:
    #             print('cluster!')
    #             c = knight_to_cluster[unit.id]
    #             valid_cluster= clusters.knight_cluster_sense(gc, unit, unit_loc, c, knight_to_cluster)
    #             if not valid_cluster: 
    #                 clusters.remove_cluster(c, knight_to_cluster)
    #                 # print('removed cluster')
    #             else: 
    #                 seen_knights_ids.update(c.cluster_units())
    #                 ## Update next battle locations
    #                 enemy_loc = c.target_loc
    #                 f_f_quad = (int(enemy_loc.x / 5), int(enemy_loc.y / 5))
    #                 if f_f_quad not in next_battle_locs:
    #                     next_battle_locs[f_f_quad] = (unit_loc, 1)
    #                 else:
    #                     next_battle_locs[f_f_quad] = (next_battle_locs[f_f_quad][0], next_battle_locs[f_f_quad][1]+1)

    #         except: 
    #             print('KNIGHT clustering sense didnt run')
    #             pass

    #     # elif len(list(knight_to_cluster.keys())) < 20:
    #     else: 
    #         try: 
    #             enemy = knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN, constants)
    #         except:
    #             print('KNIGHT sense didnt run')
    #             pass

    #         ## Movement
    #         if len(battle_locs) > 0: 
    #             weakest = random.choice(list(battle_locs.keys()))
    #             target_loc = battle_locs[weakest][0]

    #             shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
    #             directions = sense_util.get_best_option(shape)

    #             if directions is not None:
    #                 if len(directions) > 0 and gc.is_move_ready(unit.id): 
    #                     for d in directions: 
    #                         if gc.can_move(unit.id, d):
    #                             gc.move_robot(unit.id, d)
    #                             #print('HEALER moved to battle loc!')
    #                             break
    #         else:  
    #             ## Knight movement away from allies
    #             if direction == None:  
    #                 nearby = gc.sense_nearby_units(unit_loc,8)
    #                 direction = sense_util.best_available_direction(gc,unit,nearby)

    #             if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
    #                 gc.move_robot(unit.id, direction)
    #                 # print('moved no cluster')


# def knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN, constants): 
#     """
#     This function chooses the direction the knight should move in. If it senses enemies nearby 
#     then will return direction that it can move to. If it can attack it will say if it is in
#     range for regular attack and/or javelin.
#     Otherwise, will attempt to group with other allied knights and return a direction to clump
#     the knights up. 

#     Returns: New desired direction. 
#     """
#     new_direction = None

#     try:
#         enemies = gc.sense_nearby_units_by_team(unit_loc, int(unit.vision_range/2), constants.enemy_team)
#     except: 
#         print('KNIGHTS ARE SAD')
#         pass

#     if len(enemies) > 0:        
#         enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))

#         ## Remove knights if their clusters are too small
#         unavailable_knight_ids = set()
#         for u_knight_id in knight_to_cluster: 
#             cluster = knight_to_cluster[u_knight_id]
#             if len(cluster.cluster_units()) >= KNIGHT_CLUSTER_MIN: 
#                 unavailable_knight_ids.add(u_knight_id)

#         ## Create cluster! 
#         new_cluster = clusters.create_knight_cluster(gc, unit, unit_loc, enemies[0], unavailable_knight_ids)

#         cluster_unit_ids = new_cluster.cluster_units()
#         for unit_id in cluster_unit_ids: 
#             knight_to_cluster[unit_id] = new_cluster
#     # else:
#     #     print('knight no enemies')
