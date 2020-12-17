import time


class Model():
    """Physical Model.

    Contains all methods and values realting to the physical model.
    These include the model's current saturation state.
    A byproduct itself of the drops that fell into the model,
     with the counterpart being the model's noise values and methods.
    """

    def __init__(self, **kwargs):
        """Initialize virtualization of Physical Model.

        All relevant drop/no-drop data is saved to lists
         for later local storage.

        Dop noise and no-drop noise are calculated each frame
         to prevent unnecessary list iterations.

        Uses seconds per drop in **kwargs if given.
        Passes kywd=arg pairs down MRO chain.

        TODO: Automate setting of seconds per drops
        """
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
        """Return average noise of drop frames. If none return -1."""
        if len(self.drops) > 0:
            return self.drop_sum / len(self.drops)
        return -1

    def get_noise_average(self):
        """Return average noise of no-drop frames. If none return -1."""
        if len(self.noise) > 0:
            return self.noise_sum / len(self.noise)
        return -1

    def add_noise(self, frame_no, noise):
        """Add noise data to class for averaging."""
        self.noise_sum += noise
        self.noise.append((frame_no, noise))

    def add_drop(self, frame_no, noise, beginning, volts):
        """Add drop data to history.

        Data includes: time since beginning,
         time since last drop, frame number,
         current noise average, frame's noise,
         and current volts.
        """
        self.drops.append([time.time() - beginning,
                           time.time() - self.last_drop_time,
                           frame_no,
                           self.noise_sum / len(self.noise),
                           noise,
                           volts,
                           ])
        self.drop_sum += noise

        self.last_drop_time = time.time()
