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
ranger_unit_priority = [0.7, 1, 2, 1, 3, 5, 3]
directions = variables.directions

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Mage:
        # prob should return some kind of error
        return
    # start_time = time.time()
    gc = variables.gc
    mage_roles = variables.mage_roles
    info = variables.info
    next_turn_battle_locs = variables.next_turn_battle_locs

    if unit.id in mage_roles["go_to_mars"] and info[6] == 0:
        mage_roles["go_to_mars"].remove(unit.id)
    if unit.id not in mage_roles["fighter"]:
        mage_roles["fighter"].append(unit.id)

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
            quadrant_battles[f_f_quad].add_ally(unit.id, "mage")

        # start_time = time.time()
        map_loc = location.map_location()
        if variables.curr_planet == bc.Planet.Earth and len(mage_roles["go_to_mars"]) < 14 and unit.id not in \
                mage_roles["go_to_mars"] and unit.id in mage_roles["fighter"]:
            for rocket in variables.rocket_locs:
                target_loc = variables.rocket_locs[rocket]
                if sense_util.distance_squared_between_maplocs(map_loc, target_loc) < 150:
                    variables.which_rocket[unit.id] = (target_loc, rocket)
                    mage_roles["go_to_mars"].append(unit.id)
                    mage_roles["fighter"].remove(unit.id)
                    break
        # if variables.print_count < 10:
        #    print("Preprocessing inside:", time.time() - start_time)
        # start_time = time.time()
        dir, attack_target, snipe, move_then_attack, visible_enemies, closest_enemy, signals = mage_sense(gc, unit,
                                                                                                            variables.last_turn_battle_locs,
                                                                                                            mage_roles,
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
                next_turn_battle_locs[f_f_quad] = (map_loc, 1)
            else:
                next_turn_battle_locs[f_f_quad] = (
                next_turn_battle_locs[f_f_quad][0], next_turn_battle_locs[f_f_quad][1] + 1)

        if move_then_attack:
            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)
                ## CHANGE LOC IN NEW DATA STRUCTURE
                Ranger.add_new_location(unit.id, (map_loc.x, map_loc.y), dir)

            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id] += 1
                gc.attack(unit.id, attack_target.id)
        else:
            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id] += 1
                gc.attack(unit.id, attack_target.id)

            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)
                ## CHANGE LOC IN NEW DATA STRUCTURE
                Ranger.add_new_location(unit.id, (map_loc.x, map_loc.y), dir)
        """
        if snipe!=None and gc.can_begin_snipe(unit.id, snipe.location.map_location()) and gc.is_begin_snipe_ready(unit.id):
            gc.begin_snipe(unit.id, snipe.location)
        """
        # if variables.print_count < 10:
        # print("Doing tasks:", time.time() - start_time)
        # if variables.print_count<10:
        #    variables.print_count+=1

"""
def add_healer_target(gc, ranger_loc):
    healer_target_locs = variables.healer_target_locs
    valid = True

    locs_near = gc.all_locations_within(ranger_loc, variables.healer_radius)
    for near in locs_near:
        near_coords = (near.x, near.y)
        if near_coords in healer_target_locs:
            valid = False
            break
    if valid:
        healer_target_locs.add((ranger_loc.x, ranger_loc.y))


def go_to_mars_sense(gc, unit, battle_locs, location, enemies, direction_to_coord, bfs_dict, targeting_units, bfs_fineness, rocket_locs):
"""


def go_to_mars_sense(gc, unit, battle_locs, location, enemies, direction_to_coord, bfs_array, targeting_units,
                     rocket_locs):
    # print('GOING TO MARS')
    signals = {}
    dir = None
    attack = None
    blink = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False

    if len(enemies) > 0:
        visible_enemies = True
        attack = Ranger.get_attack(gc, unit, location, targeting_units)
    start_coords = (location.x, location.y)

    # # rocket was launched
    if unit.id not in variables.which_rocket or variables.which_rocket[unit.id][1] not in variables.rocket_locs:
        variables.mage_roles["go_to_mars"].remove(unit.id)
        return dir, attack, blink, move_then_attack, visible_enemies, closest_enemy, signals
    target_loc = variables.which_rocket[unit.id][0]

    # # rocket was destroyed
    if not gc.has_unit_at_location(target_loc):
        variables.mage_roles["go_to_mars"].remove(unit.id)
        return dir, attack, blink, move_then_attack, visible_enemies, closest_enemy, signals
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

    return dir, attack, blink, move_then_attack, visible_enemies, closest_enemy, signals


def mage_sense(gc, unit, battle_locs, mage_roles, location, direction_to_coord, bfs_array, targeting_units,
                 rocket_locs):
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, variables.enemy_team)
    if unit.id in mage_roles["go_to_mars"]:
        return go_to_mars_sense(gc, unit, battle_locs, location, enemies, direction_to_coord, bfs_array,
                                targeting_units, rocket_locs)
    signals = {}
    dir = None
    attack = None
    blink = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    start_time = time.time()
    # if variables.print_count < 10:
    #    print("Sensing nearby units:", time.time() - start_time)
    if len(enemies) > 0:
        visible_enemies = True
        start_time = time.time()
        closest_enemy = None
        closest_dist = float('inf')
        for enemy in enemies:
            loc = enemy.location
            if loc.is_on_map():
                dist = sense_util.distance_squared_between_maplocs(loc.map_location(), location)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy
        # if variables.print_count < 10:
        #    print("Getting closest enemy:", time.time() - start_time)
        # sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        # closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        start_time = time.time()
        attack = Ranger.get_attack(gc, unit, location, targeting_units)
        # if variables.print_count < 10:
        #    print("Getting attack:", time.time() - start_time)
        if attack is not None:
            if closest_enemy is not None:
                start_time = time.time()
                if Ranger.check_radius_squares_factories(gc, location):
                    dir = Ranger.optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                elif (Ranger.exists_bad_enemy(closest_enemy)) or not gc.can_attack(unit.id, closest_enemy.id):
                    # if variables.print_count < 10:
                    #    print("Checking if condition:", time.time() - start_time)
                    start_time = time.time()
                    dir = sense_util.best_available_direction(gc, unit, [closest_enemy])
                    # if variables.print_count < 10:
                    #    print("Getting best available direction:", time.time() - start_time)

                    # and (closest_enemy.location.map_location().distance_squared_to(location)) ** (
                    # 0.5) + 2 < unit.attack_range() ** (0.5)) or not gc.can_attack(unit.id, attack.id):
        else:
            if gc.is_move_ready(unit.id):

                if closest_enemy is not None:
                    dir = Ranger.optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())

                    next_turn_loc = location.add(dir)
                    attack = Ranger.get_attack(gc, unit, next_turn_loc, targeting_units)
                    if attack is not None:
                        move_then_attack = True
                else:
                    dir = Ranger.run_towards_init_loc_new(gc, unit, location, direction_to_coord)
                    # if variables.print_count < 10:
                    #    print("Getting direction:", time.time() - start_time)
    else:
        # if there are no enemies in sight, check if there is an ongoing battle.  If so, go there.
        if len(rocket_locs) > 0 and gc.round() > 660 and variables.curr_planet == bc.Planet.Earth:
            dir = Ranger.move_to_rocket(gc, unit, location, direction_to_coord, bfs_array)
            if dir is not None:
                return dir, attack, blink, move_then_attack, visible_enemies, closest_enemy, signals
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

    return dir, attack, blink, move_then_attack, visible_enemies, closest_enemy, signals



def update_mages():
    """
    1. If no rockets, remove any rangers from going to mars.
    2. Account for launched / destroyed rockets (in going to mars sense)
    """
    gc = variables.gc
    mage_roles = variables.mage_roles
    which_rocket = variables.which_rocket
    rocket_locs = variables.rocket_locs
    info = variables.info

    for mage_id in mage_roles["go_to_mars"]:
        no_rockets = True if info[6] == 0 else False
        if mage_id not in which_rocket or which_rocket[mage_id][1] not in rocket_locs:
            launched_rocket = True
        else:
            launched_rocket = False
            target_loc = which_rocket[mage_id][0]
            if not gc.has_unit_at_location(target_loc):
                destroyed_rocket = True
            else:
                destroyed_rocket = False
        if no_rockets or launched_rocket or destroyed_rocket:
            mage_roles["go_to_mars"].remove(mage_id)

