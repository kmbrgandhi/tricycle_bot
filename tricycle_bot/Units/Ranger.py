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

def timestep(gc, unit, composition):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Ranger:
        # prob should return some kind of error
        return
    location = unit.location
    my_team = gc.team()
    if location.is_on_map():
        dir, attack_target, snipe, move_then_attack= ranger_sense(gc, unit)
        print('Ranger movement:',dir)
        print('Ranger attack target:', attack_target)
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
    return max(vuln_enemies, key=lambda x: attack_coefficient(gc, unit, x))

def exists_bad_enemy(enemies):
    for enemy in enemies:
        if attack_range_non_robots(enemy)>0:
            return True
    return False


def ranger_sense(gc, unit):
    dir = None
    attack = None
    snipe = None
    move_then_attack = False
    location = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        print('closest enemy:', closest_enemy)
        attack = get_attack(gc, unit, location)
        print(attack)
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
        dir = get_explore_dir(gc, unit)

    return dir, attack, snipe, move_then_attack

def optimal_direction_towards(gc, unit, location, target):
    shape = [target.x - location.x, target.y - location.y]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[0]

def closest_among_ungarrisoned(sorted_units):
    index = 0
    while index < len(sorted_units):
        if sorted_units[index].location.is_on_map():
            return sorted_units[index]
    return None

def attack_coefficient(gc, our_unit, their_unit):
    if not gc.can_attack(our_unit.id, their_unit.id):
        return 0
    our_location = our_unit.location.map_location()
    distance = their_unit.location.map_location().distance_squared_to(our_location)
    coeff = ranger_unit_priority[their_unit.unit_type]
    if distance < attack_range_non_robots(their_unit):
        coeff = coeff * sense_util.can_attack_multiplier(their_unit)
    coeff = coeff * sense_util.health_multiplier(their_unit)
    return coeff

def attack_range_non_robots(unit):
    if unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket:
        return 0
    else:
        return unit.attack_range()

def get_explore_dir(gc, unit):
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

