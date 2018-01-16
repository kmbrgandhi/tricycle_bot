import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.explore as explore

order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage,
         bc.UnitType.Healer, bc.UnitType.Factory, bc.UnitType.Rocket]  # storing order of units
ranger_unit_priority = [0.5, 1, 2, 2, 2, 1, 1]
directions = list(bc.Direction)

def timestep(gc, unit, composition, last_turn_battle_locs, next_turn_battle_locs, queued_paths):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Ranger:
        # prob should return some kind of error
        return
    location = unit.location
    my_team = gc.team()
    if location.is_on_map():
        dir, attack_target, snipe, move_then_attack, visible_enemies = ranger_sense(gc, unit, last_turn_battle_locs, queued_paths)
        #print('Ranger movement:',dir)
        #print('Ranger attack target:', attack_target)
        map_loc = location.map_location()
        f_f_quad = (int(map_loc.x/5), int(map_loc.y/5))
        if visible_enemies:
            if f_f_quad not in next_turn_battle_locs:
                next_turn_battle_locs[f_f_quad] = (map_loc, 1)
            else:
                next_turn_battle_locs[f_f_quad] = (next_turn_battle_locs[f_f_quad][0], next_turn_battle_locs[f_f_quad][1]+1)

        if move_then_attack:
            if dir!=None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)

            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                gc.attack(unit.id, attack_target.id)
        else:
            if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
                gc.attack(unit.id, attack_target.id)

            if dir != None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
                gc.move_robot(unit.id, dir)

def get_attack(gc, unit, location):
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), sense_util.enemy_team(gc))
    if len(vuln_enemies)==0:
        return None
    return max(vuln_enemies, key=lambda x: coefficient_computation(gc, unit, x))

def exists_bad_enemy(enemies):
    for enemy in enemies:
        if attack_range_non_robots(enemy)>0:
            return True
    return False


def ranger_sense(gc, unit, battle_locs, queued_paths):
    dir = None
    attack = None
    snipe = None
    move_then_attack = False
    visible_enemies = False
    location = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        if unit.id in queued_paths:
            del queued_paths[unit.id]
        visible_enemies= True
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        #print('closest enemy:', closest_enemy)
        attack = get_attack(gc, unit, location)
        #print(attack)
        if attack is not None:
            print('found it here')
            if closest_enemy is not None:
                if (exists_bad_enemy(enemies) and (closest_enemy.location.map_location().distance_squared_to(location)) ** (
                0.5) + 2 < unit.attack_range() ** (0.5)) or not gc.can_attack(unit.id, attack.id):
                    dir = sense_util.best_available_direction(gc, unit, enemies)


        else:
            if gc.is_move_ready(unit.id):
                if closest_enemy is not None:
                    dir = optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                    next_turn_loc = location.add(dir)
                    attack = get_attack(gc, unit, next_turn_loc)
                    if attack is not None:
                        move_then_attack = True
                else:
                    dir = get_explore_dir(gc, unit)

    else:
        # if there are no enemies in sight, check if there is an ongoing battle.  If so, go there.
        if unit.id in queued_paths:
            if location!=queued_paths[unit.id]:
                dir = optimal_direction_towards(gc, unit, location, queued_paths[unit.id])
                return dir, attack, snipe, move_then_attack, visible_enemies
            else:
                del queued_paths[unit.id]
        if len(battle_locs)>0:
            dir, target= go_to_battle(gc, unit, battle_locs)
            queued_paths[unit.id] = target
        else:
            dir = get_explore_dir(gc, unit)

    return dir, attack, snipe, move_then_attack, visible_enemies

def go_to_battle(gc, unit, battle_locs):
    # send a unit to battle
    weakest = random.choice(list(battle_locs.keys()))
    target = battle_locs[weakest][0]
    return optimal_direction_towards(gc, unit, unit.location.map_location(), target), target

def optimal_direction_towards(gc, unit, location, target):

    # return the optimal direction towards a target that is achievable; not A*, but faster.
    shape = [target.x - location.x, target.y - location.y]
    options = sense_util.get_best_option(shape)
    #if unit.unit_type == bc.UnitType.Mage:
    #    print(location)
    #    print(target)
    #    print(options)
    for option in options:
        if gc.can_move(unit.id, option):
            if unit.unit_type == bc.UnitType.Mage:
                print(option)
            return option
    return directions[8]

def closest_among_ungarrisoned(sorted_units):
    # pick out ungarrisoned unit among sorted units, just in case
    index = 0
    while index < len(sorted_units):
        if sorted_units[index].location.is_on_map():
            return sorted_units[index]
    return None


def coefficient_computation(gc, our_unit, their_unit):
    # compute the relative appeal of attacking a unit.  Use AOE computation if attacking unit is mage.
    if not gc.can_attack(our_unit.id, their_unit.id):
        return 0
    coeff = attack_coefficient(gc, our_unit, their_unit)
    if our_unit.unit_type != bc.UnitType.Mage:
        return coeff
    else:
        for neighbor in explore.neighbors(their_unit.location.map_location()):
            try:
                new_unit = gc.sense_unit_at_location(neighbor)
            except:
                new_unit = None
            if new_unit is not None and new_unit.team!=our_unit.team:
                coeff = coeff + attack_coefficient(gc, our_unit, new_unit)

        return coeff

def attack_coefficient(gc, our_unit, their_unit):
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

def get_explore_dir(gc, unit):
    # function to get a direction to explore by picking locations that are within some distance that are
    # not visible to the team yet, and going towards them.
    dir = None
    location = unit.location.map_location()
    close_locations = [x for x in gc.all_locations_within(location, 150) if
                       not gc.can_sense_location(x)]
    if len(close_locations) > 0:
        dir = sense_util.best_available_direction_visibility(gc, unit, close_locations)
        #dir = location.direction_to(random.choice(close_locations))
    else:
        dir = random.choice(directions)
    return dir

