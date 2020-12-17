import time

import adafruit_mcp4725
import busio

try:
    import board
except Exception as exc:
    print("Exception: {}\n".format(exc))
    BOARD = None


class Valve():
    """Electronically Proportioned Valve
    ....................................
    Uses Raspberry Pi's I2C interface to communicate with a DAC.
    Digital to Analog Converter (DAC) chosen is Adafruit's MCP4725.
    Contains all voltage controls for each control algorithm state.

    Actual voltage is set by dac.raw_value on a 12 bit scale.
    Output further restricted to improve DAC performance and lifetime.
       0 = Absolute off. 0 volts sent by the Raspberry Pi.
      45 = Calibrated off. Valve set to close at this value.
    4055 = Calibrated fully open. Maximum voltage to valve.
    4095 = Absolute open. Maximum possible voltage output.
    Off calibration must be performed physically.

    If a DAC is not connected it uses a simulated DAC.
    This allows local testing and simulations.
    """
    __DELAY = 10
    __SCALE = 100 / 4010

    def __init__(self, **kwargs):
        """
        Initializes Valve
        -----------------
        If there is an error connecting to the external DAC,
        And if user agrees, sets self.dac to use SimDac class.
        Otherwise raises Exception.

        Sets all initial volts values to calibrated off of 45.
        -----------------
        Requires no external arguments.
        Contains **kwargs to pass kywd=arg pairs down MRO chain.
        """
        super().__init__(**kwargs)

        if BOARD:
            self.__i2c = busio.I2C(board.SCL, board.SDA)
            self.dac = adafruit_mcp4725.MCP4725(self.__i2c)
        elif input('Use simulated DAC?\n(Y/N) = ').upper() == 'Y':
            print()
            self.dac = SimDac()
        else:
            raise Exception("No DAC or unsupported DAC connected.")

        self.volts = self.clog_volts = self.__optimal_volts = 45

        self.__latency = time.time()
        self.__time_open = 0
        self.clogged = False

        print(":: VALVE INITIALIZED ::\n")

    def set_volts(self, key):
        """Change voltage by:
            increasing it by 5,
            decreasing it by 5,
            or setting it to a custom value.

            Set clog volts to track current volts.
        """

        vals = {ord('+'): 5, ord('-'): -5}
        funcs = {ord('0'): self.__set_optimal_volts,
                 ord('E'): self.__set_input_volts,
                 }

        if (key & 0xDF) in funcs:
            funcs[key]()
        elif key in vals:
            self.volts += vals[key]
            self.volts = check_bounds(self.volts)

        if (self.dac.raw_value != self.volts and not self.clogged):
            print("Volts: {:.2f}%".format(self.__SCALE * (self.volts - 45)))
            self.clog_volts = self.dac.raw_value = self.volts

    def set_clog_volts(self):
        """Increase clog voltage by 80 (2%) every 5s.
        If the output is at max, increase a time_open counter.
        Once the output is max for 1min the saturation is a successs
        """
        self.clogged = True
        if (time.time() - self.__latency > self.__DELAY):
            self.__latency = time.time()
            if (self.clog_volts == 4055):
                self.__time_open += 1
                print("{}s fuly open.".format(self.__time_open * self.__DELAY))
            else:
                self.clog_volts = check_bounds(self.clog_volts + 80)
                print("Clog volts: {:.2f}%".format(
                      self.__SCALE * (self.clog_volts - 45))
                      )
        if (self.__time_open >= 12):
            return True
        return False

    def __set_optimal_volts(self):
        """Set optimal volt value according to researcher.
        Setas a function for the set_volts procedure.
        """
        self.__optimal_volts = self.volts

    def __set_input_volts(self):
        """Set optimal volt value according to researcher.
        Setas a function for the set_volts procedure.
        """
        try:
            volts = int(input("Please enter your desired voltage: "))
            self.volts = check_bounds(volts)
        except ValueError:
            print("Input was not a number")

    def calculate(self, K, seconds_per_drops, last_drop_time):
        """Calculate appropriate voltage based on most recent drop."""
        print("Calculating new voltage...")
        delta = (time.time() - last_drop_time) - seconds_per_drops
        self.volts = check_bounds((self.__optimal_volts + delta * K))

        if (self.dac.raw_value != self.volts):
            print("Volts: {:.2f}%".format(self.__SCALE * (self.volts - 45)))
            self.clog_volts = self.dac.raw_value = self.volts

    def equalize(self):
        """Reset current volts to last known volts before clogging.
        Closes valve 2x as fast as clog protocol opens it.
        """
        self.__time_open = 0
        self.clogged = False

        while(self.clog_volts > self.volts):
            self.clog_volts -= 80
            time.sleep(0.05)

        if (self.clog_volts < self.volts):
            self.clog_volts = self.volts


def shutoff_valve(dac):
    """Completely closes the valve.
    Makes the current volts a multiple of 10. Then decreases by 5.
    Continues until the volts set to 44% the calibrated 'closed' volts.
    TODO: Parallelize
    TODO: Test read capability of self.dac.raw_value
    """
    print("Shutting off valve...")
    dac.raw_value = int(dac.raw_value / 10) * 10
    while (dac.raw_value > 20):
        dac.raw_value -= 5
        time.sleep(0.1)
    print("Valve closed.\n")


def check_bounds(volts):
    """Limits voltage.
    Voltage limits are 45 (1.1%) and 4055 (99.0%) of a 4095 max.
    Valve calibrated so that at 45 (1.1%) it's fully shutoff.
    """
    if volts > 4055:
        return 4055
    elif volts < 45:
        return 45
    else:
        return volts


class SimDac():
    """Simulated Digital to Analog Converter
    ........................................
    Solely for testing and simulation purposes

    TODO: Implement further DAC methods
    """
    def __init__(self):
        self.raw_value = 0
