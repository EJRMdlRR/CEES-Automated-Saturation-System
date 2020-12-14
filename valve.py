import time

import adafruit_mcp4725
import board
import busio


class Valve():
    # Constructor
    def __init__(self, **kwargs):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dac = adafruit_mcp4725.MCP4725(self.i2c)
        self.volts = self.clog_volts = self.optimal_volts = 45
        self.scale = 100/4010

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

        self.clog_volts = self.volts = check_bounds(self.volts)
        print("Volts: {:.2f}%".format(self.scale * (self.volts - 45)))

    def set_clog_volts(self):
        """Increase clog voltage by 81 (2%)"""
        self.clog_volts = check_bounds(self.clog_volts + 80)
        print("Clog volts: {:.2f}%".format(self.scale * (self.clog_volts - 45)))

    def set_optimal_volts(self):
        """Set optimal volt value according to researcher."""
        self.optimal_volts = self.volts
        return True

    # Miscellaneous
    def calculate(self, K, seconds_per_drops, last_drop_time):
        delta = (time.time() - last_drop_time) - seconds_per_drops
        volts = (self.optimal_volts + delta * K)
        self.clog_volts = self.volts = check_bounds(volts)

        print("{:.2f}s since last drop".format(time.time() - last_drop_time))
        print("Volts: {:.2f}%".format(self.scale * ((self.volts - 45))))

    def equalize(self):
        """Reset current volts to last known volts before clogging."""
        while(self.clog_volts > self.volts):
            self.clog_volts -= 160
            time.sleep(0.05)

        if (self.clog_volts < self.volts):
            self.clog_volts = self.volts

    def shutoff(self):
        """Completely closes the valve.
        Makes the current volts a multiple of 10. Then decreases by 5.
        Continues until the volts set to 44% the calibrated 'closed' volts.
        """
        self.volts = int(self.volts / 10) * 10
        while (self.volts > 20):
            self.dac.raw_value = self.volts = self.volts - 5
            time.sleep(0.1)


def check_bounds(volts):
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
