import datetime
import select
import sys
import time
from multiprocessing import Process

try:
    import termios
    termios_lib = True
except Exception as exc:
    print("Exception: {}\n".format(exc))
    termios_lib = False

from model import Model
from monitor import Monitor
from valve import Valve, shutoff_valve


class Experiment(Monitor, Valve, Model, ):
    """
    TODO: Improve constants or parametrize
    """
    MIN_NOISE = 50
    CLOG_DELAY = 30
    NOISE_SPIKE = 5
    CALIBRATION_FRAMES = 250

    def __init__(self, title='', user='Default', viscosity=50, **kwargs):
        super().__init__(**kwargs)

        self.title = title
        self.date = datetime.datetime.now().strftime("$M.%H.%m.%d.%Y")
        self.filename = self.title + "_" + self.date + ".txt"

        self.user = user
        self.viscosity = viscosity
        self.notes = ['self.add_notes(0)']
        self.beginning = time.time()

        self.defaults_set = False

        print(":: EXPERIMENT INITIALIZED ::\n")

    def main(self):
        """
        TODO: Improve control algorithm.
        TODO: Calibration reset system
        """
        try:
            while not self.saturated:
                self.get_frame()
                if self.defaults_set:
                    noise = self.image_processing()
                    if (self.frame_no > self.CALIBRATION_FRAMES):
                        threshold = max(self.get_noise_average()
                                        * self.NOISE_SPIKE, self.MIN_NOISE)
                        time_since_drop = time.time() - self.last_drop_time

                        if noise > threshold:
                            self.check_for_drop(noise)
                        elif (time_since_drop > self.CLOG_DELAY):
                            self.saturated = self.set_clog_volts()
                        else:
                            self.add_noise(self.frame_no, noise)

                    else:
                        self.add_noise(self.frame_no, noise)

                key = self.show_frame()
                self.key_input(key)

            self.terminate()

        except Exception as exc:
            print("Exception:", exc)
            print("Shutdown complete")

    def key_input(self, key):
        self.set_volts(key)
        self.set_ROI(key)
        if key == ord('0'):
            self.defaults_set = True
            return

        key = key & 0xDF
        if key == ord('R'):
            self.defaults_set = False
        elif key == ord('N'):
            parallelize(self.add_notes, (self.frame_no,))
        elif key == ord('Q'):
            print("Program terminated by keyboard input!")
            self.terminate()

    def check_for_drop(self, noise):
        print("Checking for drop...")
        time_since_drop = time.time() - self.last_drop_time
        print("{:.2f}s since last drop".format(time_since_drop))

        if (time.time() - self.last_drop_time) > 0.1:
            print("Drop! Adding to database...")
            self.add_drop(self.frame_no, noise, self.beginning, self.volts)
            self.calculate(self.viscosity,
                           self.seconds_per_drops,
                           self.last_drop_time
                           )
            self.equalize()
        else:
            print("Ripple effect")

    def add_notes(self, frame_no):
        """Add user notes to experiment data."""
        notes = input_with_timeout("Notes: ", 30)
        self.notes.append("Notes at frame [{}]: {}".format(frame_no, notes))

    def summary(self):
        """ Print out essential experiment statistics"""
        print("Final volts: {}".format(self.volts))
        print("Total drops: {}".format(len(self.drops)))
        print("Average pixel noise: {:.2f}".format(self.get_noise_average()))
        print("Average drop noise: {:.2f}".format(self.get_drop_average()))

    def terminate(self):
        """Execute termination procedure
        1. Compile collected experiment data into strings
        2. Write collected drop data to text file.
        3. Write collected noise data to text file
        """
        print("Terminating...\n")
        self.shutoff_vision()
        parallelize(shutoff_valve, (self.dac,))
        self.summary()

        emptied = "Succesful" if self.saturated else "Unsuccesful"
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
                   str(self.volts),
                   str(len(self.drops)),
                   str(self.get_noise_average()),
                   str(self.get_drop_average()),
                   )

        drop_file = open(self.filename, "w")
        write = drop_file.write

        write(initial_data)
        for drop in self.drops:
            write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(*drop))
        write(final_data)
        for note in range(1, len(self.notes)):
            write(self.notes[note])
        if termios_lib:
            final_notes = input_with_timeout("Final Notes: ", 30)
            write("Final Notes: " + final_notes)
        drop_file.close()

        noise_file = open(self.filename + "_Noise", "w")
        for noise in self.noise:
            noise_file.write("{}\t{}\n".format(*noise))
        noise_file.close()

        raise Exception("Program has been quit")


def parallelize(function, arguments=None):
    """Parallelize functions so as to not interrupt valve operation"""
    if arguments:
        t = Process(target=function, args=arguments)
    else:
        t = Process(target=function)
    t.start()
    t.join()


def input_with_timeout(prompt, timeout):
    """Read keyboard input for [timeout]s length of time.
    Also, expect stdin to be line buffered"""
    print(prompt)
    if termios_lib:
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().rstrip('\n')
    return "None"
