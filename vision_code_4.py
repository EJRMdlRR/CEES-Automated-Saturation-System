# Import libraries
from multiprocessing import Process
from CEESClasses import Experiment
import adafruit_mcp4725
import numpy as np
import cv2 as cv
import datetime
import board
import busio
import time

# Define functions
def initialize():
    # Initialize I2C bus and MCP4725 board
    i2c = busio.I2C(board.SCL, board.SDA)     
    dac = adafruit_mcp4725.MCP4725(i2c)    
    
    # Initialize Experiment object
    title = "v4" #input("Title: ")
    exp = input("Experiment #: ")
    user = "I"   #input("User/s: ")
    spd = 2      #float(input("Desired drop Rate: "))
    visc = 60    #float(input("Liquid Viscosity: "))
    notes = "N/A"#input("Enter any additional notes: ")
    e = Experiment(title, exp, user, spd, visc, notes)
    return e

def imageProcessing(backSub, frame, coordinates):
    north, south, east, west = coordinates
    
    gray = cv.cvtColor(rect_img, cv.COLOR_BGR2GRAY)
    fgMask = backSub.apply(gray) #this is basically 80% of the program right here
    fgMask_RGB = cv.cvtColor(fgMask, cv.COLOR_GRAY2RGB)
    
    cv.rectangle(frame, (10, 2), (100,20), (0,0,0), -1)
    cv.putText(frame, str(capture.get(cv.CAP_PROP_POS_FRAMES)), (15, 15),
               cv.FONT_HERSHEY_SIMPLEX, 0.5 , (255,255,255))
    
    #Replacing the sketched image on Region of Interest
    frame[north: south, west : east] = fgMask_RGB 
    nonzero = cv.countNonZero(fgMask)  
    return frame, nonzero

def parallelize(function, arguments = None):
    t = Process(target = function, args = arguments)
    t.start()
    
def fSet(coordinates, key):
    validKeys = [ord('w'), ord('W'), ord('a'), ord('A'), ord('s'), ord('S'),
                 ord('d'), ord('D'), ord('i'), ord('I'), ord('j'), ord('J'),
                 ord('k'), ord('K'), ord('l'), ord('L'),]
    north, south, east, west = coordinates
    
    # Top-Right Corner
    if key == ord('w') or key == ord('W'):   north -= 5
    elif key == ord('a') or key == ord('A'): west -= 5
    elif key == ord('s') or key == ord('S'): north += 5
    elif key == ord('d') or key == ord('D'): west += 5
    
    # Bottom-Left Corner
    elif key == ord('i') or key == ord('I'): south -= 5
    elif key == ord('j') or key == ord('J'): east -= 5
    elif key == ord('k') or key == ord('K'): south += 5
    elif key == ord('l') or key == ord('L'): east += 5
    
    # Bound checking
    if (north < 0): north = 0
    elif (north > height): north = height
    if (south < 0): south = 0
    elif (south > height): south = height
    if (east< 0): east = 0
    elif (east > width): east = width    
    if (west < 0): west = 0
    elif (west > width): west = width
    
    if key in validKeys: print("Coordinates: ({}, {}), ({}, {})".format(north, west, south, east))
    return [north, south, east, west]

def summary():
    print("Final voltage: {:.2f}".format(voltage))
    print("Total drops: {}".format(num_drops))
    print("Average pixel delta: {:.2f}".format(pix_avg))
    print("Average drop delta: {:.2f}".format(dp_avg))    

def terminationProcedure(volts):    
    volts =int(volts/10)*10
    while (volts >= 10):
        volts -= 5
        dac.raw_value = volts
        time.sleep(0.1)        

if __name__ == '__main__':
    # Initialize settings
    e = initialize()
    frames= 0
    waitFrame = 0
    liquid = True
    mutiny = False
    success = False
    defaults = False
    calibration = False
    
    # Open video feed
    backSub = cv.createBackgroundSubtractorMOG2(history = 40, varThreshold = 60, detectShadows = False)
    capture = cv.VideoCapture(0) # 0 - laptop webcam; 1 - USB webcam; "cv.samples.findFileOrKeep(args.input))" - file
    if not capture.isOpened:
        print('Unable to open: ' + args.input)
        exit(0)
        
    # get image dimensions
    height = int(capture.get(4))
    width = int(capture.get(3))
    coords = [0, height, width, 0]

    # clog values
    timeOpen = 0
    latencyDelay = 0
    clogged = False
    
    while (liquid):
        # Takes frame input from camera
        ret, frame = capture.read()
        if frame is None:
            break    
      
        # Rectangle marker
        r = cv.rectangle(frame, (coords[3], coords[0]), (coords[2], coords[1]), (100, 50, 200), 3)
        rect_img = frame[coords[0]:coords[1], coords[3]: coords[2]]
        
        # Main processing of program
        if (defaults):
            frames += 1
            frame, delta = imageProcessing(backSub, frame, coords)
            if(calibration):
                if(delta > pixAvg * 5):
                    if (e.cGet() > e.vGet()): e.vEqualize()                     
                    if (waitFrame == 0): e.addDrop(frames, delta)
                    elif (waitFrame < 10): waitFrame += 1 # change to if frame before was drop, no drop
                    else: waitFrame = 0
                    timeOpen = 0
                    clogged = False
                else:
                    # clog protocol
                    # while there is no drop, increase voltage every 10s (to account for latency)
                    # if 60s at max voltage with no drop pass, terminate
                    if (e.tSinceDrop() > 30):
                        if (not clogged): 
                            latencyDelay = time.time()
                            clogged = True
                        if (time.time() - latencyDelay > 10):
                            print("{:.2f}".format(time.time() - latencyDelay))
                            if (e.cGet() == 4054): timeOpen += 1
                            else: e.cSet(1)
                            if (e.cGet() >= 4055): e.cSet(4054)
                            clogged = False
                        if (timeOpen >= 6):
                            e.vSet(4055)
                            success = True
                            liquid = False
                    else: pixAvg = e.addNoise(frames, delta)                   
            else: 
                mutiny = True
                dac.raw_value = 5
                time.sleep(0.01)
                if (frames < 250): 
                    pixAvg = e.addNoise(frames, delta)  
                else: 
                    print("CALIBRATION COMPLETE")
                    mutiny = False
                    calibration = True
    
        # Show the image in a resizeable frame
        cv.namedWindow('Frame',cv.WINDOW_NORMAL)
        cv.imshow('Frame', frame)      
        k = cv.waitKey(60) & 0xFF

        # Checks for keypresses
        if ((k == ord('q')) or (k == ord('Q'))): liquid = False
        elif (k == ord('0')): defaults = e.dSet()                        # Confirm default voltage and rectangle size and location
        elif ((k == ord('r')) or (k == ord('R'))): defaults = False      # Don't save data while default voltage and rectangle values are reset
        elif ((k == ord('c')) or (k == ord('C'))): calibration = False   # Calibration sequence restarts (100 frames to average noise level)
        elif ((k == ord('n')) or (k == ord('N'))): parallelize(e.addNotes, (frames,)) # Insert additional notes
        elif ((k == ord('e')) or (k == ord('E'))): e.vSet(0)
        elif (k == ord('+')): e.vSet(1)
        elif (k == ord('-')): e.vSet(2)
        elif (k != 0xFF): coords = fSet(coords, k)
        
        if (not mutiny): dac.raw_value = e.vGet()
    capture.release()
    cv.destroyAllWindows()
    parallelize(terminationProcedure, (e.vGet(),))
    e.finalNotes()
    e.terminate(success)
