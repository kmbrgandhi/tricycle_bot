import battlecode as bc
import random
import sys
import traceback

import Units.variables as variables
import Units.quadrants as quadrants
import research as research

import Units.Healer as healer
import Units.Knight as knight
import Units.Mage as mage
import Units.Ranger as ranger
import Units.Worker as worker
import Units.factory as factory
import Units.rocket as rocket

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
    # variables.quadrant_battle_locs = {}

    ## Units 
    variables.my_units = gc.my_units()
    variables.my_unit_ids = set([unit.id for unit in variables.my_units])
    variables.units = gc.units()
    num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0

    # Update which ally unit id's are still alive & deaths per quadrant
    update_quadrants() # Updates enemies in quadrant & resets num dead allies

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

    ## **************************************** UNITS **************************************** ## 

    ## Worker 
    variables.my_karbonite = gc.karbonite()
    variables.producing= [0, 0, 0, 0, 0]

    if variables.switch_to_rangers:
        research.research_step(gc)
        variables.switch_to_rangers = False

    if not worker.check_if_saviour_died():
        variables.saviour_worker_id = None
        variables.saviour_worker = False
        variables.saviour_blueprinted = False
        variables.saviour_blueprinted_id = None
        variables.num_unsuccessful_savior = 0
        variables.saviour_time_between = 0

    worker.designate_roles()

    ## Rangers
    variables.targeting_units = {}
    ranger.update_rangers()

    ## Knights
    knight.update_battles()

    ## Healers
    healer.update_healers()

    # Rockets
    rocket.update_rockets()

    ## Mages


    ## Factories
    factory.evaluate_stockpile()

def update_quadrants(): 
    gc = variables.gc 

    battle_quadrants = variables.quadrant_battle_locs

    for quadrant in battle_quadrants: 
        q_info = battle_quadrants[quadrant]
        q_info.reset_num_died()
        q_info.update_enemies(gc)

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

