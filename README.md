![GitHub](https://img.shields.io/github/license/hunar4321/life_code)

# LED-Reactive-Music
This is the finished version of my music-reacting LEDs project. It does what it says on the tin. Takes a sound file and changes the RGB value of a connected LED strip based on volume. Works on .wav files, could most definitely be adapted to work on other audio formats. Adapt the script to your needs. The code is quite messy. Here is a demo: https://drive.google.com/file/d/1v2VmfhHqBDIrM1tZ_HV1oSdyibn4wzjI/view?usp=sharing. 

You need a few things to run this: 
---------------------------------

First, you need to make sure you know how you will connect some audio output to your Raspberry Pi if you plan on hearing the music as well. Now, you need to follow this guide so that you can control the LEDs in the first place: https://dordnung.de/raspberrypi-ledstrip/. BEWARE, the guide has a link to the wrong mosfets, MAKE SURE YOU BUY LOGIC-LEVEL MOSFETS, such as IRLZ34N. Now you need to install pigpio(http://abyz.me.uk/rpi/pigpio/) and other libraries used in the script. The script will look for a folder called "Songs" in the same directory and then open a .wav file inside. It will crash if it doesn't find one. If the script crashes when you run it, it could also be because you did not turn on pigpio(```sudo pigpiod``` in a terminal)

At this point you should be able to use it. Type "help" when the script is running to see all commands. You can edit the autocorrection inside of the script to make the lights dance however you like. Do what you want with the code, but credit would be much appreciated. Have fun !

Contact info in the profile
