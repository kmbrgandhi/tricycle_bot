import battlecode as bc
import random
import sys
import traceback

import Units.variables as variables

directions = list(bc.Direction)
direction_to_index = {"North": 0, "Northeast": 1, "East": 2, "Southeast": 3, "South": 4, "Southwest": 5, "West": 6,
                      "Northwest": 7, "Center": 8}

def can_attack_multiplier(unit):
    # Multiplier for the danger of a unit, given it can attack.
    return 2

def distance_squared_between_maplocs(maploc1, maploc2):
    return (maploc1.x-maploc2.x)**2 + (maploc1.y - maploc2.y)**2


def distance_squared_between_coord_maploc(coords1, maploc2):
    return (coords1[0]-maploc2.x)**2 + (coords1[1] - maploc2.y)**2



def distance_squared_between_coords(coords1, coords2):
    return (coords1[0]-coords2[0])**2 + (coords1[1] - coords2[1])**2

def health_multiplier(unit):
    # Multiplier for how appealing it is to attack a unit, given its current health.
    c = 1.75
    return 1 + c*(unit.max_health - unit.health)/unit.max_health

def opposite(d): 
    coord_dir = variables.direction_to_coord[d]
    opp_coord_dir = (-coord_dir[0],-coord_dir[1])
    return variables.coord_to_direction[opp_coord_dir]

def add_multiple(loc, d, num_add): 
    coord_dir = variables.direction_to_coord[d]
    for i in range(num_add): 
        loc = (loc[0]+coord_dir[0],loc[1]+coord_dir[1])
    return loc

def best_available_direction_visibility(gc, unit, locs):
    # move unit toward set of locations
    sum = vector_sum_locs(unit, locs)
    options = get_best_option(sum)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return random.choice(list(bc.Direction))

def vector_sum_locs(unit, locs):
    # Computes the vector sum of map locations
    sum = [0, 0]
    count = 0
    for loc in locs:
        sum[0]+=(loc.x - unit.location.map_location().x)
        sum[1]+=(loc.y - unit.location.map_location().y)
    return sum

def best_available_direction(gc, unit, units, weights = None):
    # Returns the best available direction for unit to move, given units it is trying to get away from, and a set of weights.
    sum = vector_sum(unit, units, weights)
    options = get_best_option(sum)
    for option in options:
        if gc.can_move(unit.id, option):
            return option
    return directions[direction_to_index["Center"]]

def vector_sum(unit, units, weights = None):
    # Computes the vector sum of the map locations of non-garrisoned units in units.
    if weights == None:
        weights = [1 for i in range(len(units))]
    sum = [0, 0]
    for unit_index in range(len(units)):
        if units[unit_index].location.is_on_map():
            sum[0]-=(units[unit_index].location.map_location().x - unit.location.map_location().x) * weights[unit_index]
            sum[1]-=(units[unit_index].location.map_location().y- unit.location.map_location().y) * weights[unit_index]
    return sum

def get_best_option(optimal_dir):
    # Given an exact optimal direction, gives an ordered tuple of the best map directions to move.
    ratio = abs(optimal_dir[0]/(optimal_dir[1]+0.001))
    if optimal_dir[0]>0:
        if optimal_dir[1]>0:
            if ratio <0.5:
                return [bc.Direction.North, bc.Direction.Northeast, bc.Direction.East, bc.Direction.Northwest, bc.Direction.West, bc.Direction.Southeast, bc.Direction.Southwest, bc.Direction.South]
            elif ratio > 2:
                return [bc.Direction.East, bc.Direction.Northeast, bc.Direction.North, bc.Direction.Southeast, bc.Direction.South, bc.Direction.Northwest, bc.Direction.Southwest, bc.Direction.West]
            else:
                return [bc.Direction.Northeast, bc.Direction.North, bc.Direction.East, bc.Direction.Southeast, bc.Direction.Northwest, bc.Direction.South, bc.Direction.West, bc.Direction.Southwest]
        else:
            if ratio <0.5:
                return [bc.Direction.South, bc.Direction.Southeast, bc.Direction.East, bc.Direction.Southwest, bc.Direction.West, bc.Direction.Northeast, bc.Direction.Northwest, bc.Direction.North]
            elif ratio > 2:
                return [bc.Direction.East, bc.Direction.Southeast, bc.Direction.South, bc.Direction.Northeast, bc.Direction.Southwest, bc.Direction.North, bc.Direction.Northwest, bc.Direction.West]
            else:
                return [bc.Direction.Southeast, bc.Direction.South, bc.Direction.East, bc.Direction.Northeast, bc.Direction.Southwest, bc.Direction.North, bc.Direction.West, bc.Direction.Northwest]
    else:
        if optimal_dir[1]>0:
            if ratio <0.5:
                return [bc.Direction.North, bc.Direction.Northwest, bc.Direction.West, bc.Direction.Northeast, bc.Direction.East, bc.Direction.Southwest, bc.Direction.Southeast, bc.Direction.South]
            elif ratio > 2:
                return [bc.Direction.West, bc.Direction.Northwest, bc.Direction.North, bc.Direction.Southwest, bc.Direction.South, bc.Direction.Northeast, bc.Direction.Southeast, bc.Direction.East]
            else:
                return [bc.Direction.Northwest, bc.Direction.North, bc.Direction.West, bc.Direction.Southwest, bc.Direction.Northeast, bc.Direction.South, bc.Direction.East, bc.Direction.Southeast]
        else:
            if ratio<0.5:
                return [bc.Direction.South, bc.Direction.Southwest, bc.Direction.West, bc.Direction.Southeast, bc.Direction.East, bc.Direction.Northwest, bc.Direction.Northeast, bc.Direction.North]
            elif ratio > 2:
                return [bc.Direction.West, bc.Direction.Southwest, bc.Direction.South, bc.Direction.Northwest, bc.Direction.Southeast, bc.Direction.North, bc.Direction.Northeast, bc.Direction.East]
            else:
                return [bc.Direction.Southwest, bc.Direction.South, bc.Direction.West, bc.Direction.Northwest, bc.Direction.Southeast, bc.Direction.North, bc.Direction.East, bc.Direction.Northwest]

