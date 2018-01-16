import battlecode as bc
import random
import sys
import traceback

class Constants: 
    def __init__(self, directions, my_team, enemy_team, locs_next_to_terrain, karbonite_locations):
        self.directions = directions
        self.my_team = my_team
        self.enemy_team = enemy_team
        self.locs_next_to_terrain = locs_next_to_terrain
        self.karbonite_locations = karbonite_locations