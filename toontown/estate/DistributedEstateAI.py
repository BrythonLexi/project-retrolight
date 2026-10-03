from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
import time

class DistributedEstateAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedEstateAI')
# I've stolen this code from the Anesidora DistrubedEstateAi.py file

    def __init__(self, air, avId, zoneId, ts, dawn, valDict = None):
        DistributedObjectAI.DistributedObjectAI.__init__(self, air)

        # the avatar currently in charge of the estate
        self.notify.debug("created with avId = %d and zoneId = %d" % (avId, zoneId))
        self.avId = avId
        self.zoneId = zoneId

        # simbase.air.lastEstate = self inable to check the estate.

        self.estateType = 0
        self.estateButterflies = None
        self.fishingSpots = None
        self.fishingPonds = None
        self.goons = None
        self.estateTreasurePlanner = None
        self.estateFlyingTreasurePlanner = None
        self.estateFireworks = None
        self.target = None
        self.picnicTable = None
        self.gardenList = [[], [], [], [], [], []]
        self.gardenBoxList = [[], [], [], [], [], []]
        self.houseList = []

        # if not hasattr(self, "decorData"):
        #    self.decorData = []

        self.cannonsEnabled = 0  # simbase.config.GetBool('estate-cannons', 0)
        self.fireworksEnabled = 0
        self.goonEnabled = 0
        self.goons = None
        self.gagBarrels = None
        self.crate = None

        self.cannonFlag = 0
        self.gameTableFlag = False

        # for day/night
        self.serverTime = ts
        self.dawnTime = dawn

        # here we load in all the database fields
        if valDict:
            for key in valDict:
                if hasattr(self, key):
                    self.dclass.directUpdate(self, key, valDict[key])

        # keep track of generation/deletion from stateserver
        self.Estate_generated = 0
        #testFlower = DistributedFlowerAI.DistributedFlowerAI()
        #testGagTree = DistributedGagTreeAI.DistributedGagTreeAI()
        #testStatuary = DistributedStatuaryAI.DistributedStatuaryAI()

        if not hasattr(self, "lastEpochTimeStamp"):
            self.lastEpochTimeStamp = time.time()

        self.accept('gardenTest', self.placeTestGarden)
        self.accept('gardenClear', self.clearMyGarden)
        self.accept('gardenNuke', self.nukeMyGarden)
        self.accept('gardenPlant', self.plantFlower)
        self.accept('wiltGarden', self.wiltMyGarden)
        self.accept('unwiltGarden', self.unwiltMyGarden)
        self.accept('waterGarden', self.setWaterLevelMyGarden)
        self.accept('growthGarden', self.setGrowthLevelMyGarden)
        self.accept('epochGarden', self.doEpochMagicWord)

        self.maxSlots = 32
        self.toonsPerAccount = 6
        #self.timePerEpoch = 300 #five minutes
        #self.timePerEpoch = 30000 #5000 minutes #NO LONGER A VALID CONCEPT AS EPOCHS HAPPEN ONCE A DAY
        self.gardenTable = []
        for count in range(self.toonsPerAccount):

            self.gardenTable.append([0] * self.maxSlots) #ACCOUNT HAS 6 TOONS


    def generate(self):
        DistributedEstateAI.notify.debug("DistEstate generate: %s" % self.doId)
        self.Estate_generated = 1
        DistributedObjectAI.DistributedObjectAI.generate(self)


    def generateWithRequiredAndId(self, doId, air, zoneId):
        self.notify.debug("DistributedEstateAI generateWithRequiredAndId")


        DistributedObjectAI.DistributedObjectAI.generateWithRequiredAndId(self, doId, air, zoneId)

    def initEstateData(self, estateVal=None, numHouses=0, houseId=None, houseVal=None):
        # these parameters have just been read from the database..
        # now we have to do something with them.
        self.numHouses = numHouses
        self.houseType = [None] * self.numHouses
        self.housePos = [None] * self.numHouses
        self.houseId = houseId
        self.houseVal = houseVal
        self.estateVal = estateVal

        # start treasure planner
        self.estateTreasurePlanner = ETreasurePlannerAI.ETreasurePlannerAI(self.zoneId)
        self.estateTreasurePlanner.start()

        # start butterflies
        self.estateButterflies = []
        if simbase.config.GetBool('want-estate-butterflies', 0):
            ButterflyGlobals.generateIndexes(self.avId, ButterflyGlobals.ESTATE)
            for i in range(0,
                    ButterflyGlobals.NUM_BUTTERFLY_AREAS[ButterflyGlobals.ESTATE]):
                for j in range(0,
                    ButterflyGlobals.NUM_BUTTERFLIES[ButterflyGlobals.ESTATE]):
                    bfly = DistributedButterflyAI.DistributedButterflyAI(self.air,
                                         ButterflyGlobals.ESTATE, i, self.avId)
                    bfly.generateWithRequired(self.zoneId)
                    bfly.start()
                    self.estateButterflies.append(bfly)

        # Create fishing docks
        dnaStore = DNAStorage()
        dnaData = simbase.air.loadDNAFileAI(dnaStore,
                  simbase.air.lookupDNAFileName('estate_1.dna'))
        self.fishingSpots = []
        self.fishingPonds = []
        if (isinstance(dnaData, DNAData)):
            fishingPonds, fishingPondGroups = self.air.findFishingPonds(dnaData, self.zoneId, MyEstate, overrideDNAZone = 1)
            self.fishingPonds += fishingPonds
            for dnaGroup, distPond in zip(fishingPondGroups, fishingPonds):
                self.fishingSpots += self.air.findFishingSpots(dnaGroup, distPond)
        else:
            self.notify.warning("loadDNAFileAI failed for 'estate_1.dna'")

        if simbase.wantPets:
            if 0:#__dev__:
                from pandac.PandaModules import ProfileTimer
                pt = ProfileTimer()
                pt.init('estate model load')
                pt.on()

            if not DistributedEstateAI.EstateModel:
                # load up the estate model for the pets
                self.dnaStore = DNAStorage()
                simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('storage_estate.dna'))
                node = simbase.air.loadDNAFile(
                    self.dnaStore,
                    self.air.lookupDNAFileName('estate_1.dna'))
                DistributedEstateAI.EstateModel = hidden.attachNewNode(
                    node)
            render = self.getRender()
            self.geom = DistributedEstateAI.EstateModel.copyTo(render)
            # for debugging, show what's in the model
            if not DistributedEstateAI.printedLs:
                DistributedEstateAI.printedLs = 1
                #self.geom.ls()

            if 0:#__dev__:
                pt.mark('loaded estate model')
                pt.off()
                pt.printTo()



        if self.fireworksEnabled:
            pos = (29.7, -1.77, 10.93)
            import DistributedFireworksCannonAI
            self.estateFireworks = DistributedFireworksCannonAI.DistributedFireworksCannonAI(self.air, *pos)
            self.estateFireworks.generateWithRequired(self.zoneId)

        if self.goonEnabled:
            from toontown.suit import DistributedGoonAI
            self.goons = [None]*3
            for i in range(3):
                self.goons[i] = DistributedGoonAI.DistributedGoonAI(self.air,None,i)
                self.goons[i].setupSuitDNA(1, 1, "c")
                self.goons[i].generateWithRequired(self.zoneId)

            from toontown.coghq import DistributedGagBarrelAI
            self.gagBarrels = [None]*4
            for i in range(4):
                self.gagBarrels[i] = DistributedGagBarrelAI.DistributedGagBarrelAI(self.air, None,
                                                                                   -100-10*i, 30-10*i, 0.2,i,i)
                self.gagBarrels[i].generateWithRequired(self.zoneId)
            from toontown.coghq import DistributedBeanBarrelAI
            jelly = DistributedBeanBarrelAI.DistributedBeanBarrelAI(self.air, None,-150, -20, 0.2)
            jelly.generateWithRequired(self.zoneId)
            self.gagBarrels.append(jelly)

            from toontown.coghq import DistributedCrateAI
            self.crate = DistributedCrateAI.DistributedCrateAI(self.air, -142, 0, 0.0)
            self.crate.generateWithRequired(self.zoneId)

        #self.testPlant = DistributedPlantAI.DistributedPlantAI(self.air)
        #self.testPlant.generateWithRequired(self.zoneId)
        #self.placeOnGround(self.testPlant.doId)
        simbase.estate = self
        #self.b_setDecorData([[2,[0,42,42,1],[512,1024,2048]],[1,[2,3],[512,1024,2048]]])
        #self.air.queryObjectField("DistributedEstate", "setDecorData", self.doId, None)
        #self.b_setDecorData([[1,0,16,16,0]])
    def postHouseInit(self):
        #print("post house Init")

        currentTime = time.time()
        #print("time: %s \n cts:%s" % (currentTime, self.rentalTimeStamp))
        if self.rentalTimeStamp >= currentTime:
            #print("starting cannons")
            if self.rentalType == ToontownGlobals.RentalCannon:
                self.makeCannonsUntil(self.rentalTimeStamp)
            elif self.rentalType == ToontownGlobals.RentalGameTable:
                self.makeGameTableUntil(self.rentalTimeStamp)
        else:
            self.b_setRentalTimeStamp(0)
            pass
            #print("not starting cannons")

    def bootStrapEpochs(self):
        #first update the graden data based on how much time has based
        #print ("last time %s" % (self.lastEpochTimeStamp))
        currentTime = time.time()
        #print ("current time %s" % (currentTime))
        timeDiff = currentTime - self.lastEpochTimeStamp
        #print ("time diff %s" % (timeDiff))

        #self.lastEpochTimeStamp = time.mktime((2006, 8, 24, 10, 50, 31, 4, 237, 1))

        tupleNewTime = time.localtime(currentTime - self.epochHourInSeconds)
        tupleOldTime = time.localtime(self.lastEpochTimeStamp)

        #tupleOldTime = (2006, 6, 18, 0, 36, 45, 0, 170, 1)
        #tupleNewTime = (2006, 6, 19, 3, 36, 45, 0, 170, 1)

        listLastDay = list(tupleOldTime)
        listLastDay[3] = 0 #set hour to epoch time
        listLastDay[4] = 0 #set minute to epoch time
        listLastDay[5] = 0 #set second to epoch time
        tupleLastDay = tuple(listLastDay)

        randomDelay = random.random() * 5 * 60 # random five minute range

        secondsNextEpoch = (time.mktime(tupleLastDay) + self.epochHourInSeconds + self.dayInSeconds + randomDelay) - currentTime


        #should we do the epoch for the current day?
        #beforeEpoch = 1
        #if  tupleNewTime[3] >= self.timeToEpoch:
        #    beforeEpoch = 0

        epochsToDo =  int((time.time() - time.mktime(tupleLastDay)) / self.dayInSeconds)
        #epochsToDo -= beforeEpoch
        if epochsToDo < 0:
            epochsToDo = 0

        print("epochsToDo %s" % (epochsToDo))

        #print("tuple times")
        #print tupleNewTime
        #print tupleOldTime


        if epochsToDo:
            pass
            print("doingEpochData")
            self.doEpochData(0, epochsToDo)
        else:
            pass
            print("schedualing next Epoch")
            #print("Delaying inital epoch")
            self.scheduleNextEpoch()
            self.sendUpdate("setLastEpochTimeStamp", [self.lastEpochTimeStamp])
            #time2Epoch = self.timePerEpoch - timeDiff

    def placeLawnDecor(self, toonIndex, itemList):
        boxList = GardenGlobals.estateBoxes[toonIndex]
        for boxPlace in boxList:
            newBox = DistributedGardenBoxAI.DistributedGardenBoxAI(boxPlace[3])
            newBox.setPosition(boxPlace[0], boxPlace[1], 16)
            newBox.setH(boxPlace[2])
            newBox.generateWithRequired(self.zoneId)
            newBox.setEstateId(self.doId)
            newBox.setupPetCollision()
            self.gardenBoxList[toonIndex].append(newBox)
        plotList = GardenGlobals.estatePlots[toonIndex]
        for plotPointIndex in (range(len(plotList))):
            item = self.findItemAtHardPoint(itemList, plotPointIndex)
            if not item or not GardenGlobals.PlantAttributes.get(item[0]):
                item = None
            if item:
                type = item[0]
                if type not in GardenGlobals.PlantAttributes.keys():
                    self.notify.warning('type %d not found in PlantAttributes, forcing it to 48' % type)
                    type = 48
                hardPoint = item[1]
                waterLevel = item[2]
                growthLevel = item[3]
                optional = item[4] #all fields are 8bit except optional which is 16bits
                itemdoId = self.addLawnDecorItem(toonIndex, type, hardPoint, waterLevel, growthLevel, optional)
            else:
                #pass
                self.addGardenPlot(toonIndex, plotPointIndex)

    def updateToonBonusLevels(self, index):
        # find the trees with fruit
        numTracks = len(ToontownBattleGlobals.Tracks)
        hasBonus = [[] for n in range(numTracks)]
        for distLawnDecor in self.gardenTable[index]:
            # keep track of which trees are blooming
            if distLawnDecor and distLawnDecor.hasGagBonus():
                hasBonus[distLawnDecor.gagTrack].append(distLawnDecor.gagLevel)

        # find the lowest gaglevel for each track that immediately preceeds a non-fruited tree
        # EG.  [0, 1, 2, 4, 5, 6] should find 2
        bonusLevels = [-1] * len(ToontownBattleGlobals.Tracks)
        for track in range(len(hasBonus)):
            hasBonus[track].sort()
            for gagLevel in hasBonus[track]:
                if gagLevel == (bonusLevels[track] + 1):
                    bonusLevels[track] = gagLevel
                else:
                    break

        # tell the toon
        toonId = self.getToonId(index)
        toon = simbase.air.doId2do.get(toonId)
        if toon:
            toon.b_setTrackBonusLevel(bonusLevels)

    def getEstateType(self):
        assert(self.notify.debug("getEstateType"))
        return self.estateType

    def getDawnTime(self):
        return self.dawnTime

    def requestServerTime(self):
        #print ("requestServerTime")
        requesterId = self.air.getAvatarIdFromSender()
        self.serverTime = time.time() % HouseGlobals.DAY_NIGHT_PERIOD
        self.sendUpdateToAvatarId(requesterId, "setServerTime", [self.serverTime])


# lots of get and set functions, not really the prettiest way to do this but it works

    def getToonId(self, slot):
        if slot == 0:
            if hasattr(self, "slot0ToonId"):
                return self.slot0ToonId
        elif slot == 1:
            if hasattr(self, "slot1ToonId"):
                return self.slot1ToonId
        elif slot == 2:
            if hasattr(self, "slot2ToonId"):
                return self.slot2ToonId
        elif slot == 3:
            if hasattr(self, "slot3ToonId"):
                return self.slot3ToonId
        elif slot == 4:
            if hasattr(self, "slot4ToonId"):
                return self.slot4ToonId
        elif slot == 5:
            if hasattr(self, "slot5ToonId"):
                return self.slot5ToonId
        else:
            return None

    def setToonId(self, slot, tag):
        if slot == 0:
            self.slot0ToonId = tag
        elif slot == 1:
            self.slot1ToonId = tag
        elif slot == 2:
            self.slot2ToonId = tag
        elif slot == 3:
            self.slot3ToonId = tag
        elif slot == 4:
            self.slot4ToonId = tag
        elif slot == 5:
            self.slot5ToonId = tag

    def d_setToonId(self, slot, avId):
        if avId:
            if slot == 0:
                self.sendUpdate("setSlot0ToonId", [avId])
            elif slot == 1:
                self.sendUpdate("setSlot1ToonId", [avId])
            elif slot == 2:
                self.sendUpdate("setSlot2ToonId", [avId])
            elif slot == 3:
                self.sendUpdate("setSlot3ToonId", [avId])
            elif slot == 4:
                self.sendUpdate("setSlot4ToonId", [avId])
            elif slot == 5:
                self.sendUpdate("setSlot5ToonId", [avId])

    def b_setToonId(self, slot, avId):
        self.setToonId(slot, avId)
        self.d_setToonId(slot, avId)

    def getItems(self, slot):
        if slot == 0:
            if hasattr(self, "slot0Items"):
                return self.slot0Items
        elif slot == 1:
            if hasattr(self, "slot1Items"):
                return self.slot1Items
        elif slot == 2:
            if hasattr(self, "slot2Items"):
                return self.slot2Items
        elif slot == 3:
            if hasattr(self, "slot3Items"):
                return self.slot3Items
        elif slot == 4:
            if hasattr(self, "slot4Items"):
                return self.slot4Items
        elif slot == 5:
            if hasattr(self, "slot5Items"):
                return self.slot5Items
        else:
            return None

    def setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1, waterLevel=None, growthLevel=-1, variety=-1):
        assert ownerIndex >= 0 and ownerIndex < 6
        itemList = self.getItems(ownerIndex)
        itemsIndex = self.findItemPositionInItemList(itemList, hardPointIndex)
        if itemsIndex != -1 and gardenItemType == -1:
            gardenItemType = itemList[itemsIndex][0]
        if itemsIndex != -1  and waterLevel == None:
            waterLevel = itemList[itemsIndex][2]
        if itemsIndex != -1  and growthLevel == -1:
            growthLevel = itemList[itemsIndex][3]
        if itemsIndex != -1  and variety == -1:
            variety = itemList[itemsIndex][4]
        newInfo = (gardenItemType, hardPointIndex, waterLevel, growthLevel, variety)
        #since itemList is a reference, just update it
        if itemsIndex != -1 :
            itemList[itemsIndex] = newInfo
        else:
            itemList.append(newInfo)

    # Note there is no d_setOneItem, since the whole itemList gets updated

    def b_setOneItem(self, ownerIndex, hardPointIndex, gardenItemType=-1,
                    waterLevel=-1, growthLevel=-1, variety=-1):
       """
       If you're changing multiple items, it's better to call b_setItems than
       multiple calls to b_setOneItem
       """
       self.setOneItem(ownerIndex, hardPointIndex, gardenItemType,
                       waterLevel, growthLevel, variety)
       self.d_setItems(ownerIndex, self.getItems(ownerIndex))




    def setItems(self, slot, items):
        if slot == 0:
            self.slot0Items = items
        elif slot == 1:
            self.slot1Items = items
        elif slot == 2:
            self.slot2Items = items
        elif slot == 3:
            self.slot3Items = items
        elif slot == 4:
            self.slot4Items = items
        elif slot == 5:
            self.slot5Items = items

    def d_setItems(self, slot, items):
        items = self.checkItems(items)
        if slot == 0:
            self.sendUpdate("setSlot0Items", [items])
        elif slot == 1:
            self.sendUpdate("setSlot1Items", [items])
        elif slot == 2:
            self.sendUpdate("setSlot2Items", [items])
        elif slot == 3:
            self.sendUpdate("setSlot3Items", [items])
        elif slot == 4:
            self.sendUpdate("setSlot4Items", [items])
        elif slot == 5:
            self.sendUpdate("setSlot5Items", [items])

    def checkItems(self, items, slot = 0):
        toonId = self.getToonId(slot)
        for item in items:
            if (item[0] < 0) or (item[1] < 0) or (item[4] < 0):
                self.air.writeServerEvent("Removing_Invalid_Garden_Item_on_Toon ", toonId, " item %s" % str(item))
                items.remove(item)
        return items


    def b_setItems(self, slot, items):
        items = self.checkItems(items)
        self.setItems(slot, items)
        self.d_setItems(slot, items)

    def setSlot0ToonId(self, avId):
        self.slot0ToonId = avId

    def setSlot1ToonId(self, avId):
        self.slot1ToonId = avId

    def setSlot2ToonId(self, avId):
        self.slot2ToonId = avId

    def setSlot3ToonId(self, avId):
        self.slot3ToonId = avId

    def setSlot4ToonId(self, avId):
        self.slot4ToonId = avId

    def setSlot5ToonId(self, avId):
        self.slot5ToonId = avId

    def setSlot0Items(self, items):
        self.slot0Items = items

    def setSlot1Items(self, items):
        self.slot1Items = items

    def setSlot2Items(self, items):
        self.slot2Items = items

    def setSlot3Items(self, items):
        self.slot3Items = items

    def setSlot4Items(self, items):
        self.slot4Items = items

    def setSlot5Items(self, items):
        self.slot5Items = items


    def getSlot0ToonId(self):
        if hasattr(self, "slot0ToonId"):
            return self.slot0ToonId
        else:
            return 0

    def getSlot1ToonId(self):
        if hasattr(self, "slot1ToonId"):
            return self.slot1ToonId
        else:
            return 0

    def getSlot2ToonId(self):
        if hasattr(self, "slot2ToonId"):
            return self.slot2ToonId
        else:
            return 0

    def getSlot3ToonId(self):
        if hasattr(self, "slot3ToonId"):
            return self.slot3ToonId
        else:
            return 0

    def getSlot4ToonId(self):
        if hasattr(self, "slot4ToonId"):
            return self.slot4ToonId
        else:
            return 0

    def getSlot5ToonId(self):
        if hasattr(self, "slot5ToonId"):
            return self.slot5ToonId
        else:
            return 0

    def getSlot0Items(self):
        if hasattr(self, "slot0Items"):
            return self.slot0Items
        else:
            return []

    def getSlot1Items(self):
        if hasattr(self, "slot1Items"):
            return self.slot1Items
        else:
            return []

    def getSlot2Items(self):
        if hasattr(self, "slot2Items"):
            return self.slot2Items
        else:
            return []

    def getSlot3Items(self):
        if hasattr(self, "slot3Items"):
            return self.slot3Items
        else:
            return []

    def getSlot4Items(self):
        if hasattr(self, "slot4Items"):
            return self.slot4Items
        else:
            return []

    def getSlot5Items(self):
        if hasattr(self, "slot5Items"):
            return self.slot5Items
        else:
            return []

    def gardenInit(self, avIdList):
        self.sendUpdate('setIdList', [avIdList])
        #self.bootStrapEpochs()


        self.avIdList = avIdList
        #check to see if the av field tags match the house owners
        for index in range(len(avIdList)):
            if self.getToonId(index) != avIdList[index]:
                self.notify.debug("Mismatching Estate Tag index %s id %s list %s" % (index, self.getToonId(index) , avIdList[index]))
            if self.getItems(index) == None:
                self.notify.debug("Items is None index %s items %s" % (index, self.getItems(index)))
            if self.getToonId(index) != avIdList[index] or self.getItems(index) == None:
                self.notify.debug("Resetting items index %s" % (index))
                self.b_setToonId(index, avIdList[index])
                #resetting the item database
                #self.b_setItems(index, [])
                self.b_setItems(index, [(255,0,-1,-1,0)]) #empty garden tag
            if self.getItems(index) == [(255,0,-1,-1,0)]:
                #case where the garden has been tagged as empty
                pass
            elif self.getItems(index) or self.getItems(index) == []:
                self.placeLawnDecor(index, self.getItems(index))
                #print "Item Check"
                #print self.getItems(index)
                pass
            self.updateToonBonusLevels(index)
        self.bootStrapEpochs()
        #self.b_setItems(1,[[49,0,16,16,0]])#get some data up for testing