import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):
    garrison = unit.structure_garrison()
    directions = list(bc.Direction)
    if len(garrison) > 0:
        d = random.choice(directions)
        if gc.can_unload(unit.id, d):
            print('unloaded a knight!')
            gc.unload(unit.id, d)
    elif gc.can_produce_robot(unit.id, bc.UnitType.Knight):
        gc.produce_robot(unit.id, bc.UnitType.Knight)
        print('produced a knight!')