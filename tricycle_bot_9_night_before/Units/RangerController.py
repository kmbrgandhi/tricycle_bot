import battlecode as bc
import random
import sys
import traceback

class MapView:
    def __init__(self, gc):
        self.x = gc.starting_map(gc.planet()).height
        self.y = gc.starting_map(gc.planet()).width
        self.initial_units = gc.starting_map(gc.planet())
        self.enemy_locs = []
        for unit in self.units:
            if unit.team!=gc.team():
                self.enemy_locs.append(unit.location.map_location())
        self.visibility = {}
        for i in range(self.x):
            for j in range(self.y):
                self.visibility[(i, j)] =0

    def update(self):
        return


def getMapLoc(gc, x, y):
    return bc.MapLocation(gc.planet(), x, y)


class PathController:
    def __init__(self, gc):
        self.gc = gc
        self.units = []
        self.units_to_move = {}
        self.visibility = {}

    def add_unit(self, unit, dest):
        # add a unit to the movement queue
        self.units_to_move[unit] = dest


    def remove_unit(self, unit):
        # if a unit enters battle, it will likely get removed from the movement queue
        if unit in self.units_to_move:
            del self.units_to_move[unit]

    def process_movements(self):
        return








