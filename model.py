import time


class Model():
    """Physical Model
    Contains all methods and values realting to the physical model.
    These include the model's current saturation state.
    A byproduct itself of the drops that fell into the model,
    with the counterpart being the model's noise values and methods.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.last_drop_time = time.time()
        self.drop_sum = 0
        self.seconds_per_drops = kwargs.pop('spd') if 'spd' in kwargs else 2
        self.drops = []

        self.noise = []
        self.noise_sum = 0

        self.saturated = False

        print(":: MODEL INITIALIZED ::\n")

    def get_drop_average(self):
        if len(self.drops):
            return self.drop_sum / len(self.drops)
        else:
            return -1

    def get_noise_average(self):
        if len(self.noise):
            return self.noise_sum / len(self.noise)
        else:
            return -1

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
