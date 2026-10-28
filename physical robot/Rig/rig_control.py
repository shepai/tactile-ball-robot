
"""
X/Z Rig Controller
------------------
Sends commands to an Arduino over USB serial.

Expected Arduino command protocol:
    MOVE X <steps> <speed>
    MOVE Z <steps> <speed>
    STOP
    STATUS

Example:
    MOVE X 200 400
    MOVE Z -100 200

Positive/negative steps determine direction.
Speed is expressed in steps per second.

DC motor support can be added later.
"""

import sys
import threading
import time

import serial
from serial.tools import list_ports


BAUD_RATE = 115200
SERIAL_TIMEOUT = 0.2

# Safety-oriented software limits for commanded movement.
# Adjust these after determining the physical travel of your rig.
MAX_COMMAND_STEPS = 10000
MAX_SPEED = 1000


def show_ports():
    """List serial ports detected by the computer."""
    ports = list(list_ports.comports())

    if not ports:
        print("No serial ports detected.")
        return

    print("\nAvailable serial ports:")
    for port in ports:
        print(f"  {port.device}: {port.description}")


def serial_reader(connection, stop_event):
    """Print messages sent back by the Arduino."""
    while not stop_event.is_set():
        try:
            if connection.in_waiting:
                message = connection.readline().decode(
                    "utf-8", errors="replace"
                ).strip()

                if message:
                    print(f"\nArduino: {message}")
                    print("> ", end="", flush=True)
            else:
                time.sleep(0.02)

        except (serial.SerialException, OSError):
            if not stop_event.is_set():
                print("\nSerial connection lost.")
            break


def send_command(connection, command):
    """Send one newline-terminated command to the Arduino."""
    connection.write((command + "\n").encode("utf-8"))
    connection.flush()
    print(f"Sent: {command}")


def move_axis(connection, axis, steps, speed):
    """Validate and send a relative movement command."""
    axis = axis.upper()

    if axis not in ("X", "Z"):
        print("Invalid axis. Use X or Z.")
        return

    if steps == 0:
        print("Steps must be non-zero.")
        return

    if abs(steps) > MAX_COMMAND_STEPS:
        print(f"Maximum movement per command is "
              f"{MAX_COMMAND_STEPS} steps.")
        return

    if not 0 < speed <= MAX_SPEED:
        print(f"Speed must be between 1 and {MAX_SPEED} steps/sec.")
        return

    send_command(
        connection,
        f"MOVE {axis} {steps} {speed}"
    )


def print_help():
    print("""
Commands
--------
move X <steps> <speed>    Move X axis
move Z <steps> <speed>    Move Z axis
x+ <steps> [speed]        Move X in positive direction
x- <steps> [speed]        Move X in negative direction
z+ <steps> [speed]        Move Z in positive direction
z- <steps> [speed]        Move Z in negative direction
stop                      Request motion stop
status                    Request Arduino status
ports                     List serial ports
help                      Show commands
quit                      Exit controller

Examples
--------
move X 200 400
move Z -100 200
x+ 500
z- 100 150

Movement is in motor steps, not millimetres.
""")


def main():
    if len(sys.argv) < 2:
        print("Usage: python rig_control.py <serial_port>")
        print("Example: python rig_control.py COM3")
        print("Example: python rig_control.py /dev/ttyACM0")
        show_ports()
        return

    port = sys.argv[1]

    try:
        connection = serial.Serial(
            port=port,
            baudrate=BAUD_RATE,
            timeout=SERIAL_TIMEOUT,
            write_timeout=2,
        )
    except (serial.SerialException, OSError) as exc:
        print(f"Could not open {port}: {exc}")
        show_ports()
        return

    # Many Arduino boards reset when the serial port opens.
    print(f"Connected to {port} at {BAUD_RATE} baud.")
    print("Waiting for Arduino to initialise...")
    time.sleep(2)

    # Discard startup messages already received.
    connection.reset_input_buffer()

    stop_event = threading.Event()
    reader = threading.Thread(
        target=serial_reader,
        args=(connection, stop_event),
        daemon=True,
    )
    reader.start()

    print("Rig controller ready. Type 'help' for commands.")

    try:
        while True:
            try:
                raw = input("> ").strip()
            except EOFError:
                break

            if not raw:
                continue

            parts = raw.split()
            command = parts[0].lower()

            if command == "help":
                print_help()

            elif command == "ports":
                show_ports()

            elif command == "quit":
                # Ask the Arduino to stop before disconnecting.
                send_command(connection, "STOP")
                time.sleep(0.1)
                break

            elif command == "stop":
                send_command(connection, "STOP")

            elif command == "status":
                send_command(connection, "STATUS")

            elif command in ("x+", "x-", "z+", "z-"):
                if len(parts) not in (2, 3):
                    print(f"Usage: {command} <steps> [speed]")
                    continue

                try:
                    steps = abs(int(parts[1]))
                    speed = int(parts[2]) if len(parts) == 3 else 200

                    if command.endswith("-"):
                        steps = -steps

                    move_axis(
                        connection,
                        command[0].upper(),
                        steps,
                        speed,
                    )
                except ValueError:
                    print("Steps and speed must be integers.")

            elif command == "move":
                if len(parts) != 4:
                    print("Usage: move <X|Z> <steps> <speed>")
                    continue

                try:
                    axis = parts[1].upper()
                    steps = int(parts[2])
                    speed = int(parts[3])

                    move_axis(connection, axis, steps, speed)
                except ValueError:
                    print("Steps and speed must be integers.")

            else:
                print("Unknown command. Type 'help'.")

    except KeyboardInterrupt:
        print("\nStopping requested...")
        try:
            send_command(connection, "STOP")
            time.sleep(0.1)
        except (serial.SerialException, OSError):
            pass

    except (serial.SerialException, OSError) as exc:
        print(f"\nSerial error: {exc}")

    finally:
        stop_event.set()
        reader.join(timeout=1)
        connection.close()
        print("Serial connection closed.")


def move(connection, axis, steps, speed):
    """Send a validated relative move to the Arduino."""

    axis = axis.upper()

    if axis not in ("X", "Z"):
        print("Axis must be X or Z.")
        return

    if steps == 0 or abs(steps) > 10000:
        print("Invalid step count.")
        return

    if not 1 <= speed <= 400:
        print("Speed must be between 1 and 400 steps/sec.")
        return

    command = f"MOVE {axis} {steps} {speed}\n"

    connection.write(command.encode("ascii"))
    connection.flush()

    print(f"Sent: {command.strip()}")

if __name__ == "__main__":
    main()
