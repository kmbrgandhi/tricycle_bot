import battlecode as bc
import random
import sys
import traceback
import Units.map_info as map_info
import Units.sense_util as sense_util


gc = bc.GameController()

## CONSTANTS ##
directions = list(bc.Direction)


## GENERAL VARIABLES ##

# map info
karbonite_locations = map_info.get_initial_karbonite_locations(gc)
locs_next_to_terrain = map_info.get_locations_next_to_terrain(gc,bc.Planet(0))
earth_start_map = gc.starting_map(bc.Planet.Earth)
mars_start_map = gc.starting_map(bc.Planet.Mars)
my_team = gc.team()
enemy_team = sense_util.enemy_team(gc)

init_enemy_locs = []
for unit in earth_start_map.initial_units: 
    if unit.team == enemy_team:
        init_enemy_locs.append(unit.location.map_location())

num_enemies = 0
info = []
directions = list(bc.Direction)

## WORKER VARIABLES ##
blueprinting_queue = []
building_assignment = {}
blueprinting_assignment = {}

current_worker_roles = {"miner":[],"builder":[],"blueprinter":[],"boarder":[], "repairer":[]}

## KNIGHT VARIABLES ##
battle_locations = {}
assigned_knights = {}
for loc in init_enemy_locs: 
    battle_locations[(loc.x, loc.y)] = set()



# class Constants: 
#     def __init__(self, directions, my_team, enemy_team, starting_map, locs_next_to_terrain, karbonite_locations):
#         self.directions = directions
#         self.my_team = my_team
#         self.enemy_team = enemy_team
#         self.locs_next_to_terrain = locs_next_to_terrain
#         self.karbonite_locations = karbonite_locations
#         self.starting_map = starting_map
#         self.init_enemy_locs = []

#         for unit in self.starting_map.initial_units: 
#             if unit.team == self.enemy_team: 
#                 self.init_enemy_locs.append(unit.location.map_location())