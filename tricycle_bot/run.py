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
import research


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
research.research_step(gc)


##SHARED TEAM INFORMATION##

# WORKER
building_queue = []
blueprinter_assignment = {}
current_worker_roles = {"miner":[],"builder":[],"blueprinter":[]}

# KNIGHT
my_team = gc.team()
knight_clusters = set()
knight_to_cluster = {}


##AI EXECUTION##
while True:
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round())
    try:
        # walk through our units:
        num_workers= num_knights=num_rangers= num_mages= num_healers= num_factory= num_rocket = 0
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Worker:
                num_workers+=1
            elif unit.unit_type == bc.UnitType.Knight:
                num_knights+=1
            elif unit.unit_type == bc.UnitType.Ranger:
                num_rangers+=1
            elif unit.unit_type == bc.UnitType.Mage:
                num_mages+=1
            elif unit.unit_type == bc.UnitType.Healer:
                num_healers+=1
            elif unit.unit_type == bc.UnitType.Factory:
                num_factory+=1
            elif unit.unit_type == bc.UnitType.Rocket:
                num_rocket+=1
        info = [num_workers, num_knights, num_rangers, num_mages, num_healers, num_factory, num_rocket]
        for unit in gc.my_units():
            # resepective unit types execute their own AI
            if unit.unit_type == bc.UnitType.Worker:
                worker.timestep(gc,unit,building_queue,blueprinter_assignment,current_worker_roles)
            elif unit.unit_type == bc.UnitType.Knight:
                knight.timestep(gc,unit,info,knight_to_cluster)
            elif unit.unit_type == bc.UnitType.Ranger:
                ranger.timestep(gc,unit,info)
            elif unit.unit_type == bc.UnitType.Mage:
                mage.timestep(gc,unit,info)
            elif unit.unit_type == bc.UnitType.Healer:
                healer.timestep(gc,unit,info)
            elif unit.unit_type == bc.UnitType.Factory:
                factory.timestep(gc,unit,info)
            elif unit.unit_type == bc.UnitType.Rocket:
                rocket.timestep(gc,unit,info)
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


class Knight_Cluster():
    def __init__(self):
        self.knight_ids = set()
        self.target_loc = None
        self.target_unit = None

    def add_knight(self, knight_id):
        self.knight_ids.add(knight_id)

    def remove_knight(self, knight_id):
        if knight_id in self.knight_ids:
            self.knight_ids.remove(knight_id)

    def set_target_loc(self, loc):
        self.target_loc = loc

    def set_target_unit(self, unit):
        self.target_unit = unit
