import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

import numpy as np

def timestep(gc, unit, composition, battle_locs, constants):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Healer:
        return

    my_team = gc.team()
    direction = None
    location = unit.location

    if location.is_on_map():
        unit_loc = location.map_location()
        #print('HEALER LOC: ', unit_loc)

        direction, heal_target = healer_sense(gc, unit, unit_loc, battle_locs, constants)

        ## Movement
        try: 
            if direction is not None and gc.is_move_ready(unit.id):
                gc.move_robot(unit.id, direction)
                #print('HEALER moving!')

            ## Healer movement away from allies
            else:  
                nearby = gc.sense_nearby_units(unit_loc,8)
                direction = sense_util.best_available_direction(gc,unit,nearby)

                if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
                    gc.move_robot(unit.id, direction)
                    #print('HEALER moved away from allies!')

        except:
            pass
            #print('HEALER movement didnt go through')

        ## Healing
        try:
            if heal_target is not None: 
                if gc.is_heal_ready(unit.id) and gc.can_heal(unit.id, heal_target.id):
                    gc.heal(unit.id, heal_target.id) # heal it, if possible
                    #print('healed ', heal_target.id)
        except:
            pass
            #print('HEALER healing didnt go through')

def healer_sense(gc, unit, unit_loc, battle_locs, constants):
    direction = None
    heal_target = None

    ## If healer sees an enemy in vision range, move away from enemy
    enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, constants.enemy_team)
    if len(enemies) > 0: 
        enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))
        dir_to_enemy = unit_loc.direction_to(enemies[0].location.map_location())
        new_loc = unit_loc.subtract(dir_to_enemy)
        new_dir = unit_loc.direction_to(new_loc)

        if gc.can_move(unit.id, new_dir):
            direction = new_dir

    ## Otherwise attempt to send healer to battle location
    if direction is None and len(battle_locs) > 0: 
        weakest = random.choice(list(battle_locs.keys()))
        target_loc = battle_locs[weakest][0]

        shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
        directions = sense_util.get_best_option(shape)

        for d in directions: 
            if gc.can_move(unit.id, d):
                direction = d
                break

    ## Attempt to heal nearby units
    nearby = gc.sense_nearby_units_by_team(unit_loc, unit.ability_range()-1, constants.my_team)
    if len(nearby) > 0: 
        nearby = sorted(nearby, key=lambda x: x.health/x.max_health)
        heal_target = nearby[0]

    return direction, heal_target
