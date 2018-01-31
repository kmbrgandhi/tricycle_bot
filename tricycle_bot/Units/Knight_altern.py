import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.explore as explore
import Units.variables as variables
import Units.Ranger as Ranger
import time

if variables.curr_planet == bc.Planet.Earth:
    passable_locations = variables.passable_locations_earth
else:
    passable_locations = variables.passable_locations_mars
order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]  # storing order of units
knight_unit_priority = [1, 3, 3, 1, 3, 4, 3.4]
directions = variables.directions

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return
    # start_time = time.time()
    gc = variables.gc
    knight_roles = variables.knight_roles
    info = variables.info
    next_turn_battle_locs = variables.next_turn_battle_locs

    if unit.id in knight_roles["go_to_mars"] and info[6] == 0:
        knight_roles["go_to_mars"].remove(unit.id)
    if unit.id not in knight_roles["fighter"]:
        knight_roles["fighter"].append(unit.id)

    # if variables.print_count<10:
    # print("Preprocessing:", time.time()-start_time)

    location = unit.location
    my_team = variables.my_team
    targeting_units = variables.targeting_units

    quadrant_battles = variables.quadrant_battle_locs
    if variables.curr_planet == bc.Planet.Earth:
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    if location.is_on_map():
        ## Add new ones to unit_locations, else just get the location
        if unit.id not in variables.unit_locations:
            loc = unit.location.map_location()
            variables.unit_locations[unit.id] = (loc.x, loc.y)
            f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
            quadrant_battles[f_f_quad].add_ally(unit.id, "knight")

        # start_time = time.time()
        map_loc = location.map_location()
        if variables.curr_planet == bc.Planet.Earth and len(knight_roles["go_to_mars"]) < 14 and unit.id not in \
                knight_roles["go_to_mars"] and unit.id in knight_roles["fighter"]:
            for rocket in variables.rocket_locs:
                target_loc = variables.rocket_locs[rocket]
                if sense_util.distance_squared_between_maplocs(map_loc, target_loc) < 150:
                    variables.which_rocket[unit.id] = (target_loc, rocket)
                    knight_roles["go_to_mars"].append(unit.id)
                    knight_roles["fighter"].remove(unit.id)
                    break
        # if variables.print_count < 10:
        #    print("Preprocessing inside:", time.time() - start_time)
        # start_time = time.time()
        dir, attack_target, javelin, move_then_attack, visible_enemies, closest_enemy, signals = knight_sense(gc, unit,
                                                                                                            variables.last_turn_battle_locs,
                                                                                                            knight_roles,
                                                                                                            map_loc,
                                                                                                            variables.direction_to_coord,
                                                                                                            variables.bfs_array,
                                                                                                            targeting_units,
                                                                                                            variables.rocket_locs)
        # print("middlepart",time.time() - start_coord)
        # if variables.print_count < 10:
        #    print("Sensing:", time.time() - start_time)
        # start_time = time.time()
        if visible_enemies and closest_enemy is not None:
            enemy_loc = closest_enemy.location.map_location()
            f_f_quad = (int(enemy_loc.x / 5), int(enemy_loc.y / 5))
            if f_f_quad not in next_turn_battle_locs:
                next_turn_battle_locs[f_f_quad] = (enemy_loc, 1)
            else:
                next_turn_battle_locs[f_f_quad] = (
                next_turn_battle_locs[f_f_quad][0], next_turn_battle_locs[f_f_quad][1] + 1)

        if move_then_attack:
            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)
                ## CHANGE LOC IN NEW DATA STRUCTURE
                add_new_location(unit.id, (map_loc.x, map_loc.y), dir)

            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id] += 1
                gc.attack(unit.id, attack_target.id)
                if unit.id in variables.knight_attacks:
                    variables.knight_attacks[unit.id] += 1
                else:
                    variables.knight_attacks[unit.id] = 1
                variables.overcharge_targets.add(unit.id)

        else:
            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id] += 1
                gc.attack(unit.id, attack_target.id)
                if unit.id in variables.knight_attacks:
                    variables.knight_attacks[unit.id] += 1
                else:
                    variables.knight_attacks[unit.id] = 1
                variables.overcharge_targets.add(unit.id)

            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)
                ## CHANGE LOC IN NEW DATA STRUCTURE
                add_new_location(unit.id, (map_loc.x, map_loc.y), dir)

def go_to_mars_sense(gc, unit, battle_locs, location, enemies, direction_to_coord, bfs_array, targeting_units,
                     rocket_locs):
    # print('GOING TO MARS')
    signals = {}
    dir = None
    attack = None
    javelin = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False

    if len(enemies) > 0:
        visible_enemies = True
        attack = get_attack(gc, unit, location, targeting_units)
    start_coords = (location.x, location.y)

    # # rocket was launched
    if unit.id not in variables.which_rocket or variables.which_rocket[unit.id][1] not in variables.rocket_locs:
        variables.knight_roles["go_to_mars"].remove(unit.id)
        return dir, attack, javelin, move_then_attack, visible_enemies, closest_enemy, signals
    target_loc = variables.which_rocket[unit.id][0]

    # # rocket was destroyed
    if not gc.has_unit_at_location(target_loc):
        variables.knight_roles["go_to_mars"].remove(unit.id)
        return dir, attack, javelin, move_then_attack, visible_enemies, closest_enemy, signals
    # print(unit.id)
    # print('MY LOCATION:', start_coords)
    # print('GOING TO:', target_loc)
    if max(abs(target_loc.x - start_coords[0]), abs(target_loc.y - start_coords[1])) == 1:
        rocket = gc.sense_unit_at_location(target_loc)
        if gc.can_load(rocket.id, unit.id):
            gc.load(rocket.id, unit.id)
    else:
        target_coords = (target_loc.x, target_loc.y)
        start_coords_val = Ranger.get_coord_value(start_coords)
        target_coords_val = Ranger.get_coord_value(target_coords)
        # target_coords_thirds = (int(target_loc.x / bfs_fineness), int(target_loc.y / bfs_fineness))

        if bfs_array[start_coords_val, target_coords_val] != float('inf'):
            best_dirs = Ranger.use_dist_bfs(start_coords, target_coords, bfs_array)
            choice_of_dir = random.choice(best_dirs)
            shape = direction_to_coord[choice_of_dir]
            options = sense_util.get_best_option(shape)
            for option in options:
                if gc.can_move(unit.id, option):
                    dir = option
                    break
                    # print(dir)

    return dir, attack, javelin, move_then_attack, visible_enemies, closest_enemy, signals


def knight_sense(gc, unit, battle_locs, knight_roles, location, direction_to_coord, bfs_array, targeting_units,
                 rocket_locs):
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, variables.enemy_team)
    if unit.id in knight_roles["go_to_mars"]:
        return go_to_mars_sense(gc, unit, battle_locs, location, enemies, direction_to_coord, bfs_array,
                                targeting_units, rocket_locs)
    signals = {}
    dir = None
    attack = None
    javelin = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    # if variables.print_count < 10:
    #    print("Sensing nearby units:", time.time() - start_time)
    if len(enemies) > 0:
        visible_enemies = True
        closest_enemy = None
        closest_dist = -float('inf')
        for enemy in enemies:
            enemy_loc = enemy.location
            if enemy_loc.is_on_map():
                enemy_map_loc = enemy_loc.map_location()
                coeff = Ranger.coefficient_computation(gc, unit, enemy, enemy_map_loc, location)
                # dist = sense_util.distance_squared_between_maplocs(loc.map_location(), location)
                if coeff > closest_dist:
                    closest_dist = coeff
                    closest_enemy = enemy
        # if variables.print_count < 10:
        #    print("Getting closest enemy:", time.time() - start_time)
        # sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        # closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        attack = get_attack(gc, unit, location, targeting_units, knight_unit_priority)

        if attack is not None:
            if closest_enemy is not None:
                dir = Ranger.go_to_loc(unit, location,
                                closest_enemy.location.map_location())  # optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
        else:
            if gc.is_move_ready(unit.id):
                if closest_enemy is not None:
                    dir = Ranger.go_to_loc(unit, location,
                                    closest_enemy.location.map_location())  # optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                    if dir is None or dir == variables.directions[8]:
                        dir = Ranger.optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                    next_turn_loc = location.add(dir)
                    attack = get_attack(gc, unit, next_turn_loc, targeting_units, knight_unit_priority)
                    if attack is not None:
                        move_then_attack = True
                else:
                    if variables.curr_planet == bc.Planet.Earth:
                        # print('IS RUNNING TOWARDS INIT LOC')
                        dir = Ranger.run_towards_init_loc_new(gc, unit, location, direction_to_coord)
                    else:
                        # print('EXPLORING')
                        dir = Ranger.get_explore_dir(gc, unit, location)
                    # if variables.print_count < 10:
                    #    print("Getting direction:", time.time() - start_time)
    else:
        # if there are no enemies in sight, check if there is an ongoing battle.  If so, go there.
        if len(rocket_locs) > 0 and gc.round() > 660 and variables.curr_planet == bc.Planet.Earth:
            dir = Ranger.move_to_rocket(gc, unit, location, direction_to_coord, bfs_array)
            if dir is not None:
                return dir, attack, javelin, move_then_attack, visible_enemies, closest_enemy, signals
        if len(battle_locs) > 0:
            # print('IS GOING TO BATTLE')
            dir = Ranger.go_to_battle_new(gc, unit, battle_locs, location, direction_to_coord)
            # queued_paths[unit.id] = target
        else:
            # dir = move_away(gc, unit, battle_locs)
            if variables.curr_planet == bc.Planet.Earth:
                # print('IS RUNNING TOWARDS INIT LOC')
                dir = Ranger.run_towards_init_loc_new(gc, unit, location, direction_to_coord)
            else:
                # print('EXPLORING')
                dir = Ranger.get_explore_dir(gc, unit, location)
        # if variables.print_count < 10:
        #    print("regular movement:", time.time() - start_time)

    return dir, attack, javelin, move_then_attack, visible_enemies, closest_enemy, signals

def get_attack(gc, unit, location, targeting_units, priority = knight_unit_priority):
    enemy_team = variables.enemy_team
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), enemy_team)
    if len(vuln_enemies)==0:
        return None
    #return vuln_enemies[0]
    best = None
    lowest_health = float('inf')
    for enemy in vuln_enemies:
        if enemy.id in targeting_units:
            if enemy.unit_type == variables.unit_types["knight"]:
                mult = 30 - enemy.knight_defense()
            else:
                mult = 30
            remaining_health = enemy.health - targeting_units[enemy.id] * mult
            if remaining_health > 0 and remaining_health < lowest_health:
                best = enemy
                lowest_health = remaining_health
    if best is not None:
        return best
    return max(vuln_enemies, key=lambda x: Ranger.coefficient_computation(gc, unit, x, x.location.map_location(), location))


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

def update_knights():
    """
    1. If no rockets, remove any rangers from going to mars.
    2. Account for launched / destroyed rockets (in going to mars sense)
    """
    gc = variables.gc
    knight_roles = variables.knight_roles
    which_rocket = variables.which_rocket
    knight_attacks = variables.knight_attacks
    rocket_locs = variables.rocket_locs
    info = variables.info

    remove = set()
    for knight_id in knight_attacks:
        if knight_id not in variables.my_unit_ids:
            remove.add(knight_id)

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

    for knight_id in knight_roles["go_to_mars"]:
        no_rockets = True if info[6] == 0 else False
        if knight_id not in which_rocket or which_rocket[knight_id][1] not in rocket_locs:
            launched_rocket = True
        else:
            launched_rocket = False
            target_loc = which_rocket[knight_id][0]
            if not gc.has_unit_at_location(target_loc):
                destroyed_rocket = True
            else:
                destroyed_rocket = False
        if no_rockets or launched_rocket or destroyed_rocket:
            knight_roles["go_to_mars"].remove(knight_id)

