import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.clusters as clusters


def timestep(gc, unit,composition, knight_to_cluster, knight_clusters):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()

    direction = None
    attack_target = None
    javelin_target = None

    ## Clustering: if has a goal location keep moving there
    if unit in knight_to_cluster: 
        try:
            c = knight_to_cluster[unit]
            direction, attack_target, javelin_target = clusters.knight_cluster_sense(gc, unit, c)
        except: 
            print('clustering sense didnt run')

    else: 
        try: 
            direction, attack_target, javelin_target = knight_sense(gc, unit, my_team)
        except:
            print('knight sense didnt run')

    ## Attack
    try:
        ## Check if can javelin
        if unit.is_ability_unlocked() and javelin_target is not None:
            if gc.can_javelin(unit.id, javelin_target.id) and gc.is_javelin_ready(unit.id):
                gc.javelin(unit.id, javelin_target.id)

        ## Check if can attack regularly
        if attack_target is not None:
            if gc.can_attack(unit.id, attack_target.id) and gc.is_attack_ready(unit.id): 
                gc.attack(unit.id, attack_target.id)

    except:
        print('attacks didnt go through')
  
    ## Movement
    try: 
        ## Knight movement away from allies
        if direction == None:  
            nearby = gc.sense_nearby_units(unit.location.map_location(),8)
            direction = sense_util.best_available_direction(gc,unit,nearby)

        if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
            gc.move_robot(unit.id, direction)

            print('knight dir: ', direction)

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
    enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))

    if len(enemies) > 0:
        # Check if in attack range / javelin range
        sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   
        attack_range = unit.attack_range()
        javelin_range = unit.ability_range()

        if unit_loc.is_within_range(attack_range, sorted_enemies[0].location.map_location()):
            target_attack = sorted_enemies[0]

        if unit_loc.is_within_range(javelin_range, sorted_enemies[0].location.map_location()):
            target_javelin = sorted_enemies[0]

        new_direction = unit_loc.direction_to(sorted_enemies[0].location.map_location())

    return (new_direction, target_attack, target_javelin)

def knight_protect_workers(gc, unit, my_team): 
    """
    This function senses nearby workers that are in danger. Attempts to attack the attacker. 

    Returns: Direction to the worker being attacked (only works for melee enemies).
    """
    new_direction = None
    worker_in_danger = None

    unit_loc = unit.location.map_location()

    ## Filter workers by team and then if their health is less than max health, 
    ## assume being attacked
    ally_workers = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, bc.UnitType.Worker)
    if len(ally_workers) > 0: 
        ally_workers = filter(lambda x: x.team == my_team, ally_workers)
    if len(ally_workers) > 0:
        ally_workers = filter(lambda x: x.health < x.max_health, ally_workers)

    ## Sort remaining ally workers by distance from knight
    ## Get direction of the worker and store worker id, otherwise return None for both params
    if len(ally_workers) > 0: 
        ally_workers = sorted(ally_workers, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))
        new_direction = unit_loc.direction_to(ally_workers[0].location.map_location())
        worker_in_danger = ally_workers[0]

    return (new_direction, worker_in_danger)



