import tkinter as tk
import queue
import tkinter.ttk as ttk
from PIL import Image, ImageTk

ALPHA_VISIBLE = 0.5
ALPHA_SEMIVISIBLE = 0.1
ALPHA_INVISIBLE = 0

class Overlay:
	def __init__(self, tk: tk.Tk, queue: queue.Queue):
		self.root = tk
		self.queue = queue
		self.enabled = True
		self.onHover = False

	def init(self) -> None:
		self.main = tk.Frame(self.root, padx=5, pady=5, bg="#808080", borderwidth=3, relief="solid")
		self.main.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S)) 

		titleFrame = tk.Frame(self.main, bg="#808080")
		titleFrame.grid(column=0, row=0, columnspan=2, sticky=tk.W)

		titleLabel = tk.Label(titleFrame, text="PySoundboard", font=("Arial", 12, "bold"), bg="#808080")
		titleLabel.pack(side=tk.LEFT)

		try:
			image = Image.open("./src/icon_no_text.png")
			image = image.resize((40, 40), Image.Resampling.LANCZOS)
			photo = ImageTk.PhotoImage(image)
			icon_label = ttk.Label(titleFrame, image=photo, background="#808080")
			icon_label.image = photo
			icon_label.pack(side=tk.RIGHT)
		except Exception as e:
			print(e)
			pass

		self.statusLabel = tk.Label(self.main, text="Status: None", font=("Arial", 8), padx=2, pady=2, anchor="w", width=25, bg="#808080")
		self.statusLabel.grid(column=0, row=1, columnspan=2)

		self.keyLabel = tk.Label(self.main, text="Key: None", font=("Arial", 8), padx=2, pady=2, anchor="w", width=25, bg="#808080")
		self.keyLabel.grid(column=0, row=2, columnspan=2)

		self.filenameLabel = tk.Label(self.main, text="Playback: None", font=("Arial", 8), padx=2, pady=2, anchor="w", width=25, bg="#808080")
		self.filenameLabel.grid(column=0, row=3, columnspan=2)

		self.root.geometry(f"+{self.root.winfo_screenwidth() // 4 }+5")
		self.root.overrideredirect(True) #NON METTE LA ROBA DI WINDOWS DI DEFAULT
		self.root.wm_attributes("-topmost", True) #SEMPRE IN PRIMO PIANO
		self.root.wm_attributes("-alpha", ALPHA_VISIBLE)

		self.root.bind("<Enter>", self.onHoverIn)
		self.root.bind("<Leave>", self.onHoverOut)

		self.root.bind("<Button-2>", self.startMoving)
		self.root.bind("<B2-Motion>", self.moveOverlay)

	def toggleOveray(self, enabled: bool):
		self.enabled = enabled

		if self.enabled:
			self.root.wm_attributes("-topmost", True) #SEMPRE IN PRIMO PIANO
			self.root.wm_attributes("-alpha", ALPHA_VISIBLE)
		else:
			self.root.wm_attributes("-topmost", False)
			self.root.wm_attributes("-alpha", ALPHA_INVISIBLE)

			
	def updateStatus(self, status: str):
		self.statusLabel.config(text="Status: {0}".format(status), foreground="green" if status == "ENABLED!" else "red")

	def updateKey(self, key: str):
		self.keyLabel.config(text="Key: {0}".format(key))

	def updateFilename(self, filename: str):
		self.filenameLabel.config(text="Playback: {0}".format(filename))

	def onHoverIn(self, event):
		self.onHover = True
		self.root.wm_attributes("-alpha", ALPHA_SEMIVISIBLE)

	def onHoverOut(self, event):
		self.onHover = False
		self.root.wm_attributes("-alpha", ALPHA_VISIBLE)

	def startMoving(self, event):
		self.root.x = event.x_root
		self.root.y = event.y_root

	def moveOverlay(self, event): 
		dx = event.x_root - self.root.x
		dy = event.y_root - self.root.y
		x = self.root.winfo_x() + dx
		y = self.root.winfo_y() + dy
		self.root.geometry(f"+{x}+{y}")
		self.root.x = event.x_root
		self.root.y = event.y_root
