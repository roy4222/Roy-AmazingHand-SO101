# AmazingHand bring-up copy — Roy's right hand, finger1 (servo ID 1,2)
# Source: PythonExample/AmazingHand_Hand_FingerMiddlePos.py (upstream pollen-robotics/AmazingHand)
#
# CHANGES vs upstream:
#   - serial_port "COM11" -> by-id path of THIS Pi's AmazingHand USB-TTL adapter
#     (CH343, serial 5B42133808). by-id is stable across re-plug and CANNOT
#     accidentally point at the SO-101 adapters (serials 5AAF220371 / 5AAF220335).
#   - SAFETY GUARD: refuses to open the bus / enable torque / move unless
#     env AH_BRINGUP_ARM=1 is set. A bare `python ...` run does nothing.
#
# PURPOSE: drive servos ID_1/ID_2 to their middle position so you can fit the
#   servo horns at neutral. MiddlePos_1/MiddlePos_2 (degrees) start at 0 and MUST
#   be calibrated for THIS hand — the author's r_hand.toml offsets are HIS hand.
#
# DO NOT run for real until Roy confirms bus + 5V power. Then:
#   AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python AmazingHand_Hand_FingerMiddlePos.py
import os
import time
import numpy as np

from rustypot import Scs0009PyController


ID_1 = 1  # servo ID to calibrate
ID_2 = 2  # servo ID to calibrate
MiddlePos_1 = 0  # middle position (deg) for ID_1 — CALIBRATE for this hand
MiddlePos_2 = 0  # middle position (deg) for ID_2 — CALIBRATE for this hand

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"

c = None  # constructed inside main() AFTER the safety guard


def main():
    if os.environ.get("AH_BRINGUP_ARM") != "1":
        print("REFUSING TO MOVE: this enables torque and drives ID",
              ID_1, "and", ID_2, "to MiddlePos.")
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
        ServosInMiddle()
        time.sleep(3)


def ServosInMiddle():
    c.write_goal_speed(ID_1, 6)  # max speed
    c.write_goal_speed(ID_2, 6)  # max speed
    Pos_1 = np.deg2rad(MiddlePos_1)
    Pos_2 = np.deg2rad(MiddlePos_2)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    time.sleep(0.01)


if __name__ == '__main__':
    main()
