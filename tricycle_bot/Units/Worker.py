import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.movement as movement
import Units.explore as explore

def timestep(gc, unit, info, karbonite_info, blueprinting_queue, building_assignment, current_roles):
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team = gc.team()	

	my_location = unit.location
	# make sure unit can actually perform actions ie. not in garrison
	if not my_location.is_on_map():
		return	

	print("ON UNIT #",unit.id, "position: ",unit.location.map_location())	
	role = get_role(gc,unit,blueprinting_queue,current_roles,karbonite_info)

	if gc.team() == bc.Team(0):	
		print("current_roles",current_roles)
		print("blueprinting_queue",blueprinting_queue)
		print("building_assignment",building_assignment)
	
	current_num_workers = info[0]	
	max_num_workers = 10
	worker_spacing = 10

	# replicates if unit is able to (cooldowns, available directions etc.)	
	if current_num_workers < max_num_workers:
		replicate(gc,unit)	
		return

	# runs this block every turn if unit is miner
	if role == "miner":
		mine(gc,unit,karbonite_info,current_roles)
	# if unit is builder
	elif role == "builder":
		build(gc,unit,building_assignment,current_roles)
	# if unit is blueprinter
	elif role == "blueprinter":
		blueprint(gc,unit,blueprinting_queue,building_assignment,current_roles)
	# if unit is idle
	elif role == "idle":
		nearby = gc.sense_nearby_units(my_location.map_location(), worker_spacing)
		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)
		movement.try_move(gc,unit,away_from_units)


# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def get_role(gc,my_unit,blueprinting_queue,current_roles,karbonite_info):
	my_location = my_unit.location	
	start_map = gc.starting_map(bc.Planet(0))
	nearby = gc.sense_nearby_units(my_location.map_location(), my_unit.vision_range)
	all_factory_count = 0	
	please_move = False	
	
	for unit in gc.my_units():
		if unit.unit_type == bc.UnitType.Factory: # count ALL factories
			if my_location.map_location().is_adjacent_to(unit.location.map_location()):
				please_move = True
			all_factory_count += 1	
	
	for role in current_roles.keys():
		if my_unit.id in current_roles[role]:
			if role == "miner" and please_move: 
				print(my_unit.id, "NEEDS TO MOVE")
				return "idle"
			else:
				return role

	num_miners = len(current_roles["miner"])
	num_blueprinters = len(current_roles["blueprinter"])
	num_builders = len(current_roles["builder"])

	max_num_blueprinters = 1 #len(blueprinting_queue)*2 + 1 # at least 1 blueprinter, 2 blueprinters per cluster
	max_num_factories = get_cluster_limit(gc)*4	
	num_miners_per_deposit = 2 #approximate, just to cap miner count as deposit number decreases

	# early game miner production
	if gc.karbonite() < 100 and num_miners < 2:
		new_role = "miner"	
	# become blueprinter
	elif num_blueprinters < max_num_blueprinters and all_factory_count < max_num_factories:	
		new_role = "blueprinter" 
	# default to becoming miner mid game
	elif num_miners_per_deposit * len(karbonite_info) > num_miners:
		new_role = "miner"
	else:
		return "idle"
	current_roles[new_role].append(my_unit.id)
	return new_role

# function to get all unit types in a certain detection radius
def get_all_units_within_range(gc,unit,type_of_unit,detection_radius=None):
	my_position = unit.location.map_location()
	if detection_radius == None:
		nearby = gc.my_units()
	elif detection_radius >= 0:
		nearby = gc.sense_nearby_units(my_position,detection_radius)
	else:
		return []

	units_in_radius = []
	for unit in nearby:
		if unit.unit_type == type_of_unit:
			units_in_radius.append(unit)
	return units_in_radius
			

def replicate(gc,unit):
	if gc.karbonite() >= bc.UnitType.Worker.replicate_cost():
		directions = list(bc.Direction)
		for direction in directions:
			if gc.can_replicate(unit.id,direction):

				gc.replicate(unit.id,direction)

# FOR EARTH ONLY
def update_deposit_info(gc,unit,karbonite_info):
	position = unit.location.map_location()
	planet = bc.Planet(0)
	karbonite_info_keys = list(karbonite_info.keys())[:]
	for x,y in karbonite_info_keys:
		map_location = bc.MapLocation(planet,x,y)
		# we can only update info about deposits we can see with our units
		if not position.is_within_range(unit.vision_range,map_location):
			continue	
		current_karbonite = gc.karbonite_at(map_location)
		if current_karbonite == 0:
			del karbonite_info[(x,y)]
		elif karbonite_info[(x,y)] != current_karbonite:
			karbonite_info[(x,y)] = current_karbonite
	
# returns map location of closest karbonite deposit	
def get_closest_deposit(gc,unit,karbonite_info):	
	update_deposit_info(gc,unit,karbonite_info)	
	
	planet = bc.Planet(0)	
	position = unit.location.map_location()
	
	current_distance = float('inf')
	closest_deposit = bc.MapLocation(planet,-1,-1)
	for x,y in karbonite_info.keys():
		map_location = bc.MapLocation(planet,x,y)
		distance_to_deposit = position.distance_squared_to(map_location)	
		#keep updating current closest deposit to unit	
		if distance_to_deposit < current_distance:
			current_distance = distance_to_deposit 
			closest_deposit = map_location
	return closest_deposit	
	
def mine(gc,unit,karbonite_info,current_roles): 
	my_location = unit.location
	position = my_location.map_location()
	directions = list(bc.Direction)
	closest_deposit = get_closest_deposit(gc,unit,karbonite_info)
	start_map = gc.starting_map(bc.Planet(0))

	#check to see if there even are deposits
	if start_map.on_map(closest_deposit):
		direction_to_deposit = position.direction_to(closest_deposit)
		print(unit.id, "is trying to mine at", direction_to_deposit)
		if position.is_adjacent_to(closest_deposit) or position == closest_deposit:
			# mine if adjacent to deposit
			if gc.can_harvest(unit.id,direction_to_deposit):
				gc.harvest(unit.id,direction_to_deposit)
				current_roles["miner"].remove(unit.id)	
				print(unit.id," just harvested!")
		else:
			# move toward deposit
			movement.try_move(gc,unit,direction_to_deposit)	
	else:
		current_roles["miner"].remove(unit.id)



def build(gc,unit,building_assignment,current_roles):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))

	assigned_site = building_assignment[unit.id]
	blueprint_at_site = gc.sense_unit_at_location(assigned_site)
	assert blueprint_at_site.unit_type == bc.UnitType.Factory or blueprint_at_site.unit_type == bc.UnitType.Rocket

	if blueprint_at_site.structure_is_built():
		print(unit.id, "has finished building a structure at ",assigned_site)
		current_roles["builder"].remove(unit.id)
		del building_assignment[unit.id]		
	else:	
		if my_location.map_location().is_adjacent_to(assigned_site):
			if gc.can_build(unit.id,blueprint_at_site.id):
				#print(unit.id, "is building factory at ",assigned_site)
				gc.build(unit.id,blueprint_at_site.id)
			return
		# if not adjacent move toward it
		else:
			#print(unit.id, "is trying to move toward factory at ",assigned_site)
			direction_to_blueprint = my_location.map_location().direction_to(blueprint_at_site.location.map_location())
			movement.try_move(gc,unit,direction_to_blueprint)
		



# generates locations to build factories that are arranged in clusters of 4 for space efficiency	
def generate_factory_locations(start_map,center):
	x = center.x
	y = center.y
	planet = center.planet
	biggest_cluster = []
	relative_block_locations = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]

	for i in range(4):
		cluster = [center]
		for j in range(3):
			d = relative_block_locations[(2*i + j) % 8]
			block_location = bc.MapLocation(planet,x+d[0],y+d[1])
			if start_map.on_map(block_location) and start_map.is_passable_terrain_at(block_location):
				cluster.append(block_location)
		if len(cluster) > len(biggest_cluster):
			biggest_cluster = cluster
	return biggest_cluster


# function to flexibly determine when a good time to expand factories
def can_blueprint(gc,structure_type):
	#TODO
	return gc.karbonite() >= structure_type.blueprint_cost()

def get_cluster_limit(gc):
	start_map = gc.starting_map(bc.Planet(0))
	return 1
	return start_map.width * start_map.height / 100 

def get_closest_site(gc,unit,blueprinting_queue):
	nearby_sites = []	
	for cluster in blueprinting_queue:
		for potential_factory in cluster:
			nearby_sites.append(potential_factory) # this is used for blueprint assignment 
	
	smallest_distance = float('inf')
	closest_site = None	
	for site in nearby_sites:
		distance_to_site = unit.location.map_location().distance_squared_to(site) 
		if distance_to_site < smallest_distance:
			smallest_distance = distance_to_site
			closest_site = site
	return closest_site
		
 
def blueprint(gc,unit,blueprinting_queue,building_assignment,current_roles):
	my_location = unit.location
	start_map = gc.starting_map(bc.Planet(0))
	directions = list(bc.Direction)

	blueprint_spacing = 20
	nearby = gc.sense_nearby_units(my_location.map_location(),blueprint_spacing)
	is_nearby_factories = False
	is_nearby_potential_factories = False

	# if it finds a nice location for factory cluster, put it in queue	
	if len(blueprinting_queue) < get_cluster_limit(gc):
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory:
				is_nearby_factories = True
				break
		for cluster in blueprinting_queue:
			for potential_factory in cluster:
				if my_location.map_location().distance_squared_to(potential_factory) < blueprint_spacing:
					is_nearby_potential_factories = True
					break
		if not (is_nearby_factories or is_nearby_potential_factories):
			future_factory_locations = generate_factory_locations(start_map,my_location.map_location())
			blueprinting_queue.extend([future_factory_locations])	
			#print(unit.id," just added to building queue")


	# assign this unit to build a blueprint, if nothing to build just move away from other factories
	if unit.id not in building_assignment:
		if len(blueprinting_queue) > 0:
			closest_building_site = get_closest_site(gc,unit,blueprinting_queue)
			for cluster in blueprinting_queue:
				if closest_building_site in cluster:
					cluster.remove(closest_building_site)
					if len(cluster) == 0:
						blueprinting_queue.remove(cluster)
					break
			building_assignment[unit.id] = closest_building_site
			#print(unit.id, "has been assigned to this building ",closest_building_site)
		else:	
			all_factories = []
			for other in gc.my_units():
				if other.unit_type == bc.UnitType.Factory:
					all_factories.append(other)
			away_from_factories = sense_util.best_available_direction(gc,unit,all_factories)
			# pick other direction if direction is center
			if away_from_factories == directions[8]:
				away_from_factories = directions[1]
			movement.try_move(gc,unit,away_from_factories)
			#print(unit.id, " is exploring the map for build sites")

	# build blueprint in assigned square
	if unit.id in building_assignment:
		assigned_site = building_assignment[unit.id]
		direction_to_site = my_location.map_location().direction_to(assigned_site)
		if my_location.map_location().is_adjacent_to(assigned_site):
			if can_blueprint(gc,bc.UnitType.Factory) and gc.can_blueprint(unit.id, bc.UnitType.Factory, direction_to_site):
				gc.blueprint(unit.id, bc.UnitType.Factory, direction_to_site)
				current_roles["blueprinter"].remove(unit.id)
				current_roles["builder"].append(unit.id)
				print(unit.id, " just created a blueprint!")
			else:
				pass
				#print(unit.id, "can't build but is right next to assigned site")
		elif my_location.map_location() == assigned_site:
			# when unit is currently on top of the queued building site
			d = random.choice(list(bc.Direction))
			movement.try_move(gc,unit,d)
			#print(unit.id, " is on top of its build site and is moving away")
		else:
			# move toward queued building site
			print(assigned_site)
			next_direction = my_location.map_location().direction_to(assigned_site)	
			movement.try_move(gc,unit,next_direction)	
			"""
			path = explore.movement_path(gc,unit,assigned_site)
			next_direction = my_location.map_location().direction_to(path[0])	
			movement.try_move(gc,unit,next_direction)	
			"""
			#print(unit.id, " is moving to its assigned build site")
		
	


