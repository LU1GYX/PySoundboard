import tkinter as tk
import soundboard as sb
import trayicon as tr
import overlay as ov
import queue

class PySoundBoard:
    def __init__(self, root: tk.Tk):
        self.queue = queue.Queue()
        self.root = root
        self.board = sb.SoundBoard(self.queue)
        self.tray = tr.TrayIcon(self.queue)
        self.overlay = ov.Overlay(root, self.queue)

    def start(self):
        # Start threads with queue communication
        self.board.init().start()
        self.tray.init().start()
        self.overlay.init()

        self.process_queue()

    def process_queue(self):
        while not self.queue.empty():
            message = str(self.queue.get())

            if ":" in message:
                message = message.split(":")

                print(message)

                match message[0]:
                    case "pressed":
                        self.overlay.updateKey(message[1])
                        break
                    case "playing":
                        self.overlay.updateFilename(message[1])
                        break
                    case "sbStatus":
                        self.board.toggleSoundboard(message[1] == "True")
                        self.overlay.updateStatus("ENABLED!" if message[1] == "True" else "DISABLED!")
                        break 
                    case "ovStatus":
                        self.overlay.toggleOveray(message[1] == "True")
                        break
                    case "addBind":
                        break
                    case "listBinds":
                        #Apre finestra (o solo file di testo) lista bind
                        pass

        self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    PySoundBoard(root).start()

    root.mainloop()