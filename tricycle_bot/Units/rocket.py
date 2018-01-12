import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit,composition):
    
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Rocket:
		# prob should return some kind of error
		return


def rocket_durations_sorted(gc):
	# gets orbit pattern, sorts round numbers by duration time, returns the resultant array.
	orbit_pattern = gc.orbit_pattern()
	rounds = [i for i in range(1, 1001)]
	durations = [(i, orbit_pattern.duration(i)) for i in range(1, 1001)]
	sorted_rounds_by_duration = sorted(rounds, key = lambda x: orbit_pattern.duration(x))
	return sorted_rounds_by_duration