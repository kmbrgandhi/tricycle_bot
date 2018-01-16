import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

import numpy as np

def timestep(gc, unit, composition, last_turn_battle_locs):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Healer:
        return

    my_team = gc.team()
    direction = None
    location = unit.location

    if location.is_on_map():
        unit_loc = location.map_location()
        #print('HEALER LOC: ', unit_loc)

        directions, heal_target = healer_sense(gc, unit, last_turn_battle_locs)

        ## Movement
        try: 
            if directions is not None:
                if len(directions) > 0 and gc.is_move_ready(unit.id): 
                    for d in directions: 
                        if gc.can_move(unit.id, d):
                            gc.move_robot(unit.id, d)
                            #print('HEALER moved to battle loc!')
                            break

            ## Healer movement away from allies
            else:  
                nearby = gc.sense_nearby_units(unit.location.map_location(),8)
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

def healer_sense(gc, unit, battle_locs):
    directions = None
    heal_target = None

    unit_loc = unit.location.map_location()

    ## Attempt to send healer to battle location
    if len(battle_locs) > 0: 
        try: 
            weakest = random.choice(list(battle_locs.keys()))
            target_loc = battle_locs[weakest][0]

            shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
            directions = sense_util.get_best_option(shape)
        except:
            pass
            #print('HEALER cant process battle locs')

    ## Attempt to heal nearby units
    nearby = gc.sense_nearby_units_by_team(unit_loc, unit.ability_range(), gc.team())
    if len(nearby) > 0: 
        nearby = sorted(nearby, key=lambda x: x.health/x.max_health)
        heal_target = nearby[0]

    return directions, heal_target
