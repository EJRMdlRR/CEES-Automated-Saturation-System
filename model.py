import time


class ROI():
    def __init__(self, bounds):
        self.bounds = bounds
        self.coordinates = [0, bounds[0], 0, bounds[1]]
        self.set = False

    def get_ROI(self):
        return self.coordinates

    def set_ROI(self, key):
        """Set region of interest to where drops fall using keys"""
        keys = {ord('W'): (0, -5), ord('S'): (0, 5),
                ord('A'): (1, -5), ord('D'): (1, 5),
                ord('I'): (2, -5), ord('K'): (2, 5),
                ord('J'): (3, -5), ord('L'): (3, 5),
                }

        self.coordinates[keys[key][0]] += keys[key][1]
        self.bounds_checker()

        if key in keys:
            print("Coordinates: ({0}, {1}), ({2}, {3})"
                  .format(*self.coordinates)
                  )

    def bounds_checker(self):
        """Restric ROI to camera capture dimensions"""
        if self.coordinates[0] < 0:
            self.coordinates[0] = 0
        if self.coordinates[1] > self.bounds[0]:
            self.coordinates[1] = self.bounds[0]
        if self.coordinates[2] < 0:
            self.coordinates[2] = 0
        if self.coordinates[3] > self.bounds[1]:
            self.coordinates[3] = self.bounds[1]

class Valve():
    pass

class Model(ROI):
    def __init__(self, **kwargs):
        self.ROI = ROI(kwargs['bounds']) if 'bounds' in kwargs else None

        self.last_drop_time = self.drop_sum = 0
        self.seconds_per_drops = kwargs['spd'] if 'spd' in kwargs else 2
        self.drops = []

        self.noise = []
        self.noise_sum = 0

    # Getters
    def get_drops(self):
        return len(self.drops)

    def get_last_drop(self):
        return self.last_drop_time

    def time_since_drop(self):
        if self.last_drop_time:
            return time.time() - self.last_drop_time
        else:
            return "No drops"

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

    def get_ROI(self):
        if self.ROI:
            return self.ROI.get_ROI()
        else:
            return None

    # Setters
    def add_noise(self, frame_no, noise):
        """Add noise data to class for averaging."""
        self.noise_sum += noise
        self.noise.append((frame_no, noise))

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

        self.last_drop_time = time.time()
