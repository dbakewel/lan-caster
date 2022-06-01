"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap
import engine.server


class ServerMap(engine.servermap.ServerMap):
    """This servermap tests the follow mechanic."""

    def triggerAddFollow(self, trigger, sprite):
        """Add follows to follow player. 

        This is hardcoded to make it a simple test.
        """
        p = self.findObject(type='player')
        f1 = self.findObject(name="f1")
        f2 = self.findObject(name="f2")
        f3 = self.findObject(name="f3")
        if p and f1 and f2 and f3:
            f1['collisionType'] = 'none'
            f2['collisionType'] = 'none'
            f3['collisionType'] = 'none'
            self.addFollower(sprite, f1)
            self.addFollower(sprite, f2)
            self.addFollower(f2, f3)
            #self.logFollow(self)

    def triggerRemoveFollow(self, trigger, sprite):
        """Remove follows from player. 
        
        This is hardcoded to make it a simple test.
        """
        p = self.findObject(type='player')
        f1 = self.findObject(name="f1")
        f2 = self.findObject(name="f2")
        f3 = self.findObject(name="f3")
        if p and f1 and f2 and f3:
            self.removeFollower(p, f1)
            self.removeFollower(p, f2)
            self.removeFollower(f2, f3)
            #self.logFollow(self)