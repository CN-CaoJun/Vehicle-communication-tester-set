import can
from can.interface import Bus
import threading
import time
from collections import defaultdict

can.rc['interface'] = 'vector'
can.rc['bustype'] = 'vector'
can.rc['channel'] = '0'
can.rc['app_name'] = 'IMS_Diag_CLient'
 
can.rc['fd'] = False  
can.rc['bitrate'] = 500000
# can.rc['data_bitrate'] = 2000000

can.rc['sjw_abr'] = 16
can.rc['tseg1_abr'] = 63
can.rc['tseg2_abr'] = 16
can.rc['sam_abr'] = 1


class CANFrameController:
    def __init__(self, bus, can_id, initial_data, phase_change_count, intervals, switch_data=1):
        self.bus = bus
        self.can_id = can_id
        self.initial_data = initial_data
        self.phase_data = initial_data
        self.phase_change_count = phase_change_count
        self.intervals = intervals
        self.frame_count = 0
        self.running = False
        self.thread = None
        self.switch_data = switch_data  # New parameter to control data switching

    def _send_loop(self):
        while self.running:
            if self.switch_data:  # Check if data switching is enabled
                phase_index = 0 if self.frame_count < self.phase_change_count else 1
            else:
                phase_index = 0  # If data switching is disabled, use initial data
            msg = can.Message(
                arbitration_id=self.can_id,
                data=self.phase_data[phase_index],
                is_extended_id=False
            )
            self.bus.send(msg)
            self.frame_count += 1
            time.sleep(self.intervals[phase_index]/1000)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._send_loop)
            self.thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.thread.join()
            self.frame_count = 0

# Shell control interface
def shell_control():
    bus = Bus()
    
    controller_600 = CANFrameController(
        bus=bus,
        can_id=0x600,
        initial_data={
            0: [0x00]*8,
            1: [0x00]*8
        },
        phase_change_count=10,
        intervals=[20, 1000]
    )

    controller_391 = CANFrameController(
        bus=bus,
        can_id=0x391,
        initial_data={
            0: [0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00],
            1: [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]
        },
        phase_change_count=10,
        intervals=[20, 20]
    )
    
    controller_2EA = CANFrameController(
        bus=bus,
        can_id=0x2EA,
        initial_data={
            0: [0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            1: [0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        },
        phase_change_count=10,
        intervals=[20, 20]
    )
    
    controller_600_arm = CANFrameController(
        bus=bus,
        can_id=0x600,
        initial_data={
            0: [0x00]*8,
            1: [0x00]*8
        },
        phase_change_count=10,
        intervals=[1000, 1000]
    )

    controller_391_arm = CANFrameController(
        bus=bus,
        can_id=0x391,
        initial_data={
            0: [0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x00, 0x00],
            1: [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]
        },
        phase_change_count=10,
        intervals=[20, 20]
    )

    while True:
        cmd = input("Enter command (1= Normal / 2= Polling /3=exit): ").strip().lower()
        if cmd == '1':
            print("Started CAN NM transmission")
            controller_600.start()
            controller_391.start()
            controller_2EA.start()
        elif cmd == '2':
            controller_600.stop()
            controller_2EA.stop()
            controller_391.stop()
            print("Send ARM Msgs to enter polling mode")
            controller_2EA.start()
            controller_600_arm.start()
            controller_391_arm.start()
            def stop_arm_controllers():
                controller_600_arm.stop()
                controller_391_arm.stop()
                controller_2EA.stop()
                # bus.shutdown()
                print("Automatically stopped ARM messages after 5 seconds")
            threading.Timer(5.0, stop_arm_controllers).start()
            
        elif cmd == '3':
            controller_600.stop()
            controller_391.stop()
            controller_391_arm.stop()
            controller_600_arm.stop()
            controller_391_arm.stop()
            bus.shutdown()
            break

if __name__ == "__main__":
    shell_control()