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
curr_planet = gc.planet()
curr_map = gc.starting_map(curr_planet)
earth_start_map = gc.starting_map(earth)
mars_start_map = gc.starting_map(mars)

impassable_terrain_earth = map_info.get_impassable_terrain(gc,earth)
impassable_terrain_mars = map_info.get_impassable_terrain(gc,mars)
locs_next_to_terrain = map_info.get_locations_next_to_terrain(gc,earth)

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
	earth_quadrant_size = 10
elif longest > 30: 
	earth_quadrant_size = 8
else: 
	earth_quadrant_size = 5

if mars_start_map.height > mars_start_map.width: 
	longest = mars_start_map.height
else:
	longest = mars_start_map.width

if longest > 40: 
	mars_quadrant_size = 10
elif longest > 30: 
	mars_quadrant_size = 8
else: 
	mars_quadrant_size = 5
	
quadrant_battle_locs = {}

## ALL UNITS ##
my_unit_ids = set([unit.id for unit in my_units])
unit_locations = {} ## unit id: (x, y)
for unit in my_units:
	unit_location = unit.location.map_location()
	unit_locations[unit.id] = (unit_location.x, unit_location.y)

death_allies_per_quadrant = {}      ## (quad x, quad y): ((x,y), num_dead)
update_quadrant_healer_loc = True

## WORKER VARIABLES ##

factory_spacing = 5
rocket_spacing = 2
min_workers_per_building = 4
repairers_per_building = 4
recruitment_radius = 30

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

current_worker_roles = {"miner":[],"builder":[],"blueprinter":[],"boarder":[], "repairer":[]}

reserved_income = 5
factory_cost_per_round = 40 / 15 + 2 # 40 karbonite per 15 turns to make all offensive units + offset for factory cost
worker_harvest_amount = 0
current_karbonite_gain = 0
past_karbonite_gain = 0

## KNIGHT VARIABLES ##
assigned_knights = {}       ## knight_id: (x, y)
our_init_locs = []
init_enemy_locs = []
for unit in earth_start_map.initial_units:
    loc = unit.location.map_location()
    if unit.team == enemy_team:
        init_enemy_locs.append(loc)
    else:
        our_init_locs.append(loc)
knight_attacks = {}
died_without_attacking = 0

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

# Mages
mage_roles = {"fighter":[], "go_to_mars":[]}

# Rangers and mages
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
cost_of_rocket = 150

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
knight_rush = False
switch_to_rangers = False

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
    start_time = time.time()
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
    print(time.time()-start_time)
    #bfs_dict = {} # stores the distances found by BFS so far
    #precomputed_bfs = explore.precompute_earth(passable_locations_earth, coord_to_direction, wavepoints)
    #start_time = time.time()
    #precomputed_bfs_dist = explore.precompute_earth_dist(passable_locations_earth, coord_to_direction, wavepoints)
    #print(time.time()-start_time)
    dist_to_enemies = []
    dists = []
    for our_init_loc in our_init_locs:
        for their_init_loc in init_enemy_locs:
            our_coords = (our_init_loc.x, our_init_loc.y)
            their_coords = (their_init_loc.x, their_init_loc.y)
            our_coords_val = our_coords[1]*my_width + our_coords[0]
            their_coords_val = their_coords[1] * my_width + their_coords[0]
            dist = bfs_array[our_coords_val, their_coords_val]
            if dist!=float('inf'):
                dists.append(dist)

    if min(dists) < 17 and max(dists) < 30:
        knight_rush = True

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
    print(time.time()-start_time)

attacker = set([bc.UnitType.Ranger, bc.UnitType.Knight, bc.UnitType.Mage, bc.UnitType.Healer])
stockpile_until_75 = False
between_stockpiles = 0
stockpile_has_been_above = False

## Karbonite locations update

karbonite_locations = {}
initial_coords = []

for initial_unit in earth_start_map.initial_units:
	if initial_unit.team == my_team:
		initial_unit_location = initial_unit.location.map_location()
		initial_coords.append((initial_unit_location.x,initial_unit_location.y))

for x in range(earth_start_map.width):
	for y in range(earth_start_map.height):
		map_location = bc.MapLocation(earth,x,y)
		karbonite_at = earth_start_map.initial_karbonite_at(map_location)
		karbonite_coord = (x,y)

		if karbonite_at > 0:
			target_coords_val = karbonite_coord[1]*my_width + karbonite_coord[0]
			for initial_coord in initial_coords:
				our_coords_val = initial_coord[1]*my_width + initial_coord[0]
				if bfs_array[our_coords_val, target_coords_val] != float('inf'):
					karbonite_locations[(x,y)] = karbonite_at

worker_starting_cap = max(5,min(12,len(karbonite_locations)/20))