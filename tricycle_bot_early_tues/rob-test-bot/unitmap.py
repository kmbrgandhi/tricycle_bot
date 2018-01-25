import battlecode as bc
from collections import deque
import util


def empty_map(x, y):
    return [[(bc.Direction.Center, -1) for _ in range(0, y)] for _ in range(0, x)]


class Unitmap:
    def __init__(self, gc):
        self.gc = gc
        self.planet = gc.planet()
        self.planet_map = gc.starting_map(self.planet)
        self.size_x = self.planet_map.width
        self.size_y = self.planet_map.height
        self.map = empty_map(self.size_x, self.size_y)
        self.team = gc.team()

    def get_map_width(self):
        return self.size_x

    def get_map_height(self):
        return self.size_y

    def get_planet(self):
        return self.planet

    def clear_map(self):
        self.map = empty_map(self.size_x, self.size_y)

    def print_map(self):
        # print("Values")
        # print("\n".join([" ".join([str(self.map[x][y][1]) for x in range(self.size_x)]) for y in range(self.size_y - 1, -1, -1)]))
        print("Directions")
        print("\n".join(
            ["".join([util.direction_to_str(self.map[x][y][0], self.map[x][y][1]) for x in range(self.size_x)]
                     ) for y in range(self.size_y - 1, -1, -1)]))

    def get_location(self, map_location):
        return self.map[map_location.x][map_location.y]

    def get_value_at_location(self, map_location):
        return self.get_location(map_location)[1]

    def get_direction_at_location(self, map_location):
        return self.get_location(map_location)[0]

    def set_location(self, map_location, values):
        self.map[map_location.x][map_location.y] = values

    def generate_map_raw(self, enemies):
        self.clear_map()
        # location_queue = deque([enemy.location.map_location() for enemy in enemies if enemy.location.is_on_map()])
        # for location in location_queue:
        #    self.set_location(location, (bc.Direction.Center, 0))

        location_queue = deque()
        # Populate initial queue with attackable locations for each enemy
        for enemy in enemies:
            if enemy.location.is_on_map():
                # place enemy in field as goal
                enemy_location = enemy.location.map_location()
                self.set_location(enemy_location, (bc.Direction.Center, 0))
                # for each attackable direction
                for direction in util.orthogonal_directions:
                    # add location to attack from to queue
                    current_location = enemy_location.add(direction)
                    if self.planet_map.on_map(current_location) and self.planet_map.is_passable_terrain_at(current_location):
                        self.set_location(current_location, (util.get_opposite_direction(direction), 1))
                        location_queue.append(current_location)

        while location_queue:
            current_location = location_queue.popleft()
            # print("Popped location:", current_location, " remaining ", len(location_queue))
            value = self.get_value_at_location(current_location) + 1

            for direction in util.movable_directions:
                test_location = current_location.add(direction)
                # print("Testing direction ", direction, " ", get_opposite_direction(direction), " ", test_location, " ", self.planet_map.on_map(test_location), " ", self.planet_map.is_passable_terrain_at(test_location))
                if self.planet_map.on_map(test_location) and self.planet_map.is_passable_terrain_at(test_location):
                    old_value = self.get_value_at_location(test_location)
                    # print("Old value ", old_value, " new value ", value)
                    if old_value == -1 or old_value > value:
                        self.set_location(test_location, (util.get_opposite_direction(direction), value))
                        location_queue.append(test_location)

    def generate_map_from_initial_units(self):
        self.generate_map_raw([unit for unit in self.planet_map.initial_units if unit.team != self.gc.team()])

    def generate_map_from_visible_enemies(self):
        self.generate_map_raw([unit for unit in self.gc.units() if unit.team != self.gc.team()])

    def generate_map(self):
        enemies = [unit for unit in self.gc.units() if unit.team != self.gc.team()]
        if enemies:
            self.generate_map_raw(enemies)
        else:
            self.generate_map_from_initial_units()