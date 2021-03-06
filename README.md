# CEES-Automated-Saturation-System

&nbsp;&nbsp;&nbsp;&nbsp;An alternative to classic flow meters, the Automated saturation system can regulate liquid flow using an electronically controlled valve, a camera and a microcontroller. By tracking pixel changes using OpenCV within a user-designated region of interest it can detect drops even with poor visibility. Designed primarily for epxerimental setups where a model needs to be hydrated without being disturbed, it removes the need of human vigilance for the duration of the hydration.

## Key Usage Table
| Key| Function						 		     |
|----|-------------------------------------------|
| 0	 | Sets current values as defaults [1]		 |
| e  | Enter a voltage value                     |
| +	 | Increases voltage	 				     |
| -	 | Decreases voltage	 				     |
| q	 | Terminates (quits) the program	 		 |
| r	 | Resets frame adjustment sequence	 		 |
| w, a, s, d | Manipulates top-left corner of frame |
| i, j, k, l | Manipulates bottom-right corner of frame |

[1] Default values required for calibration. Can be reset at anytime using keys.

## Prime Goals
* Switch to Pi Camera
* Autoset Seconds per Drop to 80% of first K drops after researcher sets voltage value based on sight
* Model valve behavior with constant pressure water, then with gravity's pressure, then with viscous liquid
* Polish control algorithm, rolling average || bounded values || combination
* Remote access to RPi
* Reach out to other Earthquake Centers
* Design enclosure for system (including lighting)

