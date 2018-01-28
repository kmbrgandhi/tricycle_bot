import battlecode as bc
import random
import sys
import traceback
import Units.sense_util as sense_util
import Units.movement as movement
import Units.explore as explore
import Units.Ranger as Ranger
import Units.variables as variables
import time

battle_radius = 10
if variables.curr_planet==bc.Planet.Earth:
	passable_locations = variables.passable_locations_earth
else:
	passable_locations = variables.passable_locations_mars

def timestep(unit):
	#print(building_assignment)
	# last check to make sure the right unit type is running this
	start_time = time.time()
	gc = variables.gc
	info = variables.info
	karbonite_locations = variables.karbonite_locations
	blueprinting_queue = variables.blueprinting_queue
	blueprinting_assignment = variables.blueprinting_assignment
	building_assignment = variables.building_assignment
	current_roles = variables.current_worker_roles
	num_enemies = variables.num_enemies

	earth_start_map = variables.earth_start_map
	unit_types = variables.unit_types

	next_turn_battle_locs = variables.next_turn_battle_locs
	quadrant_battles = variables.quadrant_battle_locs

	if unit.unit_type != unit_types["worker"]:
		# prob should return some kind of error
		return

	# make sure unit can actually perform actions ie. not in garrison
	if not unit.location.is_on_map():
		return

	## Add new ones to unit_locations, else just get the location
	if variables.curr_planet == bc.Planet.Earth: 
		quadrant_size = variables.earth_quadrant_size
	else:
		quadrant_size = variables.mars_quadrant_size

	if unit.id not in variables.unit_locations:
		loc = unit.location.map_location()
		variables.unit_locations[unit.id] = (loc.x,loc.y)
		f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
		quadrant_battles[f_f_quad].add_ally(unit.id, "worker")

	my_location = unit.location.map_location()

	if my_location.planet is variables.mars:
		if gc.round()>720:
			try_replicate = replicate(gc, unit)
			if try_replicate:
				return
		mine_mars(gc,unit,my_location)
		return
	if gc.round() > 315 and not variables.saviour_worker and near_factory(my_location):
		variables.saviour_worker = True
		variables.saviour_worker_id = unit.id
    # TO DO: ADD CHECK THAT HE ISN'T TOO CLOSE TO ENEMIES.
	if variables.saviour_worker_id == unit.id:
		total_units = [variables.info[1] + variables.producing[1], variables.info[2] +variables.producing[2],
					   variables.info[3] + variables.producing[3], variables.info[4] + variables.producing[4]]
		if sum(total_units) < 0.9 * variables.num_enemies:
			do_nothing = True
		elif variables.saviour_blueprinted:
			try:
				corr_rocket = gc.unit(variables.saviour_blueprinted_id)
				if not corr_rocket.structure_is_built():
					if gc.can_build(unit.id, variables.saviour_blueprinted_id):
						gc.build(unit.id, variables.saviour_blueprinted_id)
				else:
					if gc.can_load(variables.saviour_blueprinted_id, unit.id):
						gc.load(variables.saviour_blueprinted_id, unit.id)
						variables.saviour_worker_id = None
						variables.saviour_worker = False
						variables.saviour_blueprinted = False
						variables.saviour_blueprinted_id = None
						variables.num_unsuccessful_savior = 0
						variables.saviour_time_between =0
			except:
				#print('got an exception')
				variables.saviour_worker_id = None
				variables.saviour_worker = False
				variables.saviour_blueprinted = False
				variables.saviour_blueprinted_id = None
				variables.num_unsuccessful_savior = 0
				variables.saviour_time_between =0
		elif variables.saviour_time_between>0:
			blueprinted = False
			for dir in variables.directions:
				map_loc = my_location.add(dir)
				map_loc_coords = (map_loc.x, map_loc.y)
				if map_loc_coords in passable_locations and passable_locations[map_loc_coords]:
					if gc.can_blueprint(unit.id, variables.unit_types["rocket"], dir):
						gc.blueprint(unit.id, variables.unit_types["rocket"], dir)
						variables.saviour_blueprinted = True
						new_blueprint = gc.sense_unit_at_location(map_loc)
						variables.saviour_blueprinted_id= new_blueprint.id
						variables.all_building_locations[variables.saviour_blueprinted_id] = map_loc
						blueprinted = True
						break
					elif variables.num_unsuccessful_savior > 5:
						variables.saviour_worker_id = None
						variables.saviour_worker = False
						variables.saviour_blueprinted = False
						variables.saviour_blueprinted_id = None
						variables.num_unsuccessful_savior = 0
						variables.saviour_time_between = 0
						if gc.has_unit_at_location(map_loc) and gc.karbonite()>150:
							in_the_way_unit = gc.sense_unit_at_location(map_loc)
							gc.disintegrate_unit(in_the_way_unit.id)
							if gc.can_blueprint(unit.id, variables.unit_types["rocket"], dir):
								gc.blueprint(unit.id, variables.unit_types["rocket"], dir)
								variables.saviour_blueprinted = True
								new_blueprint = gc.sense_unit_at_location(map_loc)
								variables.saviour_blueprinted_id = new_blueprint.id
								variables.all_building_locations[variables.saviour_blueprinted_id] = map_loc
								blueprinted = True
								break

			if not blueprinted and gc.karbonite() > 150:
				variables.num_unsuccessful_savior+=1
		else:
			variables.saviour_time_between+=1

	my_role = "idle"
	for role in current_roles:
		if unit.id in current_roles[role]:
			my_role = role
	

	# updating worker harvest amount
	if variables.worker_harvest_amount == 0:
		#print("updated worker harvest amount")
		variables.worker_harvest_amount = unit.worker_harvest_amount()


	#print()
	#print("on unit #",unit.id, "position: ",my_location, "role: ",my_role)
	#print("KARBONITE: ",gc.karbonite()
	
	current_num_workers = info[0]
	worker_starting_cap = variables.worker_starting_cap

	#print("max starting worker cap",worker_starting_cap)
	worker_spacing = 8

	if current_num_workers < worker_starting_cap and gc.round() <= 100:
		try_replicate = replicate(gc,unit)
		#print("still replicating??",try_replicate)
		if try_replicate:
			return

	# runs this block every turn if unit is miner
	if my_role == "miner":
		# start_time = time.time()
		mine(gc,unit,my_location,earth_start_map,karbonite_locations,current_roles, building_assignment, next_turn_battle_locs)
		#print("mining time: ",time.time() - start_time)
	# if unit is builder
	elif my_role == "builder":
		# start_time = time.time()
		build(gc,unit,my_location,earth_start_map,building_assignment,current_roles)
		#print("building time: ",time.time() - start_time)
	# if unit is blueprinter
	elif my_role == "blueprinter":
		# start_time = time.time()
		blueprint(gc,unit,my_location,karbonite_locations,building_assignment,blueprinting_assignment,current_roles)
		#print("blueprinting time: ",time.time() - start_time)
	# if unit is boarder
	elif my_role == "boarder": 
		board(gc,unit,my_location,current_roles)
	# if unit is idle
	elif my_role == "repairer":
		repair(gc,unit,my_location,current_roles)
	else: 	
		nearby= gc.sense_nearby_units_by_team(my_location, worker_spacing, variables.my_team)

		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		#print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)

		movement.try_move(gc,unit,(my_location.x,my_location.y),away_from_units)

def check_if_saviour_died():
	for my_unit in variables.my_units:
		if variables.saviour_worker_id ==my_unit.id:
			return True
	return False

def near_factory(my_location):
	my_location_coords = (my_location.x, my_location.y)
	for coords in explore.coord_neighbors(my_location_coords, diff = explore.diffs_50):
		if coords in passable_locations and passable_locations[coords]:
			map_loc = bc.MapLocation(bc.Planet.Earth, coords[0], coords[1])
			if variables.gc.can_sense_location(map_loc) and variables.gc.has_unit_at_location(map_loc):
				unit = variables.gc.sense_unit_at_location(map_loc)
				if unit.unit_type == variables.unit_types["factory"]:
					return True
	return False

# returns whether unit is a miner or builder, currently placeholder until we can use team-shared data to designate unit roles
def designate_roles():

	my_units = variables.my_units
	unit_types = variables.unit_types
	current_roles = variables.current_worker_roles

	if variables.curr_planet == bc.Planet.Mars:

		workers = []
		worker_id_list = []
		for my_unit in my_units:

			if not my_unit.location.is_on_map():
				continue

			elif my_unit.unit_type == unit_types["worker"]:
				workers.append(my_unit)
				worker_id_list.append(my_unit.id)
		## DESIGNATION FOR ALREADY ASSIGNED WORKERS ##
		for worker in workers:
			if worker.id not in current_roles["miner"]:
				current_roles["miner"].append(worker.id)
	else:
		gc = variables.gc
		blueprinting_queue = variables.blueprinting_queue
		blueprinting_assignment = variables.blueprinting_assignment
		building_assignment = variables.building_assignment
		current_roles = variables.current_worker_roles
		karbonite_locations = variables.karbonite_locations
		unit_types = variables.unit_types
		invalid_building_locations = variables.invalid_building_locations
		all_building_locations = variables.all_building_locations

		blueprint_count = 0
		factory_count = 0	
		damaged_factory_count = 0
		rocket_count = 0
		damaged_rocket_count = 0
		rocket_ready_for_loading = False
		please_move = False

		workers = []
		worker_id_list = []
		damaged_buildings = []
		earth = variables.earth
		start_map = variables.earth_start_map
		my_units = variables.my_units
		for my_unit in my_units:

			if not my_unit.location.is_on_map():
				continue

			if my_unit.unit_type == unit_types["factory"]: # count ALL factories
				if not my_unit.structure_is_built():
					blueprint_count += 1
				else:
					if my_unit.health < my_unit.max_health:
						damaged_buildings.append(my_unit)
						damaged_factory_count += 1
				factory_count += 1

			elif my_unit.unit_type == unit_types["rocket"]:
				if my_unit.structure_is_built() and len(my_unit.structure_garrison()) < my_unit.structure_max_capacity():
					rocket_ready_for_loading = True
					#print("UNITS IN GARRISON",unit.structure_garrison())

				if not my_unit.structure_is_built():
					if my_unit.id not in building_assignment.keys():
						building_assignment[my_unit.id] = []
					blueprint_count += 1
				else:
					if my_unit.health < my_unit.max_health:
						damaged_buildings.append(my_unit)
						damaged_rocket_count += 1
				rocket_count += 1

			elif my_unit.unit_type == unit_types["worker"]:
				workers.append(my_unit)
				worker_id_list.append(my_unit.id)

		for worker_id in blueprinting_assignment:
			build_site = blueprinting_assignment[worker_id]
			if build_site.building_type == variables.unit_types["factory"]:
				factory_count += 1
			elif build_site.building_type == variables.unit_types["rocket"]:
				rocket_count += 1

		update_for_dead_workers(gc,current_roles,blueprinting_queue,blueprinting_assignment,building_assignment)

		update_building_assignment(gc,building_assignment,blueprinting_assignment)
		update_deposit_info(gc,karbonite_locations)


		max_num_builders = 5
		max_num_blueprinters = 2 #len(blueprinting_queue)*2 + 1 # at least 1 blueprinter, 2 blueprinters per cluster
		num_miners_per_deposit = 2 #approximate, just to cap miner count as deposit number decreases


		closest_workers_to_blueprint = {} # dictionary mapping blueprint_id to a list of worker id sorted by distance to the blueprint

		for building_id in building_assignment:
			assigned_workers = building_assignment[building_id]
			blueprint_location = gc.unit(building_id).location.map_location()
			workers_per_building = get_workers_per_building(gc,start_map,blueprint_location)

			if len(assigned_workers) < workers_per_building:
				workers_dist_to_blueprint_sorted = sorted(workers,key=lambda unit:sense_util.distance_squared_between_maplocs(unit.location.map_location(), blueprint_location))
				closest_worker_ids = []
				for worker_unit in workers_dist_to_blueprint_sorted:
					if worker_unit.id in current_roles["blueprinter"] or worker_unit.id in current_roles["builder"]:
						continue

					if sense_util.distance_squared_between_maplocs(worker_unit.location.map_location(), blueprint_location) <= variables.recruitment_radius:
						closest_worker_ids.append(worker_unit.id)
				closest_workers_to_blueprint[building_id] = closest_worker_ids


		closest_workers_to_damaged_building = {}

		for damaged_building in damaged_buildings:
			damaged_building_location = damaged_building.location.map_location()
			workers_dist_to_building_sorted = sorted(workers,key=lambda unit:sense_util.distance_squared_between_maplocs(unit.location.map_location(), damaged_building_location))
			closest_worker_ids = []
			for worker_unit in workers_dist_to_building_sorted:
				if worker_unit.id in current_roles["blueprinter"] or worker_unit.id in current_roles["builder"] or worker_unit.id in current_roles["repairer"]:
					continue

				if sense_util.distance_squared_between_maplocs(worker_unit.location.map_location(), damaged_building_location) <= 2:
					closest_worker_ids.append(worker_unit.id)

			closest_workers_to_damaged_building[damaged_building.id] = closest_worker_ids


		#print("closest workers to blueprint",closest_workers_to_blueprint)
		#print("workers in recruitment range",workers_in_recruitment_range)

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

			if my_role != "repairer" and my_role != "builder" and my_role != "blueprinter":
				for building_id in closest_workers_to_damaged_building:
					if worker.id in closest_workers_to_damaged_building[building_id]:
						if my_role != "idle" and worker.id in current_roles[my_role]:
							current_roles[my_role].remove(worker.id)
						current_roles["repairer"].append(worker.id)
						role_revised = True
						my_role = "repairer"


			#print("unit: ",worker.id,my_role)
			# recruit nearby workers to finish building
			if my_role != "blueprinter" and my_role != "builder" and not role_revised:
				for building_id in building_assignment:
					assigned_workers = building_assignment[building_id]
					assigned_location = gc.unit(building_id).location.map_location()
					workers_per_building = get_workers_per_building(gc,start_map,assigned_location)
					#print("workers per building",workers_per_building)
					num_open_slots_to_build = workers_per_building - len(assigned_workers)


					if num_open_slots_to_build > 0 and building_id in closest_workers_to_blueprint:

						closest_worker_list = closest_workers_to_blueprint[building_id]
						recruitable_workers = closest_worker_list[:min(num_open_slots_to_build,len(closest_worker_list))]

						if worker.id in recruitable_workers:
							if my_role != "idle" and worker.id in current_roles[my_role]:
								current_roles[my_role].remove(worker.id)
							current_roles["builder"].append(worker.id)
							building_assignment[building_id].append(worker.id)
							role_revised = True
							my_role = "builder"
							break

			# recruit nearby worker to place down a blueprint
			if my_role != "blueprinter" and my_role != "builder" and not role_revised:
				building_in_progress_count = len(building_assignment.keys()) + len(blueprinting_assignment.keys())
				#print("building_assignment",building_assignment)
				#print("blueprinting_assignment",blueprinting_assignment)
				#print("building_in_progress_count",building_in_progress_count)
				if building_in_progress_count < building_in_progress_cap(gc):

					if can_blueprint_rocket(gc,rocket_count):

						best_location_tuple = get_optimal_building_location(gc,start_map,worker_location,unit_types["rocket"],karbonite_locations,blueprinting_queue,blueprinting_assignment)
						#print("best location is",best_location_tuple)
						#print("time for building location",time.time() - inside_time)
						if best_location_tuple is not None:
							best_location = bc.MapLocation(earth, best_location_tuple[0], best_location_tuple[1])

							if my_role != "idle" and worker.id in current_roles[my_role]:
								current_roles[my_role].remove(worker.id)

							current_roles["blueprinter"].append(worker.id)
							new_site = BuildSite(best_location,unit_types["rocket"])
							blueprinting_assignment[worker.id] = new_site
							rocket_count += 1

							nearby_sites = adjacent_locations(best_location)

							for site in nearby_sites:
								site_coord = (site.x,site.y)
								if site_coord not in passable_locations or not passable_locations[site_coord]: continue
								if invalid_building_locations[site_coord]:
									invalid_building_locations[site_coord] = False

							my_role = "blueprinter"
							#blueprinting_queue.append(new_site)
					elif can_blueprint_factory(gc,factory_count):

						best_location_tuple = get_optimal_building_location(gc,start_map,worker_location,unit_types["factory"],karbonite_locations,blueprinting_queue,blueprinting_assignment)
						#print(worker.id,"building in ",best_location_tuple)
						if best_location_tuple is not None:
							best_location = bc.MapLocation(earth, best_location_tuple[0], best_location_tuple[1])
							#print(worker.id,"can build a factory")
							if my_role != "idle" and worker.id in current_roles[my_role]:
								current_roles[my_role].remove(worker.id)

							current_roles["blueprinter"].append(worker.id)
							new_site = BuildSite(best_location,unit_types["factory"])
							blueprinting_assignment[worker.id] = new_site
							factory_count += 1

							nearby_sites = factory_spacing_locations(best_location)

							for site in nearby_sites:
								site_coord = (site.x,site.y)
								if site_coord not in passable_locations or not passable_locations[site_coord]: continue
								if invalid_building_locations[site_coord]:
									invalid_building_locations[site_coord] = False

							my_role = "blueprinter"
							#blueprinting_queue.append(new_site)	
							#print(worker.id," just added to building queue",best_location)

							#print(worker.id,"cannot build a rocket or factory")
					#print(worker.id,"cannot build a rocket or factory")
			## DESIGNATION FOR UNASSIGNED WORKERS ##
			if my_role != "idle":
				continue

			num_miners = len(current_roles["miner"])
			num_blueprinters = len(current_roles["blueprinter"])
			num_builders = len(current_roles["builder"])
			num_boarders = len(current_roles["boarder"])
			num_repairers = len(current_roles["repairer"])


			# early game miner production
			if rocket_ready_for_loading:
				new_role = "boarder"
			elif len(variables.karbonite_locations) > 0:
				new_role = "miner"
			else:
				new_role = "repairer"
			"""
			if num_miners_per_deposit * len(karbonite_locations) > num_miners:
				new_role = "miner"
			elif rocket_ready_for_loading:
				new_role = "boarder"
			else:
				new_role = "repairer"
			"""
			current_roles[new_role].append(worker.id)
	#print("current roles",variables.current_worker_roles)


# parameters: amount of karbonite on the map, factory number ( diff behavior before and after our first factory), 
def get_worker_cap(gc,karbonite_locations, info, num_enemies):
	#print("KARBONITE INFO LENGTH: ",len(karbonite_locations))
	#print("number of reachable deposits",len(karbonite_locations))

	if num_enemies > 2*sum(info[1:4])/3:
		#print('replication cap yes')
		return 6
	elif info[5] >= 1:
		return min(5 + float(len(karbonite_locations)/30),20)
	else:
		return min(3 + float(len(karbonite_locations)/3),6)




def get_workers_per_building(gc,start_map,building_location):
	max_workers_per_building = 4
	num_adjacent_spaces = 0
	adjacent = adjacent_locations(building_location)
	self_coord = (building_location.x,building_location.y)

	#print("checking workers per building")
	for location in adjacent:
		location_coord = (location.x,location.y)
		if location_coord not in passable_locations or location_coord == self_coord: continue
		if passable_locations[location_coord]:
			num_adjacent_spaces += 1

	return min(num_adjacent_spaces,max_workers_per_building)



def update_for_dead_workers(gc,current_roles,blueprinting_queue,blueprinting_assignment,building_assignment):
	live_unit_ids = [unit.id for unit in gc.my_units()]
	
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


def repair(gc, unit, my_location, current_roles):
	map_loc = my_location
	closest = None
	closest_dist = float('inf')
	closest_map_loc = None
	for fact in variables.my_units:
		if fact.unit_type == variables.unit_types["factory"]:
			if fact.structure_is_built() and fact.health < fact.max_health:
				loc = fact.location.map_location()
				dist = sense_util.distance_squared_between_maplocs(map_loc, loc)
				if dist < closest_dist:
					closest = fact
					closest_dist = dist
					closest_map_loc = loc

	if closest is not None:
		if gc.can_repair(unit.id, closest.id):
			gc.repair(unit.id, closest.id)
		else:
			try_move_smartly(unit, map_loc, closest_map_loc)
	else:
		current_roles["repairer"].remove(unit.id)

def try_move_smartly(unit, map_loc1, map_loc2):
	if variables.gc.is_move_ready(unit.id):
		our_coords = (map_loc1.x, map_loc1.y)
		target_coords = (map_loc2.x, map_loc2.y)
		#print(target_coords)
		our_coords_val = Ranger.get_coord_value(our_coords)
		#print(our_coords_val)
		target_coords_val = Ranger.get_coord_value(target_coords)
		#print(target_coords_val)
		bfs_array = variables.bfs_array
		if bfs_array[our_coords_val, target_coords_val] != float('inf'):
			best_dirs = Ranger.use_dist_bfs(our_coords, target_coords, bfs_array)
			choice_of_dir = random.choice(best_dirs)
			shape = variables.direction_to_coord[choice_of_dir]
			options = sense_util.get_best_option(shape)
			for option in options:
				if variables.gc.can_move(unit.id, option):
					variables.gc.move_robot(unit.id, option)
					## CHANGE LOC IN NEW DATA STRUCTURE
					add_new_location(unit.id, our_coords, option)
					break


def board(gc,my_unit,my_location,current_roles):
	finished_rockets = []
	for unit in variables.my_units:
		if unit.unit_type == variables.unit_types["rocket"] and unit.structure_is_built() and len(unit.structure_garrison()) < unit.structure_max_capacity():
			finished_rockets.append(unit)

	minimum_distance = float('inf')
	closest_rocket = None
	for rocket in finished_rockets:
		dist_to_rocket = sense_util.distance_squared_between_maplocs(my_location, rocket.location.map_location())
		if dist_to_rocket < minimum_distance:
			minimum_distance = dist_to_rocket
			closest_rocket = rocket

	if closest_rocket is None:
		current_roles["boarder"].remove(my_unit.id)
		return

	rocket_location = closest_rocket.location.map_location()
	if my_location.is_adjacent_to(rocket_location):
		if gc.can_load(closest_rocket.id,my_unit.id):
			gc.load(closest_rocket.id,my_unit.id)
			current_roles["boarder"].remove(my_unit.id)
	else:
		#print(unit.id, 'moving toward rocket')
		try_move_smartly(my_unit, my_location, rocket_location)
		#direction_to_rocket = my_location.direction_to(rocket_location)
		#movement.try_move(gc,my_unit,direction_to_rocket)


def replicate(gc,unit,direction=None):
	replicated = False

	if direction is not None:
		if gc.can_replicate(unit.id,direction):
			replicated = True
			gc.replicate(unit.id,direction)
			variables.info[0] += 1
			variables.my_karbonite = gc.karbonite()
	elif variables.my_karbonite >= variables.unit_types["worker"].replicate_cost():
		for direction in variables.directions:
			if gc.can_replicate(unit.id,direction):
				replicated = True
				gc.replicate(unit.id,direction)
				variables.info[0] += 1
				variables.my_karbonite = gc.karbonite()
	return replicated

# FOR EARTH ONLY
def update_deposit_info(gc,karbonite_locations):
	planet = variables.earth
	karbonite_locations_keys = list(karbonite_locations.keys())[:]
	for x,y in karbonite_locations_keys:
		map_location = bc.MapLocation(planet,x,y)
		# we can only update info about deposits we can see with our units
		if not gc.can_sense_location(map_location):
			continue	
		current_karbonite = gc.karbonite_at(map_location)
		if current_karbonite == 0:
			del karbonite_locations[(x,y)]
		elif karbonite_locations[(x,y)] != current_karbonite:
			karbonite_locations[(x,y)] = current_karbonite
	
# returns map location of closest karbonite deposit	
def get_closest_deposit(gc,unit,position,karbonite_locations,in_vision_range=False):	
	
	planet = variables.earth
	current_distance = float('inf')
	closest_deposit = bc.MapLocation(planet,-1,-1)
	position_coord = (position.x,position.y)
	# start_time = time.time()

	is_deposit_in_vision_range = False

	for location_coord in explore.coord_neighbors(position_coord, diff=explore.diffs_50, include_self=True):
		#location_coord_thirds = (int(location_coord[0]/variables.bfs_fineness), int(location_coord[1]/variables.bfs_fineness))

		if location_coord in karbonite_locations:
			our_coords_val = Ranger.get_coord_value(position_coord)
			target_coords_val = Ranger.get_coord_value(location_coord)


			if variables.curr_planet == bc.Planet.Earth: 
				quadrant_size = variables.earth_quadrant_size
			else:
				quadrant_size = variables.mars_quadrant_size

			quadrant = (int(location_coord[0] / quadrant_size), int(location_coord[1] / quadrant_size))
			q_info = variables.quadrant_battle_locs[quadrant]
			enemies_in_quadrant = len(q_info.enemies)


			if variables.bfs_array[our_coords_val, target_coords_val] != float('inf') and enemies_in_quadrant == 0:
				is_deposit_in_vision_range = True

				karbonite_location = bc.MapLocation(planet,location_coord[0],location_coord[1])
				distance_to_deposit = sense_util.distance_squared_between_coords(position_coord,location_coord)

				if distance_to_deposit < current_distance:
					current_distance = distance_to_deposit
					closest_deposit = karbonite_location

	if not is_deposit_in_vision_range:
		for x,y in karbonite_locations.keys():
			karbonite_location = bc.MapLocation(planet,x,y)
			karbonite_coord = (x,y)
			#karbonite_coord_thirds = (int(karbonite_coord[0] / variables.bfs_fineness), int(karbonite_coord[1] / variables.bfs_fineness))
			distance_to_deposit = sense_util.distance_squared_between_coords(position_coord,karbonite_coord)
			#keep updating current closest deposit to unit
			our_coords_val = Ranger.get_coord_value(position_coord)
			target_coords_val = Ranger.get_coord_value(karbonite_coord)


			if variables.curr_planet == bc.Planet.Earth: 
				quadrant_size = variables.earth_quadrant_size
			else:
				quadrant_size = variables.mars_quadrant_size

			quadrant = (int(karbonite_coord[0] / quadrant_size), int(karbonite_coord[1] / quadrant_size))
			q_info = variables.quadrant_battle_locs[quadrant]
			enemies_in_quadrant = len(q_info.enemies)


			if distance_to_deposit < current_distance and variables.bfs_array[our_coords_val, target_coords_val] != float('inf') and enemies_in_quadrant == 0:
				current_distance = distance_to_deposit 
				closest_deposit = karbonite_location

	#print("getting closest deposit time:",time.time() - start_time)
	return closest_deposit
	
def mine(gc,my_unit,my_location,start_map,karbonite_locations,current_roles, building_assignment, battle_locs):

	#start_time = time.time()
	start_time = time.time()
	closest_deposit = get_closest_deposit(gc,my_unit,my_location,karbonite_locations)
	#print("closest deposit",closest_deposit)
	#print("closest deposit time",time.time() - start_time)
	#check to see if there even are deposits
	if start_map.on_map(closest_deposit):

		direction_to_deposit = my_location.direction_to(closest_deposit)
		deposit_coord = (closest_deposit.x,closest_deposit.y)
		#print(unit.id, "is trying to mine at", direction_to_deposit)
		enemy_units = gc.sense_nearby_units_by_team(my_location, my_unit.vision_range, sense_util.enemy_team(gc))
		dangerous_types = [variables.unit_types["knight"], variables.unit_types["ranger"], variables.unit_types["mage"], variables.unit_types["factory"]]
		dangerous_enemies = []

		info = variables.info
		#print("worker cap",get_worker_cap(gc,variables.karbonite_locations,info,variables.num_enemies))
		if info[0] < get_worker_cap(gc,variables.karbonite_locations,info,variables.num_enemies):
			away_from_enemies = sense_util.best_available_direction(gc,my_unit,enemy_units) # includes factories
			try_replicate = replicate(gc,my_unit,direction_to_deposit)
			if try_replicate:
				return

		# only adds enemy units that can attack
		for unit in enemy_units:
			if unit.unit_type in dangerous_types:
				dangerous_enemies.append(unit)


		if len(dangerous_enemies) > 0:
			dir = sense_util.best_available_direction(gc, my_unit, dangerous_enemies)
			movement.try_move(gc, my_unit, (my_location.x,my_location.y), dir)	
		elif my_location != closest_deposit:
			# move toward deposit
			#print("my location",my_location)
			#print("trying to move to closest deposit",closest_deposit)

			my_location_coord = (my_location.x,my_location.y)
			mineable_spots = explore.coord_neighbors(deposit_coord,include_self=True)

			if variables.curr_planet == bc.Planet.Earth: 
				quadrant_size = variables.earth_quadrant_size
			else:
				quadrant_size = variables.mars_quadrant_size

			quadrant = (int(closest_deposit.x / quadrant_size), int(closest_deposit.y / quadrant_size))
			q_info = variables.quadrant_battle_locs[quadrant]
			ally_ids_in_quadrant = q_info.all_allies()


			ally_on_deposit_list = []
			for ally_id in ally_ids_in_quadrant:
				ally_coord = variables.unit_locations[ally_id]
				if ally_coord in mineable_spots:
					ally_on_deposit_list.append(ally_coord)

			for mineable_spot in mineable_spots:
				if mineable_spot in passable_locations:
					if passable_locations[mineable_spot] and mineable_spot not in ally_on_deposit_list:
						target_loc = bc.MapLocation(variables.curr_planet,mineable_spot[0],mineable_spot[1])
						try_move_smartly(my_unit, my_location, target_loc)
						break


		if my_location.is_adjacent_to(closest_deposit) or my_location == closest_deposit:

			# mine if adjacent to deposit
			#print("trying to harvest at:",closest_deposit)
			if gc.can_harvest(my_unit.id,direction_to_deposit):

				gc.harvest(my_unit.id,direction_to_deposit)
				
				variables.current_karbonite_gain += min(variables.worker_harvest_amount,karbonite_locations[deposit_coord])
				variables.my_karbonite = gc.karbonite()
				
				current_roles["miner"].remove(my_unit.id)
				#print(unit.id," just harvested!")

	else:
		current_roles["miner"].remove(my_unit.id)
		#print(unit.id," no deposits around")



def mine_mars(gc,unit,my_location):
	all_locations = gc.all_locations_within(my_location,unit.vision_range)
	planet = variables.mars
	start_map = variables.mars_start_map
	worker_spacing = 8

	current_distance = float('inf')
	closest_deposit = bc.MapLocation(planet,-1,-1)
	for deposit_location in all_locations:
		deposit_location_coords = (deposit_location.x, deposit_location.y)
		if gc.karbonite_at(deposit_location) == 0 or not passable_locations[deposit_location_coords]:
			continue
		distance_to_deposit = sense_util.distance_squared_between_maplocs(my_location, deposit_location)
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
			try_move_smartly(unit, my_location, closest_deposit)
			#movement.try_move(gc,unit,direction_to_deposit)
	else:
		nearby = gc.sense_nearby_units_by_team(my_location, worker_spacing, variables.my_team)

		away_from_units = sense_util.best_available_direction(gc,unit,nearby)	
		#print(unit.id, "at", unit.location.map_location(), "is trying to move to", away_from_units)
		movement.try_move(gc,unit,(my_location.x,my_location.y),away_from_units)

# updates building assignments in case buildings are destroyed before they are built
def update_building_assignment(gc,building_assignment,blueprinting_assignment):
	keys = list(building_assignment.keys())[:]
	invalid_building_locations = variables.invalid_building_locations
	my_unit_ids = [unit.id for unit in gc.my_units()]
	for building_id in keys:

		if building_id not in my_unit_ids: # update for dead buildings

			if building_id in building_assignment:
				workers = building_assignment[building_id]
				del building_assignment[building_id]
				for worker_id in workers:
					variables.current_worker_roles["builder"].remove(worker_id)

			removed_building_location = variables.all_building_locations[building_id]

			reevaluated_sites = factory_spacing_locations(removed_building_location)

			# reevaluate
			for site in reevaluated_sites:
				site_coords = (site.x,site.y)

				if site_coords not in passable_locations or not passable_locations[site_coords]: continue
				if invalid_building_locations[site_coords]: continue

				nearby = gc.sense_nearby_units(site,variables.factory_spacing)

				for other in nearby:
					if other.unit_type == variables.unit_types["factory"] or other.unit_type == variables.unit_types["rocket"]:
						invalid_building_locations[site_coords] = False
						continue

				for worker_id in blueprinting_assignment:
					assigned_site = blueprinting_assignment[worker_id]
					if sense_util.distance_squared_between_maplocs(site, assigned_site.map_location) < variables.factory_spacing:
						invalid_building_locations[site_coords] = False
						continue

				invalid_building_locations[site_coords] = True

		else:

			building_unit = gc.unit(building_id)
			if building_unit.structure_is_built(): # update for completed buildings
				workers = building_assignment[building_id]
				del building_assignment[building_id]
				for worker_id in workers:
					variables.current_worker_roles["builder"].remove(worker_id)



def assign_unit_to_build(gc,my_unit,my_location,start_map,building_assignment):
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
		distance_to_blueprint = sense_util.distance_squared_between_maplocs(my_location, blueprint_location)
		if distance_to_blueprint < smallest_distance:
			smallest_distance = distance_to_blueprint
			closest_building = blueprint
	#print("my_unit.id",my_unit.id,"closest_building",closest_building)

	if closest_building is not None:
		building_assignment[closest_building.id].append(my_unit.id)
	return closest_building

def build(gc,my_unit,my_location,start_map,building_assignment,current_roles):
	#print("building_assignment",building_assignment)
	my_nearby_units = variables.my_units
	unit_was_not_assigned = True
	info = variables.info

	assigned_building = None

	for building_id in building_assignment:
		if my_unit.id in building_assignment[building_id] and building_id in variables.my_unit_ids:
			assigned_building = gc.unit(building_id)


	#print("unit has been assigned to build at",assigned_building.location.map_location())
	assigned_location = assigned_building.location.map_location()
	adjacent_locs_to_blueprint = adjacent_locations(assigned_location)

	if my_location.is_adjacent_to(assigned_location):
		if len(building_assignment[assigned_building.id]) < variables.min_workers_per_building and info[0] < get_worker_cap(gc,variables.karbonite_locations,info,variables.num_enemies):
			#print("going to try to replicate")
			if variables.my_karbonite >= variables.unit_types["worker"].replicate_cost():
				adjacent_to_my_location = adjacent_locations(my_location)
				for adjacent_location in adjacent_to_my_location:
					if adjacent_location == my_location or adjacent_location == assigned_location: 
						continue
					if gc.has_unit_at_location(adjacent_location): continue

					if adjacent_location in adjacent_locs_to_blueprint:
						#print("found adjacent region",adjacent_location)
						direction = my_location.direction_to(adjacent_location)

						if gc.can_replicate(my_unit.id,direction):
							#print("right before replication")
							gc.replicate(my_unit.id,direction)

							variables.my_karbonite = gc.karbonite()
							info[0] += 1
							new_unit = gc.sense_unit_at_location(adjacent_location)

							#print("new replicated unit",new_unit.id)
							current_roles["builder"].append(new_unit.id)
							building_assignment[assigned_building.id].append(new_unit.id)
							break

		# movement around building
		
		open_spaces = explore.coord_neighbors((assigned_location.x,assigned_location.y), diff = explore.diff_neighbors, include_self = False)
		self_adjacent = explore.coord_neighbors((my_location.x,my_location.y), diff = explore.diff_neighbors, include_self = False)
		for x,y in open_spaces:
			if (x,y) in passable_locations and passable_locations[(x,y)] and (x,y) in open_spaces:
				map_loc = bc.MapLocation(variables.earth,x,y)
				if not gc.has_unit_at_location(map_loc):
					#print("i am at",my_location)
					#print("moving to location",map_loc)
					direction_to_move = my_location.direction_to(map_loc)
					if gc.is_move_ready(my_unit.id) and gc.can_move(my_unit.id,direction_to_move):
						gc.move_robot(my_unit.id,direction_to_move)
						## CHANGE LOC IN NEW DATA STRUCTURE
						add_new_location(my_unit.id, (my_location.x, my_location.y), direction_to_move)

		if gc.can_build(my_unit.id,assigned_building.id):
			#print(my_unit.id, "is building at ",assigned_location)
			gc.build(my_unit.id,assigned_building.id)
			#print("assigned_building location",assigned_building.location.map_location())
			#print("assigned building is done?",assigned_building.structure_is_built())
			if assigned_building.structure_is_built():
				workers = building_assignment[building_id]
				del building_assignment[building_id]
				for worker_id in workers:
					current_roles["builder"].remove(worker_id)
			return



	# if not adjacent move toward it
	else:
		try_move_smartly(my_unit, my_location, assigned_location)
		#direction_to_blueprint = my_location.direction_to(assigned_location)
		#movement.try_move(gc,my_unit,direction_to_blueprint)


def adjacent_locations(location):
	d = [(0,0),(0,1),(1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1)]
	planet = location.planet
	x = location.x
	y = location.y
	output = []
	for dx,dy in d:
		if (x+dx,y+dy) in passable_locations:
			if passable_locations[(x+dx,y+dy)]:
				output.append(bc.MapLocation(planet,x+dx,y+dy))
	return output


def factory_spacing_locations(location):
	d = variables.factory_spacing_diff
	planet = location.planet
	x = location.x
	y = location.y
	output = []
	for dx,dy in d:
		if (x+dx,y+dy) in passable_locations:
			if passable_locations[(x+dx,y+dy)]:
				output.append(bc.MapLocation(planet,x+dx,y+dy))
	return output


# generates locations to build factories that are close to karbonite deposits
def get_optimal_building_location(gc, start_map, center, building_type, karbonite_locations, blueprinting_queue, blueprinting_assignment):
	adjacent_locations = explore.coord_neighbors((center.x,center.y), include_self = True)
	potential_adjacent_locations = []
	karbonite_adjacent_locations = {}
	deposits_located = False
	center_coords = (center.x, center.y)

	if building_type == variables.unit_types["rocket"]:
		for default_location_coords in adjacent_locations:
			default_location = bc.MapLocation(variables.curr_planet, default_location_coords[0],
											  default_location_coords[1])
			if default_location_coords in passable_locations and passable_locations[default_location_coords] and variables.invalid_building_locations[default_location_coords]:
				return default_location_coords

	for location_coords in explore.coord_neighbors(center_coords, diff=explore.diffs_20, include_self=True):
		location = bc.MapLocation(variables.curr_planet, location_coords[0], location_coords[1])
		#print("can we build here?",variables.invalid_building_locations[location_coords],location)
		if location_coords in passable_locations and passable_locations[location_coords] and variables.invalid_building_locations[location_coords]:
			# print("optimal building location time",time.time() - start_time)
			
			if variables.curr_planet == bc.Planet.Earth: 
				quadrant_size = variables.earth_quadrant_size
			else:
				quadrant_size = variables.mars_quadrant_size

			quadrant = (int(location_coords[0] / quadrant_size), int(location_coords[1] / quadrant_size))
			q_info = variables.quadrant_battle_locs[quadrant]
			enemies_in_quadrant = len(q_info.enemies)

			adjacent_spaces = get_workers_per_building(gc,start_map,location)

			#print("location",location,"adjacent spaces",adjacent_spaces)
			if adjacent_spaces >= 3 and enemies_in_quadrant == 0:

				if location_coords in adjacent_locations:
					potential_adjacent_locations.append(location_coords)

				for adjacent_location in explore.coord_neighbors(location_coords):
					if adjacent_location in karbonite_locations:
						karbonite_value = karbonite_locations[adjacent_location]
					else:
						karbonite_value = 0

					if location_coords not in karbonite_adjacent_locations:
						karbonite_adjacent_locations[location_coords] = karbonite_value
					else:
						karbonite_adjacent_locations[location_coords] += karbonite_value
				# print("par t2 location time",time.time() - start_time)
				if karbonite_adjacent_locations[location_coords] > 0:
					deposits_located = True
					
			else:
				continue


	if deposits_located:
		return max(list(karbonite_adjacent_locations.keys()), key=lambda loc: karbonite_adjacent_locations[loc])
	elif len(potential_adjacent_locations) > 0:
		return potential_adjacent_locations[0]
	else:
		return None

# function to flexibly determine when a good time to expand factories
def can_blueprint_factory(gc,factory_count):
	if (gc.round() > 250 and variables.num_enemies < 5) or gc.round() > 400:
		return False
	return factory_count < get_factory_limit()

def can_blueprint_rocket(gc,rocket_count):
	if variables.num_passable_locations_mars > 0 and variables.research.get_level(variables.unit_types["rocket"]) > 0:
		if gc.round() > 250:
			return True

	return False

def blueprinting_queue_limit(gc):
	return 1

def get_factory_limit():
	factory_count = variables.info[5]
	factory_cost_per_round = variables.factory_cost_per_round
	usable_income = variables.past_karbonite_gain - variables.reserved_income
	#print("factory cap is now", min(usable_income/factory_cost_per_round,15))
	return min(usable_income/factory_cost_per_round,15)

def get_rocket_limit():
	return 4

def get_closest_site(my_unit,my_location,blueprinting_queue):
	
	smallest_distance = float('inf')
	closest_site = None	
	for site in blueprinting_queue:
		distance_to_site = sense_util.distance_squared_between_maplocs(my_location, site.map_location)
		if distance_to_site < smallest_distance:
			smallest_distance = distance_to_site
			closest_site = site
	return closest_site

# controls how many buildings we can have in progress at a time, can modify this to scale with karbonite number, round # or number of units (enemy or ally)
def building_in_progress_cap(gc):
	return max(1,variables.my_karbonite/150)


def blueprint(gc,my_unit,my_location,karbonite_locations,building_assignment,blueprinting_assignment,current_roles):
	directions = variables.directions
	#print('BLUEPRINTING')

	# assign this unit to build a blueprint, if nothing to build just move away from other factories
	if my_unit.id not in blueprinting_assignment:
		# print(my_unit.id,"currently has no assigned site")
		current_roles["blueprinter"].remove(my_unit.id)

	# build blueprint in assigned square
	if my_unit.id in blueprinting_assignment:
		assigned_site = blueprinting_assignment[my_unit.id]
		assigned_location = assigned_site.map_location
		# if my_unit.id in blueprinting_assignment:
		#print("unit",my_unit.id,"blueprinting at",blueprinting_assignment[my_unit.id])
		#print(unit.id, "is assigned to building in", assigned_site.map_location)
		direction_to_site = my_location.direction_to(assigned_site.map_location)
		if variables.my_karbonite >= variables.unit_types["factory"].blueprint_cost():
			if my_location.is_adjacent_to(assigned_site.map_location):
				if gc.can_blueprint(my_unit.id, assigned_site.building_type, direction_to_site):
					gc.blueprint(my_unit.id, assigned_site.building_type, direction_to_site)
					
					if assigned_site.building_type == variables.unit_types["factory"]:
						variables.info[5] += 1
					else:
						variables.info[6] += 1

					variables.my_karbonite = gc.karbonite()

					new_blueprint = gc.sense_unit_at_location(assigned_site.map_location)

					variables.all_building_locations[new_blueprint.id] = assigned_site.map_location
					# update shared data structures

					building_assignment[new_blueprint.id] = [my_unit.id] # initialize new building

					del blueprinting_assignment[my_unit.id]
					current_roles["blueprinter"].remove(my_unit.id)
					current_roles["builder"].append(my_unit.id)
				else:
					pass
					#print(my_unit.id, "can't build but is right next to assigned site")
			elif my_location == assigned_site.map_location:
				# when unit is currently on top of the queued building site
				d = random.choice(variables.directions)
				movement.try_move(gc,my_unit,(my_location.x,my_location.y),d)
			else:
				# move toward queued building site
				#next_direction = my_location.direction_to(assigned_site.map_location)
				#movement.try_move(gc,my_unit,next_direction)
				try_move_smartly(my_unit,my_location,assigned_site.map_location)
		else:
			my_coord = (assigned_location.x,assigned_location.y)
			standby_mining_locations = explore.coord_neighbors(my_coord,diff=explore.diffs_5,include_self=True)

			closest_distance = float('inf')
			closest_deposit_coord = None

			for coord in standby_mining_locations:
				if coord in karbonite_locations:
					distance_to_deposit =  sense_util.distance_squared_between_coords(coord,my_coord)
					if distance_to_deposit < closest_distance:
						closest_distance = distance_to_deposit
						closest_deposit_coord = coord

			if closest_deposit_coord is not None:
				closest_deposit = bc.MapLocation(variables.earth,closest_deposit_coord[0],closest_deposit_coord[1])
				direction_to_deposit = my_location.direction_to(closest_deposit)
				if my_location.is_adjacent_to(closest_deposit) or my_location == closest_deposit:
					# mine if adjacent to deposit
					#print("trying to harvest at:",closest_deposit)
					if gc.can_harvest(my_unit.id,direction_to_deposit):

						gc.harvest(my_unit.id,direction_to_deposit)

						variables.current_karbonite_gain += min(variables.worker_harvest_amount,karbonite_locations[closest_deposit_coord])
						variables.my_karbonite = gc.karbonite()
						#print(unit.id," just harvested!")
				else:
					# move toward deposit
					try_move_smartly(my_unit, my_location, closest_deposit)




def add_new_location(unit_id, old_coords, direction):
	if variables.curr_planet == bc.Planet.Earth: 
		quadrant_size = variables.earth_quadrant_size
	else:
		quadrant_size = variables.mars_quadrant_size

	unit_mov = variables.direction_to_coord[direction]
	new_coords = (old_coords[0]+unit_mov[0], old_coords[1]+unit_mov[1])
	variables.unit_locations[unit_id] = new_coords

	old_quadrant = (int(old_coords[0] / quadrant_size), int(old_coords[1] / quadrant_size))
	new_quadrant = (int(new_coords[0] / quadrant_size), int(new_coords[1] / quadrant_size))

	if old_quadrant != new_quadrant: 
		variables.quadrant_battle_locs[old_quadrant].remove_ally(unit_id)
		variables.quadrant_battle_locs[new_quadrant].add_ally(unit_id, "worker")

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

