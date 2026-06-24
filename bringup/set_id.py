# AmazingHand bring-up — set ONE isolated servo's ID (EEPROM write).
#
# This is a WRITE that persists to the servo's EEPROM. It does NOT move the servo
# (no torque enable, no goal position) — no motion.
#
# SAFETY:
#   - Requires env AH_SET_ID=1 to actually write. Without it, runs a DRY RUN.
#   - Refuses unless EXACTLY ONE servo answers on the bus and it is FROM_ID.
#     (Prevents renumbering two servos at once, or the wrong one.)
#   - Sequence: unlock EEPROM -> write id -> relock -> verify.
#   - factory_reset() is available for recovery if something goes wrong.
#
# Use (only when a SINGLE servo is connected + powered):
#   ~/amazinghand/.venv/bin/python set_id.py              # DRY RUN (read-only census)
#   AH_SET_ID=1 ~/amazinghand/.venv/bin/python set_id.py  # actually write FROM_ID -> TO_ID
import os
from rustypot import Scs0009PyController

SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00"
FROM_ID = int(os.environ.get("AH_FROM_ID", "1"))   # current ID of the lone connected servo
TO_ID = int(os.environ.get("AH_TO_ID", "2"))       # ID to assign it

c = Scs0009PyController(serial_port=SERIAL_PORT, baudrate=1000000, timeout=0.3)

# 1) read-only census: who is on the bus right now?
present = []
for sid in range(1, 9):
    try:
        c.read_present_position(sid)
        present.append(sid)
    except Exception:
        pass
print("present IDs:", present)

if present != [FROM_ID]:
    print(f"ABORT: expected exactly one servo at ID {FROM_ID}, got {present}.")
    print("Connect ONLY the servo you want to renumber, then retry.")
    raise SystemExit(1)

if os.environ.get("AH_SET_ID") != "1":
    print(f"DRY RUN ok: exactly one servo at ID {FROM_ID}. "
          f"Would change ID {FROM_ID} -> {TO_ID}.")
    print("Set AH_SET_ID=1 to actually write. Exiting without writing.")
    raise SystemExit(0)

# 2) EEPROM write sequence (lock register is a bool: True=locked, False=unlocked)
print(f"lock(FROM) before: {c.read_lock(FROM_ID)}")
c.write_lock(FROM_ID, False)    # unlock EEPROM
c.write_id(FROM_ID, TO_ID)      # change ID
c.write_lock(TO_ID, True)       # relock (servo now answers as TO_ID)


def _scalar(v):
    try:
        return v[0]
    except (TypeError, IndexError, KeyError):
        return v


# 3) verify
ok_new = False
try:
    ok_new = (_scalar(c.read_id(TO_ID)) == TO_ID)
except Exception as e:
    print("verify read_id(TO) failed:", e)
gone_old = False
try:
    c.read_present_position(FROM_ID)
except Exception:
    gone_old = True

print(f"read_id({TO_ID}) confirmed: {ok_new}; old ID {FROM_ID} now silent: {gone_old}")
print("SUCCESS: servo is now ID %d." % TO_ID if (ok_new and gone_old)
      else "REVIEW: ID change NOT confirmed — do not assume success.")
