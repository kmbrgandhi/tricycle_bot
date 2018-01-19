import battlecode as bc
import random
import sys
import traceback

import Units.sense_util as sense_util


#placeholder function for pathfinding algorithm
def try_move(gc,unit,direction):
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

def optimal_direction_towards(gc, unit, location, target, directions):
    # return the optimal direction towards a target that is achievable; not A*, but faster.
    shape = [target.x - location.x, target.y - location.y]
    options = sense_util.get_best_option(shape)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[8]

