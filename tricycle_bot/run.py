import battlecode as bc
import random
import sys
import traceback
import Units.Healer as healer
import Units.Knight as knight
import Units.Mage as mage
import Units.Ranger as ranger
import Units.Worker as worker
import Units.factory as factory
import Units.rocket as rocket


print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)

my_team = gc.team()

while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round())

    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():

        	# resepective unit types execute their own AI
        	if unit.unit_type == bc.UnitType.Worker:
        		worker.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Knight:
        		knight.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Ranger:
        		ranger.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Mage:
        		mage.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Healer:
        		healer.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Factory:
        		factory.timestep(gc,unit)
        	elif unit.unit_type == bc.UnitType.Rocket:
        		rocket.timestep(gc,unit)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()