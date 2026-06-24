# AmazingHand bring-up copy — Roy's right hand, finger1 (servo ID 1,2)
# Source: PythonExample/AmazingHand_FingerTest.py (upstream pollen-robotics/AmazingHand)
#
# CHANGES vs upstream:
#   - serial_port "COM11" -> by-id path of THIS Pi's AmazingHand USB-TTL adapter
#     (CH343, serial 5B42133808).
#   - SAFETY GUARD: refuses to open the bus / enable torque / move unless
#     env AH_BRINGUP_ARM=1 is set.
#   - upstream enables torque on ID_1 only; both servos move, so this also enables
#     torque on ID_2. (Observation noted in bringup/README.md.)
#
# PURPOSE: AFTER MiddlePos is calibrated, this exercises the finger:
#   close = (MiddlePos_1+90, MiddlePos_2-90), open = (MiddlePos_1-30, MiddlePos_2+30).
#   The two servos are ANTAGONISTIC (opposite signs) — this is the differential
#   finger mechanism. Air movement only; never against an object.
#
# GATED: do NOT run until (1) bus + power confirmed, (2) MiddlePos calibrated,
#   (3) Roy explicitly approves. Then:
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python AmazingHand_FingerTest.py
import os
import time
import numpy as np

from rustypot import Scs0009PyController


ID_1 = 1  # servo ID to test
ID_2 = 2  # servo ID to test
MiddlePos_1 = 0  # copy the calibrated value from MiddlePos calibration
MiddlePos_2 = 0  # copy the calibrated value from MiddlePos calibration

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"

c = None  # constructed inside main() AFTER the safety guard


def main():
    if os.environ.get("AH_BRINGUP_ARM") != "1":
        print("REFUSING TO MOVE: this enables torque and cycles ID",
              ID_1, "and", ID_2, "open/close around MiddlePos.")
        print("Set AH_BRINGUP_ARM=1 to actually run. Exiting without touching the bus.")
        raise SystemExit(0)

    global c
    c = Scs0009PyController(
        serial_port=SERIAL_PORT,
        baudrate=1000000,
        timeout=0.5,
    )

    c.write_torque_enable(ID_1, 1)
    c.write_torque_enable(ID_2, 1)
    # 1 = On / 2 = Off / 3 = Free

    while True:
        CloseFinger()
        time.sleep(3)
        OpenFinger()
        time.sleep(1)


def CloseFinger():
    c.write_goal_speed(ID_1, 6)  # max speed
    c.write_goal_speed(ID_2, 6)  # max speed
    Pos_1 = np.deg2rad(MiddlePos_1 + 90)
    Pos_2 = np.deg2rad(MiddlePos_2 - 90)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    time.sleep(0.01)


def OpenFinger():
    c.write_goal_speed(ID_1, 6)  # max speed
    c.write_goal_speed(ID_2, 6)  # max speed
    Pos_1 = np.deg2rad(MiddlePos_1 - 30)
    Pos_2 = np.deg2rad(MiddlePos_2 + 30)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    time.sleep(0.01)


if __name__ == '__main__':
    main()
