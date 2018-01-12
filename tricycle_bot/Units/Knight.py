import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util


def timestep(gc, unit,composition, knight_to_cluster, knight_clusters):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()

    try: 
        direction, attack_target, javelin_target = knight_sense(gc, unit, my_team)
    except:
        print('knight sense didnt run')

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

def create_knight_cluster(gc, unit, knight_to_cluster, knight_clusters, distress=False):
    """
    This function assumes that current unit received distress signal from nearby worker 
                                        OR
    has sensed a "relevant" enemy and has chosen to set it as its attack target. 

    It creates a knight cluster given nearby knights that will have a common goal: either
    defend the worker or attack a specific target. 

    The distress parameter dictates whether the cluster will be used to protect a worker 
    vs. attack an enemy. 
    """
    ## Create new cluster for this unit only if unit not already in cluster
    if unit not in knight_to_cluster:
        ## Find all nearby allied knights 
        ally_knights = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, bc.UnitType.Knight) 
        if len(ally_knights) > 0:
            ally_knights = sorted(ally_knights, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))

        ## Create a cluster of nearby allied knights
        new_knight_cluster = Knight_Cluster()
        new_knight_cluster.add_knight(unit)
        for knight in ally_knights: 
            if knight not in knight_to_cluster: 
                new_knight_cluster.add_knight(knight)
                knight_to_cluster[knight] = new_knight_cluster # Modify knight clustering data structure

        ## If detected distress signal then read from wherever its from
        if distress: 
            print('distress')
        else: 
            enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
            if len(enemies) > 0: 
                enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   
                new_knight_cluster.set_target_loc(enemies[0].location.map_location())
                new_knight_cluster.set_target_unit(enemies[0])

        ## Modify knight clustering data structures
        knight_clusters.add(new_knight_cluster)

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

    # if len(enemies) == 0: 
    #     # Sense allied knights and find direction to approach them
    #     ally_knights = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, bc.UnitType.Knight) 
    #     if len(ally_knights) > 0:
    #         ally_knights = sorted(ally_knights, key=lambda x: x.location.map_location().distance_squared_to(unit_loc), reverse=True)
    #         new_direction = unit_loc.direction_to(ally_knights[0].location.map_location())

    # else: 

    if len(enemies) > 0:
        # Broadcast enemy location? 

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


class Knight_Cluster:
    def __init__(self):
        self.knights = set()
        self.target_loc = None
        self.target_unit = None
        self.protect_loc = None 
        self.protect_unit = None

    def add_knight(self, knight):
        self.knights.add(knight)

    def remove_knight(self, knight):
        if knight in self.knights:
            self.knights.remove(knight)

    def knight_set(self): ## MUTABLE 
        return self.knights

    def set_target_loc(self, loc):
        self.target_loc = loc

    def set_target_unit(self, unit):
        self.target_unit = unit

    def set_protect_loc(self, loc):
        self.protect_loc = loc

    def set_protect_unit(self, unit):
        self.protect_unit = unit

    def reset_target(self):
        self.target_loc = None
        self.target_unit = None

    def reset_protect(self):
        self.protect_loc = None
        self.protect_unit = None
