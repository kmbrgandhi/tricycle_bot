import gc as gcollector
import battlecode as bc
import random
import sys
import time
import traceback

import research
import Units.Healer as healer
import Units.Knight as knight
import Units.Knight_altern as knight_altern
import Units.Mage as mage
import Units.Ranger as ranger
import Units.Worker as worker
import Units.factory as factory
import Units.rocket as rocket
import Units.variables as variables
import Units.update_functions as update
import Units.explore as explore

#print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.

gc = variables.gc


print("Thank you devs for all your hard work")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
research.research_step(gc)

## MAKE QUADRANTS
update.initiate_quadrants()

# GENERAL
# print('NEXT TO TERRAIN',locs_next_to_terrain)

# constants = variables.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, variables.locs_next_to_terrain, variables.karbonite_locations)
##AI EXECUTION##
#print(variables.earth_quadrant_size)

while True:
    beginning_start_time = time.time()
    # time_left = gc.get_time_left_ms()
    #print("PYROUND:",gc.round())
    # print("TIME LEFT:", gc.get_time_left_ms())
    start_time = time.time()
    update.update_variables()
    #print("UPDATE_TIME",time.time()-start_time)
    time_rangers = 0
    time_workers = 0
    time_healers = 0
    time_factories = 0
    unit_types = variables.unit_types
    info = variables.info

    #print('TIME LEFT', gc.get_time_left_ms())
    ##print("past karbonite gain",variables.past_karbonite_gain)

    try:
        for unit in variables.in_order_units:
            if gc.get_time_left_ms()<250:
                break
            # respective unit types execute their own AI
            if unit.unit_type == unit_types["worker"]:
                try:
                    start_time = time.time()
                    
                    worker.timestep(unit)
                    variables.collective_worker_time += (time.time()-start_time) #DO NOT COMMENT OUT

                    time_workers += (time.time()-start_time)

                except Exception as e:
                    print('Error:', e)
                    # use this to show where the error was
                    traceback.print_exc()
            elif unit.unit_type == unit_types["knight"]:
                #start_time = time.time()
                if variables.curr_planet == bc.Planet.Mars or min(variables.dists)<5 and gc.round()<175:
                    knight.timestep(unit)
                else:
                    knight_altern.timestep(unit)
                #time_knights+=(time.time()-start_time)
            elif unit.unit_type == unit_types["ranger"]:
                try:
                    start_time = time.time()
                    ranger.timestep(unit)
                    time_rangers += (time.time()-start_time)
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
                start_time = time.time()
                healer.timestep(unit)
                variables.collective_healer_time += (time.time() - start_time)
                time_healers+=(time.time()-start_time)
            elif unit.unit_type == unit_types["factory"]:
                start_time = time.time()
                factory.timestep(unit)
                time_factories+=time.time()-start_time
            elif unit.unit_type == unit_types["rocket"]:
                #start_time = time.time()
                rocket.timestep(unit)
                #time_knights+=(time.time()-start_time)

        # if gc.planet() == bc.Planet.Mars:
        #     print('ranger roles: ', variables.ranger_roles)
        # if gc.planet() == bc.Planet.Earth: 
        #     print("QUADRANTS: ", variables.quadrant_battle_locs)
        #     locs_correct = True
        #     for unit in gc.my_units(): 
        #         if unit.id in variables.unit_locations: 
        #             loc_coords = (unit.location.map_location().x, unit.location.map_location().y)
        #             recorded = variables.unit_locations[unit.id]
        #             if loc_coords != recorded: 
        #                 locs_correct = False
        #                 print('unit: ', unit)
        #                 print('coords recorded: ', recorded)
        #     print('are locs correct for all units: ', locs_correct)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.

    #print('TIME SPENT ON WORKERS:', time_workers)

    #if time_rangers > 0.02:
    #print('TIME SPENT ON RANGERS:', time_rangers)

    #print('TIME SPENT ON HEALERS:', time_healers)
    #print('TIME SPENT ON FACTORIES:', time_factories)
    #print('TOTAL TIME:', time.time()-beginning_start_time)
    if gc.round()%5==0:
        gcollector.collect()
    gc.next_turn()
    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()

				
				




