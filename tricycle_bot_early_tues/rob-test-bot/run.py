import battlecode as bc
import random
import sys
import traceback
import unitmap
import util

print("pystarting")

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
gc = bc.GameController()

util.gc = gc

umap = unitmap.Unitmap(gc)
umap.generate_map_from_initial_units()
if gc.planet() == bc.Planet.Earth:
    umap.print_map()

print("pystarted")

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Knight)

my_team = gc.team()
if my_team == bc.Team.Red:
    opponent_team = bc.Team.Blue
else:
    opponent_team = bc.Team.Red

while True:
    if gc.planet() == bc.Planet.Mars:
        gc.next_turn()
        continue

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

        if gc.round() % 25 == 0:
            print('Rob:', gc.round(),
                  ' karbonite:', gc.karbonite(),
                  ' units:', len(myWorkers), ',', len(myFactories), ',', len(myKnights), ' debug:', someLoc)

        if len(myWorkers) < 5 and gc.karbonite() > 16:
            # print('Not enough workers:', gc.karbonite())
            d = util.get_random_direction()
            for worker in myWorkers:
                if gc.can_replicate(worker.id, d):
                    gc.replicate(worker.id, d)
                    # print('replicated! ', gc.karbonite())
                    break

        if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and (len(myFactories) < 2 or gc.karbonite() > 300):
            d = util.get_random_direction()
            for worker in myWorkers:
                if gc.can_blueprint(worker.id, bc.UnitType.Factory, d):
                    gc.blueprint(worker.id, bc.UnitType.Factory, d)
                    break

        factoriesToHeal = []
        for factory in myFactories:
            # print("Factory:", factory, " garrison ", len(factory.structure_garrison()), " can produce? ", gc.can_produce_robot(factory.id, bc.UnitType.Knight), "   kar", gc.karbonite())
            if factory.health < factory.max_health:
                factoriesToHeal.append(factory)
            garrison = factory.structure_garrison()
            if len(garrison) > 0:
                d = util.get_random_direction()
                if gc.can_unload(factory.id, d):
                    gc.unload(factory.id, d)
                    # print("Unloaded a knight")
                    continue
            elif gc.can_produce_robot(factory.id, bc.UnitType.Knight):
                gc.produce_robot(factory.id, bc.UnitType.Knight)
                # print("Produced a knight")
                continue

        # Have workers move to
        # TODO: handle being in a garrison
        for worker in myWorkers:
            location = worker.location
            if location.is_on_map():
                closest_factory = None
                closest_factory_distance = 999
                my_location = location.map_location()
                for factory in factoriesToHeal:
                    if my_location.is_adjacent_to(factory.location.map_location()):
                        util.try_build(worker, factory)
                        util.try_repair(worker, factory)
                        # if gc.can_build(worker.id, factory.id):
                        #     # print("Worker ", worker.id, " build factory ", factory.id)
                        #     gc.build(worker.id, factory.id)
                        # if gc.can_repair(worker.id, factory.id):
                        #     # print("Worker ", worker.id, " repaired factory ", factory.id)
                        #     gc.repair(worker.id, factory.id)
                    factory_distance = my_location.distance_squared_to(factory.location.map_location())
                    if factory_distance < closest_factory_distance:
                        closest_factory = factory
                        closest_factory_distance = factory_distance

                util.try_harvesting(worker)

                if closest_factory:
                    direction = my_location.direction_to(closest_factory.location.map_location())
                    if gc.is_move_ready(worker.id) and gc.can_move(worker.id, direction):
                        gc.move_robot(worker.id, direction)
                else:
                    direction = util.get_random_direction()
                    if gc.is_move_ready(worker.id) and gc.can_move(worker.id, direction):
                        gc.move_robot(worker.id, direction)

        enemies = [unit for unit in gc.units() if unit.team != my_team]
        if enemies:
            umap.generate_map_raw(enemies)
        else:
            umap.generate_map_from_initial_units()

        # moves knights towards enemy
        for knight in myKnights:
            location = knight.location
            if location.is_on_map():
                my_location = knight.location.map_location()
                d = umap.get_direction_at_location(location.map_location())
                # if gc.is_move_ready(knight.id) and gc.can_move(knight.id, d):
                #     gc.move_robot(knight.id, d)
                util.try_move_loose(knight, d, 1)

                nearby_enemies = [unit for unit in gc.sense_nearby_units(location.map_location(), 2) if unit.team != my_team]
                for enemy in nearby_enemies:
                    # print("Trying to attack unit: ", gc.is_attack_ready(knight.id), " ", gc.can_attack(knight.id, enemy.id), " D:", my_location.distance_squared_to(enemy.location.map_location()))
                    if gc.is_attack_ready(knight.id) and gc.can_attack(knight.id, enemy.id):
                        # print('attacked a thing!')
                        gc.attack(knight.id, enemy.id)
                        continue

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
