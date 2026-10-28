
"""
X/Z rig keyboard controller + DC motor.

1 = X negative
2 = X positive
3 = Z negative
4 = Z positive
5 = DC forward
6 = DC reverse
7 = DC stop
Q = Quit

Windows terminal version.
"""

import time
import msvcrt
import serial

import rig_control


PORT = "COM3"           # Change to your Arduino COM port
STEP_DISTANCE = 100
STEPPER_SPEED = 100


def send(connection, command):
    connection.write((command + "\n").encode("ascii"))
    connection.flush()
    print(f"Sent: {command}")


def main():
    try:
        connection = serial.Serial(
            PORT,
            rig_control.BAUD_RATE,
            timeout=0.1,
            write_timeout=2,
        )
    except (serial.SerialException, OSError) as exc:
        print(f"Could not connect to Arduino: {exc}")
        return

    print("Connecting to Arduino...")
    time.sleep(2)

    # Read any initial READY message.
    while connection.in_waiting:
        print(connection.readline().decode(
            "utf-8", errors="replace"
        ).strip())

    print("""
X/Z Rig Controller
------------------
1 = X negative
2 = X positive
3 = Z negative
4 = Z positive
5 = DC forward
6 = DC reverse
7 = DC stop
Q = Quit

Press a key to send a command.
""")

    try:
        while True:
            # Display Arduino replies when available.
            while connection.in_waiting:
                reply = connection.readline().decode(
                    "utf-8", errors="replace"
                ).strip()

                if reply:
                    print(f"\nArduino: {reply}")

            if not msvcrt.kbhit():
                time.sleep(0.02)
                continue

            key = msvcrt.getwch().lower()

            if key == "1":
                rig_control.move(
                    connection, "X", -STEP_DISTANCE,
                    STEPPER_SPEED
                )

            elif key == "2":
                rig_control.move(
                    connection, "X", STEP_DISTANCE,
                    STEPPER_SPEED
                )

            elif key == "3":
                rig_control.move(
                    connection, "Z", -STEP_DISTANCE,
                    STEPPER_SPEED
                )

            elif key == "4":
                rig_control.move(
                    connection, "Z", STEP_DISTANCE,
                    STEPPER_SPEED
                )

            elif key == "5":
                send(connection, "DC FORWARD")

            elif key == "6":
                send(connection, "DC REVERSE")

            elif key == "7":
                send(connection, "DC STOP")

            elif key == "q":
                send(connection, "STOP")
                time.sleep(0.1)
                break

    except KeyboardInterrupt:
        print("\nStopping motors...")
        try:
            send(connection, "STOP")
            time.sleep(0.1)
        except (serial.SerialException, OSError):
            pass

    finally:
        connection.close()
        print("Controller closed.")


if __name__ == "__main__":
    main()
