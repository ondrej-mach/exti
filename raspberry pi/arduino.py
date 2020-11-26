from serial import Serial
import time
import threading
import queue

inputs = queue.Queue()
outputs = queue.Queue()

ser = Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=0.5)

stopFlag = False

fire = False
lTouch = False
rTouch = False
lLine = False
rLine = False

motorBusy = False
dist = 255

def distance():
    return dist

def busy():
    return motorBusy

def go(distance):
    distance = int(distance)
    outputs.put(bytes(f"D{distance}\n", encoding='utf8'))

def turn(angle):
    angle = int(angle)
    outputs.put(bytes(f"T{angle}\n", encoding='utf8'))
    
def fanSet(state):
    outputs.put(bytes(f"F{state}\n", encoding='utf8'))
    
def ledSet(mode):
    outputs.put(bytes(f"L{mode}\n", encoding='utf8'))
    

def communicate():
    print("Comm thread started")
     
    global stopFlag
    
    while not stopFlag:
        while not outputs.empty():
            ser.write(outputs.get())
            
        time.sleep(0.05)
        getInput()
        
    time.sleep(0.1)
    ser.close()


def getInput(): 
    ser.write(bytes("S\n", encoding='utf8'))
    
    global stopFlag
    global fire
    global lTouch
    global rTouch
    global lLine
    global rLine
    global motorBusy
    global dist
    
    global inputs
    
    fireOld = fire
    motorBusyOld = motorBusy
    lTouchOld = lTouch
    rTouchOld = rTouch
    lLineOld = lLine
    rLineOld = rLine
    
    inByte = ser.read()
    if len(inByte) == 1:
        inByte = ord(inByte)
    else:
        inByte = 0
    
    fire = bool(inByte & 1 << 0)
    lTouch = bool(inByte & 1 << 1)
    rTouch = bool(inByte & 1 << 2)
    lLine = bool(inByte & 1 << 3)
    rLine = bool(inByte & 1 << 4)
    
    inByte = ord(ser.read())
    motorBusy = bool(inByte & 1 << 0)
    button = bool(inByte & 1 << 1)
    halt = bool(inByte & 1 << 2)
    
    if(halt):
        inputs.put('H')
    if(button):
        inputs.put('B')
    if(not motorBusy and motorBusyOld):
        inputs.put('M')
    if(not fireOld and fire):
        inputs.put('F')
    if(not lTouchOld and lTouch):
        inputs.put('LT')
    if(not rTouchOld and rTouch):
        inputs.put('RT')
    if(not lLineOld and lLine):
        inputs.put('LL')
    if(not rLineOld and rLine):
        inputs.put('RL')

    dist = ser.read()
    if len(dist) == 1:
        dist = ord(dist)
    else:
        dist = 255
        
    while ser.inWaiting():
        ser.read()
    
commThread = threading.Thread(target=communicate)

if __name__ == "__main__":
    commThread.start()
    
