import battlecode as bc
import random
import sys
import traceback


# ######################## INITIALIZE ########################
print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()
directions = list(bc.Direction)

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6139)

# GLOBALS
enemy_locations = []
enemies = []

# ######################## Functions ########################


# Simple Actions
def try_harvest(worker):
    for direction in directions:
        if gc.can_harvest(worker.id, direction):
            # TODO: pick best place to harvest
            gc.harvest(worker.id, direction)
            return True
    return False


def try_move_strict(robot, direction):
    if gc.can_move(robot.id, direction) and gc.is_move_ready(robot.id):
        gc.move_robot(robot.id, direction)
        return True
    return False


def try_move_loose(robot, direction, tollerance):
    if not gc.is_move_ready(robot.id):
        return False
    if try_move_strict(robot, direction):
        return True
    left = direction
    right = direction
    for i in range(1, tollerance):
        left = rotate_left(left)
        right = rotate_right(right)
        if try_move_strict(robot, left) or try_move_strict(robot, right):
            return True
    return False


def nearest_enemy(my_map_location):
    nearest = None
    # print("Finding nearest of:", len(enemies), ' to ', my_map_location)
    if len(enemies) > 0:
        nearest_distance = 9999
        for enemy in enemies:
            if enemy.location.is_on_map():
                enemy_distance = my_map_location.distance_squared_to(enemy.location.map_location())
                # print("Enemy is ", enemy_distance, " away.")
                if nearest_distance > enemy_distance:
                    # print("Closer!", enemy_distance)
                    nearest_distance = enemy_distance
                    nearest = enemy
            # else:
            #     print("Enemy not on map:", enemy)
    # print("Found:", nearest)
    return nearest


# basic helper functions
def rotate_left(direction):
    if direction == bc.Direction.North:
        return bc.Direction.Northwest
    if direction == bc.Direction.Northwest:
        return bc.Direction.West
    if direction == bc.Direction.West:
        return bc.Direction.Southwest
    if direction == bc.Direction.Southwest:
        return bc.Direction.South
    if direction == bc.Direction.South:
        return bc.Direction.Southeast
    if direction == bc.Direction.Southeast:
        return bc.Direction.East
    if direction == bc.Direction.East:
        return bc.Direction.Northeast
    if direction == bc.Direction.Northeast:
        return bc.Direction.North
    if direction == bc.Direction.Center:
        return bc.Direction.Center


def rotate_right(direction):
    if direction == bc.Direction.North:
        return bc.Direction.Northeast
    if direction == bc.Direction.Northwest:
        return bc.Direction.North
    if direction == bc.Direction.West:
        return bc.Direction.Northwest
    if direction == bc.Direction.Southwest:
        return bc.Direction.West
    if direction == bc.Direction.South:
        return bc.Direction.Southwest
    if direction == bc.Direction.Southeast:
        return bc.Direction.South
    if direction == bc.Direction.East:
        return bc.Direction.Southeast
    if direction == bc.Direction.Northeast:
        return bc.Direction.East
    if direction == bc.Direction.Center:
        return bc.Direction.Center


def get_opposite_direction(direction):
    if direction == bc.Direction.North:
        return bc.Direction.South
    if direction == bc.Direction.Northwest:
        return bc.Direction.Southeast
    if direction == bc.Direction.West:
        return bc.Direction.East
    if direction == bc.Direction.Southwest:
        return bc.Direction.Northeast
    if direction == bc.Direction.South:
        return bc.Direction.North
    if direction == bc.Direction.Southeast:
        return bc.Direction.Northwest
    if direction == bc.Direction.East:
        return bc.Direction.West
    if direction == bc.Direction.Northeast:
        return bc.Direction.Southwest
    if direction == bc.Direction.Center:
        return bc.Direction.Center

# ######################## Main ##############################

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Rocket)

my_team = gc.team()
if my_team == bc.Team.Red:
    opponent_team = bc.Team.Blue
else:
    opponent_team = bc.Team.Red

while True:
    # We only support Python 3, which means brackets around print()

    myFactories = []
    myWorkers = []
    myHealers = []
    myKnights = []
    myMages = []
    myRangers = []
    myRockets = []

    someLoc = None

    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():
            if unit.unit_type == bc.UnitType.Factory:
                myFactories.append(unit)
            elif unit.unit_type == bc.UnitType.Worker:
                myWorkers.append(unit)
            elif unit.unit_type == bc.UnitType.Knight:
                myKnights.append(unit)
            elif unit.unit_type == bc.UnitType.Ranger:
                myRangers.append(unit)
            elif unit.unit_type == bc.UnitType.Healer:
                myHealers.append(unit)
            elif unit.unit_type == bc.UnitType.Mage:
                myMages.append(unit)
            elif unit.unit_type == bc.UnitType.Rocket:
                myRockets.append(unit)
            else:
                print("ERROR: Unknown unit type ", unit)
            if someLoc is None and unit.location.is_on_map():
                someLoc = unit.location.map_location()
        """
        print('Ranger Rush:', gc.round(),
              ' karbonite:', gc.karbonite(),
              ' units:', len(myWorkers), ',', len(myFactories), ',', len(myRangers))
        """
        if len(myWorkers) < 5 and gc.karbonite() > 16:
            #print('Not enough workers:', gc.karbonite())
            d = random.choice(directions)
            for worker in myWorkers:
                if gc.can_replicate(worker.id, d):
                    gc.replicate(worker.id, d)
                    #print('replicated! ', gc.karbonite())
                    break

        if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and (len(myFactories) < 3 or gc.karbonite() > 300):
            d = random.choice(directions)
            for worker in myWorkers:
                if gc.can_blueprint(worker.id, bc.UnitType.Factory, d):
                    gc.blueprint(worker.id, bc.UnitType.Factory, d)
                    break

        factoriesToHeal = []
        for factory in myFactories:
            if factory.health < factory.max_health:
                factoriesToHeal.append(factory)
            garrison = factory.structure_garrison()
            if len(garrison) > 0:
                d = random.choice(directions)
                if gc.can_unload(factory.id, d):
                    gc.unload(factory.id, d)
                    continue
            elif gc.can_produce_robot(factory.id, bc.UnitType.Ranger):
                gc.produce_robot(factory.id, bc.UnitType.Ranger)
                continue

        # Have workers move to
        for worker in myWorkers:
            location = worker.location
            if not location.is_on_map():
                # can't do anything, in garrison or rocket
                continue
            map_location = location.map_location()

            # what to do?
            # Action: try building or repairing
            nearby = gc.sense_nearby_units(map_location, 2)
            for other in nearby:
                if gc.can_build(worker.id, other.id):
                    gc.build(worker.id, other.id)
                    # print('built a factory!')
                    # skip moving
                    continue
                if gc.can_repair(worker.id, other.id):
                    gc.repair(worker.id, other.id)
                    #print('repaired a factory!')
                    continue
            # Action: try harvesting
            try_harvest(worker)

            # where to go?
            if len(factoriesToHeal) > 0:  # move towards closest factory
                closestFactory = None
                distance = 999
                mapLocation = location.map_location()
                for factory in factoriesToHeal:
                    loc = factory.location.map_location()
                    dist = mapLocation.distance_squared_to(loc)
                    if dist < distance:
                        distance = dist
                        closestFactory = factory
                if closestFactory is not None:
                    # print("Moving to closest factory:", dist)
                    d = mapLocation.direction_to(factory.location.map_location())
                    try_move_strict(worker, d)
                    # if gc.is_move_ready(worker.id) and gc.can_move(worker.id, d):
                    #     gc.move_robot(worker.id, d)
            else:  # move randomly
                d = random.choice(directions)
                try_move_loose(worker, d, 1)
                # if gc.is_move_ready(worker.id) and gc.can_move(worker.id, d):
                #     gc.move_robot(worker.id, d)

        enemy_locations = []
        # sense enemies
        if someLoc is not None:
            enemies = list(gc.sense_nearby_units_by_team(someLoc, 5001, opponent_team))
            #print('enemies sensed:', len(enemies))
            for unit in enemies:
                if unit.location.is_on_map():
                    enemy_locations.append(unit.location.map_location())

        # moves knights around randomly
        for ranger in myRangers:
            location = ranger.location
            if location.is_on_map():
                mapLoc = location.map_location()
                nearby = gc.sense_nearby_units(location.map_location(), 2)
                for other in nearby:
                    if other.team != my_team and gc.is_attack_ready(ranger.id) and gc.can_attack(ranger.id, other.id):
                        #print('attacked a thing!')
                        gc.attack(ranger.id, other.id)
                        continue

                target = nearest_enemy(mapLoc)
                if target is not None:
                    if gc.is_attack_ready(ranger.id) and gc.can_attack(ranger.id, target.id):
                        #print('better attack')
                        gc.attack(ranger.id, target.id)
                    distance = mapLoc.distance_squared_to(target.location.map_location())
                    if not target.location.map_location().is_within_range(ranger.attack_range(), mapLoc):
                        try_move_loose(ranger, mapLoc.direction_to(target.location.map_location()), 2)
                    elif target.location.map_location().is_within_range(ranger.ranger_cannot_attack_range()+1, mapLoc):
                        try_move_loose(ranger, target.location.map_location().direction_to(mapLoc), 2)

                else:
                    d = random.choice(directions)
                    if gc.is_move_ready(ranger.id) and gc.can_move(ranger.id, d):
                        gc.move_robot(ranger.id, d)

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
