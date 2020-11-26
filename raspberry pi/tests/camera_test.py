import time
import numpy as np
from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2


resX = 1280
resY = 1280

camera = PiCamera()
camera.resolution = (resX, resY)
camera.framerate = 30
rawCapture = PiRGBArray(camera, size=(resX,resY))

time.sleep(0.1)

for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    image = frame.array 
        
    try:
        cv2.imshow("Captured image", image)
        key = cv2.waitKey(1) & 0xFF
    except:
        print("Unable to display image")
        
    rawCapture.truncate(0)
    
camera.close()
cv2.destroyAllWindows()
