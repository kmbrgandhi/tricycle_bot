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
# print('NEXT TO TERRAIN',locs_next_to_terrain)

# constants = variables.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, variables.locs_next_to_terrain, variables.karbonite_locations)

##AI EXECUTION##
while True:
    #beginning_start_time = time.time()
    time_left = gc.get_time_left_ms()
    # We only support Python 3, which means brackets around print()
    variables.last_turn_battle_locs = variables.next_turn_battle_locs.copy()
    variables.next_turn_battle_locs = {}
    variables.curr_round = gc.round()
    variables.num_enemies = 0
    variables.print_count = 0

    print("PYROUND:", variables.curr_round)
    print("TIME LEFT:", gc.get_time_left_ms())
    for poss_enemy in variables.units:
        if poss_enemy.team != variables.my_team and poss_enemy.unit_type in variables.attacker:
            variables.num_enemies += 1
    start_time = time.time()
    knight.update_battles()
    #if time.time()-start_time > 0.02:
    #    print('KNIGHT UPDATE BATTLES:', time.time()-start_time)

    start_time = time.time()
    healer.update_healers()
    #if time.time() - start_time > 0.02:
    #    print('HEALER UPDATE TIME:', time.time()-start_time)

    start_time = time.time()
    ranger.update_rangers()
    #if time.time() - start_time > 0.02:
    #    print('RANGER UPDATE TIME: ', time.time()-start_time)

    start_time = time.time()
    worker.designate_roles()
    #if time.time() - start_time > 0.02:
    #    print('DESIGNATING ROLES TIME:', time.time()-start_time)

    #time_workers = 0
    #time_rangers = 0
    #time_healers = 0
    # time_factories = 0
    # time_knights = 0
    
    #print("current worker roles: ", variables.current_worker_roles)

    try:
        # walk through our units:
        #start_time = time.time()
        variables.my_units = gc.my_units()
        variables.units = gc.units()
        variables.my_karbonite = gc.karbonite()
        variables.list_of_unit_ids = [unit.id for unit in variables.my_units]
        variables.research = gc.research_info()
        num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0
        variables.targeting_units = {}
        variables.producing= [0, 0, 0, 0, 0]
        unit_types = variables.unit_types
        #print('PROCESSING TIME:', time.time()-start_time)

        for unit in variables.my_units:
            if unit.unit_type == unit_types["worker"]:
                num_workers+=1
            elif unit.unit_type == unit_types["knight"]:
                num_knights+=1
            elif unit.unit_type == unit_types["ranger"]:
                num_rangers+=1
            elif unit.unit_type == unit_types["mage"]:
                num_mages+=1
            elif unit.unit_type == unit_types["healer"]:
                num_healers+=1
            elif unit.unit_type == unit_types["factory"]:
                num_factory+=1
            elif unit.unit_type == unit_types["rocket"]:
                num_rocket+=1
        variables.info = [num_workers, num_knights, num_rangers, num_mages, num_healers, num_factory, num_rocket]
        info = variables.info
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



        ## Reset knight turn clusters
        seen_knights_ids = set()

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

				
				




