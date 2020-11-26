import time
import threading
import numpy as np
from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2
from math import atan2, degrees


global fire
fire = []
stopFlag = False
display = True

def detect():
    print("Camera thread started")
    global fire
    global stopFlag
    
    threshold = np.array([128,128,128])
    threshold1 = np.array([96,96,96])

    resX = 1280
    resY = 1280
    center = (636, 607)

    camera = PiCamera()
    camera.resolution = (resX, resY)
    camera.framerate = 30
    camera.exposure_mode = "off"
    camera.awb_mode = "off"
    camera.awb_gains = (1.245,1.455)
    camera.shutter_speed = 2000
    camera.contrast = 0
    camera.brightness = 50
    rawCapture = PiRGBArray(camera, size=(resX,resY))

    time.sleep(0.1)
    lastFrame = int()
    
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array
        
        pts = np.array([[316,1280],[515,866],[491,495],[804,484],[802,876],[1028,1280]], np.int32)
        pts = pts.reshape((-1,1,2))
        cv2.fillPoly(image,[pts],(0,0,50))
        
        mask = cv2.inRange(image, threshold, np.array([255,255,255]))
        
        _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x:cv2.contourArea(x), reverse=True)
        
        fire0 = []
        
        for index, cnt in enumerate(contours):
            (x, y, w, h) = cv2.boundingRect(cnt)
            
            # convert to middle points
            x = int((2 * x + w) / 2)
            y = int((2 * y + h) / 2)
            
            # circle every detected flame
            if index == 0:
                color = (0,255,255)
            else:
                color = (0,0,255)
            cv2.circle(image, (x,y), 20, color, thickness=3)
            
            angle = degrees(atan2(x - center[0], y - center[1]))
            angle = int((angle + 0) % 360 - 180)
            
            fire0.append(angle)
            
        fire = fire0
        
        fps = 1 / (time.clock_gettime(time.CLOCK_MONOTONIC) - lastFrame)
        lastFrame = time.clock_gettime(time.CLOCK_MONOTONIC)
        cv2.putText(image, "{} FPS".format(round(fps)), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        
        if display:
            cv2.imshow("Captured image", image)
            key = cv2.waitKey(1) & 0xFF
            
        rawCapture.truncate(0)
        
        if stopFlag:
            break
        
    camera.close()
    cv2.destroyAllWindows()
    
camThread = threading.Thread(target=detect)

if __name__ == "__main__":
    camThread.start()
