import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):

	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team = gc.team()
	start_map = gc.starting_map(bc.Planet(0))

	# find all karbonite deposits close to current unit
	print("KARBONITE COUNT: ",gc.karbonite())
	location = unit.location
	if location.is_on_map():
		position = unit.location.map_location()
		closest_deposit = get_closest_deposit(gc, unit)

		#check to see if there even are deposits
		if start_map.on_map(closest_deposit):
			direction_to_deposit = position.direction_to(closest_deposit)
			if position.is_adjacent_to(closest_deposit) or position == closest_deposit:
				# mine if adjacent to deposit
				if not unit.worker_has_acted():
					gc.harvest(unit.id,direction_to_deposit)
					print("harvested!")
			else:
				# move toward deposit
				if gc.is_move_ready(unit.id) and gc.can_move(unit.id, direction_to_deposit):
					gc.move_robot(unit.id, direction_to_deposit)
					print("moving toward deposit")
		else:
			d = random.choice(list(bc.Direction))
			if gc.is_move_ready(unit.id) and gc.can_move(unit.id,d):
				gc.move_robot(unit.id,d)

	"""

	space_out_factories = True
	if location.is_on_map():
		nearby = gc.sense_nearby_units(location.map_location(), 5)
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory:
				space_out_factories = False
			if gc.can_build(unit.id, other.id):
				gc.build(unit.id, other.id)
				print('built a factory!')
				return
	# okay, there weren't any dudes around
	# pick a random direction:
	directions = list(bc.Direction)
	d = random.choice(directions)

	# or, try to build a factory:
	if space_out_factories and gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
		gc.blueprint(unit.id, bc.UnitType.Factory, d)
	# and if that fails, try to move
	elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
		gc.move_robot(unit.id, d)
	"""

def get_closest_deposit(gc,unit):
	position = unit.location.map_location()
	vision_range = unit.vision_range	
	potential_karbonite_locations = gc.all_locations_within(position,vision_range)		
	
	current_distance = float('inf')
	closest_deposit = bc.MapLocation(bc.Planet(0),-1,-1)
	for potential_location in potential_karbonite_locations:
		distance_to_deposit = position.distance_squared_to(potential_location)	
		#keep updating current closest deposit to unit	
		if gc.karbonite_at(potential_location) > 0 and distance_to_deposit < current_distance:
			print("found one at: ",potential_location.x,potential_location.y)
			current_distance = distance_to_deposit 
			closest_deposit = potential_location
	return closest_deposit	
			



