#Imports
import sys
import os
import fcntl
import random
import pyaudio
import pigpio
import wave
import audioop
import numpy as np
import time

#Constants
CHUNK = 256
INTERVAL = 0.04 #How long it waits between changing the lights
AUDIO_SAMPLE_LENGTH = 100000 #100000 is most likely fine, but might cause errors on something very short

firstPin = 24 #Blue pin
secondPin = 17 #Red pin
topSignals = 10000 #Doesn't matter much anymore, changes the factor at the
                    #beginning

#Fancy input
fl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)

#Console interface
if len(sys.argv) > 1:
    used_console = True
    if sys.argv[4] != "":
        if sys.argv[1].lower() == "night":
            INTERVAL = 0.15
        else:
            INTERVAL = float(sys.argv[1])

        if sys.argv[2].lower() == "r":
            firstPin = 17
        elif sys.argv[2].lower() == "g":
            firstPin = 22
        elif sys.argv[2].lower() == "b":
            firstPin = 24
        else:
            print("Incorrect Value")
            sys.exit()

        if sys.argv[3].lower() == "r":
            secondPin = 17
        elif sys.argv[3].lower() == "g":
            secondPin = 22
        elif sys.argv[3].lower() == "b":
            secondPin = 24
        else:
            print("Incorrect Value")
            sys.exit()
        
        topSignals = int(sys.argv[4])

    else:
        print("Incorrect Values")
        sys.exit()

#Instancing objects
p = pyaudio.PyAudio()
pi = pigpio.pi()

def lights_off():
    #Turn off unused lights
    pi.set_PWM_dutycycle(17, 0)
    pi.set_PWM_dutycycle(22, 0)
    pi.set_PWM_dutycycle(24, 0)

# #Normal input stopped working when I used this, so now this looks ugly
# print("Input the name of the song")
# while True:
#     try:
#         stdin = sys.stdin.read()
#         if "\n" in stdin or "\r" in stdin:
#             audioName = stdin
#             break
#     except:
#         pass

def open_song(a = ''):
    link = random.choice(os.listdir(os.getcwd() + "/Songs"))
    rawAudio = wave.open(str(os.getcwd() + "/Songs/" + link))
    raw = wave.open(str(os.getcwd() + "/Songs/" + link))

    if a != '':
        try:
            print("Choose a Song (from the Songs folder)")
            #The script will look into the Songs folder and find a .wav file with the name given
            link = os.getcwd() + "/Songs/" + a + ".wav"
            rawAudio = wave.open(link)
            raw = wave.open(link)
        except FileNotFoundError:
            pass

    #Idk why, but you need a seperate wave object to play audio

    #Open py audio stream
    stream = p.open(format = p.get_format_from_width(rawAudio.getsampwidth()), 
                channels = rawAudio.getnchannels(), 
                rate = rawAudio.getframerate(), 
                output = True) 
    
    signal = rawAudio.readframes(-1)
    signal = np.frombuffer(signal, dtype ="int16") #data about the full song
    return rawAudio,raw,stream,signal

#Calculate factor, not sure how much of this was actually necessary to write
#Left this for future reference
    """
When you open files with wave, you get a list of big values. We first
need to find some bumber we can divide these huge numbers by to bring them
to 510, which is the brightness range of 2 LEDs. This code does this
"""
def factor_song(sig):
    #Probably unnecessary
    compressed_signal = np.linspace(
                    0,
                    len(sig),
                    num = AUDIO_SAMPLE_LENGTH
                )
    compressed_signal = np.argsort(compressed_signal)
    compressed_signal = compressed_signal[-topSignals:]
    average = audioop.rms(np.average(compressed_signal), 2)
    factor = average / 510
    return factor

def choose_song(a = ''):
    lights_off()
    rawAudio, raw, stream, signal = open_song(a)
    factor = factor_song(signal)
    return rawAudio, raw, stream, signal, factor

rawAudio, raw, stream, signal, factor = choose_song()

print("Starting stream")

pause = False
loopActive = True

while loopActive:
    #Initializing variables required for the main loop
    data = raw.readframes(CHUNK)

    start = time.time()
    intervalTimer = start
    overTimer = start
    underTimer = start

    j = 0
    secondBuffer = 0
    firstBuffer = 0

    tooBlue = 0
    firstLight = 0

    changeSong = ''

    while True:
        #Mid-loop input interface
        try:
            stdin = sys.stdin.read()

            if stdin == "help\n":
                pause = True
                print("""List of commands: 
                        \n\thelp: shows all commands
                        \n\tpause: pause/unpause the song
                        \n\tquit: quits the program
                        \n\tskip: skip current song
                        \n\t(Song_Name): Plays the chosen songif it is found
                    """)
            elif stdin == "pause\n":
                pause = not pause
            elif stdin == "skip\n":
                break
            elif stdin == "quit\n":
                loopActive = False
                break
            else:
                try:
                    link = os.getcwd() + "/Songs/" + stdin[:-1] + ".wav"
                    print(link)
                    test = wave.open(link)

                    changeSong = stdin[:-1]
                    break
                except FileNotFoundError:
                    print("File not found")
        except:
            pass

        if pause:
            continue

        if time.time() - start >= (len(signal) / rawAudio.getframerate()) / 2:
            print("Ended")
            break

        brightness = abs(audioop.rms(data, 2) / factor)
        if brightness > 510:
            brightness = 510

        #This sucks
        if brightness > 255:
            first = 255
            second = brightness - first
        else:
            first = brightness
            second = 0
        
        #Stores brightness values between each color change
        secondBuffer += second
        firstBuffer += first
        j += 1

        if time.time() - intervalTimer >= INTERVAL:
            secondLight = secondBuffer / j

            firstLight = (firstBuffer / j) - tooBlue
            if firstLight >= 255:
                firstLight = 255
            elif firstLight <= 0:
                firstLight = 0

            pi.set_PWM_dutycycle(secondPin, secondLight/5)
            pi.set_PWM_dutycycle(firstPin, firstLight/5)

            #Radicalizer(Automatically assigns factor)
            #If too red, decrease brightness
            if secondLight <= 150:
                overTimer = time.time()

            #If not bright enough, increase brightness
            if firstBuffer / j >= 225:
                underTimer = time.time()

            #If blue is always in full brightness, tune it down
            if tooBlue < 100 and secondLight > 0:
                tooBlue += 1
            else:
                if tooBlue >= 0:
                    tooBlue -= 1
            

            if time.time() - overTimer >= 0.075:
                factor += 1
                overTimer = time.time()
            elif time.time() - underTimer >= 0.18:
                factor -= 1
                underTimer = time.time()

            #Uncomment to see info
            #print("Factor is, ", factor, "Brightness is", brightness, " Lights are (" , firstLight, ", ", secondLight, ")")

            j = 0
            secondBuffer = 0
            firstBuffer = 0
            intervalTimer = time.time()

        # writing to the stream is what *actually* plays the sound
        stream.write(data)
        data = raw.readframes(CHUNK)

    rawAudio, raw, stream, signal, factor = choose_song(changeSong)
    print("Next Song")

#Cleanup
stream.close()    
p.terminate()
