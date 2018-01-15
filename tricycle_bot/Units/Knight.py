import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.clusters as clusters


def timestep(gc, unit,composition, knight_to_cluster, seen_knights_ids):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()

    direction = None

    location = unit.location

    if location.is_on_map() and unit.id not in seen_knights_ids: 
        ## Clustering: if has a goal location keep moving there
        if unit.id in knight_to_cluster: 
            try:
                c = knight_to_cluster[unit.id]
                print('cluster units: ', c.cluster_units())

                valid_cluster = clusters.knight_cluster_sense(gc, unit, c)
                print('valid_cluster: ', valid_cluster)

                if not valid_cluster: 
                    clusters.remove_cluster(c, knight_to_cluster)
                else: 
                    for cluster_unit_id in c.cluster_units(): 
                        seen_knights_ids.add(cluster_unit_id)
                        
                print('new seen knights ids: ', seen_knights_ids)
                print('knight to cluster: ', knight_to_cluster)

            except: 
                print('KNIGHT clustering sense didnt run')

        else: 
            try: 
                knight_sense(gc, unit, knight_to_cluster)
            except:
                print('KNIGHT sense didnt run')

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
            print('KNIGHT movement didnt go through')

def knight_sense(gc, unit, knight_to_cluster): 
    """
    This function chooses the direction the knight should move in. If it senses enemies nearby 
    then will return direction that it can move to. If it can attack it will say if it is in
    range for regular attack and/or javelin.
    Otherwise, will attempt to group with other allied knights and return a direction to clump
    the knights up. 

    Returns: New desired direction. 
    """
    new_direction = None

    unit_loc = unit.location.map_location()
    try:
        enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
    except: 
        print('KNIGHTS ARE FUCKERS')

    if len(enemies) > 0:
        ## Create cluster! 
        unavailable_knights = set(knight_to_cluster.keys())

        new_cluster = clusters.create_knight_cluster(gc, unit, enemies[0], unavailable_knights)

        cluster_unit_ids = new_cluster.cluster_units()
        for unit_id in cluster_unit_ids: 
            knight_to_cluster[unit_id] = new_cluster

        # print('knight to cluster: ', knight_to_cluster)

    else:
        print('KNIGHT no enemies')

    #     # Check if in attack range / javelin range
    #     sorted_enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   
    #     attack_range = unit.attack_range()
    #     javelin_range = unit.ability_range()

    #     if unit_loc.can_attack(unit.id, sorted_enemies[0].id):
    #         target_attack = sorted_enemies[0]

    #     if unit_loc.can_javelin(unit.id, sorted_enemies[0].id):
    #         target_javelin = sorted_enemies[0]

    #     shape = [sorted_enemies[0].location.map_location().x - unit_loc.x, sorted_enemies[0].location.map_location().y - unit_loc.y]
    #     directions = sense_util.get_best_option(shape)
    #     for d in directions: 
    #         if gc.can_move(unit.id, d):
    #             new_direction = d

    # return (new_direction, target_attack, target_javelin)
