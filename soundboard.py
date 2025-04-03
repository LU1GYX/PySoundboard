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
from mutagen.mp3 import MP3

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
            "thread": None, #Thread per la riproduzione async
            "timer": None, #Timer per il callback
        }

    def init(self):
        self.findVirtualCable()

        if self.vcable == None:
            raise Exception("Virtual Audio Cable not found.")

        self.loadBinds()

        return threading.Thread(target=self.scanKey, daemon=True)

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
            if device['max_output_channels'] > 2: #Da provare anche quello a 2 canali a vedere se si sente meglio
                self.vcable = device
                self.outChs = device['max_output_channels']
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
            print("Error in opening '{0}' file.Error: \n{1}".format(self.bindsFile, e))

    def addBind(self, data: dict  = None):
        try:
            if data == None or None in data.values():
                raise ValueError("Missing data in bind.")

            if data != None:
                filename = data["filename"]
                key = data["key"]
                volume = int(data["volume"])
                process = data["process"]

            new_bind = {
                "filename": filename,
                "volume": volume
            }
            
            try:
                self.binds[process][key] = new_bind
            except KeyError:
                self.binds[process] = {}

            self.binds[process][key] = new_bind    
            
            with open('binds.json', 'w') as f:
                json.dump(self.binds, f, indent=4)
            
            print(f"Bind added for key: {key}")

            self.loadBinds()
        except Exception as e:
            self.queue.put("error|Cannot add Bind. Error:" + str(e))

    def scanKey(self):
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN and self.enabled:
                self.onKey(event)

    def onKey(self, event):    
        key = event.name.lower()
        process = "default"
        
        #print("Pressed {0}".format(key[0]), end="\r", flush=True)
        self.queue.put("pressed|{0}".format(key))

        #Se un processo e' specificato nel file, allora seguo solo il processo
        #altrimenti ez skip

        for processName in self.binds:
            if any(proc.name() == processName for proc in psutil.process_iter()):
                process = processName
                break

        keyBinds = self.binds[process]

        if key in keyBinds:
            keyBind = keyBinds[key]

            if os.path.exists(os.path.abspath(keyBind["filename"])):
                if not self.audio["playing"]:
                    #Se la key premuta e' la stessa, evito di ricaricare il tutto
                    if key != self.audio["latest"]:
                        self.audio["filename"] = keyBind["filename"]
                        #Carico il file
                        audio = AudioSegment.from_mp3(os.path.abspath(keyBind["filename"]))
                        
                        #Sistemo il volume
                        volume_change_db = keyBind["volume"] 
                        audio = audio + volume_change_db

                        #Salvo tutte le info necessarie a far partire l'audio nel thread
                        self.audio["buffer"] = np.array(audio.get_array_of_samples()).reshape((-1, 2))
                        self.audio["sample"] = audio.frame_rate
                        self.audio["length"] = MP3(os.path.abspath(keyBind["filename"])).info.length

                    #Runno tutto nel thread, salvando la reference ad esso per eventualmente stopparlo
                    self.audio["playing"] = True
                    self.audio["thread"] = threading.Thread(target=self.playAudio, daemon=True)
                    self.audio["thread"].run()
            else:
                self.queue.put("playing|File NOT Found!")

            self.audio["latest"] = key
            
        if key == self.stopKey and self.audio["playing"]:    
            self.stopAudio()
            self.audio["latest"] = key

    def playAudio(self):
        self.queue.put("playing|{0}".format(self.audio["filename"]))
        
        sd.play(data=self.audio["buffer"], samplerate=self.audio["sample"], device=self.vcable['index'])

        self.audio["timer"] = threading.Timer(self.audio["length"], self.stopAudio)
        self.audio["timer"].start()

    def stopAudio(self):
        sd.stop()
        self.audio["playing"] = False
        self.queue.put_nowait("playing|INTERRUPTED!")

        #Resetto il timer (failsafe nel caso di spam di pauseButton)
        if self.audio["timer"] != None:
            self.audio["timer"].cancel()
            self.audio["timer"] = None

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
