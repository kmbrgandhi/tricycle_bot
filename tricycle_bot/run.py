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
import Units.constants as c
import research
import map_info
import time
import cProfile


print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
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
karbonite_locations = map_info.get_initial_karbonite_locations(gc)
locs_next_to_terrain = map_info.get_locations_next_to_terrain(gc,bc.Planet(0))
start_map = gc.starting_map(bc.Planet(0))
# print('NEXT TO TERRAIN',locs_next_to_terrain)

constants = c.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, locs_next_to_terrain, karbonite_locations)

#ROCKETS
rocket_launch_times = {}
rocket_landing_sites = {}

# WORKER
blueprinting_queue = []
building_assignment = {}
blueprinting_assignment = {}

current_worker_roles = {"miner":[],"builder":[],"blueprinter":[],"boarder":[], "repairer":[]}

# KNIGHT
knight_clusters = list()
seen_knights_ids = set()
knight_to_cluster = {} ## Remove knights not in cluster 
KNIGHT_CLUSTER_MIN = 2

# RANGER
ranger_roles = {"fighter":[],"sniper":[]}
ranger_to_cluster = {}
ranger_clusters = set()

#FIGHTERS
last_turn_battle_locs = {}
next_turn_battle_locs = {}
passable_locations_earth = {}
earth = bc.Planet.Earth
earth_map = gc.starting_map(earth)


for x in range(-1, earth_map.width+1):
    for y in range(-1, earth_map.height + 1):
        coords = (x, y)
        if x==-1 or y==-1 or x == earth_map.width or y== earth_map.height:
            passable_locations_earth[coords]= False
        elif earth_map.is_passable_terrain_at(bc.MapLocation(earth, x, y)):
            passable_locations_earth[coords] = True
        else:
            passable_locations_earth[coords]= False

coord_to_direction = {(-1, -1): directions.Southwest, (-1, 1): directions.Northwest, (1, -1): directions.Southeast,
                    (1, 1): directions.Northeast, (0, 1): directions.North, (0, -1): directions.South,
                    (1, 0): directions.East, (-1, 0): directions.West}
direction_to_coord = {v: k for k, v in coord_to_direction.items()}

earth_width = earth_map.width
earth_height = earth_map.height
print(earth_width)
print(earth_height)
start_time = time.time()
precomputed_bfs = explore.precompute_earth(passable_locations_earth, earth_width, earth_height, coord_to_direction)
print(time.time()-start_time)
attacker = set([bc.UnitType.Ranger, bc.UnitType.Knight, bc.UnitType.Mage])
##AI EXECUTION##
while True:
    # We only support Python 3, which means brackets around print()
    print('PYROUND:', gc.round())
    last_turn_battle_locs = next_turn_battle_locs.copy()
    next_turn_battle_locs = {}

    num_enemies = 0
    for poss_enemy in gc.units():
        if poss_enemy.team != gc.team() and poss_enemy.unit_type in attacker:
            num_enemies += 1
    #Update knight cluster min
    """
    try: 
        my_knights = list(filter(lambda x: x.unit_type == bc.UnitType.Knight, gc.my_units()))
        if len(my_knights) > 25: 
            KNIGHT_CLUSTER_MIN =8
        elif len(my_knights) > 15:
            KNIGHT_CLUSTER_MIN = 5
        else: 
            KNIGHT_CLUSTER_MIN = 2
    except: 
        pass
    """
    worker.designate_roles(gc,blueprinting_queue,blueprinting_assignment,building_assignment,current_worker_roles,karbonite_locations)
    print("current worker roles: ",current_worker_roles)
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
        info = [num_workers, num_knights, num_rangers, num_mages, num_healers, num_factory, num_rocket]

        for unit in gc.my_units():
            # resepective unit types execute their own AI
            if unit.unit_type == bc.UnitType.Worker:
                try:
                    worker.timestep(gc,unit,info,karbonite_locations,blueprinting_queue,blueprinting_assignment,building_assignment,current_worker_roles, num_enemies)
                except Exception as e:
                    print('Error:', e)
                    # use this to show where the error was
                    traceback.print_exc()
            elif unit.unit_type == bc.UnitType.Knight:
                knight.timestep(gc,unit,info,knight_to_cluster,seen_knights_ids, KNIGHT_CLUSTER_MIN, constants)
            elif unit.unit_type == bc.UnitType.Ranger:
                ranger.timestep(gc,unit,info,last_turn_battle_locs, next_turn_battle_locs, queued_paths, ranger_roles, constants, direction_to_coord, precomputed_bfs, targeting_units)
            elif unit.unit_type == bc.UnitType.Mage:
                mage.timestep(gc,unit,info,last_turn_battle_locs,next_turn_battle_locs, queued_paths)
            elif unit.unit_type == bc.UnitType.Healer:
                healer.timestep(gc,unit,info,last_turn_battle_locs,constants)
            elif unit.unit_type == bc.UnitType.Factory:
                factory.timestep(gc,unit,info, building_assignment, last_turn_battle_locs, constants, mining_rate = 3*len(current_worker_roles["miner"]))
            elif unit.unit_type == bc.UnitType.Rocket:
                print('hi')
                rocket.timestep(gc,unit,info, rocket_launch_times, rocket_landing_sites)

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

				
				




