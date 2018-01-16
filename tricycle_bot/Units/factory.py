import battlecode as bc
import random
import sys
import traceback
import numpy as np

def timestep(gc, unit,composition, building_assignments, mining_rate = 0, current_production = 0, karbonite_lower_limit = 100):
	curr_round = gc.round()
	optimal_composition = [0, 0, 0, 0, 1] # optimal composition, order is Worker, Knight, Ranger, Mage, Healer
	# should alter based on curr_round.  this is a temporary idea.
	calculate = [max((optimal_composition[i]-composition[i]), 0) for i in range(len(optimal_composition))] #offset from optimal
	order = [bc.UnitType.Worker, bc.UnitType.Knight, bc.UnitType.Ranger, bc.UnitType.Mage, bc.UnitType.Healer] # storing order of units
	# last check to make sure the right unit type is running this
	if unit.unit_type != bc.UnitType.Factory:
		# prob should return some kind of error
		return
	garrison = unit.structure_garrison() # units inside of factory
	directions = list(bc.Direction)
	if len(garrison) > 0: # try to unload a unit if there exists one in the garrison
		optimal_unload_dir = optimal_unload(gc, unit, directions, building_assignments)
		if optimal_unload_dir is not None:
			gc.unload(unit.id, optimal_unload_dir)

	if gc.can_produce_robot(unit.id, bc.UnitType.Worker): #and should_produce_robot(gc, mining_rate, current_production, karbonite_lower_limit): # otherwise produce a unit, based on most_off_optimal
		best = None
		most = -float('inf')
		tiebreaker = -float('inf')
		for i in range(len(calculate)):
			if calculate[i] > most:
				best = i
				tiebreaker = optimal_composition[i]
				most = calculate[i]
			elif calculate[i]==most:
				if optimal_composition[i]> tiebreaker:
					best = i
					tiebreaker = optimal_composition[i]
					most = calculate[i]

		produce = bc.UnitType.Ranger
		gc.produce_robot(unit.id, produce)
		#current_production += order[best].factory_cost()

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

def optimal_unload(gc, unit, directions, building_assignments):
	best = None
	best_val = -float('inf')
	for d in directions:
		build_sites = list(map(lambda site : site.map_location,list(building_assignments.values())))
		if gc.can_unload(unit.id, d) and unit.location.map_location().add(d) not in build_sites:
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



