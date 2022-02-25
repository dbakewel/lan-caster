"""ServerMap for Engine Test Map."""

from engine.log import log
import engine.servermap


class ServerMap(engine.servermap.ServerMap):
    """LAYER SHOW MECHANIC

        Only show a layer during steps that a sprite
        is inside a trigger.

        Uses Mechanics: layer visibility.
    """

    def stepMapStartLayerShow(self):
        """LAYER SHOW MECHANIC: stepMapStart method.

        Hide all layers that in listed in layerShow
        trigger properties.

        This needs to be done every step since we don't
        know if a sprite is inside a trigger yet during
        this step.
        """
        for trigger in self.findObject(type="layerShow", objectList=self['triggers'], returnAll=True):
            if not self.checkKeys(trigger, ["prop-layerName"]):
                log("Cannot process layerShow trigger because layerName is missing from trigger properties.", "ERROR")
                return
            self.setLayerVisablitybyName(trigger['prop-layerName'], False)

    def triggerLayerShow(self, trigger, sprite):
        """LAYER SHOW MECHANIC: stepMapStart method.

        Show layer based on trigger properties.

        Trigger Properties:
            layerName: The name of the layer to show.
        """
        if not self.checkKeys(trigger, ["prop-layerName"]):
            log("Cannot process layerShow trigger because layerName is missing from trigger properties.", "ERROR")
            return
        self.setLayerVisablitybyName(trigger['prop-layerName'], True)
