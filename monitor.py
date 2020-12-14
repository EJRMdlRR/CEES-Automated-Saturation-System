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
        self.capture = cv2.VideoCapture(src)
        if not self.capture.isOpened:
            print("Unable to open", src)
            exit(1)

        self.backSub = cv2.createBackgroundSubtractorMOG2(40, 60, False)

        bounds = (int(self.capture.get(4)), int(self.capture.get(3)))
        super().__init__(bounds=bounds, **kwargs)

    def image_processing(self, frame):
        """Process image to capture moving pixels.
        Crop image to region of interest (ROI), then convert to grayscalexp.
        After that use background subtraction on ROI.
        """
        north, south, east, west = self.coordinates

        """TARGET: Better variable names"""
        gray = cv2.cvtColor(rect_img, cv2.COLOR_BGR2GRAY)
        fgMask = self.backSub.apply(gray)
        fgMask_RGB = cv2.cvtColor(fgMask, cv2.COLOR_GRAY2RGB)

        cv2.rectangle(frame,
                    (10, 2),
                    (100, 20),
                    (0, 0, 0),
                    -1
                    )
        cv2.putText(frame,
                    str(capture.get(cv2.CAP_PROP_POS_FRAMES)),
                    (15, 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255)
                    )

        frame[north: south, west: east] = fgMask_RGB
        noise = cv2.countNonZero(fgMask)
        return frame, noise
