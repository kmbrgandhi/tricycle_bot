import battlecode as bc
import random
import sys
import traceback

def timestep(gc, unit):

    # last check to make sure the right unit type is running this
    if unit.unit_type != bc.UnitType.Worker:
        # prob should return some kind of error
        return
    my_team = gc.team()

    # first, let's look for nearby blueprints to work on
    location = unit.location
    space_out_factories = True
    if location.is_on_map():
        nearby = gc.sense_nearby_units(location.map_location(), 5)
        for other in nearby:
            if other.unit_type == bc.UnitType.Factory:
                space_out_factories = False
            if gc.can_build(unit.id, other.id):
                gc.build(unit.id, other.id)
                print('built a factory!')
                return
    # okay, there weren't any dudes around
    # pick a random direction:
    directions = list(bc.Direction)
    d = random.choice(directions)

    # or, try to build a factory:
    if space_out_factories and gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
        gc.blueprint(unit.id, bc.UnitType.Factory, d)
    # and if that fails, try to move
    elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
        gc.move_robot(unit.id, d)