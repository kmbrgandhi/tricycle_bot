import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.movement as movement
import Units.explore as explore
import Units.Ranger as Ranger



def timestep(gc, unit, info, karbonite_locations, locs_next_to_terrain, blueprinting_queue, blueprinting_assignment, building_assignment, current_roles):
	#print(building_assignment)
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team = gc.team()	

	my_location = unit.location

	# make sure unit can actually perform actions ie. not in garrison
	if not my_location.is_on_map():
		return

	if my_location.map_location().planet is bc.Planet.Mars:
		mine_mars(gc,unit)
		return

	#print()
	#print("ON UNIT #",unit.id, "position: ",unit.location.map_location())	
	role = get_role(gc,unit,blueprinting_queue,blueprinting_assignment,building_assignment,current_roles,karbonite_locations)
	
	#print("KARBONITE: ",gc.karbonite()
	
	current_num_workers = info[0]	
	max_num_workers = get_replication_cap(gc,karbonite_locations)
	worker_spacing = 8
	workers_per_building = 4

	#print("REPLICATION CAP: ",max_num_workers)
	# replicates if unit is able to (cooldowns, available directions etc.)	
	if current_num_workers < max_num_workers:

		try_replicate = replicate(gc,unit)
		if try_replicate:
			return

	# runs this block every turn if unit is miner
	if role == "miner":
		mine(gc,unit,karbonite_locations,current_roles, building_assignment)
	# if unit is builder
	elif role == "builder":
		build(gc,unit,building_assignment,current_roles,workers_per_building)
	# if unit is blueprinter
	elif role == "blueprinter":
		blueprint(gc,unit,blueprinting_queue,building_assignment,blueprinting_assignment,current_roles,locs_next_to_terrain)
	# if unit is boarder
	elif role == "boarder": 
		board(gc,unit,current_roles)
	# if unit is idle
	elif role == "repairer":
		repair(gc, unit, current_roles)
	else: 	
		nearby= gc.sense_nearby_units_by_team(my_location.map_location(), worker_spacing, gc.team())

		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		#print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)
		movement.try_move(gc,unit,away_from_units)


# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def get_role(gc,my_unit,blueprinting_queue,blueprinting_assignment,building_assignment,current_roles,karbonite_locations):
	my_location = my_unit.location.map_location()
	#print(my_location)
	start_map = gc.starting_map(bc.Planet(0))
	nearby = gc.sense_nearby_units(my_location, my_unit.vision_range)
	blueprint_count = 0
	factory_count = 0	
	rocket_count = 0
	rocket_ready_for_loading = False
	please_move = False	


	for unit in gc.my_units():
		if unit.unit_type == bc.UnitType.Factory: # count ALL factories
			if my_location.is_adjacent_to(unit.location.map_location()):
				please_move = True
			if not unit.structure_is_built():
				if unit.id not in building_assignment.keys():
					#print("added new entry into building_assignment")
					building_assignment[unit.id] = []
				blueprint_count += 1
			factory_count += 1

		elif unit.unit_type == bc.UnitType.Rocket:
			if unit.structure_is_built() and len(unit.structure_garrison()) < unit.structure_max_capacity():
				rocket_ready_for_loading = True
				#print("UNITS IN GARRISON",unit.structure_garrison())
			if not unit.structure_is_built():
				blueprint_count += 1
			rocket_count += 1
	

	update_for_dead_workers(gc,current_roles,blueprinting_assignment,building_assignment)
	update_building_assignment(gc,building_assignment)
	open_slots_to_build = False
	for building_id in building_assignment:
		assigned_workers = building_assignment[building_id]
		#print("this building:",gc.unit(building_id).location.map_location(), "is built?",gc.unit(building_id).structure_is_built())
		#print("assigned_workers", assigned_workers)
		if len(assigned_workers) < 4:
			open_slots_to_build = True
			break

	#print("blueprint_count: ",blueprint_count,"open_slots_to_build",open_slots_to_build)
	# code to prevent workers from mining in front of building entrances
	for role in current_roles.keys():
		if my_unit.id in current_roles[role]:
			if role == "miner" and please_move: 
				#print(my_unit.id, "NEEDS TO MOVE")
				return "idle"
			else:
				#print(role)
				return role

	num_miners = len(current_roles["miner"])
	num_blueprinters = len(current_roles["blueprinter"])
	num_builders = len(current_roles["builder"])

	max_num_builders = 5
	max_num_blueprinters = 3 #len(blueprinting_queue)*2 + 1 # at least 1 blueprinter, 2 blueprinters per cluster
	max_num_factories = get_cluster_limit(gc)*4	
	max_num_rockets = get_rocket_limit(gc)
	num_miners_per_deposit = 2 #approximate, just to cap miner count as deposit number decreases

	# early game miner production
	if gc.karbonite() < 100 and num_miners < 2:
		new_role = "miner"
	# become builder when there are available blueprints
	elif blueprint_count > 0 and open_slots_to_build:
		#print("blueprint_count: ",blueprint_count,"open_slots_to_build",open_slots_to_build)
		new_role = "builder"
	# become blueprinter
	elif num_blueprinters < max_num_blueprinters and (factory_count < max_num_factories or rocket_count < max_num_rockets):	
		new_role = "blueprinter" 
	# default to becoming miner mid game
	elif num_miners_per_deposit * len(karbonite_locations) > num_miners:
		new_role = "miner"
	elif rocket_ready_for_loading:
		new_role = "boarder"
	else:
		new_role = "repairer"

	current_roles[new_role].append(my_unit.id)
	#print(new_role)
	return new_role

def update_for_dead_workers(gc,current_roles,blueprinting_assignment,building_assignment):
	live_unit_ids = list_of_unit_ids(gc)
	for role in current_roles.keys():
		for worker_id in current_roles[role][:]:

			if worker_id not in live_unit_ids:
				current_roles[role].remove(worker_id)

				if role == "builder":
					for building_id in building_assignment:
						if worker_id in building_assignment[building_id]:
							building_assignment[building_id].remove(worker_id)
							break

				elif role == "blueprinter":
					if worker_id in blueprinting_assignment:
						build_site = blueprinting_assignment[worker_id]
						blueprinting_queue.append(build_site)
						del blueprinting_assignment[worker_id]


def repair(gc, unit, current_roles):
	map_loc = unit.location.map_location()
	closest = None
	closest_dist = float('inf')
	for fact in gc.my_units():
		if fact.unit_type == bc.UnitType.Factory:
			if fact.structure_is_built() and fact.health < fact.max_health:
				loc = fact.location.map_location()
				dist = map_loc.distance_squared_to(loc)
				if dist < closest_dist:
					closest = fact
					closest_dist = dist

	if closest!=None:
		if gc.can_repair(unit.id, closest.id):
			gc.repair(unit.id, closest.id)
		else:
			dir = map_loc.direction_to(closest.location.map_location())
			movement.try_move(gc, unit, dir)
	else:
		current_roles["repairer"].remove(unit.id)

def board(gc,my_unit,current_roles):
	my_location = my_unit.location.map_location()
	finished_rockets = []
	for unit in gc.my_units():
		if unit.unit_type == bc.UnitType.Rocket and unit.structure_is_built() and len(unit.structure_garrison()) < unit.structure_max_capacity():
			finished_rockets.append(unit)

	minimum_distance = float('inf')
	closest_rocket = None
	for rocket in finished_rockets:
		dist_to_rocket = my_location.distance_squared_to(rocket.location.map_location())
		if dist_to_rocket < minimum_distance:
			minimum_distance = dist_to_rocket
			closest_rocket = rocket

	if closest_rocket is None:
		current_roles["boarder"].remove(my_unit.id)
		return

	rocket_location = closest_rocket.location.map_location()
	if my_location.is_adjacent_to(rocket_location):
		if gc.can_load(closest_rocket.id,my_unit.id):
			#print(unit.id, 'loaded')
			gc.load(closest_rocket.id,my_unit.id)
			current_roles["boarder"].remove(my_unit.id)
	else:
		#print(unit.id, 'moving toward rocket')
		direction_to_rocket = my_location.direction_to(rocket_location)
		movement.try_move(gc,my_unit,direction_to_rocket)
		
	
def get_replication_cap(gc,karbonite_locations):
	#print("KARBONITE INFO LENGTH: ",len(karbonite_locations))
	#print(len(karbonite_locations))
	return min(3 + float(500+gc.round())/7000 * len(karbonite_locations),15)

def replicate(gc,unit):
	replicated = False
	if gc.karbonite() >= bc.UnitType.Worker.replicate_cost():
		directions = list(bc.Direction)
		for direction in directions:
			if gc.can_replicate(unit.id,direction):
				replicated = True
				gc.replicate(unit.id,direction)
	return replicated

# FOR EARTH ONLY
def update_deposit_info(gc,unit,karbonite_locations):
	position = unit.location.map_location()
	planet = bc.Planet(0)
	karbonite_locations_keys = list(karbonite_locations.keys())[:]
	for x,y in karbonite_locations_keys:
		map_location = bc.MapLocation(planet,x,y)
		# we can only update info about deposits we can see with our units
		if not position.is_within_range(unit.vision_range,map_location):
			continue	
		current_karbonite = gc.karbonite_at(map_location)
		if current_karbonite == 0:
			del karbonite_locations[(x,y)]
		elif karbonite_locations[(x,y)] != current_karbonite:
			karbonite_locations[(x,y)] = current_karbonite
	
# returns map location of closest karbonite deposit	
def get_closest_deposit(gc,unit,karbonite_locations):	
	update_deposit_info(gc,unit,karbonite_locations)	
	
	planet = bc.Planet(0)	
	position = unit.location.map_location()
	
	current_distance = float('inf')
	closest_deposit = bc.MapLocation(planet,-1,-1)
	for x,y in karbonite_locations.keys():
		map_location = bc.MapLocation(planet,x,y)
		distance_to_deposit = position.distance_squared_to(map_location)	
		#keep updating current closest deposit to unit	
		if distance_to_deposit < current_distance:
			current_distance = distance_to_deposit 
			closest_deposit = map_location
	return closest_deposit	
	
def mine(gc,unit,karbonite_locations,current_roles, building_assignment):
	my_location = unit.location
	position = my_location.map_location()
	closest_deposit = get_closest_deposit(gc,unit,karbonite_locations)
	start_map = gc.starting_map(bc.Planet(0))

	#check to see if there even are deposits
	if start_map.on_map(closest_deposit):
		direction_to_deposit = position.direction_to(closest_deposit)
		#print(unit.id, "is trying to mine at", direction_to_deposit)
		if position.is_adjacent_to(closest_deposit) or position == closest_deposit:
			# mine if adjacent to deposit
			if gc.can_harvest(unit.id,direction_to_deposit):
				gc.harvest(unit.id,direction_to_deposit)
				current_roles["miner"].remove(unit.id)
				#print(unit.id," just harvested!")
		else:
			# move toward deposit
			enemies = gc.sense_nearby_units_by_team(position, unit.vision_range, sense_util.enemy_team(gc))
			if len(enemies) > 0:
				dir = sense_util.best_available_direction(gc, unit, enemies)
				movement.try_move(gc, unit, dir)
				#current_roles["miner"].remove(unit.id)
				#current_roles["builder"].append(unit.id)
				#building_assignment[unit.id] = pick_closest_building_assignment(gc, unit, building_assignment)
			else:
				movement.try_move(gc,unit,direction_to_deposit)
	else:
		current_roles["miner"].remove(unit.id)

def pick_closest_building_assignment(gc, unit, building_assignment):
	closest = None
	min_dist = float('inf')
	map_loc = unit.location.map_location()
	for building in building_assignment.values():
		dist = map_loc.distance_squared_to(building.get_map_location())
		if dist< min_dist:
			closest = building
			min_dist = dist
	return closest

def mine_mars(gc,unit):
	my_location = unit.location.map_location()
	all_locations = gc.all_locations_within(my_location,unit.vision_range)
	planet = bc.Planet.Mars
	start_map = gc.starting_map(planet)
	worker_spacing = 8

	current_distance = float('inf')
	closest_deposit = bc.MapLocation(planet,-1,-1)
	for deposit_location in all_locations:
		if gc.karbonite_at(deposit_location) == 0:
			continue
		distance_to_deposit = my_location.distance_squared_to(deposit_location)	
		#keep updating current closest deposit to unit	
		if distance_to_deposit < current_distance:
			current_distance = distance_to_deposit 
			closest_deposit = deposit_location
		#check to see if there even are deposits
	
	if start_map.on_map(closest_deposit):
		direction_to_deposit = my_location.direction_to(closest_deposit)
		#print(unit.id, "is trying to mine at", direction_to_deposit)
		if my_location.is_adjacent_to(closest_deposit) or my_location == closest_deposit:
			# mine if adjacent to deposit
			if gc.can_harvest(unit.id,direction_to_deposit):
				gc.harvest(unit.id,direction_to_deposit)

				#print(unit.id," just harvested on Mars!")
		else:
			# move toward deposit
			movement.try_move(gc,unit,direction_to_deposit)	 
	else:
		nearby = gc.sense_nearby_units_by_team(my_location.map_location(), worker_spacing, gc.team())

		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		#print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)
		movement.try_move(gc,unit,away_from_units)

# updates building assignments in case buildings are destroyed before they are built
def update_building_assignment(gc,building_assignment):
	keys = list(building_assignment.keys())[:]
	for building_id in keys:
		if building_id not in list_of_unit_ids(gc):
			del building_assignment[building_id]
		else:
			building = gc.unit(building_id)
			try:
				if building.structure_is_built():
					del building_assignment[building_id]
			except:
				del building_assignment[building_id]


def assign_unit_to_build(gc,my_unit,building_assignment,workers_per_building):
	my_location = my_unit.location.map_location()
	blueprints = []

	for unit in gc.my_units():
		if (unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket):
			if not unit.structure_is_built():
				if unit.id not in building_assignment:
					blueprints.append(unit)
				else: 
					if len(building_assignment[unit.id]) < workers_per_building:
						#print("available blueprints to work on")
						blueprints.append(unit)

	smallest_distance = float('inf')
	closest_building = None
	#print(len(blueprints))
	for blueprint in blueprints:
		blueprint_location = blueprint.location.map_location()
		distance_to_blueprint = my_location.distance_squared_to(blueprint_location)
		if distance_to_blueprint < smallest_distance:
			smallest_distance = distance_to_blueprint
			closest_building = blueprint
	#print("my_unit.id",my_unit.id,"closest_building",closest_building)

	if closest_building is not None:
		building_assignment[closest_building.id].append(my_unit.id)
	return closest_building

def list_of_unit_ids(gc):
	return [unit.id for unit in gc.my_units()]

def build(gc,my_unit,building_assignment,current_roles,workers_per_building):
	my_location = my_unit.location.map_location()
	start_map = gc.starting_map(bc.Planet(0))
	#print("building_assignment",building_assignment)
	my_nearby_units = gc.my_units()
	unit_was_not_assigned = True

	assigned_building = None

	#print("unit",my_unit.id,"is building")
	# loop through building assignments and look for my_unit.id if it is assigned
	for building_id in building_assignment:
		if my_unit.id in building_assignment[building_id] and building_id in list_of_unit_ids(gc):
			assigned_building = gc.unit(building_id)
			#print("assigned_building",assigned_building.location.map_location())
			if assigned_building.structure_is_built():
				#print("assigned_building was already built")
				del building_assignment[building_id]
				#current_roles["builder"].remove(my_unit.id)
				#return
				assigned_building = assign_unit_to_build(gc,my_unit,building_assignment,workers_per_building)
				unit_was_not_assigned = False
				break
			else:
				unit_was_not_assigned = False

	if unit_was_not_assigned:
		#print("unit wasn't assigned building prior")
		assigned_building = assign_unit_to_build(gc,my_unit,building_assignment,workers_per_building)


	if assigned_building is None:
		#print(my_unit.id, "there are no blueprints around")
		current_roles["builder"].remove(my_unit.id)
		return

	#print("unit has been assigned to build at",assigned_building.location.map_location())
	assigned_location = assigned_building.location.map_location()
	if my_location.is_adjacent_to(assigned_location):
		if gc.can_build(my_unit.id,assigned_building.id):
			#print(unit.id, "is building factory at ",assigned_site)
			gc.build(my_unit.id,assigned_building.id)
			if assigned_building.structure_is_built():
				current_roles["builder"].remove(my_unit.id)
				del building_assignment[building_id]
		return
	# if not adjacent move toward it
	else:
		#print(unit.id, "is trying to move toward factory at ",assigned_site)
		direction_to_blueprint = my_location.direction_to(assigned_location)
		movement.try_move(gc,my_unit,direction_to_blueprint)

	# if no nearby blueprints around.. 

	"""
	assigned_site = building_assignment[unit.id].map_location

	if gc.has_unit_at_location(assigned_site):
		#print("building is at the location")
		blueprint_at_site = gc.sense_unit_at_location(assigned_site)
	else: # building has died
		current_roles["builder"].remove(unit.id)
		del building_assignment[unit.id]
		return
	#assert blueprint_at_site.unit_type == bc.UnitType.Factory or blueprint_at_site.unit_type == bc.UnitType.Rocket

	if blueprint_at_site.structure_is_built():
		#print(unit.id, "has finished building a structure at ",assigned_site)
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
	"""




def is_valid_blueprint_location(start_map,block_location,locs_next_to_terrain):

	if start_map.on_map(block_location) and start_map.is_passable_terrain_at(block_location):
		is_next_to_terrain = False
		for loc in locs_next_to_terrain:
			if loc == block_location:
				is_next_to_terrain = True
				break
		if not is_next_to_terrain:	
			return True
	return False

# generates locations to build factories that are arranged in clusters of 4 for space efficiency	
def generate_factory_locations(start_map,center,locs_next_to_terrain):
	x = center.x
	y = center.y
	planet = center.planet
	biggest_cluster = []
	relative_block_locations = [(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]
	
	if not is_valid_blueprint_location(start_map,center,locs_next_to_terrain):
		return [] 
	
	for i in range(4):
		cluster = [center]
		for j in range(3):
			d = relative_block_locations[(2*i + j) % 8]
			block_location = bc.MapLocation(planet,x+d[0],y+d[1])
			if is_valid_blueprint_location(start_map,block_location,locs_next_to_terrain):			
				cluster.append(block_location)
		if len(cluster) > len(biggest_cluster):
			biggest_cluster = cluster
	#print("center: ",center)
	#print("BIGGEST CLUSTER",biggest_cluster)
	return biggest_cluster


# function to flexibly determine when a good time to expand factories
def can_blueprint_factory(gc,blueprinting_queue):
	#TODO
	factory_count = 0
	max_num_factories = 4 * get_cluster_limit(gc)
	for unit in gc.my_units():
		if unit.unit_type == bc.UnitType.Factory:
			factory_count += 1
	return factory_count < max_num_factories

def can_blueprint_rocket(gc,blueprinting_queue):
	rocket_count = 0
	max_num_rockets = get_rocket_limit(gc)
	for unit in gc.my_units():
		if unit.unit_type == bc.UnitType.Rocket:
			rocket_count += 1
	return gc.research_info().get_level(bc.UnitType.Rocket) > 0 and rocket_count < max_num_rockets

def blueprinting_queue_limit(gc):
	start_map = gc.starting_map(bc.Planet(0))
	return 1
	return start_map.width * start_map.height / 100 

def get_cluster_limit(gc):
	return 2
def get_rocket_limit(gc):
	return 1

def get_closest_site(gc,my_unit,blueprinting_queue):
	my_location = my_unit.location.map_location()
	nearby_sites = []	
	for site in blueprinting_queue:
		if site.is_cluster():
			for potential_factory in site.build_sites:
				nearby_sites.append(potential_factory) # this is used for blueprint assignment 
		else:
			nearby_sites.append(site)
	
	smallest_distance = float('inf')
	closest_site = None	
	for site in nearby_sites:
		distance_to_site = my_location.distance_squared_to(site.map_location) 
		if distance_to_site < smallest_distance:
			smallest_distance = distance_to_site
			closest_site = site
	return closest_site
		
def update_blueprinting_queue(closest_building_site,blueprinting_queue):
	for site in blueprinting_queue:
		if site.is_cluster():
			if closest_building_site in site.build_sites:
				site.build_sites.remove(closest_building_site)
				if len(site.build_sites) == 0:
					blueprinting_queue.remove(site)
				break
		else:
			if closest_building_site == site:
				blueprinting_queue.remove(site)

# controls how many buildings we can have in progress at a time, can modify this to scale with karbonite number, round # or number of units (enemy or ally)
def building_in_progress_cap(gc):
	return 2


def blueprint(gc,my_unit,blueprinting_queue,building_assignment,blueprinting_assignment,current_roles,locs_next_to_terrain):
	my_location = my_unit.location.map_location()
	start_map = gc.starting_map(bc.Planet(0))
	directions = list(bc.Direction)

	blueprint_spacing = 20
	nearby = gc.sense_nearby_units(my_location,blueprint_spacing)
	is_nearby_building = False
	is_nearby_potential_buildings = False

	# if it finds a nice location for factory cluster, put it in queue	
	if len(blueprinting_queue) < blueprinting_queue_limit(gc):
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory or other.unit_type == bc.UnitType.Rocket:
				is_nearby_building = True
				break
		for site in blueprinting_queue:
			if site.is_cluster():
				for potential_building in site.build_sites:
					if my_location.distance_squared_to(potential_building.map_location) < blueprint_spacing:
						is_nearby_potential_buildings = True
						break
			else:
				if my_location.distance_squared_to(site.map_location) < blueprint_spacing:
						is_nearby_potential_buildings = True
						break
		if not (is_nearby_building or is_nearby_potential_buildings):
			if can_blueprint_rocket(gc,blueprinting_queue):
				if is_valid_blueprint_location(start_map,my_location,locs_next_to_terrain):
					new_site = BuildSite(my_location,bc.UnitType.Rocket)
					blueprinting_queue.append(new_site)
			elif can_blueprint_factory(gc,blueprinting_queue):
				future_factory_locations = generate_factory_locations(start_map,my_location,locs_next_to_terrain)
				if len(future_factory_locations) > 0:
					new_cluster = BuildSiteCluster([BuildSite(building_location,bc.UnitType.Factory) for building_location in future_factory_locations])
					blueprinting_queue.append(new_cluster)	
				#print(unit.id," just added to building queue")


	# assign this unit to build a blueprint, if nothing to build just move away from other factories
	if my_unit.id not in blueprinting_assignment:
		building_in_progress_count = len(building_assignment.keys()) + len(blueprinting_assignment.keys())
		#print("blueprinting_assignment",blueprinting_assignment)
		#print("building_assignment",building_assignment)
		#print("building in progress cap",building_in_progress_count)
		#print("blueprint assignment threshold met?",len(blueprinting_queue) > 0 and building_in_progress_count < building_in_progress_cap(gc))
		if len(blueprinting_queue) > 0 and building_in_progress_count < building_in_progress_cap(gc):
			closest_building_site = get_closest_site(gc,my_unit,blueprinting_queue)
			update_blueprinting_queue(closest_building_site,blueprinting_queue)
			blueprinting_assignment[my_unit.id] = closest_building_site
			#print(unit.id, "has been assigned to this building ",closest_building_site)
		else:	
			all_buildings = []
			for other in gc.my_units():
				if other.unit_type == bc.UnitType.Factory or other.unit_type == bc.UnitType.Rocket:
					all_buildings.append(other)
			away_from_buildings = sense_util.best_available_direction(gc,my_unit,all_buildings)
			# pick other direction if direction is center
			if away_from_buildings == bc.Direction.Center:
				away_from_buildings = bc.Direction.North
			movement.try_move(gc,my_unit,away_from_buildings)
			#print(unit.id, " is exploring the map for build sites")

	# build blueprint in assigned square
	if my_unit.id in blueprinting_assignment:
		#print(unit.id, "is in the building assignment")
		assigned_site = blueprinting_assignment[my_unit.id]

		if my_unit.id in blueprinting_assignment:
			print("unit",my_unit.id,"blueprinting at",blueprinting_assignment[my_unit.id])
		#print(unit.id, "is assigned to building in", assigned_site.map_location)
		direction_to_site = my_location.direction_to(assigned_site.map_location)

		if my_location.is_adjacent_to(assigned_site.map_location):
			if gc.can_blueprint(my_unit.id, assigned_site.building_type, direction_to_site):
				gc.blueprint(my_unit.id, assigned_site.building_type, direction_to_site)
				del blueprinting_assignment[my_unit.id]
				current_roles["blueprinter"].remove(my_unit.id)
				current_roles["builder"].append(my_unit.id)
				print(my_unit.id, " just created a blueprint!")
			#else:
			#print(unit.id, "can't build but is right next to assigned site")
		elif my_location == assigned_site.map_location:
			# when unit is currently on top of the queued building site
			d = random.choice(list(bc.Direction))
			movement.try_move(gc,my_unit,d)
			#print(unit.id, " is on top of its build site and is moving away")
		else:
			# move toward queued building site
			#print(unit.id, "is moving toward building site: ",assigned_site)
			next_direction = my_location.direction_to(assigned_site.map_location)	

			movement.try_move(gc,my_unit,next_direction)	
			"""
			next_direction = my_location.direction_to(path[0])	
			movement.try_move(gc,unit,next_direction)	
			"""
			#print(unit.id, " is moving to its assigned build site")
		

class BuildSite:
	def __init__(self,map_location,building_type):
		self.map_location = map_location
		self.building_type = building_type

	def get_map_location(self):
		return self.map_location
	
	def get_building_type(self):
		return self.building_type

	def is_cluster(self):
		return False

	def __str__(self):
		return "{map_location : " + str(self.map_location) + ", building_type : " + str(self.building_type) + " }"

class BuildSiteCluster:
	def __init__(self,build_sites):
		self.build_sites = build_sites[:]

	def get_building_type(self):
		return bc.UnitType.Factory

	def is_cluster(self):
		return True

	def __str__(self):
		output = "["
		for site in self.build_sites:
			output += str(site) + ","
		return output

