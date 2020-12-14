# Import libraries
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
    mutiny = success = defaults = calibration = False
    frames = waitFrame = 0
    liquid = True

    time_open = 0
    latency_delay = 0
    clogged = False

    while (liquid):
        ret, frame = exp.capture.read()
        if frame is None:
            print("Camera Error")
            exit(1)

        r = cv2.rectangle(frame,
                          (coords[3], coords[0]),
                          (coords[2], coords[1]),
                          (100, 50, 200),
                          3,
                          )
        rect_img = frame[coords[0]:coords[1], coords[3]: coords[2]]

        if (defaults):
            frames += 1
            frame, noise = image_processing(backSub, frame, coords)
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
        k = cv2.waitKey(60) & 0xDF

        # Checks for keypresses
        if ((k == ord('q')) or (k == ord('Q'))):
            liquid = False
        elif (k == ord('0')):
            # Confirm default volts and re size and location
            defaults = exp.set_optimal_volts()
        elif ((k == ord('r')) or (k == ord('R'))):
            # Don't save data while default volts and rect. values are reset
            defaults = False
        elif ((k == ord('c')) or (k == ord('C'))):
            # Calibration sequence restarts (100 frames to average noise level)
            calibration = False
        elif ((k == ord('n')) or (k == ord('N'))):
            parallelize(exp.add_notes, (frames,))  # Insert additional notes
        elif (k == ord('+')):
            exp.set_volts(0)
        elif (k == ord('-')):
            exp.set_volts(1)
        elif (k != 0xFF):
            coords = frame_set(coords, k)

        if (not mutiny):
            pass

    capture.release()
    cv2.destroyAllWindows()
    parallelize(exp.shutoff)
    exp.terminate(success)
