import battlecode as bc
import random
import sys
import traceback
import Units.explore as explore
import Units.variables as variable


def update_rockets():
    to_delete = []
    for rocket_id in variable.rocket_locs:
        if rocket_id not in variable.my_unit_ids:
            to_delete.append(rocket_id)
    for rocket_id in to_delete:
        del variable.rocket_locs[rocket_id]

def timestep(unit):
    
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Rocket:
    # prob should return some kind of error
        return
    curr_round = variable.gc.round()
    garrison = unit.structure_garrison()
    gc = variable.gc

    if variable.curr_planet == bc.Planet.Earth and unit.structure_is_built():
        if unit.id not in variable.rocket_locs:
            variable.rocket_locs[unit.id] = unit.location.map_location()
        if unit.id not in variable.rocket_launch_times or curr_round > variable.rocket_launch_times[unit.id]:
            time = compute_optimal_launch_time(curr_round)[0]
            variable.rocket_launch_times[unit.id] = time
            if unit.id not in variable.rocket_landing_sites:
                variable.rocket_landing_sites[unit.id] = explore.get_maploc(bc.Planet.Mars, random.choice(variable.lst_of_passable_mars))
                #rocket_launch_site[unit.id] = compute_optimal_landing_site(gc, curr_round, time, rocket_launch_site)

        if ((len(garrison)>6 and gc.round()<400) or (len(garrison)>5 and gc.round()>400) or (gc.round()>745)) and (variable.gc.round() == variable.rocket_launch_times[unit.id] or gc.round()==748) and variable.gc.can_launch_rocket(unit.id, variable.rocket_landing_sites[unit.id]):
            variable.gc.launch_rocket(unit.id, variable.rocket_landing_sites[unit.id])
            del variable.rocket_locs[unit.id]
            return

        curr_loc = unit.location.map_location()
        for dir in variable.directions[:-1]:
            near = curr_loc.add(dir)
            if gc.has_unit_at_location(near):
                nearby_unit = gc.sense_unit_at_location(near)
                if nearby_unit.unit_type!=variable.unit_types["worker"] and nearby_unit.unit_type!=variable.unit_types["factory"] and nearby_unit.unit_type!=variable.unit_types["rocket"] and gc.can_load(unit.id, nearby_unit.id):
                    gc.load(unit.id, nearby_unit.id)
                    if nearby_unit.id == variable.saviour_worker_id:
                        variable.saviour_worker_id = None
                        variable.saviour_worker = False
                        variable.saviour_blueprinted = False
                        variable.saviour_blueprinted_id = None
                        variable.num_unsuccessful_savior = 0
                        variable.saviour_time_between = 0
                    break


    else:
        #print('GARRISON LENGHT',len(garrison))
        if len(garrison) > 0:  # try to unload a unit if there exists one in the garrison
            optimal_unload_dir = rocket_unload(unit)
            if optimal_unload_dir is not None:
                variable.gc.unload(unit.id, optimal_unload_dir)


def compute_optimal_launch_time(curr_round):
	orbit_pattern = variable.gc.orbit_pattern()
	durations = [(i, orbit_pattern.duration(i)+i) for i in range(curr_round+5, curr_round + 30)]
	return min(durations, key = lambda x: x[1])

"""
def compute_optimal_landing_site(curr_round, time):
    mars_map = gc.starting_map(bc.Planet.Mars)
    best = None
    best_karbonite = 0
    asteroid_strikes = get_all_asteroid_strikes(gc, time)
    for x in range(mars_map.width):
        for y in range(mars_map.height):
            map_loc = bc.MapLocation(bc.Planet.Mars, x, y)
            nearby_karb = compute_nearby_karbonite(gc, map_loc, asteroid_strikes)
            if mars_map.is_passable_terrain_at(map_loc) and map_loc not in rocket_landing_sites.values() and nearby_karb > best_karbonite:
                best = map_loc
                best_karbonite = nearby_karb
    return best
"""
def get_all_asteroid_strikes(time):
    asteroid_pattern = variable.gc.asteroid_pattern()
    store_karbonite = {}
    for round in range(1, time+1):
        if asteroid_pattern.has_asteroid(round):
            hit = asteroid_pattern.asteroid(round)
            if (hit.location.x, hit.location.y) in store_karbonite:
                store_karbonite[(hit.location.x, hit.location.y)] +=hit.karbonite
            else:
                store_karbonite[(hit.location.x, hit.location.y)] = hit.karbonite
    return store_karbonite

def compute_nearby_karbonite(map_loc, asteroid_strikes, radius=40):
	total = 0
	for loc in variable.gc.all_locations_within(map_loc, radius):
		if (loc.x, loc.y) in asteroid_strikes: #and explore.exists_movement_path_locs(gc, map_loc, loc):
			total = total + asteroid_strikes[(loc.x, loc.y)]

	return total

"""
def optimal_unload(gc, unit, directions, building_assignments):
    best = None
    best_val = -float('inf')
    for d in directions:
        if gc.can_unload(unit.id, d) and unit.location.map_location().add(d) not in building_assignments.values():
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
"""

def rocket_unload(unit):
	best = None
	best_val = -float('inf')
	for d in variable.directions:
		if variable.gc.can_unload(unit.id, d):
			locs = variable.gc.all_locations_within(unit.location.map_location(), 6)
			locs_good = []
			for loc in locs:
				if variable.gc.can_sense_location(loc) and variable.gc.has_unit_at_location(loc):
					locs_good.append(loc)
			num_good = len(locs_good)
			if num_good > best_val:
				best_val = num_good
				best = d
	return best