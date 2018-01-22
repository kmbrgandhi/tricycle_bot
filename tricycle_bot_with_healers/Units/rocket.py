import battlecode as bc
import random
import sys
import traceback
import Units.explore as explore

directions = list(bc.Direction)


def timestep(gc, unit,composition, rocket_launch_times, rocket_launch_site):
    
    # last check to make sure the right unit type is running this
    try:
        if unit.unit_type != bc.UnitType.Rocket:
        # prob should return some kind of error
            return

        curr_round = gc.round()
        garrison = unit.structure_garrison()

        if gc.planet() == bc.Planet.Earth:

            if unit.id not in rocket_launch_times or curr_round > rocket_launch_times[unit.id]:
                if unit.id in rocket_launch_site:
                    del rocket_launch_site[unit.id]
                time = compute_optimal_launch_time(gc, curr_round)[0]
                rocket_launch_times[unit.id] = time
                rocket_launch_site[unit.id] = compute_optimal_landing_site(gc, curr_round, time, rocket_launch_site)
            elif len(garrison)>5 and gc.round() == rocket_launch_times[unit.id] and gc.can_launch_rocket(unit.id, rocket_launch_site[unit.id]):
                gc.launch_rocket()
            else:
                if len(garrison) > 0:  # try to unload a unit if there exists one in the garrison
                    optimal_unload_dir = rocket_unload(gc, unit, directions)
                    if optimal_unload_dir is not None:
                        gc.unload(unit.id, optimal_unload_dir)
                else:
                    gc.disintegrate_unit(unit.id)
    except:
        rockets_messed_up = True



def rocket_durations_sorted(gc):
	# gets orbit pattern, sorts round numbers by duration time, returns the resultant array.
	orbit_pattern = gc.orbit_pattern()
	rounds = [i for i in range(1, 1001)]
	durations = [(i, orbit_pattern.duration(i)) for i in range(1, 1001)]
	sorted_rounds_by_duration = sorted(rounds, key = lambda x: orbit_pattern.duration(x))
	return sorted_rounds_by_duration


def compute_optimal_launch_time(gc, curr_round):
	orbit_pattern = gc.orbit_pattern()
	durations = [(i, orbit_pattern.duration(i)+i) for i in range(curr_round+5, curr_round + 50)]
	return min(durations, key = lambda x: x[1])

def compute_optimal_landing_site(gc, curr_round, time):
    asteroid_pattern = gc.asteroid_pattern()
    mars_map = gc.starting_map(bc.Planet.Mars)
    best = None
    best_karbonite = 0
    asteroid_strikes = get_all_asteroid_strikes(gc, time)
    for x in range(mars_map.width):
        for y in range(mars_map.height):
            map_loc = bc.MapLocation(bc.Planet.Mars, x, y)
            nearby_karb = compute_nearby_karbonite(gc, map_loc, asteroid_strikes)
            if mars_map.is_passable_terrain(map_loc) and nearby_karb > best_karbonite:
                best = map_loc
                best_karbonite = nearby_karb
    return best

def get_all_asteroid_strikes(gc, time):
	asteroid_pattern = gc.asteroid_pattern()
	store_karbonite = {}
	for round in range(1, time+1):
		if asteroid_pattern.has_asteroid(round):
			hit = asteroid_pattern.asteroid(round)
			if hit.location in dict:
				store_karbonite[(hit.location.x, hit.location.y)] +=hit.karbonite
			else:
				store_karbonite[(hit.location.x, hit.location.y)] = hit.karbonite
	return store_karbonite

def compute_nearby_karbonite(gc, map_loc, asteroid_strikes, radius=40):
	total = 0
	for loc in gc.all_locations_within(map_loc, radius):
		if explore.exists_movement_path_locs(map_loc, loc):
			total = total + asteroid_strikes[(loc.x, loc.y)]

	return total


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

def rocket_unload(gc, unit, directions):
	best = None
	best_val = -float('inf')
	for d in directions:
		if gc.can_unload(unit.id, d):
			locs = gc.all_locations_within(unit.location.map_location(), 6)
			locs_good = []
			for loc in locs:
				if gc.can_sense_location(loc) and gc.has_unit_at_location(loc):
					locs_good.append(loc)
			num_good = len(locs_good)
			if num_good > best_val:
				best_val = num_good
				best = d
	return best