import time


class Model():
    def __init__(self, **kwargs):
        self.last_drop_time = self.drop_sum = 0
        self.seconds_per_drops = kwargs.pop('spd') if 'spd' in kwargs else 2
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

    # Setters
    def add_noise(self, frame_no, noise):
        """Add noise data to class for averaging."""
        self.noise_sum += noise
        self.noise.append((frame_no, noise))

    def add_drop(self, frame_no, noise, beginning, volts):
        """Add drop data to history"""
        self.drops.append([time.time() - beginning,
                           time.time() - self.last_drop_time,
                           frame_no,
                           self.noise_sum / len(self.noise),
                           noise,
                           volts,
                           ])
        self.drop_sum += noise

        self.last_drop_time = time.time()
