import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):
    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Knight:
        # prob should return some kind of error
        return

    my_team = gc.team()
    d = None
    directions = list(bc.Direction)
    location = unit.location
    if location.is_on_map():
        nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
        for other in nearby:
            if other.team !=my_team:
                if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                    gc.attack(unit.id, other.id)
                    d = directions[0]
                elif not gc.can_attack(unit.id, other.id):
                    d = gc.direction_to(location, other.location)

    # if no dudes, pick a random direction:
    if d == None:
        d = random.choice(directions)

    if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
        gc.move_robot(unit.id, d)
