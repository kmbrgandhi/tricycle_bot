import battlecode as bc
import random
import sys
import traceback
import numpy as np

def timestep(gc, unit,composition):
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
        for d in directions:
            if gc.can_unload(unit.id, d):
                gc.unload(unit.id, d)

    elif gc.can_produce_robot(unit.id, bc.UnitType.Worker): # otherwise produce a unit, based on most_off_optimal
        most_off_optimal = np.argmax(calculate)
        gc.produce_robot(unit.id, order[most_off_optimal])
        if order[most_off_optimal]==bc.UnitType.Healer:
            print('produced a healer!')