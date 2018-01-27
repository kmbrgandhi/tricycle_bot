import battlecode as bc
import random
import sys
import traceback
import Units.map_info as map_info
import Units.sense_util as sense_util
import Units.explore as explore
import time
import numpy as np
from scipy.sparse import dok_matrix
from scipy.sparse import csgraph


gc = bc.GameController()



## CONSTANTS ##

my_team = gc.team()
enemy_team = sense_util.enemy_team(gc)

directions = list(bc.Direction)
all_but_center_dir = directions[:-1]


earth = bc.Planet.Earth
mars = bc.Planet.Mars

unit_types = {"worker":bc.UnitType.Worker,
			"knight":bc.UnitType.Knight,
			"mage":bc.UnitType.Mage,
			"healer":bc.UnitType.Healer,
			"ranger":bc.UnitType.Ranger,
			"factory":bc.UnitType.Factory,
			"rocket":bc.UnitType.Rocket}

## GENERAL VARIABLES ##

# map info
karbonite_locations = map_info.get_initial_karbonite_locations(gc)
impassable_terrain_earth = map_info.get_impassable_terrain(gc,earth)
impassable_terrain_mars = map_info.get_impassable_terrain(gc,mars)
locs_next_to_terrain = map_info.get_locations_next_to_terrain(gc,earth)
curr_planet = gc.planet()
curr_map = gc.starting_map(curr_planet)
earth_start_map = gc.starting_map(bc.Planet.Earth)
mars_start_map = gc.starting_map(bc.Planet.Mars)



earth_diagonal = (earth_start_map.height**2 + earth_start_map.width**2)
mars_diagonal = (mars_start_map.height**2 + mars_start_map.width**2)
my_team = gc.team()
enemy_team = sense_util.enemy_team(gc)

num_enemies = 0
info = []
directions = list(bc.Direction)
non_list_directions = bc.Direction
my_units = gc.my_units()
units = gc.units()
my_karbonite = gc.karbonite()
research = gc.research_info()
curr_round = gc.round()

print_count = 0

## MAP ##
if earth_start_map.height > earth_start_map.width: 
    longest = earth_start_map.height
else:
    longest = earth_start_map.width

if longest > 40: 
    quadrant_size = 10
elif longest > 30: 
    quadrant_size = 8
else: 
    quadrant_size = 5
    
quadrant_battle_locs = {}

## ALL UNITS ##
my_unit_ids = set([unit.id for unit in my_units])
unit_locations = {} ## unit id: (x, y)
for unit in my_units:
    unit_locations[unit.id] = (unit.location.map_location().x, unit.location.map_location().y)

death_allies_per_quadrant = {}      ## (quad x, quad y): ((x,y), num_dead)

## WORKER VARIABLES ##

factory_spacing = 5
rocket_spacing = 2
min_workers_per_building = 4
recruitment_radius = 17

blueprinting_queue = []
building_assignment = {}
blueprinting_assignment = {}
all_building_locations = {}
invalid_building_locations = {}


ranger_reachable_sites = []
for x in range(earth_start_map.width):
	for y in range(earth_start_map.height):
		location = bc.MapLocation(earth,x,y)
		if location in impassable_terrain_earth:
			invalid_building_locations[(x,y)] = False
		invalid_building_locations[(x,y)] = True


"""
area = earth_start_map.width * earth_start_map.height

for unit in earth_start_map.initial_units: 
	if unit.team == enemy_team:
		loc = unit.location.map_location()

		if area < 873:
			enemy_loc_restriction = explore.coord_neighbors((loc.x,loc.y), diff=explore.diffs_50, include_self=True)
		else: 
			enemy_loc_restriction = gc.all_locations_within(loc,81)

		for enemy_prox_loc in enemy_loc_restriction:
			coord = (enemy_prox_loc.x,enemy_prox_loc.y)
			if coord not in invalid_building_locations: 
				continue
			if invalid_building_locations[coord]:
				invalid_building_locations[coord] = False
"""

factory_spacing_diff = []
for dx in [-2,-1,0,1,2]:
	for dy in [-2,-1,0,1,2]:
		factory_spacing_diff.append((dx,dy))

building_scouting_diff = []
for dx in [-4,-3,-2,-1,0,1,2,3,4]:
	for dy in [-4,-3,-2,-1,0,1,2,3,4]:
		building_scouting_diff.append((dx,dy))

"""
distance_to_karbonite_deposits = {}
for i,j in karbonite_locations:
	karbonite_location = (i,j)
	for x in range(earth_start_map.width):
		for y in range(earth_start_map.height):
			map_location = (x,y)
			distance_to_karbonite_deposits[(map_location,karbonite_location)] = sense_util.distance_squared_between_coords(map_location,karbonite_location)
"""

current_worker_roles = {"miner":[],"builder":[],"blueprinter":[],"boarder":[], "repairer":[]}

## KNIGHT VARIABLES ##
assigned_knights = {}       ## knight_id: (x, y)
init_enemy_locs = []
for unit in earth_start_map.initial_units:
    if unit.team == enemy_team:
        loc = unit.location.map_location()
        init_enemy_locs.append(loc)

## HEALER VARIABLES ##
healer_radius = 9
healer_target_locs = set()
overcharge_targets = set()  ## stored as IDs
assigned_healers = {}
assigned_overcharge = {}

#ROCKETS
rocket_launch_times = {}
rocket_landing_sites = {}
rocket_locs = {}

# RANGER
ranger_roles = {"fighter":[],"sniper":[], "go_to_mars":[]}
targeting_units = {}    ## enemy_id: num of allied units attacking it
which_rocket = {}       ## rocket_id: unit_id

#FIGHTERS
producing = [0, 0, 0, 0, 0]
last_turn_battle_locs = {}
next_turn_battle_locs = {}

coord_to_direction = {(-1, -1): non_list_directions.Southwest, (-1, 1): non_list_directions.Northwest, (1, -1): non_list_directions.Southeast,
					  (1, 1): non_list_directions.Northeast, (0, 1): non_list_directions.North, (0, -1): non_list_directions.South,
					  (1, 0): non_list_directions.East, (-1, 0): non_list_directions.West}
direction_to_coord = {v: k for k, v in coord_to_direction.items()}

passable_locations_mars = {}
saviour_worker = False
saviour_worker_id = None
saviour_blueprinted = False
saviour_blueprinted_id = None
num_unsuccessful_savior = 0
saviour_time_between = 0
cost_of_rocket = 75



mars = bc.Planet.Mars
mars_map = gc.starting_map(mars)
mars_width = mars_map.width
mars_height = mars_map.height

for x in range(-1, mars_width + 1):
    for y in range(-1, mars_height + 1):
        coords = (x, y)
        if x == -1 or y == -1 or x == mars_map.width or y == mars_map.height:
            passable_locations_mars[coords] = False
        elif mars_map.is_passable_terrain_at(bc.MapLocation(mars, x, y)):
            passable_locations_mars[coords] = True
        else:
            passable_locations_mars[coords] = False

lst_of_passable_mars = [loc for loc in passable_locations_mars if passable_locations_mars[loc]]

num_passable_locations_mars = len(passable_locations_mars)

if curr_planet == bc.Planet.Earth:
    passable_locations_earth = {}

    earth = bc.Planet.Earth
    earth_map = gc.starting_map(earth)
    earth_width = earth_map.width
    earth_height = earth_map.height
    my_width = earth_width
    my_height = earth_height

    for x in range(-1, earth_width+1):
        for y in range(-1, earth_height+1):
            coords = (x, y)
            if x==-1 or y==-1 or x == earth_map.width or y== earth_map.height:
                passable_locations_earth[coords]= False
            elif earth_map.is_passable_terrain_at(bc.MapLocation(earth, x, y)):
                passable_locations_earth[coords] = True
            else:
                passable_locations_earth[coords]= False

    number_of_cells = earth_width * earth_height
    S = dok_matrix((number_of_cells, number_of_cells), dtype=int)
    for x in range(earth_width):
        for y in range(earth_height):
            curr = (x, y)
            if passable_locations_earth[curr]:
                val = y*earth_width + x
                for coord in explore.coord_neighbors(curr):
                    if passable_locations_earth[coord]:
                        val2 = coord[1]*earth_width + coord[0]
                        S[val, val2] = 1
                        S[val2, val] = 1

    bfs_array = csgraph.shortest_path(S, method = 'D', unweighted = True)
    #bfs_dict = {} # stores the distances found by BFS so far
    #precomputed_bfs = explore.precompute_earth(passable_locations_earth, coord_to_direction, wavepoints)
    #start_time = time.time()
    #precomputed_bfs_dist = explore.precompute_earth_dist(passable_locations_earth, coord_to_direction, wavepoints)
    #print(time.time()-start_time)

else:
    my_width = mars_width
    my_height = mars_height
    number_of_cells = mars_width * mars_height
    start_time = time.time()
    S = dok_matrix((number_of_cells, number_of_cells), dtype=int)
    for x in range(mars_width):
        for y in range(mars_height):
            curr = (x, y)
            if passable_locations_mars[curr]:
                val = y * mars_width + x
                for coord in explore.coord_neighbors(curr):
                    if passable_locations_mars[coord]:
                        val2 = coord[1] * mars_width + coord[0]
                        S[val, val2] = 1

    bfs_array = csgraph.shortest_path(S, method='D', unweighted=True)

attacker = set([bc.UnitType.Ranger, bc.UnitType.Knight, bc.UnitType.Mage, bc.UnitType.Healer])
stockpile_until_75 = False
between_stockpiles = 0
stockpile_has_been_above = False
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