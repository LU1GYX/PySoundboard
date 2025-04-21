<p align="center"><img src="https://github.com/LU1GYX/PySoundboard/blob/main/src/icon_no_text.png?raw=true" alt="TkForge Logo" width="100" height="100"></p>

# PySoundboard

An Almost-Without dependencies Python Soundboard! (WINDOWS ONLY!)

## Disclamer

This isn't finished, it can be optimized in many ways! __If you want to help, you're Welcome to contribute!__

## Requirements

* [Virtual Audio Cable](https://vb-audio.com/Cable/) 
+ Python 3.13

For python, verify you installed python correctly and check the PATH if it contains the Python path.

## Installation

Clone the repo, open a terminal inside the repo folder and run:

```
python -r requirements.txt
```

This will install all the dependencies needed to run the Soundboard.

After the installation, run this command to start the Soundboard: 

```
python .
```

__N.B:! RUN THIS COMMAND INSIDE THE REPO FOLDER!__

After the startup, the program will check automatically for the Virtual Cable presence and will load the configured Binds

## How to Use

### Overlay 

+ The overlay is toggleable, you can choose to disable it or not. 
- You can change the position of it by clicking __MIDDLE MOUSE__ while on the window.
* When the cursor is over the window, it will change the opacity of it.

### Soundboard

+ The Soundboard is toggleable. 
- To play a sound, you need to add new Bindings. There are 2 ways to add a bind: 

__GUI__

By left-clicking on the TrayIcon, an option called "Add Bind" will show.
To add a valid bind, you need to provide 4 informations:

* __Path__: A valid path to an '.MP3' file.
+ __Process__: A process name, it will provide a list of the current active processes. When 'default' is setted, the audio will play every time you hit the key.
- __Volume__: The volume value for the Audio. The range is -100 (silent) to +100 (LOUD)
* __Key__: The name of the key. If you select the textbox, the key will be automatically inserted.

__Manual__

The bindings inserted in the 'binds.json' is formatted this way:

```
"default": { #Process Name
    "q": { #Key
        "filename": "./sounds/Qiguanchanghong.mp3", #Path to filename
        "volume": -15 #Volume value
    }
},
```

Simply copy this and modify the values you need to change.

> To see the current configured bindings, you can use the "List Binds" option under the "Add Bind"!

#Todo

- [ ] Add presistent setting file
- [ ] Revamp for tk windows
- [ ] Overlay Customization
- - [ ] Size
- - [ ] Text
- - [ ] Colors