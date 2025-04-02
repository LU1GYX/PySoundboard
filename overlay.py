# Standard Library
import tkinter
import tkvideo as tkv
import queue
from PIL import Image, ImageTk

class Overlay:
	"""
	Creates an overlay window using tkinter
	Uses the "-topmost" property to always stay on top of other Windows
	"""
	def __init__(self, tk: tkinter.Tk, queue: queue.Queue):
		self.root = tk
		self.queue = queue
		self.enabled = True

	def init(self) -> None:
		self.root.config(bg="#f8c300")

		self.statusLabel = tkinter.Label(text="PySoundboard: ENABLED!", font=("fixedsys", 10), fg="red", bg="#f8c300")
		self.statusLabel.pack()

		self.keyLabel = tkinter.Label(text="Pressed: None", font=("fixedsys", 10), fg="red", bg="#f8c300")
		self.keyLabel.pack()

		self.filenameLabel = tkinter.Label(font=("fixedsys", 10), fg="red", bg="#f8c300")

		# Set up Ping Label
		#self.videoLabel = tkinter.Label(self.root)
		#self.videoLabel.configure(bg="#f8c300")
		#self.videoLabel.grid(row=1, column=0)
		
		# Set up the video
		""" self.videoPlayer = tkv.tkvideo(r"C:\\Users\\galax\\Desktop\\Loops\\videoplayback.mp4", self.videoLabel, loop=1)
		self.videoPlayer.play() """

		# Define Window Geometry
		self.root.geometry(f"+{self.root.winfo_screenwidth() // 4 }+10")  # Move window to (1/5 width, 100 pixels from top)
		self.root.overrideredirect(True) #NON METTE LA ROBA DI WINDOWS DI DEFAULT
		self.root.wm_attributes("-topmost", True) #SEMPRE IN PRIMO PIANO
		self.root.wm_attributes("-transparentcolor", "#f8c300")

	def toggleOveray(self, enabled: bool):
		self.enabled = enabled

		if self.enabled:
			self.statusLabel.pack()
			self.keyLabel.pack()
			self.filenameLabel.pack()
		else:
			self.statusLabel.pack_forget()
			self.keyLabel.pack_forget()
			self.filenameLabel.pack_forget()
			
	def updateStatus(self, status: str):
		self.statusLabel.config(text="PySoundboard: {0}".format(status))

	def updateKey(self, key: str):
		self.keyLabel.config(text="Pressed: {0}".format(key))

	def updateFilename(self, filename: str):
		self.filenameLabel.config(text="Playing: {0}".format(filename))
		self.filenameLabel.pack()

		self.root.after(2000, self.filenameLabel.pack_forget)

