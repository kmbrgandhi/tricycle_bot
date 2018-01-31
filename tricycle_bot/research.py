import battlecode as bc
import random
import sys
import traceback
import Units.variables as variables

def research_step(gc):
    if variables.curr_planet == bc.Planet.Earth:
        gc.queue_research(bc.UnitType.Worker) #25   25
        if variables.knight_rush:
            gc.queue_research(bc.UnitType.Knight) #25: 50
            gc.queue_research(bc.UnitType.Ranger) # 25: 75
            gc.queue_research(bc.UnitType.Knight) #100: 175
        else:
            current = gc.research_info()
            if current.get_level(variables.unit_types["knight"])<2:
                gc.reset_research()
            if variables.curr_planet == bc.Planet.Earth and len(variables.dists)==0:
                gc.queue_research(bc.UnitType.Rocket)
            if current.get_level(variables.unit_types["worker"])!=1:
                gc.queue_research(bc.UnitType.Worker)
            if current.get_level(variables.unit_types["ranger"]) != 1:
                gc.queue_research(bc.UnitType.Ranger)  # 25: 50
            gc.queue_research(bc.UnitType.Healer) #25:  75
            gc.queue_research(bc.UnitType.Healer) #100: 225
            if current.get_level(variables.unit_types["rocket"]) != 1:
                gc.queue_research(bc.UnitType.Rocket) #50:  125
            gc.queue_research(bc.UnitType.Healer)  # 100: 325
            gc.queue_research(bc.UnitType.Ranger) #100: 425
            gc.queue_research(bc.UnitType.Ranger) #200: 625
            gc.queue_research(bc.UnitType.Worker) #75: 700
