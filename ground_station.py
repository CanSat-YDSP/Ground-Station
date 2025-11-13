import serial
import struct
import asyncio
from datetime import datetime
from prompt_toolkit import Application
from prompt_toolkit.widgets import TextArea, Frame, Label
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, ConditionalContainer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings

class SerialReader:
    def __init__(self, port, baudrate=9600, timeout=0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def read_line(self):
        if self.ser.in_waiting > 0:
            # also check if line starts with 0xFF and ends with 0x0A
            line = self.ser.readline()
            if line.startswith(b'\xFF') and line.endswith(b'\x0A'):
                return line  # strip start, length, checksum, and end
        return None

    def write_line(self, data: bytes):
        self.ser.write(b'\xFF')
        no_bytes = len(data)
        self.ser.write(bytes([no_bytes]))
        self.ser.write(data)
        self.ser.write(bytes([self.calculate_xor_checksum(data)]))
        self.ser.write(b'\x0A')

    def calculate_xor_checksum(self, data: bytes) -> int:
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    def close(self):
        self.ser.close()

gs = SerialReader('COM10', 9600)

show_raw = True

# Raw hex output
raw_output = TextArea(
    focusable=False,
    scrollbar=True,
    wrap_lines=False
)

# Decoded info output
decoded_output = TextArea(
    focusable=False,
    scrollbar=True,
    wrap_lines=False
)

instructions = Label(
    text='Type commands. Press Enter to send. F2: toggle raw/decoded. Type "exit" to quit.',
    dont_extend_height=True
)

input_field = TextArea(
    height=1,
    prompt='> ',
    wrap_lines=False
)
input_field.buffer.cursor_position = len(input_field.text)

kb = KeyBindings()

# Toggle screen with F2
@kb.add("f2")
def _(event):
    global show_raw
    show_raw = not show_raw

@kb.add("enter")
def _(event):
    user_input = input_field.text.strip()
    if user_input:
        parts = user_input.split()
        if parts[0] == "pressure" and len(parts) == 2:
            try:
                value = float(parts[1])
                gs.write_line(b'\x02' + struct.pack('<f', value))
                raw_output.text += f"Sent pressure: {value}\n"
                decoded_output.text += f"Sent pressure: {value}\n"
            except ValueError:
                raw_output.text += "Invalid pressure value\n"
                decoded_output.text += "Invalid pressure value\n"

        elif parts[0] == "launch":
            gs.write_line(b'\x01')
            raw_output.text += "Sent launch command\n"
            decoded_output.text += "Sent launch command\n"

        elif parts[0] == "enter-sim":
            gs.write_line(b'\x03')
            raw_output.text += "Entered simulation mode\n"
            decoded_output.text += "Entered simulation mode\n"

        elif parts[0] == "send-sim":
            async def send_simulation():
                try:
                    with open("cansat_pressure_profile.csv", "r") as f:
                        next(f)  # skip header
                        for line in f:
                            if not line.strip():
                                continue
                            time_s, pressure_Pa = line.strip().split(",")
                            pressure_value = float(pressure_Pa)
                            gs.write_line(b'\x02' + struct.pack('<f', pressure_value))
                            raw_output.text += f"Sent simulated pressure: {pressure_value}\n"
                            decoded_output.text += f"Sent simulated pressure: {pressure_value}\n"
                            raw_output.buffer.cursor_position = len(raw_output.text)
                            decoded_output.buffer.cursor_position = len(decoded_output.text)
                            await asyncio.sleep(1)
                except FileNotFoundError:
                    raw_output.text += "Error: cansat_pressure_profile.csv not found.\n"
                    decoded_output.text += "Error: cansat_pressure_profile.csv not found.\n"
                except Exception as e:
                    raw_output.text += f"Error during simulation: {e}\n"
                    decoded_output.text += f"Error during simulation: {e}\n"

            asyncio.create_task(send_simulation())
            raw_output.text += "Started simulated pressure transmission...\n"
            decoded_output.text += "Started simulated pressure transmission...\n"

        elif parts[0] == "save-log":
            filename = parts[1] if len(parts) > 1 else "serial_log.csv"
            try:
                with open(filename, "w", newline="") as f:
                    f.write("timestamp,data_hex\n")
                    for line in raw_output.text.strip().split("\n"):
                        if line.strip():
                            f.write(f"{datetime.now().isoformat()},{line}\n")
                raw_output.text += f"Saved log to {filename}\n"
                decoded_output.text += f"Saved log to {filename}\n"
                raw_output.buffer.cursor_position = len(raw_output.text)
                decoded_output.buffer.cursor_position = len(decoded_output.text)
            except Exception as e:
                raw_output.text += f"Error saving log: {e}\n"
                decoded_output.text += f"Error saving log: {e}\n"

        elif parts[0] == "help":
            msg = (
                "Available commands:\n"
                " launch           - start launch\n"
                " enter-sim        - enter simulation mode\n"
                " send-sim         - send simulated pressure data\n"
                " pressure <value> - send pressure float\n"
                " save-log [file]  - save current raw output to CSV\n"
                " help             - show this message\n"
                " exit             - quit\n"
            )
            raw_output.text += msg + "\n"
            decoded_output.text += msg + "\n"

        elif parts[0] == "exit":
            raw_output.text += "Exiting application...\n"
            decoded_output.text += "Exiting application...\n"
            gs.close()
            event.app.exit()
        else:
            raw_output.text += f"Unknown command: {user_input}\n\n"
            decoded_output.text += f"Unknown command: {user_input}\n\n"

    # Reset input field
    input_field.text = ''
    input_field.buffer.cursor_position = len(input_field.text)

    # Scroll both outputs to bottom
    raw_output.buffer.cursor_position = len(raw_output.text)
    decoded_output.buffer.cursor_position = len(decoded_output.text)

layout = Layout(
    HSplit([
        ConditionalContainer(content=Frame(raw_output, title="Raw Hex Output"),
                             filter=Condition(lambda: show_raw)),
        ConditionalContainer(content=Frame(decoded_output, title="Decoded Info"),
                             filter=Condition(lambda: not show_raw)),
        instructions,
        input_field
    ])
)

modes = ["MODE_SIMULATION", "MODE_FLIGHT"]
states = ["LAUNCH_PAD", "ASCENT", "DESCENT", "PROBE_RELEASE", "LANDED"]

def decode_line(line: bytes) -> str:
    packet_count = line[1]
    mode = modes[line[2]]
    state = states[line[3]]
    try:
        altitude = struct.unpack('<f', line[4:8])[0]
        pressure = struct.unpack('<f', line[8:12])[0]
    except struct.error:
        altitude = 0.0
        pressure = 0.0
    decoded = (
        f"Packet Count: {packet_count} --------------------\n"
        f"Mode: {mode}\n"
        f"State: {state}\n"
        f"Altitude: {altitude:.2f} m\n"
        f"Pressure: {pressure:.2f} Pa\n"
    )
    return decoded

async def refresh():
    while True:
        line = gs.read_line()
        if line:
            # raw hex
            hex_line = ' '.join(f'{b:02X}' for b in line)
            raw_output.text += hex_line + "\n"
            raw_output.buffer.cursor_position = len(raw_output.text)

            # decoded info example: first 4 bytes as float pressure
            if len(line) >= 4:
                decoded_output.text += decode_line(line) + "\n\n"
                decoded_output.buffer.cursor_position = len(decoded_output.text)
        await asyncio.sleep(0.05)

# -------- Main --------
async def main():
    asyncio.create_task(refresh())
    app = Application(layout=layout, key_bindings=kb, full_screen=True)
    await app.run_async()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        gs.close()
