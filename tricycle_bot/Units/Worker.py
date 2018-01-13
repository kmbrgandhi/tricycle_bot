import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

def timestep(gc, unit, building_queue, blueprinter_assignment, current_roles):

	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team = gc.team()	
	print("UNIT ID: ", unit.id)
	print("KARBONITE COUNT:",gc.karbonite())
	
	my_location = unit.location
	# make sure unit can actually perform actions ie. not in garrison
	if not my_location.is_on_map():
		return	

	role = get_role(gc,unit,current_roles)

	# runs this block every turn if unit is miner
	if role == "miner":
		mine(gc,unit,current_roles)
	# if unit is builder
	elif role == "builder":
		build(gc,unit,building_queue,current_roles)
	# if unit is blueprinter
	elif role == "blueprinter":
		blueprint(gc,unit,building_queue,blueprinter_assignment,current_roles)
	# if unit is idle
	elif role == "idle":	
		nearby = gc.sense_nearby_units(my_location.map_location(),unit.vision_range)
		away_from_allies = sense_util.best_available_direction(gc,unit,nearby)
		try_move(gc,unit,away_from_allies)
	
	print("current_roles",current_roles)

# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def get_role(gc,my_unit,current_roles):
	my_location = my_unit.location	
	nearby = gc.sense_nearby_units(my_location.map_location(), my_unit.vision_range)
	unfinished_factory_count = 0
	all_factory_count = 0
	for other in nearby:
		if other.unit_type == bc.UnitType.Factory and not other.structure_is_built(): # count unfinished factories
			unfinished_factory_count += 1
	for unit in gc.units():
		if unit.unit_type == bc.UnitType.Factory: # count ALL factories
			all_factory_count += 1	
	
	for role in current_roles.keys():
		if my_unit.id in current_roles[role]:
			return role

	max_num_blueprinters = 2
	max_num_factories = 12	
	
	# become builder	
	if unfinished_factory_count > len(current_roles["builder"]):
		new_role = "builder"
	# become miner
	elif gc.karbonite() < 100 and len(current_roles["miner"]) < 2:
		new_role = "miner"	
	# become blueprinter
	elif len(current_roles["blueprinter"]) < max_num_blueprinters and all_factory_count < max_num_factories:	
		new_role = "blueprinter" 
	# default to becoming miner
	else:
		new_role = "miner"
	current_roles[new_role].append(my_unit.id)
	return new_role
	

# placeholder function for pathfinding algorithm
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
			current_distance = distance_to_deposit 
			closest_deposit = potential_location
	return closest_deposit	
	
def mine(gc,unit,current_roles): 
	my_location = unit.location
	position = my_location.map_location()
	closest_deposit = get_closest_deposit(gc, unit)
	start_map = gc.starting_map(bc.Planet(0))

	#check to see if there even are deposits
	if start_map.on_map(closest_deposit):
		direction_to_deposit = position.direction_to(closest_deposit)
		if position.is_adjacent_to(closest_deposit) or position == closest_deposit:
			# mine if adjacent to deposit
			if not unit.worker_has_acted():
				gc.harvest(unit.id,direction_to_deposit)
				current_roles["miner"].remove(unit.id)	
				print("harvested!")
		else:
			# move toward deposit
			try_move(gc,unit,direction_to_deposit)	

# CHANGE IS_BUILDER() SO IT RETURNS TRUE IF THERE ARE NEARBY BLUEPRINTS
def build(gc,unit,building_queue,current_roles):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))
	nearby = gc.sense_nearby_units(my_location.map_location(), unit.vision_range)
	
	for other in nearby:
		if other.unit_type == bc.UnitType.Factory and not other.structure_is_built(): #located an unfinished factory	
			# we need to be adjacent to blueprint to build
			if my_location.is_adjacent_to(other.location):
				if gc.can_build(unit.id, other.id):
					gc.build(unit.id,other.id)
				return
			# if not adjacent move toward it
			else:
				direction_to_blueprint = my_location.map_location().direction_to(other.location.map_location())
				try_move(gc,unit,direction_to_blueprint)
				return

	# this code is reached only when there are NO unfinished factories around	
	current_roles["builder"].remove(unit.id)	
	print("BUILT FACTORY")
		

# generates locations to build factories that are arranged in clusters of 4 for space efficiency	
def generate_factory_locations(start_map,center):
	x = center.x
	y = center.y
	planet = center.planet
	
	build_locations = []
	edges = [bc.MapLocation(planet,x,y+1),bc.MapLocation(planet,x+1,y),bc.MapLocation(planet,x,y-1),bc.MapLocation(planet,x-1,y)]
	corners = [bc.MapLocation(planet,x+1,y+1),bc.MapLocation(planet,x+1,y-1),bc.MapLocation(planet,x-1,y-1),bc.MapLocation(planet,x-1,y+1)]
	
	for i in range(4):
		if start_map.on_map(corners[i]):
			return [center,corners[i],edges[i],edges[(i+1)%4]] 	

# function to flexibly determine when a good time to expand factories
def can_blueprint(gc):
	#TODO
	return gc.karbonite() > bc.UnitType.Factory.blueprint_cost()

def get_cluster_limit(gc):
	#TODO
	return 2
 
def blueprint(gc,unit,building_queue,blueprinter_assignment,current_roles):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))
	directions = list(bc.Direction)

	blueprint_spacing = 30
	nearby = gc.sense_nearby_units(my_location.map_location(),blueprint_spacing)
	is_nearby_factories = False
	is_nearby_potential_factories = False

	# if it finds a nice location for factory cluster, put it in queue	
	if len(building_queue) < get_cluster_limit(gc):
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory:
				is_nearby_factories = True
				break
		for cluster in building_queue:
			for potential_factory in cluster:
				if my_location.map_location().distance_squared_to(potential_factory) < blueprint_spacing:
					is_nearby_potential_factories = True
					break
		if not (is_nearby_factories or is_nearby_potential_factories):
			future_factory_locations = generate_factory_locations(start_map,my_location.map_location())
			building_queue.extend([future_factory_locations])	
			print("added to building queue")

	# assign this unit to build a blueprint, if nothing to build just move away from other factories
	if unit.id not in blueprinter_assignment:
		if len(building_queue) > 0:
			next_building_site = building_queue[0].pop(0)	
			if len(building_queue[0]) == 0:
				building_queue.pop(0) # remove empty list	
			blueprinter_assignment[unit.id] = next_building_site
		else:	
			all_factories = []
			for other in gc.my_units():
				if other.unit_type == bc.UnitType.Factory:
					all_factories.append(other)
			away_from_factories = sense_util.best_available_direction(gc,unit,all_factories)
			# pick other direction if direction is center
			if away_from_factories == directions[8]:
				away_from_factories = directions[1]
			try_move(gc,unit,away_from_factories)

	# build blueprint in assigned square
	if unit.id in blueprinter_assignment:
		assigned_site = blueprinter_assignment[unit.id]
		direction_to_site = my_location.map_location().direction_to(assigned_site)
		if my_location.map_location().is_adjacent_to(assigned_site):
			if can_blueprint(gc) and gc.can_blueprint(unit.id, bc.UnitType.Factory, direction_to_site):
				print("created blueprint!")
				gc.blueprint(unit.id, bc.UnitType.Factory, direction_to_site)
				current_roles["blueprinter"].remove(unit.id)
				del blueprinter_assignment[unit.id]
		elif my_location.map_location() == assigned_site:
			# when unit is currently on top of the queued building site
			d = random.choice(list(bc.Direction))
			try_move(gc,unit,d)
		else:
			# move toward queued building site
			try_move(gc,unit,direction_to_site)	
		
	


