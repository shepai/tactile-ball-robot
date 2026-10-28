
"""
Keyboard controller for the X/Z rig.

Requires:
    rig_control.py
    pyserial

Keys:
    1 = X negative
    2 = X positive
    3 = Z negative
    4 = Z positive
    Q = quit

Windows terminal version.
"""

import time
import serial
import rig_control


# ---------------- SETTINGS ----------------

PORT = "COM3"       # Change to your Arduino's COM port
SPEED = 100         # Requested steps per second
STEP_DISTANCE = 100 # Steps per keypress

# ------------------------------------------


def main():
    try:
        connection = serial.Serial(
            PORT,
            rig_control.BAUD_RATE,
            timeout=rig_control.SERIAL_TIMEOUT,
            write_timeout=2,
        )
    except (serial.SerialException, OSError) as exc:
        print(f"Could not connect to Arduino: {exc}")
        return

    print("Connecting to rig...")
    time.sleep(2)

    print("\nX/Z Keyboard Controller")
    print("-----------------------")
    print("1 = X negative")
    print("2 = X positive")
    print("3 = Z negative")
    print("4 = Z positive")
    print("Q = Quit")
    print(f"\nStep distance: {STEP_DISTANCE}")
    print(f"Speed: {SPEED} steps/sec")
    print("\nPress a key then Enter to move.")

    try:
        while True:
            key = input("Key: ").strip().lower()

            if key == "q":
                connection.write(b"STOP\n")
                connection.flush()
                break

            elif key == "1":
                rig_control.move(
                    connection, "X", -STEP_DISTANCE, SPEED
                )

            elif key == "2":
                rig_control.move(
                    connection, "X", STEP_DISTANCE, SPEED
                )

            elif key == "3":
                rig_control.move(
                    connection, "Z", -STEP_DISTANCE, SPEED
                )

            elif key == "4":
                rig_control.move(
                    connection, "Z", STEP_DISTANCE, SPEED
                )

            elif key == "":
                continue

            else:
                print("Use keys 1, 2, 3, 4 or Q.")

    except KeyboardInterrupt:
        print("\nStopping rig...")
        try:
            connection.write(b"STOP\n")
            connection.flush()
        except (serial.SerialException, OSError):
            pass

    finally:
        connection.close()
        print("Controller closed.")


if __name__ == "__main__":
    main()
