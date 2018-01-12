import battlecode as bc
import random
import sys
import traceback

directions = list(bc.Direction)
direction_to_index = {"North": 0, "Northeast": 1, "East": 2, "Southeast": 3, "South": 4, "Southwest": 5, "West": 6,
                      "Northwest": 7, "Center": 8}

def can_attack_multiplier(unit):
    # Multiplier for the danger of a unit, given it can attack.
    return 2

def health_multiplier(unit):
    # Multiplier for how appealing it is to attack a unit, given its current health.
    c = 1
    return 1 + c*(unit.max_health - unit.health)/unit.max_health

def enemy_team(gc):
    # Returns the enemy team
    teams = bc.Team
    for team in teams:
        if team != gc.team(): return team

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
    return direction_to_index["Center"]

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
                return (directions[direction_to_index["North"]], directions[direction_to_index["Northeast"]], directions[direction_to_index["East"]])
            elif ratio > 2:
                return (directions[direction_to_index["East"]], directions[direction_to_index["Northeast"]], directions[direction_to_index["North"]])
            else:
                return (directions[direction_to_index["Northeast"]], directions[direction_to_index["North"]], directions[direction_to_index["East"]])
        else:
            if ratio <0.5:
                return (directions[direction_to_index["South"]], directions[direction_to_index["Southeast"]], directions[direction_to_index["East"]])
            elif ratio > 2:
                return (directions[direction_to_index["East"]], directions[direction_to_index["Southeast"]], directions[direction_to_index["South"]])
            else:
                return (directions[direction_to_index["Southeast"]], directions[direction_to_index["South"]], directions[direction_to_index["East"]])
    else:
        if optimal_dir[1]>0:
            if ratio <0.5:
                return (directions[direction_to_index["North"]], directions[direction_to_index["Northwest"]], directions[direction_to_index["West"]])
            elif ratio > 2:
                return (directions[direction_to_index["West"]], directions[direction_to_index["Northwest"]], directions[direction_to_index["North"]])
            else:
                return (directions[direction_to_index["Northwest"]], directions[direction_to_index["North"]], directions[direction_to_index["West"]])
        else:
            if ratio<0.5:
                return (directions[direction_to_index["South"]], directions[direction_to_index["Southwest"]], directions[direction_to_index["West"]])
            elif ratio > 2:
                return (directions[direction_to_index["West"]], directions[direction_to_index["Southwest"]], directions[direction_to_index["South"]])
            else:
                return (directions[direction_to_index["Southwest"]], directions[direction_to_index["South"]], directions[direction_to_index["West"]])

