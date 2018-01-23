import battlecode as bc
import random
import sys
import traceback
import numpy as np
import Units.sense_util as sense_util
import Units.variables as variables


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
	garrison = unit.structure_garrison() # units inside of factory
	if len(garrison) > 0: # try to unload a unit if there exists one in the garrison
		optimal_unload_dir = optimal_unload(gc, unit, directions, building_assignments, battle_locs)
		if optimal_unload_dir is not None:
			gc.unload(unit.id, optimal_unload_dir)


	rockets_need_filling = (len(variables.rocket_locs) >0) and (len(variables.ranger_roles["go_to_mars"])<10)
	if gc.can_produce_robot(unit.id, bc.UnitType.Ranger) and (rockets_need_filling and  gc.round() < 150 or num_attacking_units<min(max(1.5*(variables.earth_start_map.width*variables.earth_start_map.height)**(0.5), 40), 100) or num_attacking_units < 2.7*variables.num_enemies): #and should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit): # otherwise produce a unit, based on most_off_optimal
		if total_units[0]<4 and gc.can_produce_robot(unit.id, bc.UnitType.Worker):
			gc.produce_robot(unit.id, bc.UnitType.Worker)
		elif total_units[1]<5 and gc.round() < 70:
			gc.produce_robot(unit.id, bc.UnitType.Knight)
		elif total_units[2] < 0.85 * num_non_workers:
			gc.produce_robot(unit.id, bc.UnitType.Ranger)
		else:
			gc.produce_robot(unit.id, bc.UnitType.Healer)
		#current_production += order[best].factory_cost()
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



