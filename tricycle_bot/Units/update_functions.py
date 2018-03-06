import battlecode as bc
import random
import sys
import traceback
import time 
import Units.variables as variables
import Units.quadrants as quadrants

import Units.Healer as healer
import Units.Knight as knight
import Units.Knight_altern as knight_altern
import Units.Mage as mage
import Units.Ranger as ranger
import Units.Worker as worker
import Units.factory as factory
import Units.rocket as rocket
import Units.sense_util as sense_util
import time

def update_variables():
    gc = variables.gc 

    ## **************************************** GENERAL **************************************** ## 

    ## Constants
    variables.curr_round = gc.round()
    variables.num_enemies = 0
    variables.print_count = 0
    variables.research = gc.research_info()

    ## Battle locations
    variables.last_turn_battle_locs = variables.next_turn_battle_locs.copy()
    variables.next_turn_battle_locs = {}

    if variables.curr_round % 2 == 0: 
        variables.update_quadrant_healer_loc = True
    else:
        variables.update_quadrant_healer_loc = False


    # variables.quadrant_battle_locs = {}

    ## Units
    variables.my_units = gc.my_units()
    variables.my_unit_ids = set([unit.id for unit in variables.my_units])
    variables.units = gc.units()
    num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0
    if variables.ranged_enemies >= 5: 
        variables.ranged_enemies = 5
    else: 
        variables.ranged_enemies = 0

    if variables.switch_to_rangers:
        current = gc.research_info()
        if current.get_level(variables.unit_types["knight"]) < 2:
            gc.reset_research()
        if variables.curr_planet == bc.Planet.Earth and len(variables.dists) == 0:
            gc.queue_research(bc.UnitType.Rocket)
        if current.get_level(variables.unit_types["worker"]) != 1:
            gc.queue_research(bc.UnitType.Worker)
        if current.get_level(variables.unit_types["ranger"]) != 1:
            gc.queue_research(bc.UnitType.Ranger)  # 25: 50
        gc.queue_research(bc.UnitType.Healer)  # 25:  75
        if current.get_level(variables.unit_types["rocket"]) != 1:
            gc.queue_research(bc.UnitType.Rocket)  # 50:  125
        gc.queue_research(bc.UnitType.Healer)  # 100: 225
        gc.queue_research(bc.UnitType.Healer)  # 100: 325
        gc.queue_research(bc.UnitType.Ranger)  # 100: 425
        gc.queue_research(bc.UnitType.Ranger)  # 200: 625
        gc.queue_research(bc.UnitType.Worker)  # 75: 700
        variables.switch_to_rangers = False

    # Update which ally unit id's are still alive & deaths per quadrant
    # start_time = time.time()
    update_quadrants() # Updates enemies in quadrant & resets num dead allies
    # print('update quadrants time: ', time.time()-start_time)

    if variables.curr_planet == bc.Planet.Earth: 
        quadrant_size = variables.earth_quadrant_size
    else:
        quadrant_size = variables.mars_quadrant_size

    remove = set()
    for unit_id in variables.unit_locations: 
        if unit_id not in variables.my_unit_ids: 
            remove.add(unit_id)

    for unit_id in remove: 
        loc = variables.unit_locations[unit_id]
        del variables.unit_locations[unit_id]

        f_f_quad = (int(loc[0] / quadrant_size), int(loc[1] / quadrant_size))
        variables.quadrant_battle_locs[f_f_quad].remove_ally(unit_id)

    # Update % health of fighting allies in quadrant
    for quadrant in variables.quadrant_battle_locs: 
        q_info = variables.quadrant_battle_locs[quadrant]
        q_info.update_ally_health_coefficient(gc)

    # Something something enemies
    for poss_enemy in variables.units:
        if poss_enemy.team != variables.my_team and poss_enemy.unit_type in variables.attacker:
            variables.num_enemies += 1

    # Update num of ally units of each type
    unit_types = variables.unit_types
    variables.producing = [0, 0, 0, 0, 0]
    variables.in_order_units = []
    workers = []
    rangers = []
    knights = []
    mages = []
    healers = []
    factories = []
    rockets = []
    for unit in variables.my_units:
        if unit.unit_type == unit_types["worker"]:
            num_workers+=1
            workers.append(unit)
        elif unit.unit_type == unit_types["knight"]:
            num_knights+=1
            rangers.append(unit)
        elif unit.unit_type == unit_types["ranger"]:
            num_rangers+=1
            knights.append(unit)
        elif unit.unit_type == unit_types["mage"]:
            num_mages+=1
            mages.append(unit)
        elif unit.unit_type == unit_types["healer"]:
            num_healers+=1
            healers.append(unit)
        elif unit.unit_type == unit_types["factory"]:
            num_factory+=1
            factories.append(unit)
            if unit.is_factory_producing():
                type = unit.factory_unit_type()
                if type == variables.unit_types["worker"]:
                    variables.producing[0]+=1
                elif type == variables.unit_types["knight"]:
                    variables.producing[1]+=1
                elif type == variables.unit_types["ranger"]:
                    variables.producing[2]+=1
                elif type == variables.unit_types["mage"]:
                    variables.producing[3]+=1
                else:
                    variables.producing[4]+=1
        elif unit.unit_type == unit_types["rocket"]:
            num_rocket+=1
            rockets.append(unit)

    # process factories in order of unit production
    already_producing = []
    not_producing = []
    for fact in factories:
        if fact.is_factory_producing():
            already_producing.append(fact)
        else:
            not_producing.append(fact)
    proxy = None
    battle_locs = variables.last_turn_battle_locs
    if len(battle_locs)>0:
        random_choice = random.choice(list(battle_locs.keys()))
        corr_loc = battle_locs[random_choice][0]
    else:
        corr_loc = random.choice(variables.init_enemy_locs)
    not_producing.sort(key = lambda x: sense_util.distance_squared_between_maplocs(x.location.map_location(), corr_loc))

    variables.info = [num_workers, num_knights, num_rangers, num_mages, num_healers, num_factory, num_rocket]
    variables.in_order_units.extend(rangers)
    variables.in_order_units.extend(workers)
    variables.in_order_units.extend(knights)
    variables.in_order_units.extend(mages)
    variables.in_order_units.extend(healers)
    variables.in_order_units.extend(not_producing)
    variables.in_order_units.extend(already_producing)
    variables.in_order_units.extend(rockets)
    ## **************************************** UNITS **************************************** ## 

    ## Worker 
    variables.my_karbonite = gc.karbonite()
    variables.collective_worker_time = 0

    ## Income
    variables.worker_harvest_amount = 0
    variables.past_karbonite_gain = variables.current_karbonite_gain + max(0,10 - int(variables.my_karbonite/40))
    variables.current_karbonite_gain = 0 # reset counter



    if not worker.check_if_saviour_died():
        variables.saviour_worker_id = None
        variables.saviour_worker = False
        variables.saviour_blueprinted = False
        variables.saviour_blueprinted_id = None
        variables.num_unsuccessful_savior = 0
        variables.saviour_time_between = 0

    #start_time = time.time()
    worker.designate_roles()
    #print("designating roles time: ",time.time() - start_time)

    ## Rangers
    variables.targeting_units = {}
    ranger.update_rangers()

    ## Knights
    if variables.curr_planet == bc.Planet.Mars or len(variables.dists)==0 or min(variables.dists)<5 and gc.round()<175:
        knight.update_battles()
    else:
        knight_altern.update_knights()

    ## Healers
    variables.collective_healer_time = 0
    healer.update_healers()

    ## Rockets
    rocket.update_rockets()

    ## Factories
    factory.evaluate_stockpile()

def update_quadrants(): 
    gc = variables.gc 

    battle_quadrants = variables.quadrant_battle_locs
    battle_locs = variables.last_turn_battle_locs

    # if variables.curr_planet == bc.Planet.Earth: 
    #     quadrant_size = variables.earth_quadrant_size
    # else:
    #     quadrant_size = variables.mars_quadrant_size

    # already_included_quadrants = set()
    # for q_loc in battle_locs: 
    #     map_loc = battle_locs[q_loc][0]
    #     my_quadrant = (int(map_loc.x/quadrant_size), int(map_loc.y/quadrant_size))
    #     already_included_quadrants.add(my_quadrant)

    for quadrant in battle_quadrants: 
        q_info = battle_quadrants[quadrant]
        q_info.reset_num_died()
        q_info.update_in_battle()
    
    if variables.update_quadrant_healer_loc: 
        for quadrant in battle_quadrants: 
            q_info = battle_quadrants[quadrant]
            q_info.update_healer_locs()
            new_battle_locs, ranged = q_info.update_enemies(gc)
            variables.ranged_enemies += ranged

def initiate_quadrants(): 
    ## MAKE QUADRANTS
    if variables.curr_planet == bc.Planet.Earth: 
        width = variables.earth_start_map.width
        height = variables.earth_start_map.height
        quadrant_size = variables.earth_quadrant_size
    else: 
        width = variables.mars_start_map.width
        height = variables.mars_start_map.height
        quadrant_size = variables.mars_quadrant_size

    x_coords = set([x for x in range(0,width,quadrant_size)])
    y_coords = set([x for x in range(0,height,quadrant_size)])

    for x in x_coords: 
        for y in y_coords: 
            variables.quadrant_battle_locs[(int(x/quadrant_size),int(y/quadrant_size))] = quadrants.QuadrantInfo((x,y))

    if variables.curr_planet == bc.Planet.Earth: 
        for unit in variables.earth_start_map.initial_units: 
            loc = unit.location.map_location() 
            quadrant = (int(loc.x/quadrant_size),int(loc.y/quadrant_size))
            if unit.team == variables.enemy_team: 
                variables.quadrant_battle_locs[quadrant].add_enemy(unit, unit.id, (loc.x,loc.y))
            else:
                variables.quadrant_battle_locs[quadrant].add_ally(unit.id, "worker")

