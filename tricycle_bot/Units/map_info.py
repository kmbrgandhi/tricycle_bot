import battlecode as bc
import random
import sys
import traceback

def get_initial_karbonite_locations(gc):
    deposit_locations = {}
    start_map = gc.starting_map(bc.Planet(0))
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(bc.Planet(0),x,y)
            karbonite_at = start_map.initial_karbonite_at(map_location)
            if karbonite_at > 0:
                deposit_locations[(x,y)] = karbonite_at
    return deposit_locations

# returns list of MapLocation that are impassable terrain
def get_impassable_terrain(gc,planet):
    impassable_terrain = []
    start_map = gc.starting_map(planet)
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(planet,x,y)   
            if not start_map.is_passable_terrain_at(map_location):
                impassable_terrain.append(map_location)
    return impassable_terrain

def is_next_to_terrain(gc,start_map,location):
    cardinal_directions = [bc.Direction.North, bc.Direction.East, bc.Direction.South, bc.Direction.West]
    for direction in cardinal_directions:
        next_location = location.add(direction)
        if not start_map.on_map(next_location) or not start_map.is_passable_terrain_at(next_location):
            return True
    return False
        

def get_locations_next_to_terrain(gc,planet):
    locations = []
    start_map = gc.starting_map(planet) 
    for x in range(start_map.width):
        for y in range(start_map.height):
            map_location = bc.MapLocation(planet,x,y)
            if not start_map.is_passable_terrain_at(map_location):
                continue
            elif is_next_to_terrain(gc,start_map,map_location):
                locations.append(map_location)
    return locations



    # def update_allies(self): 
    #     ## Knights
    #     remove = set()
    #     for knight_id in self.knights: 
    #         if knight_id not in variables.my_unit_ids: 
    #             remove.add(knight_id)
    #     for unit_id in remove: 
    #         self.knights.remove(unit_id)
    #         self.num_died += 1

    #     ## Rangers 
    #     remove = set() 
    #     for ranger_id in self.rangers: 
    #         if ranger_id not in variables.my_unit_ids: 
    #             remove.add(ranger_id)
    #     for unit_id in remove: 
    #         self.rangers.remove(unit_id)
    #         self.num_died += 1

    #     ## Mages 
    #     remove = set() 
    #     for mage_id in self.mages: 
    #         if mage_id not in variables.my_unit_ids: 
    #             remove.add(mage_id)
    #     for unit_id in remove: 
    #         self.mages.remove(unit_id)
    #         self.num_died += 1

    #     ## Healers 
    #     remove = set() 
    #     for healer_id in self.healers:
    #         if healer_id not in variables.my_unit_ids: 
    #             remove.add(healer_id)
    #     for unit_id in remove: 
    #         self.healers.remove(unit_id)
    #         self.num_died += 1

    #     ## Workers 
    #     remove = set() 
    #     for worker_id in self.healers:
    #         if worker_id not in variables.my_unit_ids: 
    #             remove.add(worker_id)
    #     for unit_id in remove: 
    #         self.workers.remove(unit_id)
    #         self.num_died += 1
