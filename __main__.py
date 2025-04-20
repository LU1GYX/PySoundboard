import tkinter as tk
import soundboard as sb
import trayicon as tr
import overlay as ov
import queue
import psutil

from tkinter import filedialog, ttk, messagebox

class PySoundBoard:
    def __init__(self, root: tk.Tk):
        self.queue = queue.Queue()
        self.root = root
        self.board = sb.SoundBoard(self.queue)
        self.tray = tr.TrayIcon(self.queue)
        self.overlay = ov.Overlay(root, self.queue)

    def start(self):
        # Start threads with queue communication
        self.board.init()
        self.tray.init().start()
        self.overlay.init()

        self.processQueue()

    def processQueue(self):
        while not self.queue.empty():
            message = str(self.queue.get())
            message = message.split("|") if "|" in message else [message, None]

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
                    self.bindWindow.deiconify()
                    self.bindWindow.focus_force()
                    break
                case "listBinds":
                    self.listWindow.deiconify()
                    self.listWindow.focus_force()
                    pass
                case "error":
                    messagebox.showerror("Error", message[1])
                    break

        self.root.after(100, self.processQueue)

    def setupAddBind(self): 
        self.bindWindow = tk.Toplevel(self.root)
        self.bindWindow.title("Add new Bind")
        self.bindWindow.resizable(False, False)

        varVolume = tk.IntVar()
        varPath = tk.StringVar()
        varProcess = tk.StringVar()
        varKey = tk.StringVar()

        def selectFile():
            pathSelected = filedialog.askopenfilename(title="Select a Sound", filetypes=[("MP3 Files", "*.mp3"), ("All files", "*.*")])
            if pathSelected:
                varPath.set(pathSelected)
        
        def getProcesses():
            processes = []

            #Prendo tutti i processi Attivi
            for process in psutil.process_iter(["pid", "name", "username"]):
                try:
                    user = process.username()
                    if user != "None":
                        processes.append(process.name())
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            #Rimuovo duplicati e sorto
            processes = list(set(processes))
            processes.sort()

            processes.insert(0, "default") #Aggiungo None come prima opzione

            return processes
        
        def addBind():
            bindData = {
                "filename": path.get() or None,
                "process": process.get() or None,
                "volume": volume.get() or None,
                "key": key.get() or None
            }
            self.board.addBind(bindData)
            messagebox.showinfo("Bind Added", "Bind added successfully!")
            self.bindWindow.withdraw()

        def keyHandler(event):
            varKey.set(str(event.keysym))
            return "break" #Evito di triggerare l'evento di default
        
        def idleHandler():
            #Imposto i valori di default e carico i processi correnti da mettere dentro la combobox
            process.config(values=getProcesses())
            process.set("default")
            volume.set(0)

        #Labels
        tk.Label(self.bindWindow, text="Path", anchor="w", width=10).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.bindWindow, text="Process", anchor="w", width=10).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.bindWindow, text="Volume", anchor="w", width=10).grid(row=2, column=0, padx=5, pady=2, sticky="w")
        tk.Label(self.bindWindow, text="Key", anchor="w", width=10).grid(row=3, column=0, padx=5, pady=2, sticky="w")

        #File
        path = tk.Entry(self.bindWindow, textvariable=varPath, width=23)
        path.grid(row=0, column=1, padx=5, sticky="w")

        #Browse
        tk.Button(self.bindWindow, text="Browse", command=selectFile, width=10, height=1).grid(row=0, column=2, padx=5, pady=2, sticky="w")

        #Process
        process = ttk.Combobox(self.bindWindow, width=35, textvariable=varProcess, state="readonly")
        process.grid(row=1, column=1, columnspan=2, padx=5, pady=2, sticky="w")

        #Volume
        volume = ttk.Spinbox(self.bindWindow, textvariable=varVolume, from_=-100, to=100, width=5, increment=1)
        volume.grid(row=2, column=1, columnspan=2, padx=5, pady=2, sticky="w")

        #Key
        key = tk.Entry(self.bindWindow, textvariable=varKey, width=20)
        key.grid(row=3, column=1, padx=5, sticky="w")
        key.bind("<KeyPress>", keyHandler)

        #Add Bind
        tk.Button(self.bindWindow, text="Add Bind", command=addBind).grid(row=4, column=0, padx=5, pady=2, columnspan=3)
        
        #Event Handlers
        self.bindWindow.protocol("WM_DELETE_WINDOW", lambda: self.bindWindow.withdraw())
        self.bindWindow.bind("<Return>", lambda event: addBind())
        self.bindWindow.after("idle", idleHandler)

        self.bindWindow.withdraw()

    def setupListBind(self):
        self.listWindow = tk.Toplevel(self.root)
        self.listWindow.title("Binds List")
        self.listWindow.geometry("800x300")

        columns = ("Process", "Key", "Filename", "Volume")
        tree = ttk.Treeview(self.listWindow, columns=columns, show="headings", height=10)
        tree.pack(padx=10, pady=10, anchor="ne", fill="both", expand=True)

        for col in columns:
            tree.heading(col, text=col)

            match col:
                case "Process":
                    tree.column(col, width=50, anchor="center")
                    pass
                case "Key":
                    tree.column(col, width=10, anchor="center")
                    pass
                case "Filename":
                    tree.column(col, width=200, anchor="center")
                    pass
                case "Volume":
                    tree.column(col, width=10, anchor="center")
                    pass

        # Populate treeview with binds
        def populateTree():
            for item in tree.get_children():
                tree.delete(item)  # Clear existing items

            for key, bind in self.board.binds["data"].items():
                for keyBind, bindData in bind.items():
                    tree.insert("", "end", values=(key, keyBind, bindData["filename"], bindData["volume"]))

        self.listWindow.protocol("WM_DELETE_WINDOW", lambda: self.listWindow.withdraw())
        self.listWindow.after("idle", populateTree)

        self.listWindow.withdraw()

if __name__ == "__main__":
    root = tk.Tk()

    app = PySoundBoard(root)
    app.setupAddBind()
    app.setupListBind()
    app.start()

    root.mainloop()