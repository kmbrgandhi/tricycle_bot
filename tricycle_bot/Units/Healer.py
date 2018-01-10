import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):

	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Healer:
		return

	directions = list(bc.Direction)
	d = random.choice(directions)

	if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
		gc.move_robot(unit.id, d)
