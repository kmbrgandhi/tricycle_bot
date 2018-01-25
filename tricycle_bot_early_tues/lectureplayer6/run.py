import battlecode as bc
import random
import sys
import traceback
import os
import time

gc = bc.GameController()
directions = [bc.Direction.North, bc.Direction.Northeast, bc.Direction.East, bc.Direction.Southeast, bc.Direction.South, bc.Direction.Southwest, bc.Direction.West, bc.Direction.Northwest]
allDirections = list(bc.Direction)#includes center, and is weirdly ordered
tryRotate = [0,-1,1,-2,2]
random.seed(6137)
my_team = gc.team()
if my_team==bc.Team.Red:enemy_team = bc.Team.Blue
else: enemy_team = bc.Team.Red

def invert(loc):#assumes Earth
	newx = earthMap.width-loc.x
	newy = earthMap.height-loc.y
	return bc.MapLocation(bc.Planet.Earth,newx,newy)

def locToStr(loc):
	return '('+str(loc.x)+','+str(loc.y)+')'

def onEarth(loc):
	if (loc.x<0) or (loc.y<0) or (loc.x>=earthMap.width) or (loc.y>=earthMap.height): return False
	return True
	
class mmap():
	def __init__(self,width,height):
		self.width=width
		self.height=height
		self.arr=[[0]*self.height for i in range(self.width)];
	def onMap(self,loc):
		if (loc.x<0) or (loc.y<0) or (loc.x>=self.width) or (loc.y>=self.height): return False
		return True
	def get(self,mapLocation):
		if not self.onMap(mapLocation):return -1
		return self.arr[mapLocation.x][mapLocation.y]
	def set(self,mapLocation,val):
		self.arr[mapLocation.x][mapLocation.y]=val
	def printout(self):
		print('printing map:')
		for y in range(self.height):
			buildstr=''
			for x in range(self.width):
				buildstr+=format(self.arr[x][self.height-1-y],'2d')
			print(buildstr)
	def addDisk(self,mapLocation,r2,val):
		locs = gc.all_locations_within(mapLocation,r2)
		for loc in locs:
			if self.onMap(loc):
				self.set(loc,self.get(loc)+val)
	def multiply(self,mmap2):
		for x in range(self.width):
			for y in range(self.height):
				ml = bc.MapLocation(bc.Planet.Earth,x,y);
				self.set(ml,self.get(ml)*mmap2.get(ml))
	def findBest(self,mapLocation,r2):
		locs = gc.all_locations_within(mapLocation,r2)
		bestAmt = 0
		bestLoc = None
		for loc in locs:
			amt = self.get(loc)
			if amt>bestAmt:
				bestAmt=amt
				bestLoc=loc
		return bestAmt, bestLoc

if gc.planet() == bc.Planet.Earth:
	gc.queue_research(bc.UnitType.Worker)
	gc.queue_research(bc.UnitType.Ranger)
	gc.queue_research(bc.UnitType.Ranger)
	oneLoc = gc.my_units()[0].location.map_location()
	loadStart = time.time()
	earthMap = gc.starting_map(bc.Planet.Earth)
	loadEnd = time.time()
	print('loading the map took '+str(loadEnd-loadStart)+'s')
	enemyStart = invert(oneLoc);
	print('worker starts at '+locToStr(oneLoc))
	print('enemy worker presumably at '+locToStr(enemyStart))
	
	#test out addDisk function
	tmap = mmap(earthMap.width,earthMap.height)
	tmap.addDisk(bc.MapLocation(bc.Planet.Earth,1,5),30,1)
	tmap.addDisk(bc.MapLocation(bc.Planet.Earth,3,10),30,1)
	tmap.printout()
	
	#store the map locally
	storageStart=time.time()
	passableMap = mmap(earthMap.width,earthMap.height);
	kMap = mmap(earthMap.width,earthMap.height);
	for x in range(earthMap.width):
		for y in range(earthMap.height):
			ml = bc.MapLocation(bc.Planet.Earth,x,y);
			passableMap.set(ml,earthMap.is_passable_terrain_at(ml))
			kMap.set(ml,earthMap.initial_karbonite_at(ml))
	storageEnd=time.time()
	print('storing the maps took '+str(storageEnd-storageStart)+'s')
	passableMap.printout()
	kMap.printout()
	print('printing the maps took '+str(time.time()-storageEnd)+'s')
	accessLocation = bc.MapLocation(bc.Planet.Earth,10,10)
	accessStart=time.time()
	for x in range(10000):
		locData = gc.starting_map(bc.Planet.Earth).is_passable_terrain_at(accessLocation)
	accessEnd=time.time()
	print('accessing (x10,000) the gc map took '+str(accessEnd-accessStart)+'s')
	accessStart=time.time()
	for x in range(10000):
		locData = passableMap.get(accessLocation)
	accessEnd=time.time()
	print('accessing (x10,000) the local map took '+str(accessEnd-accessStart)+'s')
	
	#generate an ordered list of karbonite locations, sorted by distance to start
	tOrderStart=time.time()
	kLocs = []
	currentLocs = []
	evalMap = mmap(earthMap.width,earthMap.height)
	for unit in gc.my_units():
		currentLocs.append(unit.location.map_location())
	while(len(currentLocs)>0):
		nextLocs = []
		for loc in currentLocs:
			for dir in directions:
				newPlace = loc.add(dir)
				if evalMap.get(newPlace)==0:
					evalMap.set(newPlace,1)
					nextLocs.append(newPlace)
					if kMap.get(newPlace)>0:
						kLocs.append(loc)
		currentLocs=nextLocs
	print('generating kLocs took '+str(time.time()-tOrderStart)+'s')	
	
def rotate(dir,amount):
	ind = directions.index(dir)
	return directions[(ind+amount)%8]

def goto(unit,dest):
	d = unit.location.map_location().direction_to(dest)
	if gc.can_move(unit.id, d):
		gc.move_robot(unit.id,d)
		
def fuzzygoto(unit,dest):
	if unit.location.map_location()==dest:return
	toward = unit.location.map_location().direction_to(dest)
	for tilt in tryRotate:
		d = rotate(toward,tilt)
		if gc.can_move(unit.id, d):
			gc.move_robot(unit.id,d)
			break

def checkK(loc):
	if not onEarth(loc): return 0
	return gc.karbonite_at(loc)
			
def bestKarboniteDirection(loc):
	mostK = 0
	bestDir = None
	for dir in allDirections:
		newK = checkK(loc.add(dir))
		if newK>mostK:
			mostK=newK
			bestDir=dir
	return mostK, bestDir

if gc.planet() == bc.Planet.Earth:
	w=earthMap.width
	h=earthMap.height
else:
	marsMap=gc.starting_map(bc.Planet.Mars)
	w=marsMap.width
	h=marsMap.height

while True:
	try:
		#prepare splash firing map
		umap = mmap(w,h)
		fmap = mmap(w,h)
		for unit in gc.units():
			if not unit.location.is_in_garrison():
				if unit.team==my_team: amt=-1
				else: amt=1
				fmap.addDisk(unit.location.map_location(),2,amt)
				umap.set(unit.location.map_location(),1)
		fmap.multiply(umap)
		if gc.round()==45:
			fmap.printout()
		
		#count things: unfinished buildings, workers
		numWorkers = 0
		blueprintLocation = None
		blueprintWaiting = False
		for unit in gc.my_units():
			if unit.unit_type== bc.UnitType.Factory:
				if not unit.structure_is_built():
					ml = unit.location.map_location()
					blueprintLocation = ml
					blueprintWaiting = True
			if unit.unit_type== bc.UnitType.Worker:
				numWorkers+=1
		
		for unit in gc.my_units():
			if unit.unit_type == bc.UnitType.Worker:
				d = random.choice(directions)
				if numWorkers<10:
					replicated=False
					for d in directions:
						if gc.can_replicate(unit.id,d):
							gc.replicate(unit.id,d)
							replicated=True
							break
					if replicated:continue
				if gc.karbonite() > bc.UnitType.Factory.blueprint_cost():#blueprint
					if gc.can_blueprint(unit.id, bc.UnitType.Factory, d):
						gc.blueprint(unit.id, bc.UnitType.Factory, d)
						continue
				adjacentUnits = gc.sense_nearby_units(unit.location.map_location(), 2)
				for adjacent in adjacentUnits:#build
					if gc.can_build(unit.id,adjacent.id):
						gc.build(unit.id,adjacent.id)
						continue
				#head toward blueprint location
				if gc.is_move_ready(unit.id):
					if blueprintWaiting:
						ml = unit.location.map_location()
						bdist = ml.distance_squared_to(blueprintLocation)
						if bdist>2:
							fuzzygoto(unit,blueprintLocation)
							continue
				#harvest karbonite from nearby
				mostK, bestDir = bestKarboniteDirection(unit.location.map_location())
				if mostK>0:#found some karbonite to harvest
					if gc.can_harvest(unit.id,bestDir):
						gc.harvest(unit.id,bestDir)
						continue
				elif gc.is_move_ready(unit.id):#need to go looking for karbonite
					if len(kLocs)>0:
						dest=kLocs[0]
						if gc.can_sense_location(dest):
							kAmt = gc.karbonite_at(dest)
							if kAmt==0:
								kLocs.pop(0)
							else:
								fuzzygoto(unit,dest)
			
			if unit.unit_type == bc.UnitType.Factory:
				garrison = unit.structure_garrison()
				if len(garrison) > 0:#ungarrison
					d = random.choice(directions)
					if gc.can_unload(unit.id, d):
						gc.unload(unit.id, d)
						continue
				elif gc.can_produce_robot(unit.id, bc.UnitType.Ranger):#produce Mages
					gc.produce_robot(unit.id, bc.UnitType.Ranger)
					continue
			
			if unit.unit_type == bc.UnitType.Ranger:
				if not unit.location.is_in_garrison():#can't move from inside a factory
					attackableEnemies = gc.sense_nearby_units_by_team(unit.location.map_location(),unit.attack_range(),enemy_team)
					if len(attackableEnemies)>0:
						if gc.is_attack_ready(unit.id):
							gc.attack(unit.id, attackableEnemies[0].id)
					elif gc.is_move_ready(unit.id):
						nearbyEnemies = gc.sense_nearby_units_by_team(unit.location.map_location(),unit.vision_range,enemy_team)
						if len(nearbyEnemies)>0:
							destination=nearbyEnemies[0].location.map_location()
						else:
							destination=enemyStart
						fuzzygoto(unit,destination)
			
			# attack
			# if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
				# gc.attack(unit.id, other.id)
			
			# movement
			# elif gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
				# gc.move_robot(unit.id, d)

	except Exception as e:
		print('Error:', e)
		traceback.print_exc()

	# send the actions we've performed, and wait for our next turn.
	gc.next_turn()

	# these lines are not strictly necessary, but it helps make the logs make more sense.
	# it forces everything we've written this turn to be written to the manager.
	sys.stdout.flush()
	sys.stderr.flush()
