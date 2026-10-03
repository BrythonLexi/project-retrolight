from direct.directnotify import DirectNotifyGlobal
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from toontown.toonbase import ToontownGlobals

class EstateManagerAI(DistributedObjectAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('EstateManagerAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.air = air
        self.estateZones = {}
        print("AI: EstateManagerAI constructed, will be doId 4614")

    def getEstateZone(self, avId, name):
        print("AI: getEstateZone called avId=%s name=%s" % (avId, name))
        requesterId = self.air.getAvatarIdFromSender()
        print("AI: requesterId=%s" % requesterId)
        zoneId = self.getEstateZoneForAvatar(avId)
        print("AI: computed zoneId=%s" % zoneId)
        self.sendUpdateToAvatarId(requesterId, 'setEstateZone', [avId, zoneId])
        print("AI: response sent")

    def generate(self):
        DistributedObjectAI.generate(self)
        print("AI: EstateManagerAI.generate, doId=%s" % self.doId)

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        print("AI: EstateManagerAI.announceGenerate, doId=%s" % self.doId)

    def exitEstate(self):
        avId = self.air.getAvatarIdFromSender()

    def removeFriend(self, ownerID, friendId):
        pass

    def getEstateZoneForAvatar(self, avId):
        zone = ToontownGlobals.EstateZoneBase + (avId % 6)
        print("AI: getEstateZoneForAvatar returning", zone)
        return zone
