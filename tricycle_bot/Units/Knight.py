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
        battle_locs = variables.earth_battles
        diagonal = variables.earth_diagonal
    else: 
        battle_locs = variables.mars_battles
        diagonal = variables.mars_diagonal

    next_turn_battle_locs = variables.next_turn_battle_locs

    assigned_knights = variables.assigned_knights
    direction_to_coord = variables.direction_to_coord
    precomputed_bfs = variables.precomputed_bfs
    bfs_fineness = variables.bfs_fineness
    info = variables.info

    my_team = variables.my_team
    enemy_team = variables.enemy_team
    directions = variables.directions

    best_loc = None
    best_target = None
    assign_to_loc = None ## (x,y)
    location = unit.location

    if location.is_on_map(): 
        unit_loc = location.map_location()

        ## Attack
        best_target = get_best_target(gc, unit, unit_loc, knight_unit_priority, enemy_team)
        if best_target is not None: 
            target_loc = best_target.location.map_location()
            add_location = evaluate_battle_location(gc, target_loc, battle_locs)
            if add_location: 
                battle_locs[(target_loc.x,target_loc.y)] = clusters.Cluster(allies=set(),enemies=set([best_target.id]))
                assign_to_loc = (target_loc.x,target_loc.y)

            f_f_quad = (int(target_loc.x / 5), int(target_loc.y / 5))
            if f_f_quad not in next_turn_battle_locs:
                next_turn_battle_locs[f_f_quad] = (unit_loc, 1)
            else:
                next_turn_battle_locs[f_f_quad] = (next_turn_battle_locs[f_f_quad][0], next_turn_battle_locs[f_f_quad][1]+1)

        ## Movement 
        # If new knight assign to location 
        if unit.id not in assigned_knights: 
            if assign_to_loc is not None: 
                battle_locs[assign_to_loc].add_ally(unit.id)
            elif len(battle_locs) > 0: 
                best_loc = get_best_location(gc, unit, unit_loc, battle_locs, planet, diagonal) ## MapLocation
                cluster = battle_locs[(best_loc.x,best_loc.y)]
                cluster.add_ally(unit.id)
                # if cluster.grouping_location is None:
                #     if best_loc.x < unit_loc.x: x = unit_loc.x - 2
                #     else: x = unit_loc.x + 2
                #     if best_loc.y < unit_loc.y: y = unit_loc.y - 2
                #     else: y = unit_loc.y + 2
                #     cluster.grouping_location = bc.MapLocation(planet, x, y)
                #     assigned_knights[unit.id] = bc.MapLocation(planet, x, y)
                # elif not cluster.grouped:
                #     assigned_knights[unit.id] = cluster.grouping_location
                # else: 
                    # assigned_knights[unit.id] = best_loc
                assigned_knights[unit.id] = best_loc
            else: 
                best_dir = get_explore_dir(gc, unit, unit_loc, directions)
                if best_dir is not None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, best_dir):
                    gc.move_robot(unit.id, best_dir)
        else:
            if assign_to_loc is not None: 
                current_loc = assigned_knights[unit.id]
                if (current_loc.x, current_loc.y) in battle_locs: 
                    battle_locs[(current_loc.x, current_loc.y)].remove_ally(unit.id)
                battle_locs[assign_to_loc].add_ally(unit.id)
                assigned_knights[unit.id] = bc.MapLocation(planet, assign_to_loc[0], assign_to_loc[1])
            best_loc = assigned_knights[unit.id]

        ## Do shit
        if best_target is not None and gc.can_attack(unit.id, best_target.id):  # checked if ready to attack in get best target 
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
    most_urgent_coeff = -1 ## 0 - 5

    for loc in battle_locs: 
        map_loc = bc.MapLocation(planet,loc[0],loc[1])
        distance_coeff = 2*(1 - (float(sense_util.distance_squared_between_maplocs(unit_loc,map_loc))/diagonal))
        coeff = battle_locs[loc].urgent
        if len(battle_locs[loc].enemies) > 0: 
            coeff = 2*(coeff + distance_coeff)
        else: 
            coeff = coeff + distance_coeff
        if coeff > most_urgent_coeff:
            most_urgent_coeff = coeff 
            most_urgent = map_loc

    return most_urgent

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

def get_best_direction(gc, unit, unit_loc, target_loc, direction_to_coord, precomputed_bfs, bfs_fineness):
    start_coords = (unit_loc.x, unit_loc.y)
    target_coords_thirds = (int(target_loc.x/bfs_fineness), int(target_loc.y/bfs_fineness))
    if (start_coords, target_coords_thirds) in precomputed_bfs:
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
    planet = gc.planet()
    if planet == bc.Planet.Earth: 
        battle_locs = variables.earth_battles
    else: 
        battle_locs = variables.mars_battles
    assigned_knights = variables.assigned_knights
    
    enemy_team = variables.enemy_team

    ## Locations
    remove = set()
    for loc_coords in battle_locs:
        cluster = battle_locs[loc_coords]
        found_enemy = cluster.update_enemies(gc, loc_coords, enemy_team)
        if not found_enemy:
            remove.add(loc_coords)
        # else:
        #     if cluster.allies_grouped(gc):
        #         for ally_id in cluster.allies: 
        #             if ally_id in assigned_knights: 
        #                 assigned_knights[ally_id] = bc.MapLocation(planet, loc_coords[0], loc_coords[1])

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




