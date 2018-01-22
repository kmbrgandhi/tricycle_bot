import battlecode as bc
import random
import sys
import traceback
import time
import collections

directions = bc.Direction

"""
import functools

@functools.total_ordering
class Prioritize:

    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority
"""

def maploc_neighbors(maploc):
    return [maploc.add(dir) for dir in directions[:-1]]

def coord_neighbors(coords):
    return [(coords[0]-1, coords[1]-1), (coords[0], coords[1]-1), (coords[0]-1, coords[1]),
            (coords[0] + 1, coords[1] + 1), (coords[0] + 1, coords[1]), (coords[0], coords[1]+1),
            (coords[0] - 1, coords[1] + 1), (coords[0]+1, coords[1]-1)]

def heuristic(maploc1, maploc2):
    return abs(maploc1.x - maploc2.x) + abs(maploc1.y - maploc2.y)

def coords(maploc):
    return (maploc.x, maploc.y)

def precompute_earth(passable_locations_earth, direction_coords, wavepoints):
    store_dict = {}
    for coordinates_fineness in wavepoints:
        parent = bfs(wavepoints[coordinates_fineness], passable_locations_earth)
        for dest_coords in parent:
            direction_tup = (-dest_coords[0]+parent[dest_coords][0], -dest_coords[1]+parent[dest_coords][1])
            store_dict[(dest_coords, coordinates_fineness)] = direction_coords[direction_tup]
    return store_dict

def bfs(init_coords, passable_locations_earth):
    init = init_coords
    q = collections.deque([init])
    parent = {}
    while q:
        curr = q.popleft()
        for node in coord_neighbors(curr):
            if node not in parent and passable_locations_earth[node]:
                q.append(node)
                parent[node] = curr
    return parent

def precompute_earth_dist(passable_locations_earth, direction_coords, wavepoints):
    store_dict = {}
    for coordinates_fineness in wavepoints:
        parent = bfs(wavepoints[coordinates_fineness], passable_locations_earth)
        for dest_coords in parent:
            store_dict[(dest_coords, coordinates_fineness)] = parent[dest_coords]
    return store_dict

def bfs_distance(init_coords, passable_locations_earth):
    init = init_coords
    q = collections.deque([init])
    value = {}
    value[init] = 0
    while q:
        curr = q.popleft()
        for node in coord_neighbors(curr):
            if node not in value and passable_locations_earth[node]:
                q.append(node)
                value[node] = value[curr]+1
    del value[init]
    return value

def bfs_with_destination(init_coords, final_coords, gc, planet, passable_locations_earth, direction_coords):
    init = init_coords
    q = collections.deque([init])
    parent = {}
    while q:
        curr = q.popleft()
        if curr == final_coords:
            break
        for node in coord_neighbors(curr):
            maploc_node = get_maploc(planet, node)
            if node not in parent and passable_locations_earth[node] and not gc.has_unit_at_location(maploc_node):
                q.append(node)
                parent[node] = curr
    if final_coords not in parent:
        return None
    direction_tup = (-final_coords[0] + parent[final_coords][0], -final_coords[1] + parent[final_coords][1])
    return direction_coords[direction_tup]


def precompute_mars(passable_locations_mars, direction_coords, wavepoints):
    store_dict = {}
    for coordinates_fineness in wavepoints:
        parent = bfs_mars(wavepoints[coordinates_fineness], passable_locations_mars)
        for dest_coords in parent:
            direction_tup = (-dest_coords[0]+parent[dest_coords][0], -dest_coords[1]+parent[dest_coords][1])
            store_dict[(dest_coords, coordinates_fineness)] = direction_coords[direction_tup]
    return store_dict

def bfs_mars(init_coords, passable_locations_mars):
    init = init_coords
    q = collections.deque([init])
    parent = {}
    while q:
        curr = q.popleft()
        for node in coord_neighbors(curr):
            if node not in parent and node in passable_locations_mars:
                q.append(node)
                parent[node] = curr
    return parent

def get_maploc(planet, coords):
    map_loc = bc.MapLocation(planet, coords[0], coords[1])
    return map_loc

"""
def exists_movement_path_locs(gc, init_loc, maplocation, planet_map):
    init = init_loc
    planet_map = gc.starting_map(init.planet)
    queue = PriorityQueue()
    queue.put(Prioritize(0, init))
    parent = {}
    cost = {}
    parent[coords(init)] = None
    cost[coords(init)]= 0
    while not queue.empty():
        current = queue.get().item
        if current == maplocation:
            break
        for next in maploc_neighbors(current):
            if not planet_map.on_map(next) or not planet_map.is_passable_terrain_at(next):
                continue
            new_cost = cost[coords(current)] + 1
            if coords(next) not in cost or new_cost<cost[coords(next)]:
                cost[coords(next)] = new_cost
                priority = new_cost + heuristic(next, maplocation)
                queue.put(Prioritize(priority, next))
                parent[coords(next)] = current
    if (maplocation.x, maplocation.y) in parent:
        return True
    return False

def movement_path(gc, unit, maplocation):
    init = unit.location.map_location()
    planet_map = gc.starting_map(init.planet)
    queue = PriorityQueue()
    queue.put(Prioritize(0, init))
    parent = {}
    cost = {}
    parent[coords(init)] = None
    cost[coords(init)]= 0
    while not queue.empty():
        current = queue.get().item
        if current == maplocation:
            break
        for next in maploc_neighbors(current):
            if not planet_map.on_map(next) or not planet_map.is_passable_terrain_at(next) or gc.has_unit_at_location(next):
                continue
            new_cost = cost[coords(current)] + 1
            if coords(next) not in cost or new_cost<cost[coords(next)]:
                cost[coords(next)] = new_cost
                priority = new_cost + heuristic(next, maplocation)
                queue.put(Prioritize(priority, next))
                parent[coords(next)] = current
    iter = maplocation
    if (maplocation.x, maplocation.y) in parent:
        return True
    path = [maplocation]
    while iter!=init:
        iter = parent[coords(iter)]
        path.append(iter)
    path.reverse()
    return path
"""
