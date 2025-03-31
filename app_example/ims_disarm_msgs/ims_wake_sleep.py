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



class MessageController:
    def __init__(self, can_bus, arbitration_id, initial_data, changed_data, 
                 initial_interval, changed_interval, initial_count,
                 temp_data=None, temp_duration=0):
        self.bus = can_bus
        self.arb_id = arbitration_id
        self.initial_data = initial_data
        self.changed_data = changed_data
        self.initial_interval = initial_interval
        self.changed_interval = changed_interval
        self.initial_count = initial_count
        self.temp_data = temp_data
        self.temp_duration = temp_duration
        self.temp_counter = 0
        self.counter = 0
        self.running = True
        self.in_temp_mode = False

    def run(self):
        while self.running:
            if self.in_temp_mode:
                data = self.temp_data
                interval = self.changed_interval
                self.temp_counter += 1
                if self.temp_counter >= self.temp_duration:
                    self.in_temp_mode = False
            else:
                data = self.initial_data if self.counter < self.initial_count else self.changed_data
                interval = self.initial_interval if self.counter < self.initial_count else self.changed_interval

            msg = can.Message(
                arbitration_id=self.arb_id,
                data=data,
                is_extended_id=False
            )
            self.bus.send(msg)
            self.counter += 1
            time.sleep(interval/1000)

# CAN bus initialization
bus = Bus()

# Create controller instances
controller_600 = MessageController(
    bus,
    0x600,
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Initial data
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Data remains same
    20,            # Initial interval
    1000,          # Changed interval
    10             # Initial frame count
)

controller_391 = MessageController(
    bus,
    0x391,
    [0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00],  # Initial data
    [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],  # Changed data
    20,            # Constant interval
    20,            # Constant interval
    10,            # Initial frame count
    temp_data=[0x02, 0x00],  # Temporary data for command 2
    temp_duration=10         # 10 frames duration
)

# Start transmission when input is '1'
command = input('Enter 1 to start normal transmission, 2 for special mode: ')

if command == '1' or command == '2':
    thread_600 = threading.Thread(target=controller_600.run, daemon=True)
    thread_391 = threading.Thread(target=controller_391.run, daemon=True)
    
    thread_600.start()
    thread_391.start()
    
    if command == '2':
        # Activate temporary mode for 0x391 after 1 second
        time.sleep(1)
        controller_391.in_temp_mode = True
        
        # Schedule stop after 10 seconds
        def stop_transmission():
            time.sleep(10)
            controller_600.running = False
            controller_391.running = False
        threading.Thread(target=stop_transmission, daemon=True).start()
    
    try:
        while controller_600.running or controller_391.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        controller_600.running = False
        controller_391.running = False



# Modified input handling and control logic
current_command = None
active_controllers = []

def monitor_input():
    global current_command
    while True:
        new_cmd = input('\nEnter mode (1: normal, 2: special, q: quit): ')
        if new_cmd in ('1', '2', 'q'):
            current_command = new_cmd
        if new_cmd == 'q':
            break

input_thread = threading.Thread(target=monitor_input, daemon=True)
input_thread.start()

try:
    while True:
        if current_command in ('1', '2'):
            # Stop existing controllers
            for ctrl in active_controllers:
                ctrl.running = False
            
            # Reinitialize controllers with fresh state
            controller_600 = MessageController(
                bus, 0x600,
                [0x00]*8, [0x00]*8,
                20, 1000, 10
            )
            
            controller_391 = MessageController(
                bus, 0x391,
                [0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00],
                [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00],
                20, 20, 10,
                temp_data=[0x02, 0x00],
                temp_duration=10
            )
            
            # Start new threads
            active_controllers = [controller_600, controller_391]
            threads = [
                threading.Thread(target=ctrl.run, daemon=True) 
                for ctrl in active_controllers
            ]
            
            for t in threads:
                t.start()
            
            if current_command == '2':
                time.sleep(1)
                controller_391.in_temp_mode = True
                
            # Clear command to prevent restart loop
            current_command = None
            
        time.sleep(0.5)
        
except KeyboardInterrupt:
    for ctrl in active_controllers:
        ctrl.running = False


