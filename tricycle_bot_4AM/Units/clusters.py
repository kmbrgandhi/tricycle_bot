import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.variables as variables

class Cluster:

    BATTLE_RADIUS = 9
    GROUPING_RADIUS = 3
    DANGEROUS_ENEMIES = [bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage]

    def __init__(self, allies, enemies):
        self.allies = allies
        self.enemies = enemies
        self.urgent = 0 ## 0 - 4 where 4 is the most urgent
        self.grouping_location = None
        self.grouped = False

    def add_ally(self, ally_id):
        self.allies.add(ally_id)

    def remove_ally(self, ally_id):
        if ally_id in self.allies: 
            self.allies.remove(ally_id)

    def allies_grouped(self, gc):
        if self.grouping_location is None or len(self.allies) == 0: return False

        for ally_id in self.allies: 
            if ally_id in variables.my_unit_ids:
                ally = gc.unit(ally_id)
                if sense_util.distance_squared_between_maplocs(ally.location.map_location(), self.grouping_location) > Cluster.GROUPING_RADIUS:
                    return False
        self.grouped = True
        return True

    def update_enemies(self, gc, loc_coords, enemy_team):
        """
        Returns True if there are still enemies. 
        """
        sees_enemy = False
        self.enemies = set()
        loc = bc.MapLocation(gc.planet(), loc_coords[0], loc_coords[1])
        if gc.can_sense_location(loc): 
            enemies = gc.sense_nearby_units_by_team(loc, Cluster.BATTLE_RADIUS, enemy_team)
            if len(enemies) > 0: 
                sees_enemy = True
                self.enemies = set([x.id for x in enemies])
                self.urgency_coeff(gc)
        else: sees_enemy = True
        return sees_enemy

    def urgency_coeff(self, gc):
        """
        Computes the danger of a location in order to send more knights. 
            - More dangerous enemies (knights / rangers / mages) 
            - Higher health enemies
            - Little amount of allies
            - Allies with low health
        """
        dangerous_enemies_coeff = 0
        higher_health_enemies_coeff = 0
        little_allies_coeff = 0
        low_health_allies_coeff = 0

        ## Enemy coeffs
        dangerous = 0
        total_enemies = 0

        health = 0
        total_health = 0

        for enemy_id in self.enemies: 
            try: 
                enemy = gc.unit(enemy_id)
                if enemy.type in Cluster.DANGEROUS_ENEMIES: dangerous += 1
                total_enemies += 1

                health += enemy.health
                total_health += enemy.max_health
            except: 
                continue

        if total_enemies > 0: 
            dangerous_enemies_coeff = dangerous / total_enemies
            higher_health_enemies_coeff = health / total_health

        ## Ally coeffs
        health = 0
        total_health = 0

        for ally_id in self.allies: 
            if ally_id in variables.my_unit_ids:
                ally = gc.unit(ally_id)
                health += ally.health
                total_health += ally.max_health

        little_allies_coeff = len(self.allies) / 20
        if total_health > 0: low_health_allies_coeff = 1 - (health / total_health)

        self.urgency = 1.5*dangerous_enemies_coeff + 0.5*higher_health_enemies_coeff + little_allies_coeff + low_health_allies_coeff
        return self.urgency


    def __str__(self):
        return "allies: " + str(self.allies) + "\nenemies: " + str(self.enemies) + "\ngrouping location: " + str(self.grouping_location) + "\ngrouped: " + str(self.grouped)

    def __repr__(self):
        return "allies: " + str(self.allies) + "\nenemies: " + str(self.enemies) + "\ngrouping location: " + str(self.grouping_location) + "\ngrouped: " + str(self.grouped)

## ========================================================================================================================================================================================= ##

init_units = variables.earth_start_map.initial_units

for unit in init_units: 
    if unit.team == variables.enemy_team:
        loc = unit.location.map_location()
        variables.init_enemy_locs.append(loc)
        variables.earth_battles[(loc.x,loc.y)] = Cluster(allies=set(),enemies=set([unit.id]))
