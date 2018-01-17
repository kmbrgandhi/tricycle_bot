import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.clusters as clusters

def timestep(gc, unit, composition, knight_to_cluster, seen_knights_ids, battle_locs, KNIGHT_CLUSTER_MIN, constants):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    direction = None
    location = unit.location

    if unit.id not in seen_knights_ids and location.is_on_map(): 
        unit_loc = location.map_location()
        ## Clustering: if has a goal location keep moving there
        if unit.id in knight_to_cluster: 
            try:
                print('cluster!')
                c = knight_to_cluster[unit.id]
                valid_cluster = clusters.knight_cluster_sense(gc, unit, unit_loc, c, knight_to_cluster)
                if not valid_cluster: 
                    clusters.remove_cluster(c, knight_to_cluster)
                    # print('removed cluster')
                else: 
                    seen_knights_ids.update(c.cluster_units())
                    
            except: 
                print('KNIGHT clustering sense didnt run')
                pass

        elif len(list(knight_to_cluster.keys())) < 20: 
            try: 
                enemy = knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN, constants)
            except:
                print('KNIGHT sense didnt run')
                pass

            ## Movement
            if len(battle_locs) > 0: 
                weakest = random.choice(list(battle_locs.keys()))
                target_loc = battle_locs[weakest][0]

                shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
                directions = sense_util.get_best_option(shape)

                if directions is not None:
                    if len(directions) > 0 and gc.is_move_ready(unit.id): 
                        for d in directions: 
                            if gc.can_move(unit.id, d):
                                gc.move_robot(unit.id, d)
                                #print('HEALER moved to battle loc!')
                                break
            else:  
                ## Knight movement away from allies
                if direction == None:  
                    nearby = gc.sense_nearby_units(unit_loc,8)
                    direction = sense_util.best_available_direction(gc,unit,nearby)

                if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction):
                    gc.move_robot(unit.id, direction)
                    # print('moved no cluster')

            # except:
            #     print('KNIGHT movement didnt go through')
            #     pass

def knight_sense(gc, unit, unit_loc, knight_to_cluster, KNIGHT_CLUSTER_MIN, constants): 
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
        enemies = gc.sense_nearby_units_by_team(unit_loc, int(unit.vision_range/3), constants.enemy_team)
    except: 
        print('KNIGHTS ARE SAD')
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
    # else:
    #     print('knight no enemies')
