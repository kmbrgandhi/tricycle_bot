import battlecode as bc
import random
import sys
import traceback
from queue import PriorityQueue

directions = list(bc.Direction)

import heapq

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

def where_explore(gc, num = 3):
    return

def neighbors(maploc):
    return [maploc.add(dir) for dir in directions[:-1]]

def heuristic(maploc1, maploc2):
    return (maploc1.distance_squared_to(maploc2))**(0.5)

def coords(maploc):
    return (maploc.x, maploc.y)

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
        for next in neighbors(current):
            try:
                unit_at_location = gc.sense_unit_at_location(next)
                if unit_at_location is not None:
                    has_unit = True
            except:
                has_unit = False
            if not planet_map.on_map(next) or not planet_map.is_passable_terrain_at(next) or has_unit:
                continue
            new_cost = cost[coords(current)] + 1
            if coords(next) not in cost or new_cost<cost[coords(next)]:
                cost[coords(next)] = new_cost
                priority = new_cost + heuristic(next, maplocation)
                queue.put(Prioritize(priority, next))
                parent[coords(next)] = current
    iter = maplocation
    path = [current]
    while iter!=init:
        iter = parent[coords(iter)]
        path.append(iter)
    path.reverse()
    return path
    # initial greedy
    return unit.location.map_location().direction_to(maplocation)
