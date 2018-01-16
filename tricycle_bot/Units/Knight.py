import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.clusters as clusters

def timestep(gc, unit, composition, knight_to_cluster, seen_knights_ids, KNIGHT_CLUSTER_MIN, constants):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()
    direction = None
    location = unit.location

    if location.is_on_map() and unit.id not in seen_knights_ids: 
        unit_loc = unit.location.map_location()
        ## Clustering: if has a goal location keep moving there
        if unit.id in knight_to_cluster: 
            try:
                c = knight_to_cluster[unit.id]
                valid_cluster = clusters.knight_cluster_sense(gc, unit, unit_loc, c)
            except: 
                # print('KNIGHT clustering sense didnt run')
                pass

            try:
                if not valid_cluster: 
                    clusters.remove_cluster(c, knight_to_cluster)
                    # print('removed cluster')
                else: 
                    seen_knights_ids.update(c.cluster_units())
            except: 
                # print('cannot remove cluster OR add units to seen')
                pass

        else: 
            try: 
                enemy = knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN)
            except:
                # print('KNIGHT sense didnt run')
                pass

        ## Movement
        try: 
            ## Knight movement away from allies
            if direction == None:  
                nearby = gc.sense_nearby_units(unit_loc,8)
                direction = sense_util.best_available_direction(gc,unit,nearby)

            if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
                gc.move_robot(unit.id, direction)
                # print('moved no cluster')

        except:
            # print('KNIGHT movement didnt go through')
            pass

def knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN): 
    """
    This function chooses the direction the knight should move in. If it senses enemies nearby 
    then will return direction that it can move to. If it can attack it will say if it is in
    range for regular attack and/or javelin.
    Otherwise, will attempt to group with other allied knights and return a direction to clump
    the knights up. 

    Returns: New desired direction. 
    """
    new_direction = None

    try:
        enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
    except: 
        # print('KNIGHTS ARE SAD')
        pass

    if len(enemies) > 0:        
        enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))

        ## Remove knights if their clusters are too small
        unavailable_knight_ids = set()
        for u_knight_id in knight_to_cluster: 
            cluster = knight_to_cluster[u_knight_id]
            if len(cluster.cluster_units()) >= KNIGHT_CLUSTER_MIN: 
                unavailable_knight_ids.add(u_knight_id)

        ## Create cluster! 
        new_cluster = clusters.create_knight_cluster(gc, unit, unit_loc, enemies[0], unavailable_knight_ids)

        cluster_unit_ids = new_cluster.cluster_units()
        for unit_id in cluster_unit_ids: 
            knight_to_cluster[unit_id] = new_cluster
