
# Gateway Environment Testing Scenarios and Methods

This repository focuses on implementing and testing various communication scenarios in gateway-like environments. These scenarios are designed to simulate and evaluate real-world automotive communication systems, leveraging open-source tools and libraries.

## Current Scenarios

### 1. DoCAN Implementation Using Python CAN

The first scenario involves the implementation of Diagnostic Communication over CAN (DoCAN) based on the open-source **`python-can`** library. This setup serves as a foundational approach to simulate diagnostic communication, enabling features like message transmission, reception, and error handling in a gateway environment.

Details about this implementation can be found in the **[**`python-can-tester`**](**./python-can-tester/README.md**)** folder.

### 2. ISO-TP Over CAN Implementation with GUI

The second scenario involves the implementation of ISO-TP (ISO 15765-2) over CAN communication with a graphical user interface (GUI). This setup allows for more user-friendly interaction with the communication system, making it easier to test and debug complex messages.

Details about this implementation can be found in the **[**`isotp-can-tester-gui`**](**./isotp-can-tester-gui/README.md**)** folder.

---

## Project Structure

-**`python-can-tester`**: Contains the implementation details and examples for testing DoCAN communication scenarios using **`python-can`**. Refer to the **[**README**](**./python-can-tester/README.md**)** for a detailed guide.
-**`isotp-can-tester-gui`**: Contains the implementation details and examples for testing ISO-TP over CAN communication scenarios with a GUI. Refer to the **[**README**](**./isotp-can-tester-gui/README.md**)** for a detailed guide.

---
## Future Plans
### 1. Develop a GUI Program for CAN Network Simulation Node on Linux
-**`TODO`**: Develop a GUI program for CAN network simulation node on Linux. This program will allow users to create and configure virtual CAN network interfaces, enabling the simulation of real-world CAN communication scenarios.This part of work would be done at this folder `isotp-can-tester-gui`

### 2. Implement an ETH-to-CAN Simulated Gateway Node on Linux
-**`TODO`**: Develop an ETH-to-CAN simulated gateway node on Linux. This node will allow users to simulate the communication between CAN and Ethernet networks, enabling the testing of CAN-based communication protocols over Ethernet networks.