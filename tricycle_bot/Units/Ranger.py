import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.explore as explore
import Units.variables as variables


order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]  # storing order of units
ranger_unit_priority = [1, 0.5, 2, 0.5, 2, 5, 3]
directions = variables.directions

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Ranger:
        # prob should return some kind of error
        return
    gc = variables.gc
    ranger_roles = variables.ranger_roles
    info = variables.info
    next_turn_battle_locs = variables.next_turn_battle_locs
    if unit.id not in ranger_roles["fighter"] and unit.id not in ranger_roles["sniper"]:
        c = 13
        if info[6]>0 and len(ranger_roles["go_to_mars"]) < 6*info[6]:
            ranger_roles["go_to_mars"].append(unit.id)
        elif len(ranger_roles["fighter"]) > c * len(ranger_roles["sniper"]) and gc.research_info().get_level(
            bc.UnitType.Ranger) == 3:
            ranger_roles["sniper"].append(unit.id)
        else:
            ranger_roles["fighter"].append(unit.id)


    location = unit.location
    my_team = variables.my_team
    targeting_units = variables.targeting_units
    if location.is_on_map():
        map_loc = location.map_location()
        dir, attack_target, snipe, move_then_attack, visible_enemies, closest_enemy, signals = ranger_sense(gc, unit, variables.last_turn_battle_locs,
                                                                                                            ranger_roles, map_loc, variables.direction_to_coord, variables.precomputed_bfs, targeting_units, variables.bfs_fineness, variables.rocket_locs)
        if visible_enemies and closest_enemy is not None:
            enemy_loc = closest_enemy.location.map_location()
            f_f_quad = (int(enemy_loc.x / 5), int(enemy_loc.y / 5))
            if f_f_quad not in next_turn_battle_locs:
                next_turn_battle_locs[f_f_quad] = (map_loc, 1)
            else:
                next_turn_battle_locs[f_f_quad] = (next_turn_battle_locs[f_f_quad][0], next_turn_battle_locs[f_f_quad][1]+1)

        if move_then_attack:
            if dir!=None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)

            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id]+= 1
                gc.attack(unit.id, attack_target.id)
        else:
            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                if attack_target.id not in targeting_units:
                    targeting_units[attack_target.id] = 1
                else:
                    targeting_units[attack_target.id]+=1
                gc.attack(unit.id, attack_target.id)

            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)

        if snipe!=None and gc.can_begin_snipe(unit.id, snipe.location.map_location()) and gc.is_begin_snipe_ready(unit.id):
            gc.begin_snipe(unit.id, snipe.location)


def get_attack(gc, unit, location, targeting_units):
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), sense_util.enemy_team(gc))
    if len(vuln_enemies)==0:
        return None
    for enemy in vuln_enemies:
        if enemy.id in targeting_units and int(enemy.health/unit.damage())<targeting_units[enemy.id]:
            return enemy
    return max(vuln_enemies, key=lambda x: coefficient_computation(gc, unit, x, location))

def exists_bad_enemy(enemies):
    for enemy in enemies:
        if attack_range_non_robots(enemy)>0:
            return True
    return False

def check_radius_squares_factories(gc, unit, radius=1):
    is_factory = False
    for nearby_loc in gc.all_locations_within(unit.location.map_location(), radius):
        if gc.can_sense_location(nearby_loc) and gc.has_unit_at_location(nearby_loc) and gc.sense_unit_at_location(nearby_loc).unit_type == bc.UnitType.Factory:
            return True
    return False

def go_to_mars_sense(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness, rocket_locs):
    print('GOING TO MARS')
    signals = {}
    dir = None
    attack = None
    snipe = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        visible_enemies = True
        attack = get_attack(gc, unit, location, targeting_units)
    start_coords = (location.x, location.y)
    target_loc = random.choice(list(rocket_locs.values()))
    print(unit.id)
    print(start_coords)
    print(target_loc)
    if max(abs(target_loc.x - start_coords[0]), abs(target_loc.y-start_coords[1])) == 1:
        rocket = gc.sense_unit_at_location(target_loc)
        if gc.can_load(rocket.id, unit.id):
            gc.load(rocket.id, unit.id)
    else:

        target_coords_thirds = (int(target_loc.x / bfs_fineness), int(target_loc.y / bfs_fineness))
        shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
        options = sense_util.get_best_option(shape)
        for option in options:
            if gc.can_move(unit.id, option):
                dir = option

        if dir is None:
            dir = directions[8]

    return dir, attack, snipe, move_then_attack, visible_enemies, closest_enemy, signals

def ranger_sense(gc, unit, battle_locs, ranger_roles, location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness, rocket_locs):
    if unit.id in ranger_roles["sniper"]:
        return snipe_sense(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness)
    elif unit.id in ranger_roles["go_to_mars"]:
        return go_to_mars_sense(gc, unit, battle_locs,location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness, rocket_locs)
    signals = {}
    dir = None
    attack = None
    snipe = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        visible_enemies= True
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        attack = get_attack(gc, unit, location, targeting_units)
        if attack is not None:
            if closest_enemy is not None:
                if check_radius_squares_factories(gc, unit):
                    dir = optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                elif (exists_bad_enemy(enemies)) or not gc.can_attack(unit.id, closest_enemy.id):
                    dir = sense_util.best_available_direction(gc, unit, enemies)
                #and (closest_enemy.location.map_location().distance_squared_to(location)) ** (
                #0.5) + 2 < unit.attack_range() ** (0.5)) or not gc.can_attack(unit.id, attack.id):
        else:
            if gc.is_move_ready(unit.id):

                if closest_enemy is not None:
                    dir = optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())


                    next_turn_loc = location.add(dir)
                    attack = get_attack(gc, unit, next_turn_loc, targeting_units)
                    if attack is not None:
                        move_then_attack = True
                else:
                    dir = get_explore_dir(gc, unit, location)

    else:
        # if there are no enemies in sight, check if there is an ongoing battle.  If so, go there.
        if len(battle_locs)>0:
            dir, target= go_to_battle(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, bfs_fineness)
            #queued_paths[unit.id] = target
        else:
            #dir = move_away(gc, unit, battle_locs)
            dir = run_towards_init_loc(gc, unit, location, direction_to_coord, precomputed_bfs, bfs_fineness)
        """
        elif unit.id in queued_paths:
            if location!=queued_paths[unit.id]:
                dir = optimal_direction_towards(gc, unit, location, queued_paths[unit.id])
                return dir, attack, snipe, move_then_attack, visible_enemies, signals
            else:
                del queued_paths[unit.id]
        """



    return dir, attack, snipe, move_then_attack, visible_enemies, closest_enemy, signals


snipe_priority = {"Rocket": 5, "Factory": 4, "Ranger": 3, "Healer": 2, "Knight": 1, "Worker": 0, "Mage": -1}
def snipe_priority(unit):
    if unit.unit_type == bc.UnitType.bc.UnitType.Rocket:
        return 5
    elif unit.unit_type == bc.UnitType.bc.UnitType.Factory:
        return 4
    elif unit.unit_type == bc.UnitType.bc.UnitType.Ranger:
        return 3
    elif unit.unit_type == bc.UnitType.bc.UnitType.Healer:
        return 2
    elif unit.unit_type == bc.UnitType.bc.UnitType.Knight:
        return 1
    elif unit.unit_type == bc.UnitType.bc.UnitType.Worker:
        return 0
    else:
        return -1

def snipe_sense(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness):
    signals = {}
    dir = None
    attack = None
    snipe = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if not unit.ranger_is_sniping():
        if len(enemies) > 0:
            visible_enemies= True
            attack = get_attack(gc, unit, location, targeting_units)

        if len(enemies)>0 or check_radius_squares_factories(gc, unit, 2) or not gc.is_begin_snipe_ready(unit.id): #or how_many_adjacent(gc, unit)>5
            dir = move_away(gc, unit, battle_locs, location)

        else:
            try:
                best_unit =  None
                best_priority = -float("inf")
                for poss_enemy in gc.units():
                    if poss_enemy.location.is_on_map() and poss_enemy.team!=gc.team() and snipe_priority(poss_enemy)>best_priority:
                        best_unit = poss_enemy
                        best_priority = snipe_priority(poss_enemy)

                    # temporary always target rockets
                    if best_priority == 5:
                        break

                snipe = best_unit
            except:
                pass

    return dir, attack, snipe, move_then_attack, visible_enemies, closest_enemy, signals

def move_away(gc, unit, battle_locs, map_loc):
    lst = []
    for nearby_unit in gc.sense_nearby_units(map_loc, 10):
        if nearby_unit.location.is_on_map():
            nearby_loc = nearby_unit.location.map_location()
            if gc.can_sense_location(nearby_loc) and gc.has_unit_at_location(nearby_loc) and gc.sense_unit_at_location(nearby_loc).unit_type == bc.UnitType.Factory:
                lst.append(nearby_unit)

    return sense_util.best_available_direction(gc, unit, lst)


def how_many_adjacent(gc, unit):
    total = 0
    for dir in directions:
        nearby_loc = unit.location.map_location().add(dir)
        if gc.has_unit_at_location(nearby_loc):
            total+=1
    return total

def go_to_battle(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, bfs_fineness):
    # send a unit to battle
    weakest = random.choice(list(battle_locs.keys()))
    target = battle_locs[weakest][0]
    start_coords = (location.x, location.y)
    target_coords_thirds = (int(target.x/bfs_fineness), int(target.y/bfs_fineness))
    shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option, target
    return directions[8], target
    #return optimal_direction_towards(gc, unit, unit.location.map_location(), target, directions), target

def optimal_direction_towards(gc, unit, location, target):

    # return the optimal direction towards a target that is achievable; not A*, but faster.
    shape = [target.x - location.x, target.y - location.y]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[8]

def closest_among_ungarrisoned(sorted_units):
    # pick out ungarrisoned unit among sorted units, just in case
    index = 0
    while index < len(sorted_units):
        if sorted_units[index].location.is_on_map():
            return sorted_units[index]
    return None


def coefficient_computation(gc, our_unit, their_unit, location):
    # compute the relative appeal of attacking a unit.  Use AOE computation if attacking unit is mage.
    if not gc.can_attack(our_unit.id, their_unit.id):
        return 0
    coeff = attack_coefficient(gc, our_unit, their_unit, location)
    if our_unit.unit_type != bc.UnitType.Mage:
        return coeff
    else:
        for neighbor in explore.neighbors(their_unit.location.map_location()):
            try:
                new_unit = gc.sense_unit_at_location(neighbor)
            except:
                new_unit = None
            if new_unit is not None and new_unit.team!=our_unit.team:
                coeff = coeff + attack_coefficient(gc, our_unit, new_unit, location)

        return coeff

def attack_coefficient(gc, our_unit, their_unit, location):
    # generic: how appealing is their_unit to attack
    our_location = our_unit.location.map_location()
    distance = their_unit.location.map_location().distance_squared_to(our_location)
    coeff = ranger_unit_priority[their_unit.unit_type]
    if distance < attack_range_non_robots(their_unit):
        coeff = coeff * sense_util.can_attack_multiplier(their_unit)
    coeff = coeff * sense_util.health_multiplier(their_unit)
    return coeff

def attack_range_non_robots(unit):
    # attack range for all structures in the game
    if unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket:
        return 0
    else:
        return unit.attack_range()

def run_towards_init_loc(gc, unit, location,  direction_to_coord, precomputed_bfs, bfs_fineness):
    curr_planet_map = gc.starting_map(gc.planet())
    coords_init_location = (location.x, location.y)
    print(coords_init_location)
    coords_loc = None
    for init_unit in curr_planet_map.initial_units:
        loc = init_unit.location.map_location()
        coords_loc = (loc.x, loc.y)
        if init_unit.team!=gc.team() and (coords_init_location, coords_loc) in precomputed_bfs:
            break
    coords_loc_thirds = (int(coords_loc[0]/bfs_fineness), int(coords_loc[1]/bfs_fineness))
    shape = direction_to_coord[precomputed_bfs[(coords_init_location, coords_loc_thirds)]]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[8]


def get_explore_dir(gc, unit, location):
    # function to get a direction to explore by picking locations that are within some distance that are
    # not visible to the team yet, and going towards them.
    dir = None
    close_locations = [x for x in gc.all_locations_within(location, 150) if
                       not gc.can_sense_location(x)]
    if len(close_locations) > 0:
        dir = sense_util.best_available_direction_visibility(gc, unit, close_locations)
        #dir = location.direction_to(random.choice(close_locations))
    else:
        dir = random.choice(directions)
    return dir

