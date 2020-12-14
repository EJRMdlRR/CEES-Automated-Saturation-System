class ROI():
    def __init__(self, bounds=(99, 99), **kwargs):
        self.bounds = bounds
        self.coordinates = [0, self.bounds[0], 0, self.bounds[1]]
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
        for coord in range(3):
            if self.coordinates[coord] < 0:
                self.coordinates[coord] = 0
            elif self.coordinates[coord] > self.bounds[coord // 2]:
                self.coordinates[coord] = self.bounds[coord // 2]
