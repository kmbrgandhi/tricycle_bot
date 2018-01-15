import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

class Cluster: 

    def __init__(self, unit_ids, target, target_unit):
        self.units = set()
        self.target_loc = None
        self.target_unit_id = None

        for unit_id in unit_ids: 
            self.units.add(unit_id)

        self.target = target

        self.target_unit_id = target_unit.id
        self.target_loc = target_unit.location.map_location()

    def cluster_units(self):  
        return self.units

    # def update_target_location(self, gc): 
    #     try: 
    #         enemy = gc.unit(self.target_unit_id)
    #         self.target_loc = enemy.location.map_location()
    #         return True
    #     except: 
    #         print('target not visible OR died')
    #         return False

    def update_target(self, gc, unit): 
        """
        Updates enemy if there is another enemy closer to cluster
        """
        try: 
            unit_loc = unit.location.map_location()
            enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
            enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc)) 

            if len(enemies) > 0: 
                if enemies[0].id != self.target_unit_id: 
                    self.target_unit_id = enemies[0].id
                self.target_loc = enemies[0].location.map_location()
                return True
        except:
            return False

    def movement_unit_order(self, gc): 
        """
        Find the optimal order in which to move the units to avoid blocking. 

        Returns: list of ordered unit id's.
        """
        ordered_units = []

        for unit_id in self.units: 
            try: 
                unit = gc.unit(unit_id)
                ordered_units.append(unit)
            except: 
                print(unit_id + ' not found')
                # self.units.remove(unit_id)
                continue

        ordered_units = sorted(ordered_units, key=lambda x: x.location.map_location().distance_squared_to(self.target_loc))
        ordered_units = [x.id for x in ordered_units]
        return ordered_units

    def calculate_unit_direction(self, gc, unit): 
        """
        Check that unit is in self.units. 

        If searching for a target will not always have access to its location. If not 
        visible, just move in direction of last recorded location. 
        """
        directions = None

        if unit.id in self.units: 
            ## Try to get target's actual location
            shape = [self.target_loc.x - unit.location.map_location().x, self.target_loc.y - unit.location.map_location().y]
            
            ## Calculate appropriate direction for unit 
            directions = sense_util.get_best_option(shape)

        return directions

    def attack_enemy(self, gc, unit):
        """
        If there is a visible enemy target, see if in range for javelin / attack. 
        If protecting ally, sense closest enemy and see if in range for javelin / attack. 
        """
        unit_loc = unit.location.map_location()

        enemy_id = None
        attack = False
        javelin = False

        if unit.id in self.units: 
            if self.target: 
                try:
                    if gc.can_attack(unit.id, self.target_unit_id): attack = True
                    if gc.can_javelin(unit.id, self.target_unit_id): javelin = True
                    enemy_id = self.target_unit_id
                except: 
                    print('cannot attack or javelin self.target_unit')

            # else: 
            #     enemies = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, sense_util.enemy_team(gc))
            #     enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(unit_loc))   

            #     if len(enemies) > 0: 
            #         try: 
            #             if gc.can_attack(unit.id, enemies[0].id): attack = True
            #             if gc.can_javelin(unit.id, enemies[0].id): javelin = True
            #             enemy = enemies[0]
            #         except: 
            #             print('cannot attack or javelin searched enemy unit')

        return (enemy_id, attack, javelin)


    def __eq__(self, other): 
        return self.cluster_units() == other.cluster_units() and self.target == other.target

    def __str__(self): 
        return "Units: " + str(self.units) + '\n Target id: ' + str(self.target_unit_id) + ' \n Target loc: ' + str(self.target_loc)

# **************************************      GENERAL      ************************************ #

def remove_cluster(cluster, unit_to_cluster): 
    for unit_id in cluster.cluster_units():
        if unit_id in unit_to_cluster: 
            del unit_to_cluster[unit_id]

# **************************************      RANGERS      ************************************ #

def create_ranger_cluster(gc, unit, enemy, unavailable_ranger_ids): 
    print('hehe')

# **************************************      KNIGHTS      ************************************ #

def create_knight_cluster(gc, unit, enemy, unavailable_knight_ids):
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
    print('creating new cluster')

    unit_loc = unit.location.map_location()

    if unit.id not in unavailable_knight_ids:
        ## Find all nearby allied units 
        try: 
            nearby_ally_units = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, unit.unit_type) 
            nearby_ally_units = list(filter(lambda x: x.team == gc.team(), nearby_ally_units))
        except:
            print('fuck it')

        ## Create a cluster of nearby allied units
        cluster_allies = set()

        cluster_allies.add(unit.id)
        for knight in nearby_ally_units: 
            if knight.id not in unavailable_knight_ids: 
                cluster_allies.add(knight.id)

        new_knight_cluster = Cluster(cluster_allies, True, enemy) ## For now only create clusters when see enemy (target=True)

        return new_knight_cluster

def knight_cluster_sense(gc, unit, cluster): 
    """
    Processes movements & attack patterns for all knights in the cluster.

    Returns: True if cluster still valid, False if the target / ally died or can't be detected. 
    """
    target_dead = True

    visible = cluster.update_target(gc, unit)
    cluster_ordered_units = cluster.movement_unit_order(gc)

    for knight_id in cluster_ordered_units:
        try: 
            knight = gc.unit(knight_id)
        except: 
            print('cant find knight')
            continue

        try: 
            ## Move in direction of target / worker
            directions = cluster.calculate_unit_direction(gc, knight)
        except:
            print('KNIGHT CLUSTER cannot calculate unit dir')

        try: 
            if directions != None and len(directions) > 0 and gc.is_move_ready(knight.id): 
                for d in directions: 
                    if gc.can_move(knight.id, d):
                        gc.move_robot(knight.id, d)
                        print('moved!')
                        break
        except: 
            print('knight cluster movement errors')

        ## Attack if in range (aa or javelin)
        if visible: 
            try: 
                enemy_id, attack, javelin = cluster.attack_enemy(gc, knight)
                if enemy_id != None: 
                    try: 
                        if attack and gc.is_attack_ready(knight.id): 
                            gc.attack(knight.id, enemy_id)
                            print('attacked!')  
                        if javelin and gc.is_javelin_ready(knight.id):
                            gc.javelin(knight.id, enemy_id)
                            print('javelined!')
                    except: 
                        print('knight cluster sense attack errors')
            except: 
                print('attack enemy cluster didnt work')

    ## If cluster target / worker not visible, disband cluster
    if not visible: return False
    else: return True