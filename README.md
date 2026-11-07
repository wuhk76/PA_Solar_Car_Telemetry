
 # PA_Solar_Car_Telemetry

 **Solar Car Telemetry and Motor Controller Monitoring System**

 **Status:** Work in Progress (WIP)
 **Platform:** Python 3 / Raspberry Pi / Linux
 **Communication:** Bluetooth Low Energy (BLE)
 **Motor Controller:** Fardriver ND Series

 ## Overview

 PA_Solar_Car_Telemetry is a Python-based telemetry and diagnostic system
 being developed for a custom solar-powered vehicle.

 The project aims to provide a modular interface for collecting,
 interpreting, and displaying real-time vehicle data, with an initial
 focus on communication with a Fardriver motor controller over
 Bluetooth Low Energy (BLE).

 The application uses a Qt-based graphical interface to display motor
 controller information, including operating states, gear selections,
 warnings, and other available diagnostic data.

 The long-term goal is to integrate motor controller diagnostics with
 additional vehicle telemetry, including battery monitoring, power
 consumption, and other onboard sensor systems.

 ## Features

 ### Current Development Focus

 - Bluetooth Low Energy device discovery and connection using Bleak.
 - Modular communication interface for BLE devices.
 - Fardriver motor controller protocol handling.
 - Qt-based graphical telemetry dashboard.
 - User-configurable motor controller connection information.
 - Diagnostic and communication debugging interface.
 - Customizable telemetry widgets.
 - Support for dynamically resizing dashboard components.

 ### Planned Features

 - Real-time motor speed (RPM) monitoring.
 - Battery voltage and current monitoring.
 - Motor and controller temperature monitoring.
 - Gear and operating mode indicators.
 - Motor controller warning and fault reporting.
 - Customizable drag-and-drop telemetry dashboard.
 - Data logging and historical telemetry visualization.
 - Integration with Raspberry Pi vehicle telemetry systems.
 - Additional CAN bus and sensor interfaces.
 - Potential remote telemetry transmission.

 Feature availability depends on the supported Fardriver protocol
 commands and the implementation status of each module.

 ## Project Structure

 ```text
 PA_Solar_Car_Telemetry/
 |
 |-- main.py
 |-- fd.py
 |-- bledev.py
 |-- README.md
 `-- requirements.txt
 ```

 ### main.py — Application and GUI

 The main entry point for the telemetry application.

 Responsibilities include:

 - Starting the Qt application.
 - Scanning for the configured Fardriver controller.
 - Establishing a BLE connection.
 - Initializing the motor controller interface.
 - Displaying telemetry information.
 - Managing dashboard widgets and their layouts.
 - Displaying connection status and debugging output.

 The intended graphical dashboard supports configurable telemetry
 widgets that can be arranged to display selected motor controller
 parameters.

 ### fd.py — Fardriver Protocol Interface

 Implements the Fardriver-specific communication and telemetry
 processing layer.

 This module is intended to operate independently of the underlying
 Bluetooth implementation.

 Responsibilities include:

 - Formatting motor controller requests.
 - Processing incoming controller packets.
 - Decoding motor controller telemetry.
 - Interpreting fault and warning information.
 - Extracting controller operating states.
 - Providing a simplified Python interface to motor controller data.

 The Fd class is designed to use an external communication object
 rather than directly managing BLE hardware.

 This separation allows the Fardriver protocol implementation to be
 reused with compatible transport interfaces.

 ### bledev.py — Bluetooth Communication Layer

 Provides a reusable Bluetooth Low Energy interface built on the
 Bleak Python library.

 Responsibilities include:

 - Connecting to BLE devices.
 - Managing GATT characteristics.
 - Sending data to a BLE device.
 - Receiving data through BLE notifications.
 - Handling connection and disconnection events.
 - Providing a general-purpose communication interface.

 The Bledev class is intended to remain independent of the Fardriver
 protocol, allowing it to be reused with other BLE devices.

 ## Software Architecture

 ```text
              PA_Solar_Car_Telemetry
                       |
                    main.py
                 Qt Application
                       |
                       v
                     fd.py
              Fardriver Protocol
                       |
                       v
                   bledev.py
            Bluetooth Communication
                       |
                       v
                  Bleak Library
                       |
                       v
             Fardriver Motor Controller
 ```

 The architecture separates the user interface, motor controller
 protocol, and physical communication layer.

 This modular design is intended to improve maintainability and allow
 future communication interfaces to be introduced without requiring
 substantial changes to the Fardriver protocol implementation.

 ## Installation

 ### Requirements

 - Python 3
 - Linux, Windows, or another Bleak-compatible operating system
 - Bluetooth Low Energy adapter
 - Fardriver motor controller with compatible Bluetooth support

 ### Python Dependencies

 The application currently targets the following libraries:

 ```bash
 pip install bleak PySide6
 ```

 Additional dependencies may be introduced as development continues.

 ### Running the Application

 Clone the repository:

 ```bash
 git clone https:github.com/<organization>/PA_Solar_Car_Telemetry.git
 cd PA_Solar_Car_Telemetry
 ```

 Start the application:

 ```bash
 python3 main.py
 ```

 The application is intended to discover and connect to the configured
 motor controller before displaying available telemetry.

 ## Bluetooth Configuration

 The current development setup uses a Fardriver Bluetooth device
 advertised under a name similar to:

 ```text
 YuanQuFOC298
 ```

 The BLE communication layer requires the appropriate GATT
 characteristics for transmitting and receiving data.

 Depending on the device firmware, the Bluetooth service and
 characteristic UUIDs may need to be configured manually.

 Automatic device discovery and improved connection configuration
 are under development.

 ## Telemetry Dashboard

 The planned dashboard provides a configurable monitoring environment
 with individual widgets representing specific vehicle parameters.

 Example widgets include:

 | Widget | Description |
 |---|---|
 | Motor RPM | Motor rotational speed |
 | Battery Voltage | Controller-reported battery voltage |
 | Battery Current | Controller-reported battery current |
 | Controller Temperature | Internal controller temperature |
 | Motor Temperature | Motor temperature, when available |
 | Gear Indicator | Selected gear |
 | Operating Mode | Current controller mode |
 | Fault Monitor | Controller warnings and faults |
 | Connection Status | BLE connection information |

 Widgets are intended to be repositionable and resizable, with text
 scaling according to the dimensions of each widget.

 A compact debugging panel is planned for displaying communication
 messages and diagnostic information.

 ## Future Development

 The telemetry software is intended to become part of a larger
 Raspberry Pi-based vehicle monitoring system.

 Future development may include integration with:

 - STM32-based vehicle control electronics.
 - Battery management systems (BMS).
 - CAN bus telemetry.
 - GPS positioning.
 - Solar array and MPPT data.
 - Local telemetry recording.
 - Remote vehicle monitoring.

 The software architecture is intended to allow additional devices
 and protocols to be incorporated as independent modules.

 ## Safety Notice

 This project is experimental software intended for telemetry,
 diagnostics, and research.

 It should not be relied upon for safety-critical vehicle functions,
 including emergency shutdown, primary braking, or traction motor
 protection.

 Vehicle safety functions should remain under dedicated,
 appropriately designed hardware and control systems.

 Controller configuration or command functionality should be tested
 under controlled conditions before use on an operating vehicle.

 ## Development Status

 This project is currently under active development.

 The Bluetooth transport, Fardriver protocol interface, and Qt
 application are being developed and tested. Not all planned
 telemetry parameters or dashboard features have been verified.

 Documentation, software interfaces, and feature availability may
 change as development progresses.

 ## License

 This project is licensed under the MIT License.
 See the LICENSE file for the full license text.
