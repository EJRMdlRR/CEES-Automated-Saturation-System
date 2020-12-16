class ROI():
    """Region of Interest
    .....................
    Contains methods and values relating to the region of interest.
    Possible dimensions are bounded by camera capture input.
    """

    def __init__(self, **kwargs):
        """Initializes ROI
        ------------------
        To allow class to initialize before it's child Monitor class,
        set bounds to default of 400^2.
        Bounds will update when camera capture is first instantiated.
        ------------------
        Uses bounds in **kwargs if given.
        Passes kywd=arg pairs down MRO chain.
        """
        super().__init__(**kwargs)

        if 'bounds' in kwargs:
            self.__bounds = kwargs.pop('bounds')
        else:
            self.__bounds = (400, 400)
        self.coordinates = [0, 0, self.__bounds[1], self.__bounds[0]]

        print(":: ROI INITIALIZED ::\n")

    def set_bounds(self, bounds):
        """Update the maximum bounds for the ROI."""
        self.__bounds = bounds
        self.coordinates = [0, 0, self.__bounds[1], self.__bounds[0]]

    def set_ROI(self, key):
        """Set region of interest for drop event capture using key input.
        W/S control the top border of the ROI.
        A/D control the leftmost border of the ROI.
        I/K control the bottom border of the ROI.
        J/L control the rightmost border of the ROI.
        """
        key = key & 0xDF
        keys = {ord('W'): (1, -5), ord('S'): (1, 5),
                ord('A'): (0, -5), ord('D'): (0, 5),
                ord('I'): (3, -5), ord('K'): (3, 5),
                ord('J'): (2, -5), ord('L'): (2, 5),
                }

        if key in keys:
            self.coordinates[keys[key][0]] += keys[key][1]
            self.__check_bounds()

            print("Coordinates: ({0}, {1}), ({2}, {3})"
                  .format(*self.coordinates)
                  )

    def __check_bounds(self):
        """Restric ROI to camera capture dimensions."""
        for coord in range(3):
            if self.coordinates[coord] < 0:
                self.coordinates[coord] = 0
            elif self.coordinates[coord] > self.__bounds[coord // 2]:
                self.coordinates[coord] = self.__bounds[coord // 2]
