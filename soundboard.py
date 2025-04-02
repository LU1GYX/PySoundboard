import sounddevice as sd
import json
import keyboard
from pydub import AudioSegment
import numpy as np
import psutil
import os
import threading
import subprocess
import zipfile
import shutil
import queue

class SoundBoard:
    def __init__(self, queue: queue.Queue):
        self.vcable = None #Uscita audio
        self.stopKey = "p" #Key per interruzione dell'audioo
        self.bindsFile = "binds.json" #Nome del file per le bind
        self.binds = {} #Container delle Binds
        self.queue = queue
        self.enabled = True

        self.audio = {
            "filename": None,
            "playing": False, #Flag se l'audio parte
            "buffer": None, #Salvataggio locale audio appena riprodotto
            "sample": None, #Framerate dell'audio
            "latest": None, #Salvataggio key appena premuta
            "thread": None #Thread per la riproduzione async
        }

    def init(self):
        self.findVirtualCable()

        if self.vcable == None:
            return

        self.loadBinds()

        return threading.Thread(target=self.start, daemon=True)

    def findVirtualCable(self):
        devices = [device for device in sd.query_devices() if 'CABLE Input (VB-Audio Virtual Cable)' in device["name"]]

        if len(devices) == 0:
            print("Virtual Audio Cable not Found. Staring Download and Installation...")
            self.installPacket('https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip')

            if input("Install Voicemeeter too? (Press Enter to install, any key to skip)") == '':
                self.installPacket('https://download.vb-audio.com/Download_CABLE/VoicemeeterSetup_v2119.zip')

            print("Restart the PC and then open again this app.")
            return

        for device in devices:
            if device['max_output_channels'] == 16: #Da provare anche quello a 2 canali a vedere se si sente meglio
                self.vcable = device
                print(f'Virtual audio cable found: {self.vcable["name"]}')
                return

    def loadBinds(self):
        try:
            # Load JSON file
            with open('binds.json', 'r') as f: 
                self.binds = json.load(f)
                print(f'Loaded {len(self.binds)} binds.')

            if len(self.binds) <= 0:
                print('WARNING: No binds found in {0}'.format(self.bindsFile))

        except FileNotFoundError:
            print("'{0}' file not found. Check the path is right.")
        except OSError as e: 
            print("Error in opening '{0}' file. Error: {1}".format(self.bindsFile, e))

    def addBind(self):
        while True:
            key = input("Enter key for binding: ").strip()
            if len(key) == 1 and key.isprintable():
                break
            print("Please enter a single valid character")

        while True:
            filename = input("Enter audio filename (with extension): ").strip()
            if os.path.exists(os.path.join("./sounds", filename)):
                break
            print("File not found in sounds directory")

        while True:
            try:
                volume = float(input("Enter volume adjustment in dB (e.g. 5.0): "))
                if -100 <= volume <= 100:
                    break
                print("Volume must be between -100 and 100 dB")
            except ValueError:
                print("Please enter a valid number")

        process = input("Enter process name to monitor (optional, press Enter to skip): ").strip()
        if process and not any(proc.name() == process for proc in psutil.process_iter()):
            print("Warning: Process not currently running")

        new_bind = {
            "filename": filename,
            "volume": volume
        }
        
        if process:
            new_bind["process"] = process
    
        self.binds[key] = new_bind
        
        with open('binds.json', 'w') as f:
            json.dump(self.binds, f, indent=4)
        
        print(f"Bind added for key: {key}")

        self.loadBinds()

    def playAudio(self):
        self.queue.put("playing:{0}".format(self.audio["filename"]))
        sd.play(data=self.audio["buffer"], samplerate=self.audio["sample"], device=self.vcable['index'])
        self.audio["playing"] = False

    def onKey(self, event):    
        key = event.name.lower()
        process = "default"
        
        #print("Pressed {0}".format(key[0]), end="\r", flush=True)
        self.queue.put("pressed:{0}".format(key))

        #Se un processo e' specificato nel file, allora seguo solo il processo
        #altrimenti ez skip

        for processName in self.binds:
            if any(proc.name() == processName for proc in psutil.process_iter()):
                process = processName
                break

        keyBinds = self.binds[process]

        if key in keyBinds and not self.audio["playing"]:
            keyBind = keyBinds[key]

            self.audio["playing"] = True

            #Se la key premuta e' la stessa, evito di ricaricare il tutto
            if key != self.audio["latest"]:
                self.audio["filename"] = keyBind["filename"]

                #Carico il file
                audio = AudioSegment.from_mp3("./sounds/" + keyBind["filename"])
                    
                #Sistemo il volume
                volume_change_db = keyBind["volume"] 
                audio = audio + volume_change_db

                #Salvo tutte le info necessarie a far partire l'audio nel thread
                self.audio["buffer"] = np.array(audio.get_array_of_samples()).reshape((-1, 2))
                self.audio["sample"] = audio.frame_rate
                self.audio["latest"] = key


            #Runno tutto nel thread, salvando la reference ad esso per 
            #eventualmente stopparlo
            self.audio["thread"] = threading.Thread(target=self.playAudio, daemon=True)
            self.audio["thread"].run()
            
        if key == self.stopKey:
            sd.stop()      
            self.queue.put_nowait("playing:INTERRUPTED!")

    def start(self):
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN and self.enabled:
                self.onKey(event)

    def toggleSoundboard(self, enabled: bool): 
        self.enabled = enabled            

    def installPacket(self, url: str):
        zipFile = False
        fileName = url.split('/')[-1] 
        savePath = os.path.join('./tmp/' + fileName)

        os.mkdir("./tmp")

        if url.endswith('zip'):
            print("Downloaded file is a compressed file. Handling this variable...")
            zipFile = True

        try:
            import urllib.request
            print(f"Downloading {url}...")
            urllib.request.urlretrieve(url, savePath)
        except Exception as e:
            print(f"Failed to download file: {str(e)}")
            return

        if zipFile:
            with zipfile.ZipFile(savePath, 'r') as zip_ref:
                zip_ref.extractall('./tmp/' + fileName.split(".")[0])
            savePath = os.path.join('./tmp/' + fileName.split(".")[0])

        # Find all .exe files in the extracted folder
        exe_files = []
        for root, dirs, files in os.walk(savePath):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_files.append(os.path.join(root, file))

        # Prioritize x64 version if available
        installer_path = None
        for exe in exe_files:
            if '64' in exe.lower():
                installer_path = exe
                break
        
        if installer_path is None and exe_files:
            installer_path = exe_files[0]

        if not installer_path:
            print("No installer executable found in the extracted files")
            return
        
        subprocess.run([installer_path, "/silent"])

        shutil.rmtree("./tmp")
