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
    def __init__(self, bus, can_id, initial_data, phase_change_count, intervals):
        self.bus = bus
        self.can_id = can_id
        self.initial_data = initial_data
        self.phase_data = initial_data
        self.phase_change_count = phase_change_count
        self.intervals = intervals
        self.frame_count = 0
        self.running = False
        self.thread = None

    def _send_loop(self):
        while self.running:
            phase_index = 0 if self.frame_count < self.phase_change_count else 1
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

    while True:
        cmd = input("Enter command (start/stop/exit): ").strip().lower()
        if cmd == 'start':
            controller_600.start()
            controller_391.start()
            print("Started CAN transmission")
        elif cmd == 'stop':
            controller_600.stop()
            controller_391.stop()
            print("Stopped CAN transmission")
        elif cmd == 'exit':
            controller_600.stop()
            controller_391.stop()
            bus.shutdown()
            break

if __name__ == "__main__":
    shell_control()

