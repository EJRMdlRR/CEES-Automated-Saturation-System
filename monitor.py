import cv2
import numpy as np

from roi import ROI


class Monitor(ROI):
    # Constructor
    def __init__(self, src=0, **kwargs):
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
        print("INIT MONITOR")

        self.capture = cv2.VideoCapture(src)
        print("CAPTURED")
        if not self.capture.isOpened:
            print("Unable to open", src)
            exit(1)

        self.frame = None
        self.roi_frame = None
        self.backSub = cv2.createBackgroundSubtractorMOG2(40, 60, False)

        bounds = (int(self.capture.get(4)), int(self.capture.get(3)))
        super().__init__(bounds=bounds, **kwargs)

    def get_frame(self):
        __, self.frame = self.capture.read()

        if self.frame is None:
            print("Camera Error!")
            exit(1)

        self.draw_rectangle()

        return self.frame

    def image_processing(self):
        """Process image to capture moving pixels.
        Crop image to region of interest (ROI), then convert to grayscalexp.
        After that use background subtraction on ROI.
        """
        east, north, west, south = self.coordinates

        """TARGET: Better variable names"""
        gray = cv2.cvtColor(self.roi_frame, cv2.COLOR_BGR2GRAY)
        fgMask = self.backSub.apply(gray)
        fgMask_RGB = cv2.cvtColor(fgMask, cv2.COLOR_GRAY2RGB)

        cv2.rectangle(self.frame,
                      (10, 2),
                      (100, 20),
                      (0, 0, 0),
                      -1
                      )
        cv2.putText(self.frame,
                    str(self.capture.get(cv2.CAP_PROP_POS_FRAMES)),
                    (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255)
                    )

        self.frame[north: south, west: east] = fgMask_RGB
        noise = cv2.countNonZero(fgMask)
        return self.frame, noise

    def draw_rectangle(self):
        self.frame = cv2.rectangle(self.frame,
                                   (self.coordinates[0], self.coordinates[1]),
                                   (self.coordinates[2], self.coordinates[3]),
                                   (100, 50, 200),
                                   3,
                                   )
        self.roi_frame = self.frame[self.coordinates[0]:self.coordinates[1],
                                    self.coordinates[2]: self.coordinates[3],
                                    ]
