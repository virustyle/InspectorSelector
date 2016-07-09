
I wrote this a while ago and decided to put it up here recently.  Its not perfect, or even really finished.  Completely untested. will probably crash trying to access an invalid MObject/MDagPath at some point. I'm working on other things now.

There are methods and commented out code that will make the UI borderless, and pin it to the top right corner of the active viewpane.  It does not work as gracefully as I'd like it to, mostly due to maya callbacks. I also played with setting the background of the UI to transparent when pinned. But unfortunately this doesnt work on linux (xserver issue), so I scratched it.

to Explain:
It's similar to XSI's isolate select. Except there is one UI to cntrl isolation for all viewpanes regardless of pane layout.  So the 'isolate' button will toggle on/off isolate selection for the viewpane btns below.  There are also memory btns to the right.  right click to set one, left click to load that memory, and right click to clear.


for Maya 2016 or newer



import inspectorselector

inspectorselector.run()
