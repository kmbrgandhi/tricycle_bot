import battlecode as bc
import random
import sys
import traceback
import Units.map_info as map_info
import Units.sense_util as sense_util
import Units.explore as explore
import time

gc = bc.GameController()


## CONSTANTS ##

my_team = gc.team()
enemy_team = sense_util.enemy_team(gc)

directions = list(bc.Direction)
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

list_of_unit_ids = set([unit.id for unit in my_units])

## WORKER VARIABLES ##

factory_spacing = 10
rocket_spacing = 2
min_workers_per_building = 4
recruitment_radius = 17

blueprinting_queue = []
building_assignment = {}
blueprinting_assignment = {}
all_building_locations = {}
invalid_building_locations = {}

for x in range(earth_start_map.width):
    for y in range(earth_start_map.height):
        location = bc.MapLocation(earth,x,y)
        if location in impassable_terrain_earth:
            invalid_building_locations[(x,y)] = False
        invalid_building_locations[(x,y)] = True


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
earth_battles = {}
mars_battles = {}
assigned_knights = {}
init_enemy_locs = []

## HEALER VARIABLES ##
healer_radius = 9
healer_target_locs = set()
overcharge_targets = set() ## stored as IDs
assigned_healers = {}
assigned_overcharge = {}

#ROCKETS
rocket_launch_times = {}
rocket_landing_sites = {}
rocket_locs = {}

# RANGER
ranger_roles = {"fighter":[],"sniper":[], "go_to_mars":[]}
ranger_to_cluster = {}
ranger_clusters = set()
targeting_units = {}
which_rocket = {}
ranger_locs = {}

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

mars = bc.Planet.Mars
mars_map = gc.starting_map(mars)
mars_width = mars_map.width
mars_height = mars_map.height

for x in range(mars_width):
    for y in range(mars_height):
        coords = (x, y)
        if mars_map.is_passable_terrain_at(bc.MapLocation(mars, x, y)):
            passable_locations_mars[coords] = True

num_passable_locations_mars = len(passable_locations_mars)

if curr_planet == bc.Planet.Earth:
    passable_locations_earth = {}

    earth = bc.Planet.Earth
    earth_map = gc.starting_map(earth)
    earth_width = earth_map.width
    earth_height = earth_map.height

    for x in range(-1, earth_width+1):
        for y in range(-1, earth_height+1):
            coords = (x, y)
            if x==-1 or y==-1 or x == earth_map.width or y== earth_map.height:
                passable_locations_earth[coords]= False
            elif earth_map.is_passable_terrain_at(bc.MapLocation(earth, x, y)):
                passable_locations_earth[coords] = True
            else:
                passable_locations_earth[coords]= False

    bfs_fineness = max(int(((earth_width * earth_height)**0.5)/10), 2)
    wavepoints = {}
    if earth_width%bfs_fineness==0:
        upper_width = int(earth_width/bfs_fineness)
    else:
        upper_width = int(earth_width/bfs_fineness)+1

    if earth_height%3==0:
        upper_height = int(earth_height/bfs_fineness)
    else:
        upper_height = int(earth_height/bfs_fineness)+1

    start_time = time.time()
    for x_th in range(0, upper_width):
        for y_th in range(0, upper_height):
            lower_limit_x = x_th*bfs_fineness
            lower_limit_y = y_th*bfs_fineness
            possibs = [(lower_limit_x+i, lower_limit_y+j) for i in range(0, bfs_fineness) for j in range(0, bfs_fineness)]
            actual = None
            amount_of_karbonite = 0
            for possib in possibs:
                if possib in passable_locations_earth and passable_locations_earth[possib]:
                    if actual is None:
                        actual = possib
                    elif possib in karbonite_locations and karbonite_locations[possib]>amount_of_karbonite:
                        actual = possib
                        amount_of_karbonite = karbonite_locations[possib]
            if actual is not None:
                wavepoints[(x_th, y_th)] = actual
    precomputed_bfs = explore.precompute_earth(passable_locations_earth, coord_to_direction, wavepoints)

else:
    bfs_fineness = 2 #max(int(((mars_width * mars_height) ** 0.5) / 10), 2) + 1
    wavepoints = {}
    if mars_width % bfs_fineness == 0:
        upper_width = int(mars_width / bfs_fineness)
    else:
        upper_width = int(mars_width / bfs_fineness) + 1

    if mars_height % 3 == 0:
        upper_height = int(mars_height / bfs_fineness)
    else:
        upper_height = int(mars_height / bfs_fineness) + 1

    for x_th in range(0, upper_width):
        for y_th in range(0, upper_height):
            lower_limit_x = x_th * bfs_fineness
            lower_limit_y = y_th * bfs_fineness
            possibs = [(lower_limit_x + i, lower_limit_y + j) for i in range(0, bfs_fineness) for j in
                       range(0, bfs_fineness)]
            actual = None
            for possib in possibs:
                if possib in passable_locations_mars and passable_locations_mars[possib]:
                    actual = possib
                    break
            if actual is not None:
                wavepoints[(x_th, y_th)] = actual

    precomputed_bfs = explore.precompute_mars(passable_locations_mars, coord_to_direction, wavepoints)

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