import datetime
from model import Model
import select
import sys
import time


class Experiment(Model):
    # Constructor
    def __init__(self, title='', user='Default', viscosity=50, **kwargs):
        # Experiment Details
        self.title = title
        self.date = datetime.datetime.now().strftime("$M.%H.%m.%d.%Y")
        self.filename = self.title + "_" + self.date + ".txt"

        self.user = user
        self.viscosity = viscosity
        self.notes = [self.add_notes(0)]
        self.beginning = time.time()

        self.volts = self.clog_volts = self.optimal_volts = 45

        super().__init__(**kwargs)

    # Getters
    def get_volts(self):
        return self.volts

    def get_clog_volts(self):
        return self.clog_volts

    # Setters
    def set_volts(self, key):
        """Change voltage by:
            increasing it by 5,
            decreasing it by 5,
            or setting it to a custom value.

            Set clog volts to track current volts.
        """
        values = (5, -5)
        if key >= 2:
            self.volts = key
        else:
            self.volts += values[key]

        self.clog_volts = self.volts = bounds_checker(self.volts)
        print("Voltage: {:.2f}%".format(100 * ((self.volts - 45) / 4055)))

    def set_clog_volts(self):
        """Increase clog voltage by 81 (2%)"""
        self.clog_volts = bounds_checker(self.clog_volts + 81)
        print("Voltage: {:.2f}%".format(100 * ((self.clog_volts - 45) / 4055)))

    def set_optimal_volts(self):
        """Set optimal volt value according to researcher."""
        self.optimal_volts = self.volts
        return True

    def calculate_volts(self):
        delta = (time.time() - self.last_drop_time) - self.seconds_per_drops
        volts = (self.optimal_volts + delta * self.viscosity)
        self.clog_volts = self.volts = bounds_checker(volts)

        print("{:.2f}s since last drop"
              .format(time.time() - self.last_drop_time)
              )
        print("Voltage: {:.2f}%"
              .format(100 * (self.volts / 4055))
              )

    def equalize_volts(self):
        """Reset current volts to last known volts before clogging."""
        while(self.clog_volts > self.volts):
            self.clog_volts -= 81
            time.sleep(0.05)

        if (self.clog_volts < self.volts):
            self.clog_volts = self.volts

    def input_with_timeout(self, prompt, timeout):
        """Read keyboard input for [timeout]s length of time.
        Also, expect stdin to be line buffered"""
        print(prompt)
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if ready:
            return sys.stdin.readline().rstrip('\n')
        return "None"

    def add_notes(self, frame_no):
        """Add user notes to experiment data."""
        notes = self.input_with_timeout("Notes: ", 30)
        self.notes.append("Notes at frame [{}]: {}".format(frame_no, notes))

    def terminate(self, success):
        """Execute termination procedure
        1. Compile collected experiment data into strings
        2. Write collected drop data to text file.
        3. Write collected noise data to text file
        """
        emptied = "Succesful" if success else "Unsuccesful"
        initial_data = """Title: {0}
        Date: {1}
        User/s: {2}
        Viscosity: {3}
        Seconds per drop: {4}
        Notes: {5}
        TotalTime\tTimeSinceDrop\tFrame\tMovingPixelAvg\tMovingPixels\tVoltage
        """.format(self.title,
                   self.date,
                   self.user,
                   self.viscosity,
                   self.seconds_per_drops,
                   self.notes[0],
                   )
        final_data = """Tank emptied: {0}
        Final voltage: {1}
        Total drops: {2}
        Average pixel noise: {3}
        Average drop noise: {4}
        """.format(emptied,
                   self.volts,
                   len(self.drops),
                   self.get_noise_average(),
                   self.get_drop_average(),
                   )

        drop_file = open(self.filename, "w")
        write = drop_file.write

        write(initial_data)
        for drop in self.drops:
            write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(*drop))
        write(final_data)
        for note in range(1, len(self.notes)):
            write(self.notes[note])
        final_notes = self.input_with_timeout("Final Notes: ", 30)
        write("Final Notes: " + final_notes)
        drop_file.close()

        noise_file = open(self.filename + "_Noise", "w")
        for noise in self.noise:
            noise_file.write("{}\t{}\n".format(*noise))
        noise_file.close()


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
