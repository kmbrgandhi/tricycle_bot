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
import Units.update_functions as update
import Units.quadrants as quadrants
import research
import time
import cProfile


print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.

gc = variables.gc


print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
research.research_step(gc)

## MAKE QUADRANTS
x_coords = set([x for x in range(0,variables.earth_start_map.width,variables.quadrant_size)])
y_coords = set([x for x in range(0,variables.earth_start_map.height,variables.quadrant_size)])

for x in x_coords: 
    for y in y_coords: 
        variables.quadrant_battle_locs[(int(x/variables.quadrant_size),int(y/variables.quadrant_size))] = quadrants.QuadrantInfo((x,y))

for unit in variables.earth_start_map.initial_units: 
    loc = unit.location.map_location() 
    quadrant = (int(loc.x/variables.quadrant_size),int(loc.y/variables.quadrant_size))
    if unit.team == variables.enemy_team: 
        variables.quadrant_battle_locs[quadrant].add_enemy(unit, unit.id, (loc.x,loc.y))
    else:
        variables.quadrant_battle_locs[quadrant].add_ally(unit.id, "worker")

# GENERAL
# print('NEXT TO TERRAIN',locs_next_to_terrain)

# constants = variables.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, variables.locs_next_to_terrain, variables.karbonite_locations)

##AI EXECUTION##
while True:
    #beginning_start_time = time.time()
    time_left = gc.get_time_left_ms()

    update.update_variables()

    unit_types = variables.unit_types
    info = variables.info

    print("PYROUND:",gc.round())

    try:
        for unit in variables.my_units:
            # respective unit types execute their own AI
            if unit.unit_type == unit_types["worker"]:
                try:
                    # start_time = time.time()
                    worker.timestep(unit)
                    # time_workers += (time.time()-start_time)

                except Exception as e:
                    print('Error:', e)
                    # use this to show where the error was
                    traceback.print_exc()
            elif unit.unit_type == unit_types["knight"]:
                #start_time = time.time()
                knight.timestep(unit)
                #time_knights+=(time.time()-start_time)
            elif unit.unit_type == unit_types["ranger"]:
                try:
                    #start_time = time.time()
                    ranger.timestep(unit)
                    #time_rangers += (time.time()-start_time)
                    #print(time.time()-start_time)
                except Exception as e:
                    #print('RANGER ERROR.')
                    if ranger in variables.ranger_roles["go_to_mars"]:
                        variables.ranger_roles["go_to_mars"].remove(ranger)
                    elif ranger in variables.ranger_roles["fighter"]:
                        variables.ranger_roles["fighter"].remove(ranger)
                    elif ranger in variables.ranger_roles["sniper"]:
                        variables.ranger_roles["sniper"].remove(ranger)

                    traceback.print_exc()
            elif unit.unit_type == unit_types["mage"]:
                mage.timestep(unit)
            elif unit.unit_type == unit_types["healer"]:
                #start_time = time.time()
                healer.timestep(unit)
                #time_healers+=(time.time()-start_time)
            elif unit.unit_type == unit_types["factory"]:
                #start_time = time.time()
                factory.timestep(unit)
                #time_factories+=(time.time()-start_time)
            elif unit.unit_type == unit_types["rocket"]:
                #start_time = time.time()
                rocket.timestep(unit)
                #time_knights+=(time.time()-start_time)

        if gc.planet() == bc.Planet.Earth: 
            #print("QUADRANTS: ", variables.quadrant_battle_locs)
            locs_correct = True
            for unit in gc.my_units(): 
                if unit.id in variables.unit_locations: 
                    loc_coords = (unit.location.map_location().x, unit.location.map_location().y)
                    recorded = variables.unit_locations[unit.id]
                    if loc_coords != recorded: 
                        locs_correct = False
                        print('unit: ', unit)
                        print('coords recorded: ', recorded)
            print('are locs correct for all units: ', locs_correct)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    #if time_workers > 0.03:
    #    print('TIME SPENT ON WORKERS:', time_workers)
    #if time_rangers>0.03:
    #    print('TIME SPENT ON RANGERS:', time_rangers)
    #if time_healers > 0.03:
    #    print('TIME SPENT ON HEALERS:', time_healers)
    #print('TIME SPENT ON ROCKETS:', time_knights)
    #print('TOTAL TIME:', time.time()-beginning_start_time)
    gc.next_turn()
    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()

				
				




