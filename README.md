# CatSat: Ground Station Documentation

<p align="left">
	<!--Latest Release Version-->
	<img src="https://img.shields.io/github/v/release/CanSat-YDSP/Ground-Station?style=default&logo=github&logoColor=white&color=0080ff" alt="latest-release">
	<img src="https://img.shields.io/github/last-commit/CanSat-YDSP/Ground-Station?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/CanSat-YDSP/Ground-Station?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/CanSat-YDSP/Ground-Station?style=default&color=0080ff" alt="repo-languages">
	<img src="https://img.shields.io/github/repo-size/CanSat-YDSP/Ground-Station?style=default&color=0080ff" alt="repo-size">
</p>


This ground station is designed as part of a larger CanSat project. It is the communication link between the CanSat and the ground station. It is responsible for receiving, processing, and displaying telemetry data transmitted from the CanSat during its mission and for sending commands back to the CanSat as needed.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

The things you need before using the ground station.

#### Hardware
* 1x XBEE S2C Zigbee RF Module
* 1x XBEE Explorer USB Mini Adapter Module
* 1x CanSat

#### Software
* A functioning Python 3.x environment
* Required Python libraries:
  * pyserial
  * prompt_toolkit


### Installation

To install the necessary libraries and then run the ground station, run the following commands:

```
$ pip install pyserial prompt_toolkit
$ python3 ground_station.py
```

## Usage

An example of entering commands to simulate a CanSat mission with parachute deployment at 75% altitude:

```
$ send-bin 75percent.bin
$ startup-ack
$ enter-sim
$ launch
$ send-sim
```

## List of Commands
Here is a list of available commands for the ground station:
# Ground Station Command Reference

| Command | Arguments | Description |
|--------|-----------|-------------|
| `launch` | – | Sends a `LAUNCH_OK` event to the on-board computer, causing the CanSat to exit the `LAUNCH_PAD` state and enter the `ASCENT` state. |
| `pressure` | `<value>` | Sends a pressure value to the CanSat. Ignored when the CanSat is in `MODE_FLIGHT`. |
| `enter-sim` | – | Switches the CanSat from `MODE_FLIGHT` to `MODE_SIMULATION`, allowing pressure readings to be provided by the ground station instead of the BMP390 sensor. |
| `send-sim` | – | Reads `cansat_pressure_profile.csv` from the current directory and sends a `pressure` command for each line in the file. |
| `calibrate-altitude` | – | Records the current altitude and uses it as the reference for all future altitude calculations. |
| `save-log` | `[file]` | Saves all raw console output to a file. Defaults to `serial_log.csv` if no file is specified. |
| `save-altitude-log` | `[file]` | Saves all altitude output to a file. Defaults to `altitude_log.csv` if no file is specified. |
| `servo` | – | Rotates the CanSat’s nose cone servo. Mainly used for testing purposes. |
| `reset` | – | Enters the bootloader, allowing the CanSat to reflash its software. |
| `send-bin` | `[file]` | Packetises and sends binary data to the CanSat for reprogramming. Defaults to `binary.bin` if no file is specified. |
| `AT` | `<args>` | Changes the configuration of the CanSat’s RF module. |
| `startup-ack` | – | Acknowledges successful reception of telemetry, confirming communication with the CanSat. |
| `help` | – | Displays all available commands and their purposes. |
| `exit` | – | Exits the ground station. |

## Available Scripts

In the project directory, you can run:

1. `python3 ground_station.py`

    Runs the ground station application. Make sure the XBEE module is connected to your computer before running this command.

2. `python3 tools/data_simulator.py`

    Runs a data simulator that generates pressure data for simulating CanSat missions.
3. `python3 tools/binary_generator.py [file]`

    Generates a binary file for reprogramming the CanSat. In general, you would not need to run this script unless for testing purposes. Binaries should be generated using avr-gcc, followed by avr-objcopy to create the binary file.

## Available Binary Files

| File Name | Description |
|--------|-----------|
| 50percent.bin | Simulates parachute deployment at 50% altitude. |
| 75percent.bin | Simulates parachute deployment at 75% altitude. |
| binary.bin   | A binary file containing hex values from 0x0 to 0xFF followed by 0x0 to 0xFD. |
| blinky.bin   | Makes the CanSat's LED blink. |
| blinkyfast.bin | Makes the CanSat's LED blink faster. |
| servo.bin   | Makes the servo engage the nose cone. |

## Additional Documentation

Below are links to additional documentation related to the CanSat project:

For more details on software, [click here](https://github.com/CanSat-YDSP/Documentation/blob/main/software_details.pdf).

For an overview of the entire project and hardware, [click here](https://github.com/CanSat-YDSP/Documentation/blob/main/report.pdf).

## Contributing
<p align="left">
   <a href="https://github.com{/atlas-sat/obc/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=CanSat-YDSP/Ground-Station">
   </a>
</p>
</details>

## License

This project is not protected under any license. You are free to use, modify, and distribute the software as you see fit.