import battlecode as bc
import random
import sys
import traceback
import Units.Ranger as ranger
import Units.explore as explore
import Units.sense_util as sense_util

def timestep(gc, unit, composition):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Mage:
        # prob should return some kind of error
        return
    location = unit.location
    my_team = gc.team()
    if location.is_on_map():
        dir, attack_target, blink, move_then_attack= mage_sense(gc, unit)
        print('Mage movement:',dir)
        print('Mage attack target:', attack_target)
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


def mage_sense(gc, unit):
    dir = None
    attack = None
    blink = None
    move_then_attack = False
    location = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = ranger.closest_among_ungarrisoned(sorted_enemies)
        print('closest enemy:', closest_enemy)
        attack = ranger.get_attack(gc, unit, location)
        print(attack)
        if attack is not None:
            print('found it here')
            if closest_enemy is not None:
                if (ranger.exists_bad_enemy(enemies) and (closest_enemy.location.map_location().distance_squared_to(location)) ** (
                0.5) + 2 < unit.attack_range() ** (0.5)) or not gc.can_attack(unit.id, attack.id):
                    dir = sense_util.best_available_direction(gc, unit, enemies)


        else:
            if gc.is_move_ready(unit.id):
                if closest_enemy is not None:
                    dir = ranger.optimal_direction_towards(gc, unit, location, closest_enemy.location.map_location())
                    next_turn_loc = location.add(dir)
                    attack = ranger.get_attack(gc, unit, next_turn_loc)
                    if attack is not None:
                        move_then_attack = True
                else:
                    dir = ranger.get_explore_dir(gc, unit)

    else:
        dir = ranger.get_explore_dir(gc, unit)

    return dir, attack, blink, move_then_attack
