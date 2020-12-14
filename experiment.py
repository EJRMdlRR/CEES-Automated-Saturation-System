import datetime
from model import Model
from valve import Valve
from monitor import Monitor
import select
import sys
import time


class Experiment(Model, Valve, Monitor):
    # constructor
    def __init__(self, title='', user='Default', viscosity=50, **kwargs):
        print("INIT EXP")
        self.title = title
        self.date = datetime.datetime.now().strftime("$M.%H.%m.%d.%Y")
        self.filename = self.title + "_" + self.date + ".txt"

        self.user = user
        self.viscosity = viscosity
        self.notes = ['self.add_notes(0)']
        self.beginning = time.time()

        super().__init__()

    # setters
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
