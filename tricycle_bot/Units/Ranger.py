import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

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
        dir, attack_target, snipe = ranger_sense(gc, unit)
        print('Ranger movement:',dir)
        print('Ranger attack target:', attack_target)
        if dir!=None and gc.is_move_ready(unit.id) and gc.can_move(unit.id, dir):
            gc.move_robot(unit.id, dir)

        if attack_target is not None and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, attack_target.id):
            gc.attack(unit.id, attack_target.id)


def ranger_sense(gc, unit):
    dir = None
    attack = None
    snipe = None
    location = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    vuln_enemies = gc.sense_nearby_units_by_team(location, unit.attack_range(), sense_util.enemy_team(gc))
    if len(enemies) > 0:
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = closest_among_ungarrisoned(sorted_enemies)
        print('closest enemy:', closest_enemy)
        if len(vuln_enemies)>0:
            if gc.is_attack_ready(unit.id):
                attack = max(vuln_enemies, key = lambda x: attack_coefficient(gc, unit, x))


            if gc.is_move_ready(unit.id) and closest_enemy is not None and (closest_enemy.location.map_location().distance_squared_to(location))**(0.5) + 2 < unit.attack_range()**(0.5):
                d = sense_util.best_available_direction(gc, unit, enemies)
                if gc.can_move(unit.id, d):
                    dir = d
        else:
            if gc.is_move_ready(unit.id):
                if closest_enemy is not None:
                    dir = location.direction_to(closest_enemy.location.map_location())
                else:
                    dir = get_explore_dir(gc, unit)

    else:
        dir = get_explore_dir(gc, unit)

    return dir, attack, snipe

def closest_among_ungarrisoned(sorted_units):
    index = 0
    while index < len(sorted_units):
        if sorted_units[index].location.is_on_map():
            return sorted_units[index]
    return None

def attack_coefficient(gc, our_unit, their_unit):
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
        rand = random.choice(close_locations)
        dir = location.direction_to(rand)
    else:
        dir = random.choice(directions)
    return dir

