import battlecode as bc
import random
import sys
import traceback
import numpy as np

def timestep(gc, unit,composition):

	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Healer:
		return

	my_team = gc.team()
	d = None
	directions = list(bc.Direction)
	location = unit.location
	if location.is_on_map():
		nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
		nearby_friendly = min(gc.sense_nearby_units_by_team(location.map_location(), unit.ability_range(), my_team),
							  key=lambda x: x.health) # find the lowest nearby unit
		if gc.is_heal_ready(unit.id) and gc.can_heal(unit.id, nearby_friendly.id):
			gc.heal(unit.id, nearby_friendly.id) # heal it, if possible

	if d == None:
		d = random.choice(directions)

	if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
		gc.move_robot(unit.id, d)
