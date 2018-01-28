import battlecode as bc
import random
import sys
import traceback
import numpy as np
import Units.sense_util as sense_util
import Units.variables as variables
import Units.explore as explore


def timestep(unit):

	building_assignments = variables.building_assignment
	directions = variables.directions
	gc = variables.gc
	composition = variables.info
	producing = variables.producing
	battle_locs = variables.last_turn_battle_locs
	mining_rate = 3 * len(variables.current_worker_roles["miner"])
	total_units = [composition[0]+producing[0], composition[1]+producing[1], composition[2]+producing[2], composition[3]+producing[3], composition[4]+producing[4]]
	num_attacking_units = sum(total_units[1:3])
	num_non_workers = num_attacking_units + total_units[4]
	curr_round = gc.round()
	   
	# should alter based on curr_round.  this is a temporary idea.
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Factory:
		# prob should return some kind of error
		return
		
	unit_locations = variables.unit_locations
	quadrant_battles = variables.quadrant_battle_locs
	if variables.curr_planet == bc.Planet.Earth: 
		quadrant_size = variables.earth_quadrant_size
	else:
		quadrant_size = variables.mars_quadrant_size

	## Add new ones to unit_locations, else just get the location
	if unit.id not in unit_locations:
		loc = unit.location.map_location()
		unit_locations[unit.id] = (loc.x,loc.y)
		f_f_quad = (int(loc.x / quadrant_size), int(loc.y / quadrant_size))
		quadrant_battles[f_f_quad].add_ally(unit.id, "factory")

	garrison = unit.structure_garrison() # units inside of factory
	if len(garrison) > 0: # try to unload a unit if there exists one in the garrison
		optimal_unload_dir = optimal_unload(gc, unit, directions, building_assignments, battle_locs)
		if optimal_unload_dir is not None:
			gc.unload(unit.id, optimal_unload_dir)
	# rockets_need_filling = (len(variables.rocket_locs) >0) and (len(variables.ranger_roles["go_to_mars"])<10)
	if gc.round()>250 or variables.died_without_attacking > 0.7:
		variables.knight_rush = False
		variables.switch_to_rangers = True
	"""

	"""


	if variables.knight_rush:
		if not variables.stockpile_until_75 and gc.can_produce_robot(unit.id, bc.UnitType.Knight): #and should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit): # otherwise produce a unit, based on most_off_optimal
			if total_units[0]<2:
				if gc.can_produce_robot(unit.id, bc.UnitType.Worker):
					gc.produce_robot(unit.id, bc.UnitType.Worker)
			elif total_units[1] < 0.75* num_non_workers or total_units[2]<7:
				gc.produce_robot(unit.id, bc.UnitType.Knight)
			else:
				gc.produce_robot(unit.id, bc.UnitType.Healer)
	else:
		produce_some_knights = False
		my_location = unit.location.map_location()
		my_location_coords = (my_location.x, my_location.y)
		if gc.round() < 250:
			for neighbor in explore.coord_neighbors(my_location_coords, diff=explore.diffs_20):
				neighbor_loc = bc.MapLocation(variables.curr_planet, neighbor[0], neighbor[1])
				if gc.can_sense_location(neighbor_loc) and gc.has_unit_at_location(neighbor_loc):
					nearby_unit = gc.sense_unit_at_location(neighbor_loc)
					if nearby_unit.unit_type == variables.unit_types["factory"] and nearby_unit.team !=variables.my_team:
						produce_some_knights = True
						break

		if produce_some_knights and gc.can_produce_robot(unit.id, bc.UnitType.Knight):
			gc.produce_robot(unit.id, bc.UnitType.Knight)


		if not variables.stockpile_until_75 and (total_units[0]<2 or gc.round()<680 or len(variables.rocket_locs)>0) and gc.can_produce_robot(unit.id, bc.UnitType.Ranger) \
				and (total_units[0]<2 or gc.round() < 150 or num_attacking_units < 100 or num_attacking_units < 2*variables.num_enemies): #and should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit): # otherwise produce a unit, based on most_off_optimal
			if total_units[0]<2:
				if gc.can_produce_robot(unit.id, bc.UnitType.Worker):
					gc.produce_robot(unit.id, bc.UnitType.Worker)
			#elif total_units[1]<5 and gc.round() < 70:
			#	gc.produce_robot(unit.id, bc.UnitType.Knight)
			elif total_units[2] < 0.65 * num_non_workers or total_units[2]<2:
				gc.produce_robot(unit.id, bc.UnitType.Ranger)
			else:
				gc.produce_robot(unit.id, bc.UnitType.Healer)

		#current_production += order[best].factory_cost()

def evaluate_stockpile():
	return
	cost = variables.cost_of_factory
	composition = variables.info
	producing = variables.producing
	total_units = [composition[0], composition[1], composition[2],
				   composition[3], composition[4]]
	num_attacking_units = sum(total_units[1:4])
	if not variables.stockpile_until_75:
		if (variables.gc.round()>250 and num_attacking_units > 0.48*variables.num_enemies) or variables.gc.round()>500:
				if variables.between_stockpiles > 40 and variables.gc.karbonite()<cost * 1.25:
					variables.stockpile_until_75 = True
					variables.between_stockpiles = 0
				else:
					variables.between_stockpiles+=1
	else:
		if variables.gc.karbonite()>cost * 1.25:
			if variables.stockpile_has_been_above:
				variables.stockpile_until_75 = False
				variables.between_stockpiles = 0
				variables.stockpile_has_been_above = False
			else:
				variables.stockpile_has_been_above = True
"""
def should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit):
	# produce a robot if net karbonite at the end of the turn will be more than karbonite_lower_limit
	net_karbonite = gc.karbonite() + mining_rate - current_production + gain_rate(gc)
	if gc.karbonite() > karbonite_lower_limit and net_karbonite > karbonite_lower_limit:
		return True
	val = random.random()
	if val > 0.5 * float((100 - net_karbonite))/100:
		return True
	return False

def gain_rate(gc):
	curr = gc.karbonite()
	decrease = int(curr/40)
	return max(10 -decrease, 0)
"""
def optimal_unload(gc, unit, directions, building_assignments, battle_locs):
	"""
	Tries to find unload direction towards a battle location, otherwise finds another optimal
	direction with previous logic.

	Returns direction or None.
	"""
	unit_loc = unit.location.map_location()
	#build_sites = list(map(lambda site: site.map_location,list(building_assignments.values())))

	## Find list of best unload towards battle_locs and use best dir that doesn't interfere with building
	if len(battle_locs) > 0: 
		weakest = random.choice(list(battle_locs.keys()))
		target_loc = battle_locs[weakest][0]

		shape = [target_loc.x - unit_loc.x, target_loc.y - unit_loc.y]
		unload_dirs = sense_util.get_best_option(shape) ## never returns None or empty list

		for d in unload_dirs: 
			if gc.can_unload(unit.id, d): #and unit_loc.add(d) not in build_sites
				return d

	## Use previous optimal location
	best = None
	best_val = -float('inf')

	for d in directions:
		if gc.can_unload(unit.id, d):# and unit.location.map_location().add(d) not in build_sites
			locs = gc.all_locations_within(unit.location.map_location(), 9)
			locs_good = []
			for loc in locs:
				if gc.can_sense_location(loc) and gc.has_unit_at_location(loc):
					locs_good.append(loc)
			num_good = len(locs_good)
			if num_good > best_val:
				best_val = num_good
				best = d

	return best



