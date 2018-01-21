import battlecode as bc
import random
import sys
import traceback
import Units.map_info as map_info
import Units.sense_util as sense_util
import Units.explore as explore


gc = bc.GameController()


## CONSTANTS ##
directions = list(bc.Direction)


## GENERAL VARIABLES ##

# map info
karbonite_locations = map_info.get_initial_karbonite_locations(gc)
locs_next_to_terrain = map_info.get_locations_next_to_terrain(gc,bc.Planet(0))
curr_planet = gc.planet()
curr_map = gc.starting_map(curr_planet)
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
non_list_directions = bc.Direction

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

#ROCKETS
rocket_launch_times = {}
rocket_landing_sites = {}
rocket_locs = {}

# RANGER
ranger_roles = {"fighter":[],"sniper":[], "go_to_mars":[]}
ranger_to_cluster = {}
ranger_clusters = set()
targeting_units = {}

#FIGHTERS
last_turn_battle_locs = {}
next_turn_battle_locs = {}

coord_to_direction = {(-1, -1): non_list_directions.Southwest, (-1, 1): non_list_directions.Northwest, (1, -1): non_list_directions.Southeast,
                      (1, 1): non_list_directions.Northeast, (0, 1): non_list_directions.North, (0, -1): non_list_directions.South,
                      (1, 0): non_list_directions.East, (-1, 0): non_list_directions.West}
direction_to_coord = {v: k for k, v in coord_to_direction.items()}

passable_locations_mars = {}

mars = bc.Planet.Mars
mars_map = gc.starting_map(mars)
mars_width = mars_map.width
mars_height = mars_map.height

for x in range(mars_width):
    for y in range(mars_height):
        coords = (x, y)
        if mars_map.is_passable_terrain_at(bc.MapLocation(mars, x, y)):
            passable_locations_mars[coords] = True

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


    for x_th in range(0, upper_width):
        for y_th in range(0, upper_height):
            lower_limit_x = x_th*bfs_fineness
            lower_limit_y = y_th*bfs_fineness
            possibs = [(lower_limit_x+i, lower_limit_y+j) for i in range(0, bfs_fineness) for j in range(0, bfs_fineness)]
            actual = None
            for possib in possibs:
                if possib in passable_locations_earth and passable_locations_earth[possib]:
                    actual = possib
                    break
            if actual is not None:
                wavepoints[(x_th, y_th)] = actual

    precomputed_bfs = explore.precompute_earth(passable_locations_earth, coord_to_direction, wavepoints)
else:
    bfs_fineness = max(int(((mars_width * mars_height) ** 0.5) / 10), 2) + 1
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

attacker = set([bc.UnitType.Ranger, bc.UnitType.Knight, bc.UnitType.Mage])

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