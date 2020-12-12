import sys
import time
import select
import datetime

class Experiment: 
    # Constructor
    def __init__(self, title = 'Auto', exp = '000', user = 'Default', spd = 2, visc = 50, notes=''):
        # Independednt Data
        self.title = title
        self.experiment = exp
        self.date = datetime.datetime.now()
        self.user = user
        self.secPerDrops = spd
        self.viscosity = visc
        self.iNotes = notes
        self.filename = self.title + "_" + self.experiment + ".txt"
        self.began = time.time()
        
        # Drop Data
        self.optimalVoltage = 0
        self.dropData = []
        self.lastDrop = 0
        self.dropSum = 0
        self.volts = 5
        self.cVolts = 5
        
        # Noise data
        self.noiseData = []
        self.noiseLength = 0   # number of noise frames
        self.noiseSum = 0     # sum of noise frames
        
        # Misc
        self.notes = []

    # Getters
    def vGet(self): return self.volts
    def cGet(self): return self.cVolts
    def tSinceDrop(self): return time.time() - self.lastDrop
    def dropAvg(self): return self.dropSum / len(self.dropData)
    def pixAvg(self): return self.noiseSum / self.noiseLength
    
    # Setters
    def vEqualize(self):
        while(self.cVolts > self.volts):
            self.cVolts -= 81
            
            # Bound checking
            if self.cVolts > 4055: self.cVolts = 4055
            elif self.cVolts < 5:  self.cVolts = 5
            if (self.cVolts < self.volts): self.cVolts = self.volts
            
            time.sleep(0.05) 
        self.lastDrop = 0
        
    def vSet(self, key):
        if key == 0:   self.volts = input("Please enter a voltage: ")
        elif key == 1: self.volts += 5
        elif key == 2: self.volts -= 5
        elif key > 2: self.volts = key
        
        # Bound checking
        if self.volts > 4055: self.volts = 4055
        elif self.volts < 5:  self.volts = 5
        
        self.cVolts = self.volts
        print("Voltage: {:.2f}%".format(100 * ((self.volts - 5)/ 4050)))
        
    def cSet(self, key):
        if key == 0:   self.cVolts = input("Please enter a voltage: ")
        elif key == 1: self.cVolts += 81
        elif key == 2: self.cVolts -= 81
        elif key > 2: self.cVolts = key
        
        # Bound checking
        if self.cVolts > 4055: self.cVolts = 4055
        elif self.cVolts < 5:  self.cVolts = 5
        if (self.cVolts < self.volts): self.cVolts = self.volts
        print("Voltage: {:.2f}%".format(100 * ((self.cVolts - 5) / 4050)))      
    
    def dSet(self):
        self.optimalVoltage = self.volts
        return True
    
    # Miscellaneous
    def addNoise(self, frameNumber, nonzero):
        self.noiseLength += 1
        self.noiseSum += nonzero
        self.noiseData.append((frameNumber, nonzero))
        return self.noiseSum / self.noiseLength
        
    def addDrop(self, frameNumber, nonzero):
        # data storage
        self.dropData.append([time.time() - self.began, time.time() - self.lastDrop, frameNumber, self.noiseSum / self.noiseLength, nonzero, self.volts])
        self.dropSum += nonzero
        
        # voltage calculations
        if (self.lastDrop != 0):
            self.cVolts = self.volts = self.optimalVoltage + ((time.time() - self.lastDrop) - self.secPerDrops) * self.viscosity
            print("{:.2f}s since last drop".format(time.time() - self.lastDrop))
            print("Voltage: {:.2f}%".format(100 * (self.volts / 4050)))
        self.lastDrop = time.time()
        
        # Bound checking
        if self.volts > 4055: self.volts = 4055
        elif self.volts < 5:  self.volts = 5
        
        return self.volts
    
    def input_with_timeout(self, prompt, timeout):
        print(prompt)
        ready, _, _ = select.select([sys.stdin], [],[], timeout)
        if ready:
            return sys.stdin.readline().rstrip('\n') # expect stdin to be line-buffered
        return "None"    

    def addNotes(self, frameNumber):
        noteFrame = self.input_with_timeout("Notes: ", 30)
        self.notes.append("Notes at frame [{}]: {}".format(frameNumber, noteFrame))
    
    def finalNotes(self):
        self.fNotes = "Final Notes: " + self.input_with_timeout("Final Notes: ", 30)
    
    def terminate(self, success):
        if(success): s = "Succesful"
        else: s = "Unsuccesful"
        
        # Open file in write mode
        dropFile = open(self.filename,"w")
        
        # Write initial information
        dropFile.write("Title: {}\n".format(self.title)) 
        dropFile.write("Experiment Number: {}\n".format(self.experiment))
        dropFile.write("Date: {}\n".format(self.date))
        dropFile.write("User/s: {}\n".format(self.user))
        dropFile.write("Viscosity: {}\n".format(self.viscosity)) 
        dropFile.write("DPS: {}\n".format(self.secPerDrops)) 
        dropFile.write("Notes: {}\n".format(self.iNotes))
        dropFile.write("TotalTime\tTimeSinceDrop\tFrame\tMovingPixelAvg\tMovingPixels\tVoltage")
        
        # Write drop data
        for drop in self.dropData:
            dropFile.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(drop[0], drop[1], drop[2], drop[3], drop[4], drop[5]))
            
        # Write final information
        dropFile.write("Tank Emptied: {}\n".format(s))
        dropFile.write("Final voltage: {}\n".format(self.volts))
        dropFile.write("Total drops: {}\n".format(len(self.dropData)))
        dropFile.write("Average pixel delta: {}\n".format(self.noiseSum / self.noiseLength))
        if (len(self.dropData) == 0): dropAverage = 0
        else: dropAverage = self.dropAvg()
        dropFile.write("Average drop delta: {}\n".format(dropAverage))
        for note in self.notes:
            dropFile.write(note)
        dropFile.write(self.fNotes)
        
        # Close drop file
        dropFile.close()
        
        # Write separate file for noise data
        noiseFile = open(self.title + "_" + self.experiment + "_Noise", "w")
        
        # Write noise
        for noise in self.noiseData:
            noiseFile.write("{}\t{}\n".format(noise[0], noise[1]))
            
        noiseFile.close()