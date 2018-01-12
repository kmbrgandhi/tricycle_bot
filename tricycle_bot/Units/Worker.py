import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util

def timestep(gc, unit, building_queue, current_roles):

	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team = gc.team()	

	print("KARBONITE COUNT: WTF",gc.karbonite())
	print("unit id: ", unit.id)
	
	my_location = unit.location
	# make sure unit can actually perform actions ie. not in garrison
	if not my_location.is_on_map():
		return	

	role = get_role(gc,unit,current_roles)

	# runs this block every turn if unit is miner
	if role == "miner":
		mine(gc,unit)
	# if unit is builder
	elif role == "builder":
		print("this unit is a builder: ",unit.id)
		build(gc,unit,building_queue)
	# if unit is blueprinter
	elif role == "blueprinter":
		print("this unit is a blueprinter: ",unit.id)
		blueprint(gc,unit,building_queue)
	# if unit is idle
	elif role == "idle":	
		print("this unit is idle: ",unit.id)
		nearby = gc.sense_nearby_units(my_location.map_location(),8)
		away_from_allies = sense_util.best_available_direction(gc,unit,nearby)
		if gc.is_move_ready(unit.id) and gc.can_move(unit.id,away_from_allies):
			gc.move_robot(unit.id,away_from_allies)


# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def get_role(gc,unit,current_roles):
	my_location = unit.location	
	nearby = gc.sense_nearby_units(my_location.map_location(), 8)
	unfinished_factory_count = 0
	for other in nearby:
		if other.unit_type == bc.UnitType.Factory and not other.structure_is_built(): #located an unfinished factory
			# recruit a builder if there isn't one yet	
			unfinished_factory_count += 1
	
	current_role = "idle"
	for role in current_roles.keys():
		if unit.id in current_roles[role]:
			current_role = role
	
	# become builder	
	if unfinished_factory_count > len(current_roles["builder"]):
		print("created builder")
		current_roles["builder"].append(unit.id)
		current_role = "builder"
	# become blueprinter
	elif len(current_roles["blueprinter"]) < 2:	
		print("created blueprinter")
		current_roles["blueprinter"].append(unit.id)
		current_role = "blueprinter" 
	# become miner
	else:	
		print("created idle")
		current_role = "idle"

	# if we switched roles, we update current_roles to reflect this	
	if current_role != "idle":
		current_roles[current_role].remove(unit.id)
	return current_role
	

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
			print("found one at: ",potential_location.x,potential_location.y)
			current_distance = distance_to_deposit 
			closest_deposit = potential_location
	return closest_deposit	
	
def mine(gc,unit): 
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
				print("harvested!")
		else:
			# move toward deposit
			try_move(gc,unit,direction_to_deposit)	

# CHANGE IS_BUILDER() SO IT RETURNS TRUE IF THERE ARE NEARBY BLUEPRINTS
def build(gc,unit,building_queue):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))
	nearby = gc.sense_nearby_units(my_location.map_location(), 10)
	
	for other in nearby:
		if other.unit_type == bc.UnitType.Factory and not other.structure_is_built(): #located an unfinished factory	
			# we need to be adjacent to blueprint to build
			if my_location.is_adjacent_to(other.location):
				if gc.can_build(unit.id, other.id):
					gc.build(unit.id,other.id)
					print('built a factory!')
					break
			# if not adjacent move toward it
			else:
				direction_to_blueprint = my_location.map_location().direction_to(other.location.map_location())
				try_move(gc,unit,direction_to_blueprint)
				break
		

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
 
def blueprint(gc,unit,building_queue):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))
	directions = list(bc.Direction)
	nearby = gc.sense_nearby_units(my_location.map_location(), 10)
	is_nearby_factory = False

	# if it finds a nice location for factory cluster, put it in queue	
	print("building_queue length:",len(building_queue))
	if len(building_queue) < 4:
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory:
				is_nearby_factory = True
				break
		if not is_nearby_factory:
			future_factory_locations = generate_factory_locations(start_map,my_location.map_location())
			building_queue.extend(future_factory_locations)	
			print("added to building queue")
	
	# when queue is empty, walk away from factories	
	if len(building_queue) == 0:
		nearby_factories = []
		for other in gc.my_units():
			if other.unit_type == bc.UnitType.Factory:
				nearby_factories.append(other)
		away_from_factories = sense_util.best_available_direction(gc,unit,nearby_factories)
		# pick other direction if direction is center
		if away_from_factories == directions[8]:
			print("center is: ", directions[8].dx(), directions[8].dy())
			away_from_factories = directions[1]
		try_move(gc,unit,away_from_factories)

	# take a building site from queue and walk to it and build a blueprint
	elif len(building_queue) > 0:
		next_building_site = building_queue[0]	
		direction_to_site = my_location.map_location().direction_to(next_building_site)
		if my_location.map_location().is_adjacent_to(next_building_site):
			if can_blueprint(gc) and gc.can_blueprint(unit.id, bc.UnitType.Factory, direction_to_site):
				print("creating blueprint!")
				gc.blueprint(unit.id, bc.UnitType.Factory, direction_to_site)
				building_queue.pop(0)
		elif my_location.map_location() == next_building_site:
			# when unit is currently on top of the queued building site
			d = random.choice(list(bc.Direction))
			try_move(gc,unit,d)
		else:
			# move toward queued building site
			try_move(gc,unit,direction_to_site)	
		
	


