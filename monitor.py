import cv2
import numpy as np

from roi import ROI


class Monitor(ROI):
    """Vision Monitor
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
        """
        super().__init__(**kwargs)

        src = kwargs.pop('src') if 'src' in kwargs else 0
        self.__capture = cv2.VideoCapture(src)
        if not self.__capture.isOpened:
            raise Exception("Unable to open {}".format(src))

        self.__frame = None
        self.frame_no = 0
        self.roi_frame = None
        self.backSub = cv2.createBackgroundSubtractorMOG2(40, 60, False)

        BOUNDS = (int(self.__capture.get(4)), int(self.__capture.get(3)))
        self.set_bounds(BOUNDS)

        print(":: MONITOR INITIALIZED ::\n")

    def get_frame(self):
        """Call next frame from camera.
        Draw rectangle around region of interest on each frame.

        If next frame not found raise Exception.
        """
        __, self.__frame = self.__capture.read()

        if self.__frame is None:
            raise Exception("Camera error! Next frame not found.")

        self.__draw_rectangle()

        return self.__frame

    def show_frame(self):
        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
        cv2.imshow('Frame', self.__frame)

        return cv2.waitKey(60) & 0xFF

    def image_processing(self):
        """Process image to capture moving pixels.
        Crop image to region of interest (ROI), then convert to grayscalexp.
        After that use background subtraction on ROI.
        """
        west, north, east, south = self.coordinates

        """TODO: Better variable names"""
        gray = cv2.cvtColor(self.roi_frame, cv2.COLOR_BGR2GRAY)
        fgMask = self.backSub.apply(gray)
        fgMask_RGB = cv2.cvtColor(fgMask, cv2.COLOR_GRAY2RGB)

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

        self.__frame[north: south, west: east] = fgMask_RGB
        noise = cv2.countNonZero(fgMask)

        self.frame_no += 1
        return noise

    def shutoff_vision(self):
        print("Shutting off vision...")
        self.__capture.release()
        cv2.destroyAllWindows()
        print("Vision released.\n")

    def __draw_rectangle(self):
        """Draw rectangle around region of interest (ROI).
        Crop ROI for later processing.
        """
        self.__frame = cv2.rectangle(self.__frame,
                                     (self.coordinates[0], self.coordinates[1]),
                                     (self.coordinates[2], self.coordinates[3]),
                                     (100, 50, 200),
                                     2,
                                     )

        self.roi_frame = self.__frame[self.coordinates[1]: self.coordinates[3],
                                      self.coordinates[0]:self.coordinates[2],
                                      ]
