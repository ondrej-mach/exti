from signal import signal, SIGINT
from subprocess import call
import time
import random

from arduino import *
import arduino
import camera

camera.display = False
active = False

camera.camThread.start()
arduino.commThread.start()

time.sleep(1)

def handler(signal_received, frame):
    print("Exiting...")
    arduino.stopFlag = True
    camera.stopFlag = True
    time.sleep(0.5)
    exit(0)

def waitMotor():
    time.sleep(0.2)
    while busy():
        time.sleep(0.02)

def waitEvent(timeout = 3):
    startTime = time.time()
    while inputs.empty() and (startTime + timeout > time.time()):
        time.sleep(0.02)

    event = None

    if not inputs.empty():
        event = inputs.get()
        print(event)

    if event == 'B':
        global active
        active = not active

    elif event == 'H':
        ledSet(7)
        print("Shutting down")
        time.sleep(0.2)
        arduino.stopFlag = True
        camera.stopFlag = True
        time.sleep(1)
        call("sudo shutdown -h now", shell=True)

    else:
        return event

def clearEvents():
    while not inputs.empty():
        waitEvent()


signal(SIGINT, handler)

radius = 20
lastGo = 0
lastTurn = 0
ledSet(0)

while True:
    waitEvent()

    while active:
        if time.time() > lastGo + 1:
            ledSet(1)
            go(50)
            lastGo = time.time()

        while not inputs.empty():
            event = waitEvent()
            if event == 'B':
                ledSet(0)
                active = False
                go(0)
            elif event == 'LL':
                go(-12)
                waitMotor()
                turn(random.choice([60,100]))
                waitMotor()
                clearEvents()
            elif event == 'RL':
                go(-12)
                waitMotor()
                turn(random.choice([-60,-100]))
                waitMotor()
                clearEvents()

        if camera.fire:
            ledSet(2)
            go(0)

            time.sleep(1)
            f = camera.fire
            if f:
                turn(f[0])
                waitMotor()
                time.sleep(0.7)

                visible = True
                inRadius = False
                while visible and not inRadius:
                    visible = False
                    for angle in reversed(camera.fire):
                        if (angle < 20) and (angle > -20):
                            visible = True
                            turnAngle = angle

                    if visible:
                        if (abs(angle) > 7) and (time.time() > lastTurn + 1.5):
                            go(0)
                            waitMotor()
                            turn(turnAngle)
                            waitMotor()
                            lastTurn = time.time()
                            lastGo = 0

                        if time.time() > lastGo + 0.5:
                            go(50)
                            lastGo = time.time()

                    while not inputs.empty():
                        event = waitEvent()
                        if event in ['LL', 'RL']:
                            inRadius = True;

                if not inRadius:
                    go(40)
                    event = waitEvent(timeout = 2)
                    if event in ['LL', 'RL']:
                        inRadius = True;

                if inRadius:
                    fanSet(1)
                    go(0)
                    waitMotor()
                    go(-15)
                    waitMotor()
                    fanSet(0)
                    turn(60 * random.choice([1, -1]))
                    waitMotor()
                    clearEvents()

        if not active:
            ledSet(0)

        time.sleep(0.03)
