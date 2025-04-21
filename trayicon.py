import os
import pystray
import threading
import queue
from PIL import Image

class TrayIcon: 
    def __init__(self, queue: queue.Queue):
        self.ovStatus = True
        self.sbStatus = True

        self.queue = queue
        self.icon = pystray.Icon(
            "Soundboard",
            Image.open("./src/icon_no_text.png"),
            menu=pystray.Menu(
                pystray.MenuItem("Toggle SoundBoard", self.toggleSoundboard, checked=lambda item: self.sbStatus),
                pystray.MenuItem("Add Bind", self.addBind),
                pystray.MenuItem("List Binds", self.listBinds),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Toggle Overlay", self.toggleOverlay, checked=lambda item: self.ovStatus),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.closeEverything),
            )
        )

    def init(self):
        return threading.Thread(target=self.icon.run, daemon=True)

    def toggleOverlay(self):
        self.ovStatus = not self.ovStatus
        self.queue.put("ovStatus|{0}".format(self.ovStatus))

    def toggleSoundboard(self):
        self.sbStatus = not self.sbStatus
        self.queue.put("sbStatus|{0}".format(self.sbStatus))

    def addBind(self):
        self.queue.put("addBind")

    def listBinds(self):
        self.queue.put("listBinds")

    def closeEverything(self):
        self.icon.stop()
        os._exit(0)