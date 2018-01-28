import battlecode as bc
import random
import sys
import traceback

import Units.variables as variables
import Units.explore as explore
import Units.sense_util as sense_util

class QuadrantInfo():
    '''
    Scan all enemies and put all info into quadrants before turn
    '''
    def __init__(self, bottom_left): 
        self.bottom_left = bottom_left ## (x,y)
        if variables.curr_planet == bc.Planet.Earth:
            self.quadrant_size = variables.earth_quadrant_size 
        else:
            self.quadrant_size = variables.mars_quadrant_size 

        self.quadrant_locs = set()
        self.get_quadrant_locs()

        self.middle = (self.bottom_left[0]+int(self.quadrant_size/2), self.bottom_left[1]+int(self.quadrant_size/2))
        
        self.target_loc = None 
        self.healer_loc = None

        self.get_passable_locations()

        self.enemies = set()
        self.enemy_workers = set()
        self.enemy_factories = set()

        self.knights = set()
        self.rangers = set()
        self.healers = set()
        self.mages = set()
        self.workers = set()
        self.factories = set()

        self.num_died = 0

        self.enemy_locs = {}

        self.health_coeff = None

    def get_quadrant_locs(self):
        if variables.curr_planet == bc.Planet.Earth: 
            passable_locations = variables.passable_locations_earth
            max_width = variables.earth_start_map.width
            max_height = variables.earth_start_map.height
        else: 
            passable_locations = variables.passable_locations_mars
            max_width = variables.mars_start_map.width
            max_height = variables.mars_start_map.height
        for i in range(self.quadrant_size): 
            x = self.bottom_left[0] + i
            if x < max_width: 
                for j in range(self.quadrant_size): 
                    y = self.bottom_left[1] + j
                    if y < max_height: 
                        self.quadrant_locs.add((x,y))

    def get_passable_locations(self):
        if variables.curr_planet == bc.Planet.Earth: 
            passable_locations = variables.passable_locations_earth
            max_width = variables.earth_start_map.width
            max_height = variables.earth_start_map.height
        else: 
            passable_locations = variables.passable_locations_mars
            max_width = variables.mars_start_map.width
            max_height = variables.mars_start_map.height

        if self.middle[0] < max_width and self.middle[1] < max_height and passable_locations[self.middle]: 
            self.target_loc = self.middle
            self.healer_loc = self.middle
        else: 
            for loc in self.quadrant_locs:
                if passable_locations[loc]:
                    self.target_loc = loc 
                    self.healer_loc = loc

    def update_healer_ideal_loc(self): 
        if variables.curr_planet == bc.Planet.Earth: 
            passable_locations = variables.passable_locations_earth
        else: 
            passable_locations = variables.passable_locations_mars

        neighbor_quadrants = self.get_neighboring_quadrants() 

        enemies = set()
        most_enemies = 0
        worst_quadrant = None
        for quadrant in neighbor_quadrants: 
            if quadrant in variables.quadrant_battle_locs: 
                q_enemies = variables.quadrant_battle_locs[quadrant].enemies
                enemies.update(q_enemies)
                if len(q_enemies) > most_enemies: 
                    most_enemies = len(q_enemies)
                    worst_quadrant = quadrant

        if len(enemies) == 0: 
            return 

        worst_middle = variables.quadrant_battle_locs[worst_quadrant].middle
        furthest_away = sorted(self.quadrant_locs, key=lambda x: sense_util.distance_squared_between_coords(x, worst_middle),reverse=True)

        for loc in furthest_away: 
            if passable_locations[loc]: 
                self.healer_loc = loc
                break

    def get_neighboring_quadrants(self): 
        quadrant = (int(self.bottom_left[0] / self.quadrant_size), int(self.bottom_left[1] / self.quadrant_size))
        return explore.coord_neighbors(quadrant)

    def all_allies(self): 
        return self.knights | self.rangers | self.healers | self.mages | self.workers
    
    def fighters(self): 
        return self.knights | self.rangers | self.mages

    def reset_num_died(self):
        self.num_died = 0

    def add_enemy(self, enemy, enemy_id, enemy_loc): 
        self.enemies.add(enemy_id)
        self.enemy_locs[enemy_loc] = enemy

    def update_ally_health_coefficient(self, gc): 
        health = 0
        max_health = 0
        if len(self.fighters()) == 0: 
            self.health_coeff = None
        else: 
            for ally_id in self.fighters(): 
                ally = gc.unit(ally_id)
                health += ally.health
                max_health += ally.max_health
            self.health_coeff = 1 - (health / max_health)

    def update_enemies(self, gc): 
        ## Reset
        self.enemies = set()
        self.enemy_workers = set()
        self.enemy_factories = set()

        if variables.curr_planet == bc.Planet.Earth: 
            max_width = variables.earth_start_map.width
            max_height = variables.earth_start_map.height
        else: 
            max_width = variables.mars_start_map.width
            max_height = variables.mars_start_map.height

        ## Find enemies in quadrant
        # If enemy in location that can't be sensed don't erase it yet
        for i in range(self.quadrant_size): 
            x = self.bottom_left[0] + i
            for j in range(self.quadrant_size):
                y = self.bottom_left[1] + j
                loc = (x,y)
                if loc[0] < max_width and loc[1] < max_height: 
                    map_loc = bc.MapLocation(variables.curr_planet, x, y)
                    if gc.can_sense_location(map_loc): 
                        if gc.has_unit_at_location(map_loc):
                            unit = gc.sense_unit_at_location(map_loc)
                            if unit.team == variables.enemy_team:
                                if unit.unit_type == bc.UnitType.Worker: 
                                    self.enemy_workers.add(unit.id)
                                elif unit.unit_type == bc.UnitType.Factory: 
                                    self.enemy_factories.add(unit.id)
                                    self.enemies.add(unit.id)
                                else: 
                                    self.enemies.add(unit.id)                                    
                                self.enemy_locs[loc] = unit
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
            # self.num_died += 1
        elif ally_id in self.mages: 
            self.mages.remove(ally_id)
            # self.num_died += 1
        elif ally_id in self.workers: 
            self.workers.remove(ally_id)
            # self.num_died += 1
        elif ally_id in self.factories: 
            self.factories.remove(ally_id)

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

    def urgency_coeff(self, robot_type): 
        """
        1. Number of allied units who died in this quadrant
        3. Number of enemies in the quadrant
        """
        if robot_type == "ranger": 
            if self.health_coeff is not None: 
                return self.num_died/(self.quadrant_size**2) + self.health_coeff
            else:
                return self.num_died/(self.quadrant_size**2)
        elif robot_type == "healer":
            if self.health_coeff is not None: 
                if len(self.all_allies()) > 0: 
                    return (self.num_died/(self.quadrant_size**2)) + 1.5*self.health_coeff + (len(self.fighters())/len(self.all_allies()))
                else: 
                    return (self.num_died/(self.quadrant_size**2)) + 1.5*self.health_coeff
            else: 
                if len(self.all_allies()) > 0: 
                    return (self.num_died/(self.quadrant_size**2)) + (len(self.fighters())/len(self.all_allies()))
                else: 
                    return (self.num_died/(self.quadrant_size**2))
        elif robot_type == "knight": 
            return len(self.enemy_factories)/self.quadrant_size + 2*len(self.enemies)/(self.quadrant_size**2) + len(self.enemy_workers)/(self.quadrant_size**2)

    def __str__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ntarget loc: " + str(self.target_loc) + "\nhealer loc: " + str(self.healer_loc) + "\n"

    def __repr__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ntarget loc: " + str(self.target_loc) + "\nhealer loc: " + str(self.healer_loc) + "\n" 
