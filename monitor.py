import cv2

from roi import ROI


class Monitor(ROI):
    """Vision Monitor.

    Contains all methods and values that handle machine vision.
    This includes camera interfacing, region of interest (ROI),
     and data processing, among others.
    """

    def __init__(self, **kwargs):
        """Initialize Python-Camera interface.

        Choose video with:
         0 for laptop camera
         1 for USB camera
         cv2.samples.findFileOrKeep(<FILEPATH>) for a file

        Required background subtractor parameters are:
         [history, varThreshold, detectShadows]
        Tweaking may be necessary for optimal results.

        More on background subtraction methods at
        https://docs.opencv.org/4.5.0/de/de1/group__video__motion.html

        Uses source in **kwargs if given.
        Passes kywd=arg pairs down MRO chain.
        """
        super().__init__(**kwargs)

        src = kwargs.pop('src') if 'src' in kwargs else 0
        self.__capture = cv2.VideoCapture(src)
        if not self.__capture.isOpened:
            raise Exception("Unable to open {}".format(src))

        self.__frame = None
        self.frame_no = 0
        self.__roi_frame = None
        self.__backSub = cv2.createBackgroundSubtractorMOG2(40, 60, False)

        bounds = (int(self.__capture.get(4)), int(self.__capture.get(3)))
        self.set_bounds(bounds)

        print(":: MONITOR INITIALIZED ::\n")

    def get_frame(self):
        """Call next frame from camera.

        Draw rectangle around region of interest on each frame.
        If next frame not found raise Exception.

        Returns: OpenCV frame (numerical array)
        """
        __, self.__frame = self.__capture.read()

        if self.__frame is None:
            raise Exception("Camera error! Next frame not found.")

        self.__draw_rectangle()

        return self.__frame

    def show_frame(self):
        """Show frame in a resizeable window.

        Shows each frame for 30ms (~30 FPS),
         or until a key is pressed.

        Returns: ASCII value of key pressed (int)
        """
        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
        cv2.imshow('Frame', self.__frame)

        return cv2.waitKey(30) & 0xFF

    def image_processing(self):
        """Process image to capture moving pixels.

        Crop image to region of interest (ROI), then convert to grayscale.
        After that use background subtraction on ROI.

        TODO: Better variable names

        Returns: Amount of pixels detected to have moved (int)
        """
        west, north, east, south = self._coordinates

        gray = cv2.cvtColor(self.__roi_frame, cv2.COLOR_BGR2GRAY)
        fg_mask = self.__backSub.apply(gray)
        fg_mask_rgb = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2RGB)

        cv2.rectangle(self.__frame,
                      (10, 2),
                      (100, 20),
                      (0, 0, 0),
                      -1
                      )
        cv2.putText(self.__frame,
                    str(self.__capture.get(cv2.CAP_PROP_POS_FRAMES)),
                    (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255)
                    )

        self.__frame[north: south, west: east] = fg_mask_rgb
        noise = cv2.countNonZero(fg_mask)

        self.frame_no += 1
        return noise

    def shutoff_vision(self):
        """Release camera interface. Destroy any associated windows."""
        print("Shutting off vision...")
        self.__capture.release()
        cv2.destroyAllWindows()
        print("Vision released.\n")

    def __draw_rectangle(self):
        """Draw rectangle around ROI. Crop for later processing."""
        west, north, east, south = self._coordinates

        self.__frame = cv2.rectangle(self.__frame,
                                     (west, north),
                                     (east, south),
                                     (100, 50, 200),
                                     2,
                                     )

        self.__roi_frame = self.__frame[north: south, west: east]
