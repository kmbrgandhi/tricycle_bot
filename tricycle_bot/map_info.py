import battlecode as bc
import random
import sys
import traceback

def get_initial_karbonite_locations(gc):
	deposit_locations = {}
	start_map = gc.starting_map(bc.Planet(0))
	for x in range(start_map.width):
		for y in range(start_map.height):
			map_location = bc.MapLocation(bc.Planet(0),x,y)
			karbonite_at = start_map.initial_karbonite_at(map_location)
			if karbonite_at > 0:
				deposit_locations[(x,y)] = karbonite_at
	return deposit_locations
