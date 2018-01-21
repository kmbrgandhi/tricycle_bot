import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

class Cluster:

    BATTLE_RADIUS = 9
    GROUPING_RADIUS = 4
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
            try:
                ally = gc.unit(ally_id)
                if ally.location.map_location().distance_to(self.grouping_location) > Cluster.GROUPING_RADIUS:
                    return False
            except:
                continue
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
            locs_near = gc.all_locations_within(loc, Cluster.BATTLE_RADIUS)
            for near in locs_near: 
                if gc.has_unit_at_location(near):
                    unit = gc.sense_unit_at_location(near)
                    if unit.team == enemy_team:
                        sees_enemy = True
                        self.enemies.add(unit.id)
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
            try: 
                ally = gc.unit(ally_id)
                health += ally.health
                total_health += ally.max_health
            except: 
                continue

        little_allies_coeff = len(self.allies) / 20
        if total_health > 0: low_health_allies_coeff = 1 - (health / total_health)

        self.urgency = 1.5*dangerous_enemies_coeff + 0.5*higher_health_enemies_coeff + little_allies_coeff + low_health_allies_coeff
        return self.urgency


    def __str__(self):
        return "allies: " + str(self.allies) + "\nenemies: " + str(self.enemies) + "\ngrouping location: " + str(self.grouping_location) + "\ngrouped: " + str(self.grouped)

    def __repr__(self):
        return "allies: " + str(self.allies) + "\nenemies: " + str(self.enemies) + "\ngrouping location: " + str(self.grouping_location) + "\ngrouped: " + str(self.grouped)

