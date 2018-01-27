import battlecode as bc
import random
import sys
import traceback
import Units.explore as explore
import Units.sense_util as sense_util

def coefficient_computation(gc, our_unit, their_unit, location, priority, far=False):
    # compute the relative appeal of attacking a unit.  Use AOE computation if attacking unit is mage.
    if not gc.can_attack(our_unit.id, their_unit.id) and not far:
        return 0
    coeff = attack_coefficient(gc, our_unit, their_unit, location, priority)
    if our_unit.unit_type != bc.UnitType.Mage:
        return coeff
    else:
        for neighbor in explore.neighbors(their_unit.location.map_location()):
            try:
                new_unit = gc.sense_unit_at_location(neighbor)
            except:
                new_unit = None
            if new_unit is not None and new_unit.team!=our_unit.team:
                coeff = coeff + attack_coefficient(gc, our_unit, new_unit, location, priority)

        return coeff

def attack_coefficient(gc, our_unit, their_unit, location, priority): 
    distance = sense_util.distance_squared_between_maplocs(their_unit.location.map_location(), location)

    coeff = priority[their_unit.unit_type]
    if distance < attack_range_non_robots(their_unit):
        coeff *= sense_util.can_attack_multiplier(their_unit)
    coeff *= sense_util.health_multiplier(their_unit)
    return coeff

def attack_range_non_robots(unit):
    # attack range for all structures in the game
    if unit.unit_type == bc.UnitType.Factory or unit.unit_type == bc.UnitType.Rocket:
        return 0
    else:
        return unit.attack_range()