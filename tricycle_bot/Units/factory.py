import battlecode as bc
import random
import sys
import traceback
import numpy as np

def timestep(gc, unit,composition, mining_rate = 0, current_production = 0, karbonite_lower_limit = 100):
    curr_round = gc.round()
    optimal_composition = [0.55 - curr_round * (0.4/1000), 0.2+curr_round*(0.2/1000), 0.2 + curr_round*(0.2/1000), 0, 0.05+curr_round*(0.05/1000)] # optimal composition, order is Worker, Knight, Ranger, Mage, Healer
    # should alter based on curr_round.  this is a temporary idea.

    calculate = [(optimal_composition[i]-composition[i])/(optimal_composition[i]+0.001) for i in range(len(optimal_composition))] #offset from optimal
    order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage, bc.UnitType.Healer] # storing order of units
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Factory:
        # prob should return some kind of error
        return

    garrison = unit.structure_garrison() # units inside of factory
    directions = list(bc.Direction)
    if len(garrison) > 0: # try to unload a unit if there exists one in the garrison
        optimal_unload_dir = optimal_unload(gc, unit, directions)
        if optimal_unload_dir is not None:
            gc.unload(unit.id, optimal_unload_dir)


    elif gc.can_produce_robot(unit.id, bc.UnitType.Worker): #and should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit): # otherwise produce a unit, based on most_off_optimal
        most_off_optimal = np.argmax(calculate)
        gc.produce_robot(unit.id, order[most_off_optimal])
        current_production += order[most_off_optimal].factory_cost()

    return current_production

def should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit):
    # produce a robot if net karbonite at the end of the turn will be more than karbonite_lower_limit
    net_karbonite = gc.karbonite() + mining_rate - current_production + gain_rate(gc)
    if gc.karbonite() > karbonite_lower_limit and net_karbonite > karbonite_lower_limit:
        return True
    val = random.random()
    if val > 0.5 * float((100 - net_karbonite))/100:
        return True
    return False

def gain_rate(gc):
    curr = gc.karbonite()
    decrease = int(curr/40)
    return max(10 -decrease, 0)

def optimal_unload(gc, unit, directions):
    best = None
    best_val = -float('inf')
    for d in directions:
        if gc.can_unload(unit.id, d):
            locs = gc.all_locations_within(unit.location.map_location(), 9)
            locs_good = []
            for loc in locs:
                if gc.can_sense_location(loc):
                    try:
                        result = gc.sense_unit_at_location(loc)
                    except:
                        locs_good.append(loc)
            num_good = len(locs_good)
            if num_good > best_val:
                best_val = num_good
                best = d
    return best



