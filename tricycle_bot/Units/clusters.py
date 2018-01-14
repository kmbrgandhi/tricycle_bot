import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

class Cluster:
    def __init__(self):
        self.units = set()
        self.target_loc = None
        self.target_unit = None
        self.protect_loc = None 
        self.protect_unit = None

        self.target = False

    def add_unit(self, unit):
        self.units.add(unit)

    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)

    def unit_set(self): ## MUTABLE 
        return self.units

    def enemy_target(self): 
        self.target = True

    def set_target_unit(self, unit):
        self.target_unit = unit
        self.target_loc = unit.location.map_location()

    def set_protect_unit(self, unit):
        self.protect_unit = unit
        self.protect_loc = unit.location.map_location()

    def calculate_avg_loc(self): 
        if len(self.units) == 0: 
            return None
        avg_loc = [0,0]
        for unit in self.units: 
            avg_loc[0] += unit.location.map_location().x
            avg_loc[1] += unit.location.map_location().y
        avg_loc[0] = avg_loc[0] // len(self.units)
        avg_loc[1] = avg_loc[1] // len(self.units)

        return (avg_loc[0], avg_loc[1])

    def calculate_unit_direction(self, unit): 
        """
        Check that unit is in self.units. 

        If searching for a target will not always have access to its location. If not 
        visible, just move in direction of last recorded location. 
        """
        if unit in self.units: 
            if self.target: 
                ## Try to get target's actual location 
                try: 
                    self.target_loc = self.target_unit.location.map_location()
                except: 
                    print('target isnt visible OR target died')
            else:
                ## Find location of sad ally
                try: 
                    self.protect_loc = self.protect_unit.location.map_location()
                except: 
                    print('ally died')
            
            ## Calculate appropriate direction for unit 
            direction = None
            shape = [cluster. - location.x, target.y - location.y]
            directions = sense_util.get_best_option(shape)
            for d in directions: 
                if gc.can_move(unit.id, d):
                    direction = d

            return direction

        else: 
            return None


    # def reset_target(self):
    #     self.target_loc = None
    #     self.target_unit = None

    # def reset_protect(self):
    #     self.protect_loc = None
    #     self.protect_unit = None

def create_knight_cluster(gc, unit, knight_to_cluster, knight_clusters, distress=False):
    """
    This function assumes that current unit received distress signal from nearby worker 
                                        OR
    has sensed a "relevant" enemy and has chosen to set it as its attack target. 

    It creates a unit cluster given nearby units that will have a common goal: either
    defend the worker or attack a specific target. 

    The distress parameter dictates whether the cluster will be used to protect a worker 
    vs. attack an enemy. 
    """
    ## Create new cluster for this unit only if unit not already in cluster
    if unit not in knight_to_cluster:
        ## Find all nearby allied units 
        ally_units = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, bc.UnitType.Knight) 
        if len(ally_units) > 0:
            ally_units = sorted(ally_units, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))

        ## Create a cluster of nearby allied units
        new_knight_cluster = Cluster()
        new_knight_cluster.add_unit(unit)
        for knight in ally_units: 
            if knight not in knight_to_cluster: 
                new_knight_cluster.add_unit(knight)
                knight_to_cluster[knight] = new_knight_cluster # Modify unit clustering data structure

        ## If detected distress signal then read from wherever its from
        if distress: 
            print('distress')
        else: 
            enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
            if len(enemies) > 0: 
                enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   
                new_unit_cluster.set_target_loc(enemies[0].location.map_location())
                new_unit_cluster.set_target_unit(enemies[0])

        ## Modify unit clustering data structures
        knight_clusters.add(new_knight_cluster)

# def knight_cluster_sense(gc, unit, cluster): 
#     direction = None
#     target_attack = None
#     target_javelin = None

#     ## Move in direction of target / worker
#     shape = [cluster. - location.x, target.y - location.y]
#     directions = sense_util.get_best_option(shape)
#     for d in directions: 
#         if gc.can_move(unit.id, d):
#             direction = d
