import cv2
import datetime
import time
from multiprocessing import Process

from experiment import Experiment


def parallelize(function, arguments=None):
    """Parallelize functions so as to not interrupt valve operation"""
    if arguments:
        t = Process(target=function, args=arguments)
    else:
        t = Process(target=function)
    t.start()
    t.join()


def summary(exp):
    """ Print out essential experiment statistics"""
    print("Final volts: {:.2f}".format(exp.get_volts()))
    print("Total drops: {}".format(exp.get_drops()))
    print("Average pixel noise: {:.2f}".format(exp.get_noise_average()))
    print("Average drop noise: {:.2f}".format(exp.get_drop_average()))


if __name__ == '__main__':
    exp = Experiment("ASS_v5")
    time.sleep(4)
    mutiny = success = defaults = calibration = False
    frames = waitFrame = 0
    liquid = True

    time_open = 0
    latency_delay = 0
    clogged = False

    while (liquid):
        frame = exp.get_frame()

        if (defaults):
            frames += 1
            frame, noise = exp.image_processing()
            if(calibration):
                """TARGET: Better filtering of drop ripples"""
                if(noise > exp.get_noise_average() * 5):
                    if (exp.get_clog_volts() > exp.get_volts()):
                        exp.equalize()
                    if (waitFrame == 0):
                        exp.add_drop(frames, noise)
                    elif (waitFrame < 10):
                        waitFrame += 1
                    else:
                        waitFrame = 0
                    time_open = 0
                    clogged = False
                else:
                    # clog protocol
                    # if no drop, increase volts every 10s (latency)
                    # if 60s at max volts with no drop pass, terminate
                    if (exp.time_since_drop() > 30):
                        if (not clogged):
                            latency_delay = time.time()
                            clogged = True
                        if (time.time() - latency_delay > 10):
                            print("{:.2f}".format(time.time() - latency_delay))
                            if (exp.get_clog_volts() == 4055):
                                time_open += 1
                            else:
                                exp.set_clog_volts()
                            clogged = False
                        if (time_open >= 6):
                            success = True
                            liquid = False
                    else:
                        exp.add_noise(frames, noise)
            else:
                mutiny = True
                time.sleep(0.01)
                if (frames < 250):
                    exp.add_noise(frames, noise)
                else:
                    print("CALIBRATION COMPLETE")
                    mutiny = False
                    calibration = True

        # Show the image in a resizeable frame
        cv2.namedWindow('Frame', cv2.WINDOW_NORMAL)
        cv2.imshow('Frame', frame)
        key = cv2.waitKey(60) & 0xDF

        # Checks for keypresses
        if ((key == ord('q')) or (key == ord('Q'))):
            liquid = False
        elif (key == ord('0')):
            # Confirm default volts and re size and location
            defaults = exp.set_optimal_volts()
        elif ((key == ord('r')) or (key == ord('R'))):
            # Don't save data while default volts and rect. values are reset
            defaults = False
        elif ((key == ord('c')) or (key == ord('C'))):
            # Calibration sequence restarts (100 frames to average noise level)
            calibration = False
        elif ((key == ord('n')) or (key == ord('N'))):
            parallelize(exp.add_notes, (frames,))  # Insert additional notes
        elif (key == ord('+')):
            exp.set_volts(0)
        elif (key == ord('-')):
            exp.set_volts(1)
        elif (key != 0xFF):
            exp.set_ROI(key)

        if (not mutiny):
            pass

    exp.capture.release()
    cv2.destroyAllWindows()
    parallelize(exp.shutoff)
    exp.terminate(success)
