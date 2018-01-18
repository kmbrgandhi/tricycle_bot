import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

class Cluster: 

    def __init__(self, unit_ids, target, target_unit, unit_vision):
        self.units = set()
        self.target_loc = None
        self.target_unit_id = None

        for unit_id in unit_ids: 
            self.units.add(unit_id)

        self.target = target

        self.target_unit_id = target_unit.id
        self.target_loc = target_unit.location.map_location()

        self.radius = int(unit_vision * (1 + len(self.units)/10))

    def cluster_units(self):  
        return self.units

    def clean_cluster(self, gc, unit_to_cluster):
        units = list()
        remove = set()
        for unit_id in self.units: 
            try: 
                unit = gc.unit(unit_id)
                units.append(unit)
            except: 
                remove.add(unit_id)
                
        for unit_id in remove: 
            self.units.remove(unit_id)
            del unit_to_cluster[unit_id]

        return units

    def avg_cluster_location(self, gc): 
        avg_x = 0
        avg_y = 0
        counter = 0

        for unit_id in self.units: 
            unit = gc.unit(unit_id)
            avg_x += unit.location.map_location().x
            avg_y += unit.location.map_location().y
            counter += 1

        avg_x = int(avg_x // counter)
        avg_y = int(avg_y // counter)
        avg_loc = bc.MapLocation(bc.Planet.Earth, avg_x, avg_y)

        return avg_loc

    def update_target(self, gc): 
        """
        Updates enemy if there is another enemy closer to cluster
        """
        avg_loc = self.avg_cluster_location(gc)

        enemies = gc.sense_nearby_units_by_team(avg_loc, self.radius, sense_util.enemy_team(gc))
        enemies = sorted(enemies, key=lambda x: x.location.map_location().distance_squared_to(avg_loc)) 

        if len(enemies) > 0: 
            if enemies[0].id != self.target_unit_id: 
                self.target_unit_id = enemies[0].id
                print('new enemy: ', self.target_unit_id)
            self.target_loc = enemies[0].location.map_location()

            return True
        else:
            return False

    def movement_unit_order(self, gc, units): 
        """
        Find the optimal order in which to move the units to avoid blocking. 

        Returns: list of ordered unit id's.
        """
        ordered_units = sorted(units, key=lambda x: x.location.map_location().distance_squared_to(self.target_loc))

        return ordered_units

    def calculate_unit_direction(self, gc, unit, unit_loc): 
        """
        Check that unit is in self.units. 

        If searching for a target will not always have access to its location. If not 
        visible, just move in direction of last recorded location. 
        """
        directions = None

        ## Calculate appropriate direction for unit 
        shape = [self.target_loc.x - unit_loc.x, self.target_loc.y - unit_loc.y]
        directions = sense_util.get_best_option(shape)

        return directions

    def attack_enemy(self, gc, unit, unit_loc):
        """
        If there is a visible enemy target, see if in range for javelin / attack. 
        If protecting ally, sense closest enemy and see if in range for javelin / attack. 
        """
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
                    pass

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

def create_knight_cluster(gc, unit, unit_loc, enemy, unavailable_knight_ids):
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
    if unit.id not in unavailable_knight_ids:
        ## Find all nearby allied units 
        try: 
            nearby_ally_units = gc.sense_nearby_units_by_type(unit_loc, unit.vision_range, unit.unit_type) 
            nearby_ally_units = list(filter(lambda x: x.team == gc.team(), nearby_ally_units))
        except:
            # print('fuck it')
            pass

        ## Create a cluster of nearby allied units
        cluster_allies = set()

        cluster_allies.add(unit.id)
        for knight in nearby_ally_units: 
            if knight.id not in unavailable_knight_ids: 
                cluster_allies.add(knight.id)

        print('size cluster: ', len(cluster_allies))
        new_knight_cluster = Cluster(cluster_allies, True, enemy, unit.vision_range) ## For now only create clusters when see enemy (target=True)

        return new_knight_cluster

def knight_cluster_sense(gc, unit, unit_loc, cluster, knight_to_cluster): 
    """
    Processes movements & attack patterns for all knights in the cluster.

    Returns: True if cluster still valid, False if the target / ally died or can't be detected. 
    """
    target_dead = True

    units = cluster.clean_cluster(gc, knight_to_cluster)
    visible = cluster.update_target(gc)

    try: 
        ordered_units = cluster.movement_unit_order(gc, units)
    except:
        ordered_units = list(cluster.cluster_units())


    for knight in ordered_units:
        knight_loc = knight.location.map_location()


        ## Attack if in range (aa or javelin)
        if visible and gc.is_attack_ready(knight.id): 
            enemy_id = cluster.target_unit_id
            if gc.can_attack(knight.id, enemy_id):
                gc.attack(knight.id, enemy_id)
                print('attacked')
        else: 
            directions = cluster.calculate_unit_direction(gc, knight, knight_loc)
            if directions != None and len(directions) > 0 and gc.is_move_ready(knight.id): 
                for d in directions: 
                    if gc.can_move(knight.id, d):
                        gc.move_robot(knight.id, d)
                        print('moved!')
                        break


    ## If cluster target / worker not visible, disband cluster
    return visible


