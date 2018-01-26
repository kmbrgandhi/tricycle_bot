import battlecode as bc
import random
import sys
import traceback

import Units.variables as variables

class QuadrantInfo():
    '''
    Scan all enemies and put all info into quadrants before turn
    '''
    def __init__(self, bottom_left): 
        self.bottom_left = bottom_left ## (x,y)
        self.enemies = set()

        self.knights = set()
        self.rangers = set()
        self.healers = set()
        self.mages = set()
        self.workers = set()

        self.num_died = 0

        self.occupied_locs = {}
        
        self.quadrant_locs = set([])
        for i in range(variables.quadrant_size):
            x = self.bottom_left[0] + i
            for j in range(variables.quadrant_size): 
                y = self.bottom_left[1] + j
                self.quadrant_locs.add((x,y))

    def all_allies(self): 
        return self.knights.union(self.rangers, self.healers, self.mages, self.workers) 

    def reset_num_died(self):
        self.num_died = 0

    def add_enemy(self, enemy_id): 
        self.enemies.add(enemy_id)

    def update_enemies(self, gc): 
        ## Reset
        old_occupied_locs = self.occupied_locs
        self.occupied_locs = {}
        self.enemies = set()

        ## Find enemies in quadrant
        # If enemy in location that can't be sensed don't erase it yet
        for loc in self.quadrant_locs: 
            map_loc = bc.MapLocation(variables.curr_planet, loc[0], loc[1])
            if gc.can_sense_location(map_loc): 
                if gc.has_unit_at_location(map_loc):
                    enemy = gc.sense_unit_at_location(map_loc)
                    self.occupied_locs[loc] = enemy
                    self.enemies.add(enemy.id)
            elif loc in old_occupied_locs: 
                self.occupied_locs[loc] = old_occupied_locs[loc]
                self.enemies.add(old_occupied_locs[loc].id)

    def remove_ally(self, ally_id): 
        if ally_id in self.knights: 
            self.knights.remove(ally_id)
        elif ally_id in self.rangers: 
            self.rangers.remove(ally_id)
        elif ally_id in self.healers: 
            self.healers.remove(ally_id)
        elif ally_id in self.mages: 
            self.mages.remove(ally_id)
        elif ally_id in self.workers: 
            self.workers.remove(ally_id)
        self.num_died += 1

    def add_ally(self, ally_id, robot_type): 
        if robot_type == "knight": 
            self.knights.add(ally_id)
        elif robot_type == "ranger":
            self.rangers.add(ally_id)
        elif robot_type == "mage": 
            self.mages.add(ally_id)
        elif robot_type == "healer": 
            self.healers.add(ally_id)
        elif robot_type == "worker":
            self.workers.add(ally_id) 

    def urgency_coeff(self, healer=False): 
        """
        1. Number of allied units who died in this quadrant
        3. Number of enemies in the quadrant
        """
        if not healer: 
            return self.num_died/25 + len(self.enemies)/25
        else: 
            return 3*(self.num_died/25) + len(self.enemies)/25

    def __str__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ncoefficient: " + str(self.urgency_coeff()) 

    def __repr__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ncoefficient: " + str(self.urgency_coeff()) 
