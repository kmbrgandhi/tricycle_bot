import battlecode as bc
import random
import sys
import traceback

def research_step(gc):
    gc.queue_research(bc.UnitType.Worker) #25   25
    gc.queue_research(bc.UnitType.Healer) #25:  50
    gc.queue_research(bc.UnitType.Rocket) #50:  100
    gc.queue_research(bc.UnitType.Healer) #100: 200
    gc.queue_research(bc.UnitType.Ranger) #25: 325
    gc.queue_research(bc.UnitType.Ranger) #100: 425
    gc.queue_research(bc.UnitType.Healer) #100: 300
    gc.queue_research(bc.UnitType.Ranger) #200: 625
    gc.queue_research(bc.UnitType.Worker) #75: 700
