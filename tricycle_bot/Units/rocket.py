import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit,composition):
    
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Rocket:
		# prob should return some kind of error
		return

