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
# print('NEXT TO TERRAIN',locs_next_to_terrain)

# constants = variables.Constants(list(bc.Direction), gc.team(), sense_util.enemy_team(gc), start_map, variables.locs_next_to_terrain, variables.karbonite_locations)

##AI EXECUTION##
while True:
    # We only support Python 3, which means brackets around print()
    print('PYROUND:', gc.round())
    variables.last_turn_battle_locs = variables.next_turn_battle_locs.copy()
    variables.next_turn_battle_locs = {}

    variables.num_enemies = 0
    for poss_enemy in gc.units():
        if poss_enemy.team != variables.my_team and poss_enemy.unit_type in variables.attacker:
            variables.num_enemies += 1

    knight.update_battles()
    #print('updated battle locs: ', fighting_locations)
    worker.designate_roles()
    #print("current worker roles: ", variables.current_worker_roles)

    try:
        # walk through our units:
        num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0
        variables.targeting_units = {}
        variables.producing= [0, 0, 0, 0, 0]
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
            # respective unit types execute their own AI
            if unit.unit_type == bc.UnitType.Worker:
                try:
                    worker.timestep(unit)
                except Exception as e:
                    print('Error:', e)
                    # use this to show where the error was
                    traceback.print_exc()
            elif unit.unit_type == bc.UnitType.Knight:
                knight.timestep(unit)
            elif unit.unit_type == bc.UnitType.Ranger:
                ranger.timestep(unit)
            elif unit.unit_type == bc.UnitType.Mage:
                mage.timestep(unit)
            elif unit.unit_type == bc.UnitType.Healer:
                healer.timestep(unit)
            elif unit.unit_type == bc.UnitType.Factory:
                factory.timestep(unit)
            elif unit.unit_type == bc.UnitType.Rocket:
                # print('hi')
                rocket.timestep(unit)


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

				
				




