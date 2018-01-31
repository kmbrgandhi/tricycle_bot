import battlecode as bc
import random
import sys
import traceback

import Units.variables as variables
import Units.explore as explore
import Units.sense_util as sense_util
import Units.Ranger as Ranger

class QuadrantInfo():
    '''
    Scan all enemies and put all info into quadrants before turn
    '''
    def __init__(self, bottom_left): 
        self.bottom_left = bottom_left ## (x,y)
        if variables.curr_planet == bc.Planet.Earth:
            self.quadrant_size = variables.earth_quadrant_size 
            self.max_width = variables.earth_start_map.width
            self.max_height = variables.earth_start_map.height
            self.passable_locations = variables.passable_locations_earth
        else:
            self.quadrant_size = variables.mars_quadrant_size 
            self.max_width = variables.mars_start_map.width
            self.max_height = variables.mars_start_map.height
            self.passable_locations = variables.passable_locations_mars

        self.quadrant_locs = set()
        self.get_quadrant_locs()

        self.middle = (self.bottom_left[0]+int(self.quadrant_size/2), self.bottom_left[1]+int(self.quadrant_size/2))
        
        self.target_loc = None 
        self.healer_locs = set()

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

        self.in_battle = (False, 0) # (in battle, last_turn_quadrant_attacked)

        self.where_rangers_attacking = {}
        for d in variables.directions: 
            self.where_rangers_attacking[d] = 0

        self.assigned_healers = {}

        self.num_died = 0
        self.num_workers_assigned = 0

        self.enemy_locs = {}


        self.health_coeff = None

    def get_quadrant_locs(self):
        for i in range(self.quadrant_size): 
            x = self.bottom_left[0] + i
            if x < self.max_width: 
                for j in range(self.quadrant_size): 
                    y = self.bottom_left[1] + j
                    if y < self.max_height and self.passable_locations[(x,y)]: 
                        self.quadrant_locs.add((x,y))

    def get_passable_locations(self):
        for loc in self.quadrant_locs:
            self.target_loc = loc 
            break

    def update_healer_locs(self): 
        unit_locations = variables.unit_locations
        # Only run if there is more than one ranger here 
        if len(self.rangers) > 0: 
            ## Get avg ranger location in current quadrant
            avg_ranger_x = 0
            avg_ranger_y = 0
            for ranger_id in self.rangers: 
                ranger_loc = unit_locations[ranger_id]
                avg_ranger_x += ranger_loc[0]
                avg_ranger_y += ranger_loc[1]
            avg_ranger_x = int(avg_ranger_x/len(self.rangers))
            avg_ranger_y = int(avg_ranger_y/len(self.rangers))
            avg_ranger = (avg_ranger_x, avg_ranger_y)

            ## Get direction in which most rangers are attacking 
            best_dir = None
            best_count = 0

            for d in self.where_rangers_attacking: 
                count = self.where_rangers_attacking[d]
                if count > best_count: 
                    best_dir = d
                    best_count = count

            ## Set the group of ideal healer locations to be 3-4 squares behind rangers in 
            ## opposite direction of attack direction
            if best_dir is not None: 
                opp_best_dir = sense_util.opposite(best_dir)
                ideal_loc = sense_util.add_multiple(avg_ranger, best_dir, 2)
                self.healer_locs = self.get_ideal_healer_locs(ideal_loc, opp_best_dir)

                self.update_assigned_healer_locs()

    def get_ideal_healer_locs(self, loc, d): 
        side1 = d.rotate_right().rotate_right()
        side2 = d.rotate_left().rotate_left()

        processed_locs = set() 

        if loc in self.passable_locations and self.passable_locations[loc] and self.is_accessible_from_init_loc(loc):
            processed_locs.add(loc)

        for i in range(1,6): 
            loc1 = sense_util.add_multiple(loc, side1, i)
            loc2 = sense_util.add_multiple(loc, side2, i)

            if loc1 in self.passable_locations and self.passable_locations[loc1] and self.is_accessible_from_init_loc(loc1):
                processed_locs.add(loc1)

            if loc2 in self.passable_locations and self.passable_locations[loc2] and self.is_accessible_from_init_loc(loc2):
                processed_locs.add(loc2)

        return processed_locs

    def is_within_map(self, loc): 
        if loc[0] >= 0 and loc[0] < self.max_width and loc[1] >= 0 and loc[1] < self.max_height: 
            return True 
        return False

    def is_accessible_from_init_loc(self, coords):
        """
        Determines if location 'coords' is accessible from any of our initial locations. 
        """
        accessible = False
        if variables.curr_planet == bc.Planet.Earth:
            for init_loc in variables.our_init_locs:
                bfs_array = variables.bfs_array
                our_coords_val = Ranger.get_coord_value((init_loc.x,init_loc.y))
                target_coords_val = Ranger.get_coord_value(coords)
                if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
                    accessible = True
        else:
            accessible = True
        return accessible

    def is_accessible(self, unit_loc, target_loc): 
        bfs_array = variables.bfs_array
        our_coords_val = Ranger.get_coord_value(unit_loc)
        target_coords_val = Ranger.get_coord_value(target_loc)
        if bfs_array[our_coords_val, target_coords_val]!=float('inf'):
            return True 
        return False

    def update_assigned_healer_locs(self): 
        if len(self.healer_locs) > 0:
            for healer_id in self.assigned_healers: 
                curr_loc = variables.unit_locations[healer_id]
                for loc in self.healer_locs: 
                    if self.is_accessible(curr_loc, loc): 
                        self.assigned_healers[healer_id] = loc
                        before = variables.assigned_healers[healer_id]
                        variables.assigned_healers[healer_id] = (before[0], loc)
                        # self.healer_locs.remove(loc)
                        break

    def update_in_battle(self): 
        if self.in_battle[0]: 
            if variables.curr_round > 4 + self.in_battle[1]:
                self.in_battle = (False, variables.curr_round)

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

        ## Find enemies in quadrant
        # If enemy in location that can't be sensed don't erase it yet
        battle_locs = []
        ranged = 0
        for loc in self.quadrant_locs: 
            map_loc = bc.MapLocation(variables.curr_planet, loc[0], loc[1])
            if gc.can_sense_location(map_loc): 
                if gc.has_unit_at_location(map_loc):
                    unit = gc.sense_unit_at_location(map_loc)
                    if unit.team == variables.enemy_team:
                        if unit.unit_type == variables.unit_types["worker"]:
                            self.enemy_workers.add(unit.id)
                        elif unit.unit_type == variables.unit_types["factory"]:
                            self.enemy_factories.add(unit.id)
                            self.enemies.add(unit.id)
                        elif unit.unit_type == variables.unit_types["ranger"] or unit.unit_type == variables.unit_types["mage"]:
                            self.enemies.add(unit.id)
                            ranged += 1
                        else:
                            self.enemies.add(unit.id)
                        self.enemy_locs[loc] = unit
                        battle_locs.append((loc))
                        self.target_loc = loc
                elif loc in self.enemy_locs: 
                    del self.enemy_locs[loc]
            elif loc in self.enemy_locs: 
                self.enemies.add(self.enemy_locs[loc].id)
                battle_locs.append(loc)
        return (battle_locs, ranged)

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

    def urgency_coeff_without_add_units(self, robot_type):
        if robot_type == "healer":
            if not self.in_battle[0]:
                return 0
            else: 
                if self.health_coeff is not None: 
                    return self.num_died/(self.quadrant_size**2) + self.health_coeff
                else:
                    return (self.num_died / (self.quadrant_size ** 2)) 

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
            if len(self.rangers) == 0: assigned_coeff = 0
            else: assigned_coeff = 1 - len(self.assigned_healers)/len(self.rangers)

            if self.in_battle[0]: assigned_battle = 1
            else: assigned_battle = 0

            if self.health_coeff is not None: 
                if len(self.all_allies()) > 0: 
                    return assigned_battle + assigned_coeff + (self.num_died/(self.quadrant_size**2)) + 1.5*self.health_coeff + 0.5*(len(self.fighters())/len(self.all_allies()))
                else: 
                    return 0
            else: 
                if len(self.all_allies()) > 0: 
                    return assigned_battle + assigned_coeff + (self.num_died/(self.quadrant_size**2)) + 0.5*(len(self.fighters())/len(self.all_allies()))
                else: 
                    return 0
        elif robot_type == "knight": 
            return 1.5*len(self.enemy_factories)/self.quadrant_size + 1.5*len(self.enemies)/(self.quadrant_size**2) + 0.5*len(self.enemy_workers)/(self.quadrant_size**2)

    def __str__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ntarget loc: " + str(self.target_loc) + "\n"

    def __repr__(self):
        return "bottom left: " + str(self.bottom_left) + "\nallies: " + str(self.all_allies()) + "\nenemies: " + str(self.enemies) + "\ntarget loc: " + str(self.target_loc) + "\n" 
