# AmazingHand bring-up — READ-ONLY bus scan.
#
# This NEVER enables torque and NEVER writes a goal position. It only issues
# read_present_position() to IDs 1..8 and reports which servos answer. No motion.
#
# Purpose: electronically confirm what is on /dev/ttyACM0 BEFORE any calibration.
#   - Expect for finger1 only:        IDs 1 and 2 respond  -> consistent with AmazingHand.
#   - A full right hand:              IDs 1..8 respond.
#   - IDs 3..6 present without 7,8:   ambiguous vs SO-101 arm -> STOP, verify.
#   - Only ID 1 (or garbled):         both finger servos may still be factory ID 1
#                                     -> set ID 2 with the Feetech tool first.
#
# Run: ~/amazinghand/.venv/bin/python bus_scan.py
import numpy as np
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.3)

found = []
for sid in range(1, 9):
    try:
        pos = c.read_present_position(sid)
        deg = float(np.rad2deg(pos))
        print(f"ID {sid}: RESPOND   present_pos = {deg:7.1f} deg")
        found.append(sid)
    except Exception as e:
        print(f"ID {sid}: no response ({type(e).__name__})")

print("---")
print(f"responded IDs: {found}  ({len(found)} servo(s) on the bus)")
# finger map: f1=1,2  f2=3,4  f3=5,6  f4=7,8
if 1 in found:
    print("note: an ID-1 servo is present (factory default) — keep only ONE on the bus when setting IDs.")
