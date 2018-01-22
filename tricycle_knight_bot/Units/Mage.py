import battlecode as bc
import random
import sys
import traceback
import Units.Ranger as ranger
import Units.explore as explore
import Units.sense_util as sense_util

def timestep(gc, unit, composition, last_turn_battle_locs, next_turn_battle_locs, queued_paths):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Mage:
        # prob should return some kind of error
        return
    location = unit.location
    my_team = gc.team()
    if location.is_on_map():
        dir, attack_target, blink, move_then_attack, visible_enemies = mage_sense(gc, unit, last_turn_battle_locs, queued_paths)

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



def mage_sense(gc, unit, battle_locs, queued_paths):
    dir = None
    attack = None
    blink = None
    move_then_attack = False
    visible_enemies = False
    location = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(location, unit.vision_range, sense_util.enemy_team(gc))
    if len(enemies) > 0:
        if unit.id in queued_paths:
            del queued_paths[unit.id]
        visible_enemies = True
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(location))
        closest_enemy = ranger.closest_among_ungarrisoned(sorted_enemies)
        attack = ranger.get_attack(gc, unit, location)
        print(attack)
        if attack is not None:
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
        if unit.id in queued_paths:
            if location!=queued_paths[unit.id]:
                dir = ranger.optimal_direction_towards(gc, unit, location, queued_paths[unit.id])
                return dir, attack, blink, move_then_attack, visible_enemies
            else:
                del queued_paths[unit.id]
        if len(battle_locs)>0:
            dir, target= ranger.go_to_battle(gc, unit, battle_locs)
            queued_paths[unit.id] = target
        else:
            dir = ranger.get_explore_dir(gc, unit)

    return dir, attack, blink, move_then_attack, visible_enemies
