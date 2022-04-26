import engine.servermap

class ServerMap(engine.servermap.ServerMap):

    def triggerSayhello(self, trigger, sprite):
        self.setSpriteSpeechText(sprite, f"Hello World!")