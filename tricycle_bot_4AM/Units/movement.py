import battlecode as bc
import random
import sys
import traceback

import Units.sense_util as sense_util
import Units.variables as variables


#placeholder function for pathfinding algorithm
def try_move(gc,unit,coords,direction):
	if gc.is_move_ready(unit.id):
		current_direction = direction
		can_move = True
		while not gc.can_move(unit.id, current_direction):	
			current_direction = current_direction.rotate_left()
			if current_direction == direction:
				# has tried every direction, cannot move
				can_move = False
				break
		if can_move:	
			gc.move_robot(unit.id, current_direction)
			add_new_location(unit.id, coords, current_direction)

def add_new_location(unit_id, old_coords, direction):
	if variables.curr_planet == bc.Planet.Earth: 
		quadrant_size = variables.earth_quadrant_size
	else:
		quadrant_size = variables.mars_quadrant_size

	unit_mov = variables.direction_to_coord[direction]
	new_coords = (old_coords[0]+unit_mov[0], old_coords[1]+unit_mov[1])
	variables.unit_locations[unit_id] = new_coords

	old_quadrant = (int(old_coords[0] / quadrant_size), int(old_coords[1] / quadrant_size))
	new_quadrant = (int(new_coords[0] / quadrant_size), int(new_coords[1] / quadrant_size))

	if old_quadrant != new_quadrant: 
		variables.quadrant_battle_locs[old_quadrant].remove_ally(unit_id)
		variables.quadrant_battle_locs[new_quadrant].add_ally(unit_id, "worker")

def optimal_direction_towards(gc, unit, location, target, directions):
	# return the optimal direction towards a target that is achievable; not A*, but faster.
	shape = [target.x - location.x, target.y - location.y]
	options = sense_util.get_best_option(shape)
	for option in options:
		if gc.can_move(unit.id, option):
			return option
	return directions[8]

