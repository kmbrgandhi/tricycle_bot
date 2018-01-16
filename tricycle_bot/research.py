import battlecode as bc
import random
import sys
import traceback

def research_step(gc):
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Rocket)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Ranger)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Worker)
    gc.queue_research(bc.UnitType.Rocket)
    gc.queue_research(bc.UnitType.Rocket)

