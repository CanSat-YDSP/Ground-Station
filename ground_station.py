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
        # Attempt to read a framed packet of the form:
        # 0xFF | length (1 byte) | payload (length-1 bytes) | checksum (1 byte)
        # Use explicit reads instead of readline() to avoid double-reading parts of the frame.
        if self.ser.in_waiting > 0:
            # read header byte
            header = self.ser.read(1)
            if not header:
                return None
            if header != b'\xFF':
                return None
            
            # read length byte
            length_byte = self.ser.read(1)
            if not length_byte:
                return None
            length = length_byte[0]

            # length must include payload + checksum (so must be at least 1 for checksum)
            if length < 1:
                return None

            # read the advertised number of bytes (payload + checksum)
            data_with_checksum = self.ser.read(length)

            # if we didn't get enough bytes, abandon this frame
            if len(data_with_checksum) != length:
                return None

            payload = data_with_checksum[:-1]
            recv_checksum = data_with_checksum[-1]

            if self.calculate_xor_checksum(payload) == recv_checksum:
                return payload

            # # checksum mismatch
            # raw_output.text += "Checksum mismatch\n"
            # decoded_output.text += "Checksum mismatch\n"

            # # compare checksums
            # raw_output.text += f"Calculated checksum: {self.calculate_xor_checksum(payload):02X}, Received checksum: {recv_checksum:02X}\n"
            # decoded_output.text += f"Calculated checksum: {self.calculate_xor_checksum(payload):02X}, Received checksum: {recv_checksum:02X}\n"

        return None

    def write_line(self, data: bytes):
        # Write a framed packet to the serial port, with xFF header, length, data then checksum
        self.ser.write(b'\xFF')
        no_bytes = len(data)
        raw_output.text += f"Writing {no_bytes} bytes\n"
        decoded_output.text += f"Writing {no_bytes} bytes\n"
        self.ser.write(bytes([no_bytes]))
        self.ser.write(data)
        self.ser.write(bytes([self.calculate_xor_checksum(data)]))

    def calculate_xor_checksum(self, data: bytes) -> int:
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum

    def close(self):
        self.ser.close()

gs = SerialReader('COM5', 9600)

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

        elif parts[0] == "calibrate-altitude":
            gs.write_line(b'\x04')
            raw_output.text += "Sent calibrate altitude command\n"
            decoded_output.text += "Sent calibrate altitude command\n"
        
        elif parts[0] == "reset":
            gs.write_line(b'\x00')
            raw_output.text += "Sent reset command\n"
            decoded_output.text += "Sent reset command\n"

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
                            # timestamp is packet count, convert hex to dec
                            timestamp = line.split()[0]
                            f.write(f"{int(timestamp, 16)},{line}\n")
                raw_output.text += f"Saved log to {filename}\n"
                decoded_output.text += f"Saved log to {filename}\n"
                raw_output.buffer.cursor_position = len(raw_output.text)
                decoded_output.buffer.cursor_position = len(decoded_output.text)
            except Exception as e:
                raw_output.text += f"Error saving log: {e}\n"
                decoded_output.text += f"Error saving log: {e}\n"

        elif parts[0] == "save-altitude-log":
            filename = parts[1] if len(parts) > 1 else "altitude_log.csv"
            try:
                with open(filename, "w", newline="") as f:
                    f.write("timestamp,altitude_m\n")
                    for entry in decoded_output.text.strip().split("\n\n"):
                        if "Altitude:" in entry:
                            lines = entry.split("\n")
                            # timestamp is the packet count (take first token after the colon)
                            timestamp = lines[0].split(":", 1)[1].strip().split()[0]
                            for line in lines:
                                if line.startswith("Altitude:"):
                                    altitude_str = line.split(":")[1].strip().split()[0]
                                    f.write(f"{timestamp},{altitude_str}\n")
                raw_output.text += f"Saved altitude log to {filename}\n"
                decoded_output.text += f"Saved altitude log to {filename}\n"
                raw_output.buffer.cursor_position = len(raw_output.text)
                decoded_output.buffer.cursor_position = len(decoded_output.text)
            except Exception as e:
                raw_output.text += f"Error saving altitude log: {e}\n"
                decoded_output.text += f"Error saving altitude log: {e}\n"
        
        elif parts[0] == "send-bin":
            file_to_send = parts[1] if len(parts) > 1 else "binary.bin"
            asyncio.create_task(send_binary_file(file_to_send))
            raw_output.text += f"Started sending binary file {file_to_send}...\n"
            decoded_output.text += f"Started sending binary file {file_to_send}...\n"
            raw_output.buffer.cursor_position = len(raw_output.text)
            decoded_output.buffer.cursor_position = len(decoded_output.text)

        elif parts[0] == "help":
            msg = (
                "Available commands:\n"
                "launch - Send launch command\n" \
                "pressure <value> - Set pressure value\n" \
                "enter-sim - Enter simulation mode\n" \
                "calibrate-altitude - Calibrate altitude\n" \
                "reset - Reset the system\n" \
                "send-sim - Start sending simulated pressure data\n" \
                "save-log [filename] - Save raw hex log to CSV\n" \
                "save-altitude-log [filename] - Save altitude log to CSV\n" \
                "send-bin [filename] - Send binary file to CanSat\n" \
                "servo - Send servo command\n" \
                "AT <args> - Send AT command\n" \
                "startup-ack - Send startup acknowledgment\n" \
                "exit - Exit the application\n"
            )
            raw_output.text += msg + "\n"
            decoded_output.text += msg + "\n"

        elif parts[0] == "servo":
            gs.write_line(b'\x08')
            raw_output.text += "Sent servo command\n"
            decoded_output.text += "Sent servo command\n"

        elif parts[0] == "AT":
            at_args = ' '.join(parts[1:]).strip()  # remove extra spaces
            if at_args:
                at_payload = ('AT ' + at_args).encode('ascii')  # force ASCII
            else:
                at_payload = b'AT'
            packet = b'\x09' + at_payload
            gs.write_line(packet)

            # Logs
            readable = at_payload.decode('ascii')
            raw_output.text += f"Sent AT command: {readable}\n"
            decoded_output.text += f"Sent AT command: {readable}\n"

        elif parts[0] == "startup-ack":
            gs.write_line(b'\x0A')
            raw_output.text += "Sent startup acknowledgment\n"
            decoded_output.text += "Sent startup acknowledgment\n"

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
upload_statuses = ["NONE", "READY", "UPLOADING", "SUCCESS", "FAILURE"]
command_codes = {
    0x00: "RESET",
    0x01: "LAUNCH",
    0x02: "SET_PRESSURE",
    0x03: "ENTER_SIMULATION",
    0x04: "CALIBRATE_ALTITUDE",
    0x05: "BINARY_DATA_START",
    0x06: "BINARY_DATA_PACKET",
    0x07: "BINARY_DATA_END",
    0x08: "SERVO",
    0x09: "AT",
    0x0A: "STARTUP_ACK"
}

def decode_line(line: bytes) -> str:
    packet_count = line[0]
    mode = modes[line[1]]
    state = states[line[2]]
    command_code = line[51]
    command = command_codes.get(command_code, "UNKNOWN_COMMAND")
    app_checksum = line[52]
    upload_status = line[53]
    try:
        altitude = struct.unpack('<f', line[3:7])[0]
        pressure = struct.unpack('<f', line[7:11])[0]
        temperature = struct.unpack('<f', line[11:15])[0]
        # accel x y and z
        accel_x = struct.unpack('<f', line[15:19])[0]
        accel_y = struct.unpack('<f', line[19:23])[0]
        accel_z = struct.unpack('<f', line[23:27])[0]
        # mag x y and z
        mag_x = struct.unpack('<f', line[27:31])[0]
        mag_y = struct.unpack('<f', line[31:35])[0]
        mag_z = struct.unpack('<f', line[35:39])[0]
        # gyro x y and z
        gyro_x = struct.unpack('<f', line[39:43])[0]
        gyro_y = struct.unpack('<f', line[43:47])[0]
        gyro_z = struct.unpack('<f', line[47:51])[0]

    except struct.error:
        altitude = 0.0
        pressure = 0.0
        temperature = 0.0
        accel_x = 0.0
        accel_y = 0.0
        accel_z = 0.0
        mag_x = 0.0
        mag_y = 0.0
        mag_z = 0.0
        gyro_x = 0.0
        gyro_y = 0.0
        gyro_z = 0.0
    decoded = (
        f"Packet Count: {packet_count} --------------------\n"
        f"Mode: {mode}\n"
        f"State: {state}\n"
        f"Altitude: {altitude:.2f} m\n"
        f"Pressure: {pressure:.2f} Pa\n"
        f"Temperature: {temperature:.2f} °C"
        f"\nAccelerometer: X={accel_x:.2f} m/s², Y={accel_y:.2f} m/s², Z={accel_z:.2f} m/s²"
        f"\nMagnetometer: X={mag_x:.2f} µT, Y={mag_y:.2f} µT, Z={mag_z:.2f} µT"
        f"\nGyroscope: X={gyro_x:.2f} °/s, Y={gyro_y:.2f} °/s, Z={gyro_z:.2f} °/s"
        f"\nCommand Echo: {command_code} ({command})"
        f"\nApp Checksum: {app_checksum}"
        f"\nUpload Status: {upload_statuses[upload_status]}"
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

async def send_binary_file(filename="binary.bin"):
    try:
        # Read entire binary file
        with open(filename, "rb") as f:
            data = f.read()
        
        if not data:
            raw_output.text += f"File {filename} is empty.\n"
            decoded_output.text += f"File {filename} is empty.\n"
            return

        # Calculate total checksum
        total_checksum = gs.calculate_xor_checksum(data)

        # Split into 64-byte chunks
        chunk_size = 64
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        # Send each chunk
        for i, chunk in enumerate(chunks):
            # first packet is command 0x05, followed by 0x06 for the rest, and 0x07 for the last

            packet_command = b'\x06'  # default command for all but last
            # If it's the last chunk, append checksum and change command
            if i == len(chunks) - 1:
                packet_command = b'\x07'
                chunk = chunk + bytes([total_checksum])
            if i == 0:
                packet_command = b'\x05'
            
            gs.write_line(packet_command + chunk)
            raw_output.text += f"Sent packet {i + 1}/{len(chunks)} ({len(chunk)} bytes)\n"
            decoded_output.text += f"Sent packet {i + 1}/{len(chunks)} ({len(chunk)} bytes)\n"
            raw_output.buffer.cursor_position = len(raw_output.text)
            decoded_output.buffer.cursor_position = len(decoded_output.text)

            await asyncio.sleep(0.2)

    except FileNotFoundError:
        raw_output.text += f"Error: {filename} not found.\n"
        decoded_output.text += f"Error: {filename} not found.\n"
    except Exception as e:
        raw_output.text += f"Error sending binary file: {e}\n"
        decoded_output.text += f"Error sending binary file: {e}\n"

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
