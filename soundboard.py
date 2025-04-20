import sounddevice as sd
import soundfile as sf
import keyboard as kb
import numpy as np
import json
from pydub import AudioSegment
from psutil import process_iter

from os import path, mkdir, walk
from threading import Thread, Lock
from queue import Queue

class SoundBoard:
    def __init__(self, queue: Queue):
        #self.vcable = None #Uscita audio
        self.queue = queue
        self.enabled = True
        self.playing = False #Flag se l'audio parte

        self.stream = {
            "lock": Lock(),
            "blocksize": 2, #In teoria, se abbasso la cifra, il delay diminuisce... Provare
            "fileposition": 0,
        }

        self.binds = {
            "filename": "binds.json", #Nome del file per le bind
            "data": {} #Container delle Binds
        }

        self.keyData = {
            "latest": None, #Salvataggio key appena premuta
            "stopOn": "p", #Key per interruzione dell'audioo
        }

        self.audio = {
            "filename": None,
            "buffer": np.array([]), #Salvataggio locale audio appena riprodotto
            "samplerate": None, #Framerate dell'audio
            "lenght": None, #Quando è lunga la canzone (ms?)
            "channels": None,
            "gain": 0.1
        }

        self.virtualMic = {
            "index": None,
            "channels": None,
            "samplerate": None,
        }

        self.realMic = {
            "index": None,
            "gain": 1.0
        }

    def init(self):
        self.handleMicrophones()

        if self.virtualMic["index"] == None:
            raise Exception("Virtual Audio Cable not found.")

        self.loadBinds()

        Thread(target=self.handleKeyPress, daemon=True).start()
        Thread(target=self.handleStream, daemon=True).start()

    #MISC

    def toggleSoundboard(self, enabled: bool): 
        self.enabled = enabled 
    
    def installPacket(self, url: str):
        import subprocess
        import zipfile
        import shutil

        zipFile = False
        fileName = url.split('/')[-1] 
        savePath = path.join('./tmp/' + fileName)

        mkdir("./tmp")

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
            savePath = path.join('./tmp/' + fileName.split(".")[0])

        # Find all .exe files in the extracted folder
        exe_files = []
        for root, dirs, files in walk(savePath):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_files.append(path.join(root, file))

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

    #HANDLERS

    def handleStream(self):        
        try:
            stream = sd.Stream(samplerate=self.audio["samplerate"],
                               blocksize=self.stream["blocksize"],
                               channels=(1, 1),
                               device=(self.realMic["index"], self.virtualMic["index"]),
                               dtype='float32',
                               callback=self.onAudio)
            with stream:
                while True:
                    sd.sleep(200)
        except Exception as e:
            raise Exception(e)

    def handleMicrophones(self):
        #Becco il microfono impostato di default
        self.realMic["index"] = sd.default.device[0] #salvo il vecchio microfono

        #Cerco il virtual cable
        #FIX: Uso "CABLE Input" perchè windows taglia i caratteri del nome dopo i 20 caratteri
        outputDevices = [device for device in sorted(sd.query_devices(), key=lambda d: d["index"]) if "CABLE Input" in device["name"]]

        #Prendo sempre il primo dato che è quello originale 
        #TODO: aggiungere controlli per samplerate == 44100 e max_output_channels == 8 //Valori di default di VB
        if len(outputDevices) > 0:
            self.virtualMic["index"] = int(outputDevices[0]["index"])
            self.virtualMic["channels"] = int(outputDevices[0]["max_output_channels"])
            self.virtualMic["sampleRate"] = int(outputDevices[0]["default_samplerate"])
            print("Found VB Cable.")
        else: 
            #Se non lo trovo, faccio partire installazione
            print("Virtual Audio Cable not Found. Staring Download and Installation...")
            self.installPacket('https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack43.zip')

            raise Exception("Virtual Audio Cable Installed. Restart the PC.")
 
        #imposto il microfono virtuale come default, lascio l'output invariato
        sd.default.device = (self.virtualMic, sd.default.device[1])

    def handleKeyPress(self):
        while True:
            event = kb.read_event()
            if event.event_type == kb.KEY_DOWN and self.enabled:
                self.onKey(event)

    #BINDS

    def loadBinds(self):
        try:
            # Load JSON file
            with open('binds.json', 'r') as f: 
                self.binds["data"] = json.load(f)
                print(f'Loaded {len(self.binds["data"])} binds.')

            if len(self.binds["data"]) <= 0:
                print('WARNING: No binds found in {0}'.format(self.binds["filename"]))

        except FileNotFoundError:
            print("'{0}' file not found. Check the path is right.")
        except OSError as e: 
            print("Error in opening '{0}' file.Error: \n{1}".format(self.binds["filename"], e))

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
                self.binds["data"][process][key] = new_bind
            except KeyError:
                self.binds["data"][process] = {}

            self.binds["data"][process][key] = new_bind    
            
            with open('binds.json', 'w') as f:
                json.dump(self.binds["data"], f, indent=4)
            
            print(f"Bind added for key: {key}")

            self.loadBinds()
        except Exception as e:
            self.queue.put("error|Cannot add Bind. Error:" + str(e))

    #EVENTS

    def onKey(self, event):    
        key = event.name.lower()
        process = "default"
        
        #print("Pressed {0}".format(key[0]), end="\r", flush=True)
        self.queue.put("pressed|{0}".format(key))

        #Se un processo e' specificato nel file, allora seguo solo il processo
        #altrimenti ez skip

        for processName in self.binds["data"]:
            if any(proc.name() == processName for proc in process_iter()):
                process = processName
                break

        keyBinds = self.binds["data"][process]

        if key in keyBinds:
            keyBind = keyBinds[key]

            if os.path.exists(os.path.abspath(keyBind["filename"])):
                if not self.playing:
                    #Se la key premuta e' la stessa, evito di ricaricare il tutto
                    if key != self.keyData["latest"]:
                        self.audio["filename"] = keyBind["filename"]
                        #Carico il file
                        self.audio["buffer"], self.audio["samplerate"] = sf.read(keyBind["filename"], dtype='float32')
                        self.audio["buffer"] = np.array(self.audio["buffer"])  # Ensure buffer is a NumPy array

                        # Normalize to 2D array
                        if len(self.audio["buffer"].shape) == 1:
                            self.audio["buffer"] = self.audio["buffer"].reshape(-1, 1)

                        self.audio["channels"] = self.audio["buffer"].shape[1]

                        self.playing = True
                        self.queue.put("playing|{0}".format(self.audio["filename"]))
                        # Adjust the volume of the audio buffer
                        volume_db = keyBind["volume"]  # Volume in decibels
                        volume_factor = 10 ** (volume_db / 20)  # Convert dB to linear scale
                        self.audio["buffer"] *= volume_factor
                        """ audio = AudioSegment.from_mp3(os.path.abspath(keyBind["filename"]))
                        
                        #Sistemo il volume
                        volume_change_db = keyBind["volume"] 
                        audio = audio + volume_change_db

                        #Salvo tutte le info necessarie a far partire l'audio nel thread
                        self.audio["buffer"] = np.array(audio.get_array_of_samples()).reshape((-1, 2))
                        self.audio["sample"] = audio.frame_rate
                        self.audio["length"] = MP3(os.path.abspath(keyBind["filename"])).info.length

                    #Runno tutto nel thread, salvando la reference ad esso per eventualmente stopparlo
                    self.playing = True
                    self.playThread = Thread(target=self.playAudio, daemon=True)
                    self.playThread.run() """
            else:
                self.queue.put("playing|File NOT Found!")

            self.keyData["latest"] = key
            
        if key == self.keyData["stopOn"] and self.playing:    
            self.onAudioEnd()
            self.keyData["latest"] = key

    def onAudio(self, indata, outdata, frames, time, status): 
        if status:
            print("Stream status:", status)

        # Get file chunk
        with self.stream["lock"]:
            # Check if there's audio to play
            if len(self.audio["buffer"]) > 0:
                end = self.stream["fileposition"] + frames

                if end >= len(self.audio["buffer"]):
                    # Stop reproduction if the file reaches its end
                    self.onAudioEnd()
                    file_chunk = np.zeros(frames, dtype='float32')
                else:
                    file_chunk = self.audio["buffer"][self.stream["fileposition"]:end, :]
                    self.stream["fileposition"] += frames

                    # If not enough data left, pad
                    if file_chunk.shape[0] < frames:
                        pad = np.zeros((frames - file_chunk.shape[0], self.audio["channels"]), dtype='float32')
                        file_chunk = np.vstack((file_chunk, pad))

                    # Downmix stereo if needed
                    if file_chunk.shape[1] > 1:
                        file_chunk = file_chunk.mean(axis=1)
                    else:
                        file_chunk = file_chunk[:, 0]

                    # Apply gain
                    file_chunk *= self.audio["gain"]
            else: 
                file_chunk = np.zeros(frames, dtype='float32')

        mic_chunk = indata[:, 0] * self.realMic["gain"]

        # Mix and prevent clipping
        mixed = mic_chunk + file_chunk
        mixed = np.clip(mixed, -1.0, 1.0).reshape(-1, 1)

        outdata[:] = mixed

    def onAudioEnd(self): 
        self.playing = False
        self.audio["buffer"] = np.array([])
        self.stream["fileposition"] = 0
        self.queue.put("playing|STOPPED")
