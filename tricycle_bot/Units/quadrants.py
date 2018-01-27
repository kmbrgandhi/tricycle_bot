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

        self.enemy_locs = {}

    def all_allies(self): 
        return self.knights | self.rangers | self.healers | self.mages | self.workers
    
    def fighters(self): 
        return self.knights | self.rangers | self.mages

    def reset_num_died(self):
        self.num_died = 0

    def add_enemy(self, enemy, enemy_id, enemy_loc): 
        self.enemies.add(enemy_id)
        self.enemy_locs[enemy_loc] = enemy

    def update_enemies(self, gc): 
        ## Reset
        self.enemies = set()

        ## Find enemies in quadrant
        # If enemy in location that can't be sensed don't erase it yet
        for i in range(variables.quadrant_size): 
            x = self.bottom_left[0] + i
            for j in range(variables.quadrant_size):
                y = self.bottom_left[1] + j
                loc = (x,y)
                map_loc = bc.MapLocation(variables.curr_planet, x, y)
                if gc.can_sense_location(map_loc): 
                    if gc.has_unit_at_location(map_loc):
                        unit = gc.sense_unit_at_location(map_loc)
                        if unit.team == variables.enemy_team: 
                            self.enemy_locs[loc] = unit
                            self.enemies.add(unit.id)
                    elif loc in self.enemy_locs: 
                        del self.enemy_locs[loc]
                elif loc in self.enemy_locs: 
                    self.enemies.add(self.enemy_locs[loc].id)

    def remove_ally(self, ally_id): 
        if ally_id in self.knights: 
            self.knights.remove(ally_id)
            self.num_died += 1
        elif ally_id in self.rangers: 
            self.rangers.remove(ally_id)
            self.num_died += 1
        elif ally_id in self.healers: 
            self.healers.remove(ally_id)
            self.num_died += 1
        elif ally_id in self.mages: 
            self.mages.remove(ally_id)
            self.num_died += 1
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
            return self.num_died/(variables.quadrant_size**2) + len(self.enemies)/(variables.quadrant_size**2)
        else: 
            return 3*(self.num_died/(variables.quadrant_size**2))

    def __str__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ndied: " + str(self.num_died) + "\n" 

    def __repr__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ndied: " + str(self.num_died) + "\n" 
