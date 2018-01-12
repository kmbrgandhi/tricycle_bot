import battlecode as bc
import random
import sys
import traceback
from Units.sense_util import enemy_team


def timestep(gc, unit,composition):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()

    try: 
        direction, attack_target, javelin_target = knight_sense(gc, unit, my_team)
        print('direction: ', direction)
        print('attack target: ', attack_target)
        print('javelin target: ', javelin_target)
    except:
        print('knight sense didnt run')

    try:
        ## Check if can javelin
        if unit.is_ability_unlocked() and javelin_target is not None:
            if gc.can_javelin(unit.id, javelin_target.id) and gc.is_javelin_ready(unit.id):
                gc.javelin(unit.id, javelin_target.id)

        ## Check if can attack regularly
        if attack_target is not None:
            if gc.can_attack(unit.id, attack_target.id) and gc. is_attack_ready(unit.id): 
                gc.attack(unit.id, attack_target.id)

    except:
        print('attacks didnt go through')
  
    try: 
        ## Knight movement
        if direction == None:  
            direction = random.choice(list(bc.Direction))

        if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
            gc.move_robot(unit.id, direction)

    except:
        print('movement didnt go through')

def knight_sense(gc, unit, my_team): 
    """
    This function chooses the direction the knight should move in. If it senses enemies nearby 
    then will return direction that it can move to. If it can attack it will say if it is in
    range for regular attack and/or javelin.
    Otherwise, will attempt to group with other allied knights and return a direction to clump
    the knights up. 

    Returns: New desired direction. 
    """
    new_direction = None
    target_attack = None
    target_javelin = None

    unit_loc = unit.location.map_location()
    enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, enemy_team(gc))

    if len(enemies) == 0: 
        # Sense allied knights and find direction to approach them
        ally_knights = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, unit.unit_type) 
        if len(ally_knights) > 0:
            ally_knights.sort(key=lambda x: x.location.map_location().distance_squared_to(unit_loc), reverse=True)
            new_direction = unit_loc.direction_to(ally_knights[0].location.map_location())

    else: 
        # Broadcast enemy location? 

        # Check if in attack range / javelin range
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   
        attack_range = unit.attack_range()
        javelin_range = unit.ability_range()

        #print('closest enemy: ', sorted_enemies[0])
        #print('my loc: ', unit_loc)

        if unit_loc.is_within_range(attack_range, sorted_enemies[0].location.map_location()):
            target_attack = sorted_enemies[0]

        if unit_loc.is_within_range(javelin_range, sorted_enemies[0].location.map_location()):
            target_javelin = sorted_enemies[0]

        new_direction = unit_loc.direction_to(sorted_enemies[0].location.map_location())

    return (new_direction, target_attack, target_javelin)
