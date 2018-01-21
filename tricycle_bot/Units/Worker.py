import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.movement as movement
import Units.explore as explore
import Units.Ranger as Ranger
import Units.variables as variables
import Units.clusters as clusters

battle_radius = 9

def timestep(unit):
	#print(building_assignment)
	# last check to make sure the right unit type is running this
	gc = variables.gc
	info = variables.info
	karbonite_locations = variables.karbonite_locations
	blueprinting_queue = variables.blueprinting_queue
	blueprinting_assignment = variables.blueprinting_assignment
	building_assignment = variables.building_assignment
	current_roles = variables.current_worker_roles
	num_enemies = variables.num_enemies

	planet = gc.planet()
	if planet == bc.Planet.Earth: 
		battle_locs = variables.earth_battles
		diagonal = variables.earth_diagonal
	else: 
		battle_locs = variables.mars_battles
		diagonal = variables.mars_diagonal

	earth_start_map = variables.earth_start_map

	if unit.unit_type != bc.UnitType.Worker:
		# prob should return some kind of error
		return
	my_team =variables.my_team

	my_location = unit.location

	# make sure unit can actually perform actions ie. not in garrison
	if not my_location.is_on_map():
		return

	if my_location.map_location().planet is bc.Planet.Mars:
		mine_mars(gc,unit)
		return


	my_role = "idle"
	for role in current_roles:
		if unit.id in current_roles[role]:
			my_role = role
	
	#print()
	#print("on unit #",unit.id, "position: ",unit.location.map_location(), "role: ",my_role)

	#print("KARBONITE: ",gc.karbonite()
	
	current_num_workers = info[0]	
	max_num_workers = get_replication_cap(gc,karbonite_locations, info, num_enemies)
	worker_spacing = 8

	#print("REPLICATION CAP: ",max_num_workers)
	# replicates if unit is able to (cooldowns, available directions etc.)	
	if current_num_workers < max_num_workers:
		try_replicate = replicate(gc,unit)
		if try_replicate:
			return

	# runs this block every turn if unit is miner
	if my_role == "miner":
		mine(gc,unit,earth_start_map,karbonite_locations,current_roles, building_assignment, battle_locs)
	# if unit is builder
	elif my_role == "builder":
		build(gc,unit,earth_start_map,building_assignment,current_roles)
	# if unit is blueprinter
	elif my_role == "blueprinter":
		blueprint(gc,unit,building_assignment,blueprinting_assignment,current_roles)
	# if unit is boarder
	elif my_role == "boarder": 
		board(gc,unit,current_roles)
	# if unit is idle
	elif my_role == "repairer":
		repair(gc,unit,current_roles)
	else: 	
		nearby= gc.sense_nearby_units_by_team(my_location.map_location(), worker_spacing, gc.team())

		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		#print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)
		movement.try_move(gc,unit,away_from_units)


# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def designate_roles():
	"""
	my_location = my_unit.location.map_location()
	#print(my_location)
	start_map = gc.starting_map(bc.Planet(0))
	nearby = gc.sense_nearby_units(my_location, my_unit.vision_range)
	"""
	gc = variables.gc
	blueprinting_queue = variables.blueprinting_queue
	blueprinting_assignment = variables.blueprinting_assignment
	building_assignment = variables.building_assignment
	current_roles = variables.current_worker_roles
	karbonite_locations = variables.karbonite_locations

	blueprint_count = 0
	factory_count = 0	
	rocket_count = 0
	rocket_ready_for_loading = False
	please_move = False	
	min_workers_per_building = 3
	recruitment_radius = 20
	workers = []
	worker_id_list = []
	earth = variables.earth
	start_map = variables.earth_start_map
	my_units = gc.my_units()

	for my_unit in my_units:

		if not my_unit.location.is_on_map():
			continue

		if my_unit.unit_type == bc.UnitType.Factory: # count ALL factories
			if not my_unit.structure_is_built():
				blueprint_count += 1
			factory_count += 1

		elif my_unit.unit_type == bc.UnitType.Rocket:
			if my_unit.structure_is_built() and len(my_unit.structure_garrison()) < my_unit.structure_max_capacity():
				rocket_ready_for_loading = True
				#print("UNITS IN GARRISON",unit.structure_garrison())

			if not my_unit.structure_is_built():
				if my_unit.id not in building_assignment.keys():
					building_assignment[my_unit.id] = []
				blueprint_count += 1
			rocket_count += 1

		elif my_unit.unit_type == bc.UnitType.Worker:
			workers.append(my_unit)
			worker_id_list.append(my_unit.id)

	update_for_dead_workers(gc,current_roles,blueprinting_queue,blueprinting_assignment,building_assignment)
	update_building_assignment(gc,building_assignment)

	max_num_builders = 5
	max_num_blueprinters = 2 #len(blueprinting_queue)*2 + 1 # at least 1 blueprinter, 2 blueprinters per cluster
	num_miners_per_deposit = 2 #approximate, just to cap miner count as deposit number decreases


	# this is put outside of the for loop at the bottom because this processing must happen before workers_dist_to_site is created
	for worker in workers:

		if not worker.location.is_on_map():
			continue

		worker_location = worker.location.map_location()

		"""
		# if it finds a nice location for building, put it in queue	
		if len(blueprinting_assignment) < blueprinting_queue_limit(gc):
			best_location_tuple = get_optimal_building_location(gc,start_map,worker_location,karbonite_locations,blueprinting_queue,blueprinting_assignment)
			best_location = bc.MapLocation(earth,best_location_tuple[0],best_location_tuple[1])
			if is_valid_blueprint_location(gc,start_map,worker_location,blueprinting_queue,blueprinting_assignment):	
				if can_blueprint_rocket(gc,blueprinting_queue):
					new_site = BuildSite(best_location,bc.UnitType.Rocket)
					blueprinting_assignment[worker.id] = new_site
					#blueprinting_queue.append(new_site)
				elif can_blueprint_factory(gc,blueprinting_queue):
					new_site = BuildSite(best_location,bc.UnitType.Factory)
					blueprinting_assignment[worker.id] = new_site
					#blueprinting_queue.append(new_site)	
					#print(worker.id," just added to building queue",best_location)
		"""

	closest_workers_to_blueprint = {} # dictionary mapping blueprint_id to a list of worker id sorted by distance to the blueprint
	workers_in_recruitment_range = {}
	for building_id in building_assignment:

		assigned_workers = building_assignment[building_id]
		blueprint_location = gc.unit(building_id).location.map_location()
		workers_per_building = get_workers_per_building(gc,start_map,blueprint_location)

		if len(assigned_workers) < workers_per_building:
			workers_dist_to_blueprint_sorted = sorted(workers,key=lambda unit:unit.location.map_location().distance_squared_to(blueprint_location))
			closest_worker_ids = []
			for worker_unit in workers_dist_to_blueprint_sorted:
				if worker_unit.id in current_roles["blueprinter"] or worker_unit.id in current_roles["builder"]:
					continue
				if building_id not in workers_in_recruitment_range:
					if worker_unit.location.map_location().distance_squared_to(blueprint_location) > recruitment_radius:
						workers_in_recruitment_range[building_id] = len(closest_worker_ids)

				closest_worker_ids.append(worker_unit.id)
			closest_workers_to_blueprint[building_id] = closest_worker_ids

	#print("closest workers to blueprint",closest_workers_to_blueprint)
	#print("workers in recruitment range",workers_in_recruitment_range)

	
	closest_workers_to_site = {} # dictionary mapping blueprint_id to a list of worker id sorted by distance to the blueprint

	for assigned_blueprinting_site in blueprinting_queue:
		assigned_location = assigned_blueprinting_site.map_location
		workers_dist_to_site_sorted = sorted(workers,key=lambda unit:unit.location.map_location().distance_squared_to(assigned_location))
		closest_worker_ids = list(map(lambda unit: unit.id, workers_dist_to_site_sorted))

		for blueprinter_id in current_roles["blueprinter"]:
			if blueprinter_id in closest_worker_ids:
				closest_worker_ids.remove(blueprinter_id)

		closest_workers_to_site[assigned_blueprinting_site] = closest_worker_ids


	#print("blueprinting_assignment",blueprinting_assignment)
	#print("building_assignment",building_assignment)
	#print("blueprinting_queue",blueprinting_queue)


	######################
	## ROLE DESIGNATION ##
	######################
	for worker in workers:

		worker_location = worker.location.map_location()
		open_slots_to_build = False
		unit_build_override = False
		assigned_building_id = None
		my_role = "idle"
		role_revised = False

		## DESIGNATION FOR ALREADY ASSIGNED WORKERS ##
		for role in current_roles.keys():
			if worker.id in current_roles[role]:
				# code to prevent workers from mining in front of building entrances
				my_role = role
				#print("worker id",worker.id,"is_role_assigned",is_role_assigned)
				break

		# recruit nearby workers to finish building
		if my_role != "blueprinter" and my_role != "builder":
			for building_id in building_assignment:
				assigned_workers = building_assignment[building_id]
				assigned_location = gc.unit(building_id).location.map_location()
				workers_per_building = get_workers_per_building(gc,start_map,assigned_location)
				num_open_slots_to_build = workers_per_building - len(assigned_workers)

				if num_open_slots_to_build > 0:
					closest_worker_list = closest_workers_to_blueprint[building_id]
					if building_id in workers_in_recruitment_range:
						num_workers_in_range = workers_in_recruitment_range[building_id]
					else:
						num_workers_in_range = len(closest_worker_list)

					if len(assigned_workers) > min_workers_per_building and num_workers_in_range == 0:
						continue
					if num_open_slots_to_build <= num_workers_in_range:
						recruitable_workers = closest_worker_list[:num_open_slots_to_build]
					else:
						optimal_number = max(min_workers_per_building,num_workers_in_range)
						recruitable_workers = closest_worker_list[:optimal_number]

					if worker.id in recruitable_workers:
						if my_role != "idle" and worker.id in current_roles[my_role]:
							current_roles[my_role].remove(worker.id)
						current_roles["builder"].append(worker.id)
						building_assignment[building_id].append(worker.id)
						role_revised = True
						my_role = "builder"
						break

		# recruit nearby worker to place down a blueprint
		if my_role != "blueprinter" and not role_revised:
			building_in_progress_count = len(building_assignment.keys()) + len(blueprinting_assignment.keys())
			if building_in_progress_count < building_in_progress_cap(gc):

				# if it finds a nice location for building, put it in queue	
				if len(blueprinting_assignment) < blueprinting_queue_limit(gc):
					best_location_tuple = get_optimal_building_location(gc,start_map,worker_location,karbonite_locations,blueprinting_queue,blueprinting_assignment)

					if best_location_tuple is not None:
						best_location = bc.MapLocation(earth, best_location_tuple[0], best_location_tuple[1])

						if can_blueprint_rocket(gc,rocket_count):

							if my_role != "idle" and worker.id in current_roles[my_role]:
								current_roles[my_role].remove(worker.id)

							current_roles["blueprinter"].append(worker.id)
							new_site = BuildSite(best_location,bc.UnitType.Rocket)
							blueprinting_assignment[worker.id] = new_site
							my_role = "blueprinter"
							#blueprinting_queue.append(new_site)
						elif can_blueprint_factory(gc,factory_count):

							if my_role != "idle" and worker.id in current_roles[my_role]:
								current_roles[my_role].remove(worker.id)

							current_roles["blueprinter"].append(worker.id)
							new_site = BuildSite(best_location,bc.UnitType.Factory)
							blueprinting_assignment[worker.id] = new_site
							my_role = "blueprinter"
							#blueprinting_queue.append(new_site)	
							#print(worker.id," just added to building queue",best_location)


				"""
				for site in blueprinting_queue:
					closest_worker_list = closest_workers_to_site[site]
					if worker.id in closest_worker_list and worker.id == closest_worker_list[0]:
						if my_role != "idle" and worker.id in current_roles[my_role]:
							current_roles[my_role].remove(worker.id)
						current_roles["blueprinter"].append(worker.id)
						blueprinting_queue.remove(site)
						blueprinting_assignment[worker.id] = site
						my_role = "blueprinter"
						break
						#print(unit.id, "has been assigned to this building ",closest_building_site)
				"""


		## DESIGNATION FOR UNASSIGNED WORKERS ##
		if my_role != "idle":
			continue

		num_miners = len(current_roles["miner"])
		num_blueprinters = len(current_roles["blueprinter"])
		num_builders = len(current_roles["builder"])
		num_boarders = len(current_roles["boarder"])
		num_repairers = len(current_roles["repairer"])


		# early game miner production
		if gc.karbonite() < 100 and num_miners < 2:
			new_role = "miner"
		# become builder when there are available blueprints
		elif num_miners_per_deposit * len(karbonite_locations) > num_miners:
			new_role = "miner"
		elif rocket_ready_for_loading:
			new_role = "boarder"
		else:
			new_role = "repairer"

		current_roles[new_role].append(worker.id)

		#print(new_role)

def get_workers_per_building(gc,start_map,building_location):
	max_workers_per_building = 6
	num_adjacent_spaces = 0
	adjacent_locations = gc.all_locations_within(building_location,2)

	for location in adjacent_locations:
		if building_location == location: continue

		if start_map.is_passable_terrain_at(location):
			num_adjacent_spaces += 1

	return min(num_adjacent_spaces,max_workers_per_building)



def update_for_dead_workers(gc,current_roles,blueprinting_queue,blueprinting_assignment,building_assignment):
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
		
	
def get_replication_cap(gc,karbonite_locations, info, num_enemies):
	#print("KARBONITE INFO LENGTH: ",len(karbonite_locations))
	#print(len(karbonite_locations))
	if num_enemies > 2*sum(info[1:4])/3:
		#print('replication cap yes')
		return 3
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
	
def mine(gc,my_unit,start_map,karbonite_locations,current_roles, building_assignment, battle_locs):
	my_location = my_unit.location
	position = my_location.map_location()
	closest_deposit = get_closest_deposit(gc,my_unit,karbonite_locations)
	#check to see if there even are deposits
	if start_map.on_map(closest_deposit):
		direction_to_deposit = position.direction_to(closest_deposit)
		#print(unit.id, "is trying to mine at", direction_to_deposit)

		enemy_units = gc.sense_nearby_units_by_team(position, my_unit.vision_range, sense_util.enemy_team(gc))
		dangerous_types = [bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage]
		dangerous_enemies = []

		# only adds enemy units that can attack
		for unit in enemy_units:
			enemy_loc = unit.location.map_location()
			add_loc = evaluate_battle_location(gc, enemy_loc, battle_locs)
			if add_loc:
				battle_locs[(enemy_loc.x, enemy_loc.y)] = clusters.Cluster(allies=set(),enemies=set([unit.id]))
			if unit.unit_type in dangerous_types:
				dangerous_enemies.append(unit)

		if len(dangerous_enemies) > 0:
			dir = sense_util.best_available_direction(gc, my_unit, dangerous_enemies)
			movement.try_move(gc, my_unit, dir)
		
		elif position.is_adjacent_to(closest_deposit) or position == closest_deposit:
			# mine if adjacent to deposit
			if gc.can_harvest(my_unit.id,direction_to_deposit):
				gc.harvest(my_unit.id,direction_to_deposit)
				current_roles["miner"].remove(my_unit.id)
				#print(unit.id," just harvested!")
		else:
			# move toward deposit
			movement.try_move(gc,my_unit,direction_to_deposit)
	else:
		current_roles["miner"].remove(my_unit.id)
		#print(unit.id," no deposits around")

def evaluate_battle_location(gc, loc, battle_locs):
	"""
	Chooses whether or not to add this enemy's location as a new battle location.
	"""
	# units_near = gc.sense_nearby_units_by_team(loc, battle_radius, constants.enemy_team)
	valid = True
	locs_near = gc.all_locations_within(loc, battle_radius)
	for near in locs_near:
		near_coords = (near.x, near.y)
		if near_coords in battle_locs: 
			valid = False
	
	return valid

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
	start_map = variables.mars_start_map
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

def assign_unit_to_build(gc,my_unit,start_map,building_assignment):
	my_location = my_unit.location.map_location()
	available_blueprints = []

	for blueprint_id in building_assignment:
		possible_blueprint = gc.unit(blueprint_id)
		workers_per_building = get_workers_per_building(gc,start_map,possible_blueprint.location.map_location())
		if len(building_assignment[blueprint_id]) < workers_per_building:
			#print("available blueprints to work on")
			available_blueprints.append(possible_blueprint)

	smallest_distance = float('inf')
	closest_building = None
	#print(len(blueprints))
	for blueprint in available_blueprints:
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

def build(gc,my_unit,start_map,building_assignment,current_roles):
	my_location = my_unit.location.map_location()
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
				#print(my_unit.id,"assigned_building was already built")
				del building_assignment[building_id]
				assigned_building = assign_unit_to_build(gc,my_unit,start_map,building_assignment)
				unit_was_not_assigned = False
				break
			else:
				unit_was_not_assigned = False

	if unit_was_not_assigned:
		assigned_building = assign_unit_to_build(gc,my_unit,start_map,building_assignment)


	if assigned_building is None:
		#print(my_unit.id, "there are no blueprints around")
		current_roles["builder"].remove(my_unit.id)
		return

	#print("unit has been assigned to build at",assigned_building.location.map_location())
	assigned_location = assigned_building.location.map_location()
	if my_location.is_adjacent_to(assigned_location):

		if gc.can_build(my_unit.id,assigned_building.id):
			#print(my_unit.id, "is building factory at ",assigned_location)
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



def is_valid_blueprint_location(gc,start_map,location,blueprinting_queue,blueprinting_assignment):
	blueprint_spacing = 10
	nearby = gc.sense_nearby_units(location,blueprint_spacing)

	if start_map.on_map(location) and start_map.is_passable_terrain_at(location):
		for other in nearby:
			if other.unit_type == bc.UnitType.Factory or other.unit_type == bc.UnitType.Rocket:
				return False
		for site in blueprinting_queue:
			if location.distance_squared_to(site.map_location) < blueprint_spacing:
				return False
		for worker_id in blueprinting_assignment:
			assigned_site = blueprinting_assignment[worker_id]
			if location.distance_squared_to(assigned_site.map_location) < blueprint_spacing:
				return False
		return True

	return False


# generates locations to build factories that are close to karbonite deposits	
def get_optimal_building_location(gc,start_map,center,karbonite_locations,blueprinting_queue,blueprinting_assignment):
	potential_locations = []
	karbonite_adjacent_locations = {}
	no_deposits_located = True

	for location in gc.all_locations_within(center,20):
		if is_valid_blueprint_location(gc,start_map,location,blueprinting_queue,blueprinting_assignment):
			loc_key = (location.x,location.y)

			if loc_key in karbonite_locations:
				if karbonite_locations[loc_key] > 0:
					continue
			for adjacent_location in gc.all_locations_within(location,2):
				if location == adjacent_location: continue

				adj_key = (adjacent_location.x,adjacent_location.y)

				if adj_key in karbonite_locations:
					karbonite_value = karbonite_locations[adj_key]
				else:
					karbonite_value = 0

				if loc_key not in karbonite_adjacent_locations:
					karbonite_adjacent_locations[loc_key] = karbonite_value
				else:
					karbonite_adjacent_locations[loc_key] += karbonite_value

			if karbonite_adjacent_locations[loc_key] > 0:
				no_deposits_located = False

	if len(karbonite_adjacent_locations) == 0:
		return None
	elif no_deposits_located:
		for default_location in gc.all_locations_within(center,2):
			if is_valid_blueprint_location(gc,start_map,default_location,blueprinting_queue,blueprinting_assignment):
				return (default_location.x,default_location.y)
	
	return max(list(karbonite_adjacent_locations.keys()),key=lambda loc:karbonite_adjacent_locations[loc])


# function to flexibly determine when a good time to expand factories
def can_blueprint_factory(gc,factory_count):
	return factory_count < get_factory_limit()

def can_blueprint_rocket(gc,rocket_count):
	return gc.research_info().get_level(bc.UnitType.Rocket) > 0 and rocket_count < get_rocket_limit()

def blueprinting_queue_limit(gc):
	return 1

def get_factory_limit():
	return 4

def get_rocket_limit():
	return 2

def get_closest_site(my_unit,blueprinting_queue):
	my_location = my_unit.location.map_location()
	
	smallest_distance = float('inf')
	closest_site = None	
	for site in blueprinting_queue:
		distance_to_site = my_location.distance_squared_to(site.map_location) 
		if distance_to_site < smallest_distance:
			smallest_distance = distance_to_site
			closest_site = site
	return closest_site

# controls how many buildings we can have in progress at a time, can modify this to scale with karbonite number, round # or number of units (enemy or ally)
def building_in_progress_cap(gc):
	return 2


def blueprint(gc,my_unit,building_assignment,blueprinting_assignment,current_roles):
	my_location = my_unit.location.map_location()
	directions = list(bc.Direction)

	# assign this unit to build a blueprint, if nothing to build just move away from other factories
	if my_unit.id not in blueprinting_assignment:
		# print(my_unit.id,"currently has no assigned site")
		current_roles["blueprinter"].remove(my_unit.id)

	# build blueprint in assigned square
	if my_unit.id in blueprinting_assignment:
		assigned_site = blueprinting_assignment[my_unit.id]

		# if my_unit.id in blueprinting_assignment:
		# 	print("unit",my_unit.id,"blueprinting at",blueprinting_assignment[my_unit.id])
		#print(unit.id, "is assigned to building in", assigned_site.map_location)
		direction_to_site = my_location.direction_to(assigned_site.map_location)

		if my_location.is_adjacent_to(assigned_site.map_location):
			if gc.can_blueprint(my_unit.id, assigned_site.building_type, direction_to_site):
				gc.blueprint(my_unit.id, assigned_site.building_type, direction_to_site)
				new_blueprint = gc.sense_unit_at_location(assigned_site.map_location)

				# update shared data structures
				building_assignment[new_blueprint.id] = [] # initialize new building
				del blueprinting_assignment[my_unit.id]
				current_roles["blueprinter"].remove(my_unit.id)
				current_roles["builder"].append(my_unit.id)
				#print(my_unit.id, " just created a blueprint!")
			#else:
			#print(unit.id, "can't build but is right next to assigned site")
		elif my_location == assigned_site.map_location:
			# when unit is currently on top of the queued building site
			d = random.choice(variables.directions)
			movement.try_move(gc,my_unit,d)
		else:
			# move toward queued building site
			next_direction = my_location.direction_to(assigned_site.map_location)	
			movement.try_move(gc,my_unit,next_direction)
		

class BuildSite:
	def __init__(self,map_location,building_type):
		self.map_location = map_location
		self.building_type = building_type

	def get_map_location(self):
		return self.map_location
	
	def get_building_type(self):
		return self.building_type

	def __str__(self):
		return "{map_location : " + str(self.map_location) + ", building_type : " + str(self.building_type) + " }"

	def __repr__(self):
		return "{map_location : " + str(self.map_location) + ", building_type : " + str(self.building_type) + " }"

	def __eq__(self,other):
		return self.map_location == other.map_location and self.building_type == other.building_type

	def __hash__(self):
		return self.map_location.x + self.map_location.y

