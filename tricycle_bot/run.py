import battlecode as bc
import random
import sys
import traceback
import Units.Healer as healer
import Units.Knight as knight
import Units.Mage as mage
import Units.Ranger as ranger
import Units.Worker as worker
import Units.factory as factory
import Units.rocket as rocket
import Units.sense_util as sense_util
import Units.explore as explore
import Units.variables as variables
import research
import time
import cProfile


print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.

gc = variables.gc
directions = bc.Direction


print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
research.research_step(gc)


##SHARED TEAM INFORMATION##

# GENERAL
queued_paths = {}
start_map = gc.starting_map(bc.Planet.Earth)
# print('NEXT TO TERRAIN',locs_next_to_terrain)

constants = variables.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, variables.locs_next_to_terrain, variables.karbonite_locations)

#ROCKETS
rocket_launch_times = {}
rocket_landing_sites = {}
rocket_locs = {}

# KNIGHT
fighting_locations = {}
assigned_knights = {}
for loc in constants.init_enemy_locs: 
    fighting_locations[(loc.x, loc.y)] = set()
seen_knights_ids = set()
knight_to_cluster = {} ## Remove knights not in cluster 
KNIGHT_CLUSTER_MIN = 2

# RANGER
ranger_roles = {"fighter":[],"sniper":[], "go_to_mars":[]}
ranger_to_cluster = {}
ranger_clusters = set()

#FIGHTERS
last_turn_battle_locs = {}
next_turn_battle_locs = {}

coord_to_direction = {(-1, -1): directions.Southwest, (-1, 1): directions.Northwest, (1, -1): directions.Southeast,
                      (1, 1): directions.Northeast, (0, 1): directions.North, (0, -1): directions.South,
                      (1, 0): directions.East, (-1, 0): directions.West}
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

if gc.planet() == bc.Planet.Earth:
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


    print('BFS fineness:', bfs_fineness)
    print(earth_width)
    print(earth_height)
    start_time = time.time()
    precomputed_bfs = explore.precompute_earth(passable_locations_earth, coord_to_direction, wavepoints)
    print(time.time()-start_time)
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

    print('BFS fineness:', bfs_fineness)
    start_time = time.time()
    precomputed_bfs = explore.precompute_mars(passable_locations_mars, coord_to_direction, wavepoints)
    print(time.time() - start_time)

attacker = set([bc.UnitType.Ranger, bc.UnitType.Knight, bc.UnitType.Mage])
##AI EXECUTION##
while True:
    # We only support Python 3, which means brackets around print()
    print('PYROUND:', gc.round())
    last_turn_battle_locs = next_turn_battle_locs.copy()
    next_turn_battle_locs = {}

    variables.num_enemies = 0
    for poss_enemy in gc.units():
        if poss_enemy.team != gc.team() and poss_enemy.unit_type in attacker:
            variables.num_enemies += 1

    knight.update_battles(gc, fighting_locations, assigned_knights, constants)
    print('updated battle locs: ', fighting_locations)

    worker.designate_roles(gc)
    print("current worker roles: ", variables.current_worker_roles)

    try:
        # walk through our units:
        num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0
        targeting_units = {}
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Worker:
                num_workers+=1
            elif unit.unit_type == bc.UnitType.Knight:
                num_knights+=1
            elif unit.unit_type == bc.UnitType.Ranger:
                num_rangers+=1
            elif unit.unit_type == bc.UnitType.Mage:
                num_mages+=1
            elif unit.unit_type == bc.UnitType.Healer:
                num_healers+=1
            elif unit.unit_type == bc.UnitType.Factory:
                num_factory+=1
            elif unit.unit_type == bc.UnitType.Rocket:
                num_rocket+=1
        variables.info = [num_workers, num_knights, num_rangers, num_mages, num_healers, num_factory, num_rocket]
        info = variables.info
        for unit in gc.my_units():
            # resepective unit types execute their own AI
            if unit.unit_type == bc.UnitType.Worker:
                try:
                    worker.timestep(gc,unit)
                except Exception as e:
                    print('Error:', e)
                    # use this to show where the error was
                    traceback.print_exc()
            elif unit.unit_type == bc.UnitType.Knight:
                knight.timestep(gc,unit,info,fighting_locations,assigned_knights,constants)
            elif unit.unit_type == bc.UnitType.Ranger:
                ranger.timestep(gc,unit,info,last_turn_battle_locs, next_turn_battle_locs, queued_paths, ranger_roles, constants, direction_to_coord, precomputed_bfs, targeting_units, bfs_fineness)
            elif unit.unit_type == bc.UnitType.Mage:
                mage.timestep(gc,unit,info,last_turn_battle_locs,next_turn_battle_locs, queued_paths)
            elif unit.unit_type == bc.UnitType.Healer:
                healer.timestep(gc,unit,info,fighting_locations,constants)
            elif unit.unit_type == bc.UnitType.Factory:
                factory.timestep(gc,unit,info, building_assignment, last_turn_battle_locs, constants, mining_rate = 3*len(current_worker_roles["miner"]))
            elif unit.unit_type == bc.UnitType.Rocket:
                # print('hi')
                rocket.timestep(gc,unit,info, rocket_launch_times, rocket_landing_sites, passable_locations_mars)

        ## Reset knight turn clusters
        seen_knights_ids = set()

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()

				
				




