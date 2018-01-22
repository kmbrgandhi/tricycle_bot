import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.explore as explore
import Units.variables as variables
import time


order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]  # storing order of units
ranger_unit_priority = [1, 0.5, 2, 0.5, 2, 5, 3]
directions = variables.directions

def timestep(unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Ranger:
        # prob should return some kind of error
        return
    #start_time = time.time()
    gc = variables.gc
    ranger_roles = variables.ranger_roles
    info = variables.info
    next_turn_battle_locs = variables.next_turn_battle_locs
    if unit.id in ranger_roles["go_to_mars"] and info[6]==0:
        ranger_roles["go_to_mars"].remove(unit.id)
    if unit.id not in ranger_roles["fighter"] and unit.id not in ranger_roles["sniper"]:
        c = 13
        if info[6]>0 and len(ranger_roles["go_to_mars"]) < 4*info[6]:
            ranger_roles["go_to_mars"].append(unit.id)
        if len(ranger_roles["fighter"]) > c * len(ranger_roles["sniper"]) and variables.research.get_level(
            bc.UnitType.Ranger) == 3 and False:
            ranger_roles["sniper"].append(unit.id)
        else:
            ranger_roles["fighter"].append(unit.id)
    #if variables.print_count<10:
    #    print("Preprocessing:", time.time()-start_time)

    location = unit.location
    my_team = variables.my_team
    targeting_units = variables.targeting_units
    if location.is_on_map():
        #start_time = time.time()
        map_loc = location.map_location()
        if variables.curr_planet == bc.Planet.Earth and unit.id not in ranger_roles["go_to_mars"] and unit.id in ranger_roles["fighter"]:
            for rocket in variables.rocket_locs:
                target_loc = variables.rocket_locs[rocket]
                if sense_util.distance_squared_between_maplocs(map_loc, target_loc) < 40:
                    variables.which_rocket[unit.id] = (target_loc, rocket)
                    ranger_roles["go_to_mars"].append(unit.id)
                    ranger_roles["fighter"].remove(unit.id)
                    break
        #if variables.print_count < 10:
        #    print("Preprocessing inside:", time.time() - start_time)
        #start_time = time.time()
        dir, attack_target, snipe, move_then_attack, visible_enemies, closest_enemy, signals = ranger_sense(gc, unit, variables.last_turn_battle_locs,
                                                                                                            ranger_roles, map_loc, variables.direction_to_coord, variables.precomputed_bfs, targeting_units, variables.bfs_fineness, variables.rocket_locs)
        #if variables.print_count < 10:
        #    print("Sensing:", time.time() - start_time)
        #start_time = time.time()
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
        """
        if snipe!=None and gc.can_begin_snipe(unit.id, snipe.location.map_location()) and gc.is_begin_snipe_ready(unit.id):
            gc.begin_snipe(unit.id, snipe.location)
        """
        #if variables.print_count < 10:
        #    print("Doing tasks:", time.time() - start_time)
    if variables.print_count<10:
        variables.print_count+=1

def get_attack(gc, unit, location, targeting_units):
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), sense_util.enemy_team(gc))
    if len(vuln_enemies)==0:
        return None
    for enemy in vuln_enemies:
        if enemy.id in targeting_units and int(enemy.health/unit.damage())<targeting_units[enemy.id]:
            return enemy
    return max(vuln_enemies, key=lambda x: coefficient_computation(gc, unit, x, location))

def exists_bad_enemy(enemy):
    if attack_range_non_robots(enemy)>0:
        return True
    random_num = random.random()
    if random_num>0.5:
        return True
    return False

def check_radius_squares_factories(gc, location):
    location_coords = (location.x, location.y)
    nearby_locs = explore.coord_neighbors(location_coords)
    for nearby_loc_coords in nearby_locs:
        nearby_loc = bc.MapLocation(variables.curr_planet, nearby_loc_coords[0], nearby_loc_coords[1])
        if gc.can_sense_location(nearby_loc) and gc.has_unit_at_location(nearby_loc) and gc.sense_unit_at_location(nearby_loc).unit_type == bc.UnitType.Factory:
            return True
    return False

def go_to_mars_sense(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness, rocket_locs):
    #print('GOING TO MARS')
    signals = {}
    dir = None
    attack = None
    snipe = None
    closest_enemy = None
    move_then_attack = False
    visible_enemies = False
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, variables.enemy_team)
    if len(enemies) > 0:
        visible_enemies = True
        attack = get_attack(gc, unit, location, targeting_units)
    start_coords = (location.x, location.y)

    # rocket was launched
    if unit.id not in variables.which_rocket or variables.which_rocket[unit.id][1] not in variables.rocket_locs:
        variables.ranger_roles["go_to_mars"].remove(unit.id)
        return dir, attack, snipe, move_then_attack, visible_enemies, closest_enemy, signals
    target_loc = variables.which_rocket[unit.id][0]

    # rocket was destroyed
    if not gc.has_unit_at_location(target_loc):
        variables.ranger_roles["go_to_mars"].remove(unit.id)
        return dir, attack, snipe, move_then_attack, visible_enemies, closest_enemy, signals
    #print(unit.id)
    #print('MY LOCATION:', start_coords)
    #print('GOING TO:', target_loc)
    if max(abs(target_loc.x - start_coords[0]), abs(target_loc.y-start_coords[1])) == 1:
        rocket = gc.sense_unit_at_location(target_loc)
        if gc.can_load(rocket.id, unit.id):
            gc.load(rocket.id, unit.id)
    else:
        #print('REALLY CLOSE')
        result = explore.bfs_with_destination((target_loc.x, target_loc.y), start_coords, variables.gc, variables.curr_planet, variables.passable_locations_earth, variables.coord_to_direction)
        if result is None:
            variables.ranger_roles["go_to_mars"].remove(unit.id)
            dir = None
        else:
            dir = result
        #print(dir)

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
    #start_time = time.time()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, variables.enemy_team)
    #if variables.print_count < 10:
    #    print("Sensing nearby units:", time.time() - start_time)
    if len(enemies) > 0:
        visible_enemies= True
        #start_time = time.time()
        closest_enemy = None
        closest_dist = float('inf')
        for enemy in enemies:
            loc = enemy.location
            if loc.is_on_map():
                dist = sense_util.distance_squared_between_maplocs(loc.map_location(), location)
                if dist<closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy
        #if variables.print_count < 10:
        #    print("Getting closest enemy:", time.time() - start_time)
        #sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        #closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        #start_time = time.time()
        attack = get_attack(gc, unit, location, targeting_units)
        #if variables.print_count < 10:
        #    print("Getting attack:", time.time() - start_time)
        if attack is not None:
            if closest_enemy is not None:
                #start_time = time.time()
                if check_radius_squares_factories(gc, location):
                    dir = optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                elif (exists_bad_enemy(closest_enemy)) or not gc.can_attack(unit.id, closest_enemy.id):
                    #if variables.print_count < 10:
                    #    print("Checking if condition:", time.time() - start_time)
                    #start_time = time.time()
                    dir = sense_util.best_available_direction(gc, unit, [closest_enemy])
                    #if variables.print_count < 10:
                     #   print("Getting best available direction:", time.time() - start_time)

                #and (closest_enemy.location.map_location().distance_squared_to(location)) ** (
                #0.5) + 2 < unit.attack_range() ** (0.5)) or not gc.can_attack(unit.id, attack.id):
        else:
            #start_time = time.time()
            if gc.is_move_ready(unit.id):

                if closest_enemy is not None:
                    dir = optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())


                    next_turn_loc = location.add(dir)
                    attack = get_attack(gc, unit, next_turn_loc, targeting_units)
                    if attack is not None:
                        move_then_attack = True
                else:
                    dir = get_explore_dir(gc, unit, location)
            #if variables.print_count < 10:
             #   print("Getting direction:", time.time() - start_time)
    else:
        #start_time = time.time()
        # if there are no enemies in sight, check if there is an ongoing battle.  If so, go there.
        if len(battle_locs)>0:
            dir = go_to_battle(gc, unit, battle_locs, location, direction_to_coord, precomputed_bfs, bfs_fineness)
            #queued_paths[unit.id] = target
        else:
            #dir = move_away(gc, unit, battle_locs)
            if variables.curr_planet == bc.Planet.Earth:
                dir = run_towards_init_loc(gc, unit, location, direction_to_coord, precomputed_bfs, bfs_fineness)
            else:
                dir = get_explore_dir(gc, unit, location)
        """
        elif unit.id in queued_paths:
            if location!=queued_paths[unit.id]:
                dir = optimal_direction_towards(gc, unit, location, queued_paths[unit.id])
                return dir, attack, snipe, move_then_attack, visible_enemies, signals
            else:
                del queued_paths[unit.id]
        """
        #if variables.print_count < 10:
        #    print("regular movement:", time.time() - start_time)


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
                for poss_enemy in variables.units:
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
    if (start_coords, target_coords_thirds) not in precomputed_bfs:
        target_coords = pick_from_init_enemy_locs(start_coords)
        if target_coords is None:
            return None
        else:
            target_coords_thirds = (int(target_coords.x / bfs_fineness), int(target_coords.y / bfs_fineness))
    shape = direction_to_coord[precomputed_bfs[(start_coords, target_coords_thirds)]]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[8]
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

def pick_from_init_enemy_locs(init_loc):
    for choice in variables.init_enemy_locs:
        coords_loc_thirds = (int(choice.x /variables.bfs_fineness), int(choice.y/variables.bfs_fineness))
        if (init_loc, coords_loc_thirds) in variables.precomputed_bfs:
            return choice
    return None



def run_towards_init_loc(gc, unit, location,  direction_to_coord, precomputed_bfs, bfs_fineness):
    curr_planet_map = gc.starting_map(gc.planet())
    coords_init_location = (location.x, location.y)
    coords_loc = pick_from_init_enemy_locs(coords_init_location)
    if coords_loc is None:
        return None
    coords_loc_thirds = (int(coords_loc.x/bfs_fineness), int(coords_loc.y/bfs_fineness))
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

