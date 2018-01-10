import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):

	# last check to make sure the right unit type is running this
	if unit.unitType != bc.UnitType.Worker:
		# prob should return some kind of error
		return

    # first, let's look for nearby blueprints to work on
    location = unit.location
    if location.is_on_map():
        nearby = gc.sense_nearby_units(location.map_location(), 2)
        for other in nearby:
            if gc.can_build(unit.id, other.id):
                gc.build(unit.id, other.id)
                print('built a factory!')
                # move onto the next unit
                continue
            if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                print('attacked a thing!')
                gc.attack(unit.id, other.id)
                continue

    # okay, there weren't any dudes around
    # pick a random direction:
    d = random.choice(directions)

    # or, try to build a factory:
    if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
        gc.blueprint(unit.id, bc.UnitType.Factory, d)
    # and if that fails, try to move
    elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
        gc.move_robot(unit.id, d)