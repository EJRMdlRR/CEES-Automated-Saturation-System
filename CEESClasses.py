import datetime
import select
import sys
import time


class Experiment:
    # Constructor
    def __init__(self, title='', user='Default', viscosity=50, notes=''):
        # Experiment Details
        self.title = title
        self.date = datetime.datetime.now().strftime("$M:%H_%m/%d/%Y")
        self.user = user
        self.viscosity = viscosity
        self.notes = [notes]
        self.filename = self.title + "_" + self.date + ".txt"
        self.began = time.time()

        # Drop Data
        self.optimal_volts = self.volts = self.clog_volts = 45
        self.last_drop_time = self.drop_sum = 0
        self.seconds_per_drops = 2
        self.drops = []

        # Noise data
        self.noise = []
        self.noise_sum = 0

    # Getters
    def get_volts(self):
        return self.volts

    def get_clog_volts(self):
        return self.clog_volts

    def time_since_drop(self):
        return time.time() - self.last_drop_time

    def get_drop_average(self):
        if len(self.drops):
            return self.drop_sum / len(self.drops)
        else:
            return "No drops"

    def get_noise_average(self):
        if len(self.noise):
            return self.noise_sum / len(self.noise)
        else:
            return "No noise"

    def get_pixel_avg(self):
        return self.noise_sum / len(self.noise)

    # Setters
    def equalize_volts(self):
        """Reset current volts to last known volts before clogging."""
        while(self.clog_volts > self.volts):
            self.clog_volts -= 81
            time.sleep(0.05)

        if (self.clog_volts < self.volts):
            self.clog_volts = self.volts

        self.last_drop_time = 0

    def set_volts(self, key):
        """Change voltage by:
            increasing it by 5,
            decreasing it by 5,
            or setting it to a custom value.
        """
        values = (5, -5)
        if key >= 2:
            self.volts = key
        else:
            self.volts += values[key]

        self.clog_volts = self.volts = bounds_checker(self.volts)
        print("Voltage: {:.2f}%".format(100 * ((self.volts - 45) / 4055)))

    def set_clog_volts(self, key):
        """Change clog voltage by:
            increasing it by 5,
            decreasing it by 5,
            or setting it to a custom value.
        """
        values = (81, -81)
        if key >= 2:
            self.clog_volts = key
        else:
            self.clog_volts += values[key]

        self.clog_volts = self.volts = bounds_checker(self.volts)
        if (self.clog_volts < self.volts):
            self.clog_volts = self.volts
        print("Voltage: {:.2f}%".format(100 * ((self.clog_volts - 45) / 4055)))

    def optimal_volts_set(self):
        """Set optimal volt value according to researcher."""
        self.optimal_volts = self.volts
        return True

    # Miscellaneous
    def add_noise(self, frame_no, noise):
        """Add noise data to class for averaging."""
        self.noise_sum += noise
        self.noise.append((frame_no, noise))
        return self.noise_sum / len(self.noise)

    def add_drop(self, frame_no, noise):
        """Add drop data to history and calculate new voltage.
        New voltage is calculated as change from the optimal value.
        The optimal value is set by the researcher.
        """
        self.drops.append([time.time() - self.began,
                           time.time() - self.last_drop_time,
                           frame_no,
                           self.noise_sum / len(self.noise),
                           noise,
                           self.volts,
                           ])
        self.drop_sum += noise

        if (self.last_drop_time):
            volts = (self.optimal_volts
                     + ((time.time() - self.last_drop_time)
                        - self.seconds_per_drops) * self.viscosity)
            self.clog_volts = self.volts = volts
            print("{:.2f}s since last drop"
                  .format(time.time() - self.last_drop_time)
                  )
            print("Voltage: {:.2f}%".format(100 * (self.volts / 4055)))
        self.last_drop_time = time.time()

        return bounds_checker(self.volts)

    def input_with_timeout(self, prompt, timeout):
        """Read keyboard input for [timeout]s length of time.
        Also, expect stdin to be line buffered"""
        print(prompt)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline().rstrip('\n')
        return "None"

    def addNotes(self, frame_no):
        """Add user notes to experiment data."""
        notes = self.input_with_timeout("Notes: ", 30)
        self.notes.append("Notes at frame [{}]: {}".format(frame_no, notes))

    def finalNotes(self):
        final_notes = self.input_with_timeout("Final Notes: ", 30)
        self.notes.append("Final Notes: " + final_notes)

    def terminate(self, success):
        """Execute termination procedure
        1. Write collected drop data to text file.
        2. Write collected noise data to text file
        """
        emptied = "Succesful" if success else "Unsuccesful"
        data = """Title: {0}
        Date: {1}
        User/s: {2}
        Viscosity: {3}
        Seconds per Drop: {4}
        Notes: {5}
        TotalTime\tTimeSinceDrop\tFrame\tMovingPixelAvg\tMovingPixels\tVoltage
        """.format(self.title,
                   self.date,
                   self.user,
                   self.viscosity,
                   self.seconds_per_drops,
                   self.notes[0],
                   )

        drop_file = open(self.filename, "w")
        write = drop_file.write
        for drop in range(1, len(self.drops) - 1):
            write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(*self.drops[drop]))
        write("Tank Emptied: {}\n".format(s))
        write("Final voltage: {}\n".format(self.volts))
        write("Total drops: {}\n".format(len(self.drops)))
        write("Avg. pixel noise: {}\n".format(self.get_noise_average()))
        write("Avg. drop noise: {}\n".format(self.get_drop_average()))
        for note in self.notes:
            write(note)
        write(self.notes[-1])
        drop_file.close()

        noiseFile = open(self.filename + "_Noise", "w")
        for noise in self.noise:
            noiseFile.write("{}\t{}\n".format(*noise))
        noiseFile.close()


# Helpers
def bounds_checker(volts):
    """Limits voltage.
    Voltage limits are 45 (1.1%) and 4055 (99.0%) of a 4095 max.
    Valve calibrated so that at 45 (1.1%) it's shut.
    """
    if volts > 4055:
        return 4055
    elif volts < 45:
        return 45
    else:
        return volts
