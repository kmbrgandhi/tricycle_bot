import battlecode as bc
import random
import sys
import traceback


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
