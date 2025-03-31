#!/usr/bin/env python


# sys.path.insert(0, os.path.abspath("python-can"))
# sys.path.insert(0, os.path.abspath("python-can-isotp"))

"""
This example shows how sending a single message works.
"""

import can
from can.interface import Bus
import threading
import time
from collections import defaultdict

# 配置日志（可选，用于调试）
# logging.basicConfig(level=logging.DEBUG)


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

# CAN报文发送任务管理类
class CANTaskManager:
    def __init__(self):
        self.bus = Bus()
        self.tasks = defaultdict(dict)
        self.lock = threading.Lock()

    def periodic_send(self, can_id, interval, count=None):
        def wrapper():
            sent_count = 0
            task['pattern_count'] = 0  # Counter for the second pattern in logic 2
            while True:
                with self.lock:
                    task = self.tasks[can_id]
                    if not task['active']:
                        break

                try:
                    data = [0] * 8  # Default all zeros for 0x600
                    if can_id == 0x391:
                        task_mode = task.get('mode', 1)
                        
                        if task_mode == 1:  # Logic 1
                            if sent_count < 10:
                                data = [0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00]
                            else:
                                data = [0x00, 0x00, 0x00, 0x00, 0x02, 0x01, 0x00, 0x00]
                        
                        elif task_mode == 2:  # Logic 2
                            if sent_count < 10:
                                data = [0x00, 0x00, 0x00, 0x00, 0x02, 0x04, 0x00, 0x00]
                            elif task['pattern_count'] < 10:
                                data = [0x00, 0x00, 0x00, 0x00, 0x02, 0x02, 0x00, 0x00]
                                task['pattern_count'] += 1
                            else:
                                data = [0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00]

                    msg = can.Message(
                        arbitration_id=can_id,
                        data=data,
                        is_extended_id=False
                    )
                    self.bus.send(msg)
                    # print(f"[Success] Sent CAN message: {msg}")

                    sent_count += 1
                    if can_id == 0x600 and count and sent_count >= count:
                        with self.lock:
                            self.tasks[can_id]['interval'] = 1000
                            print(f"Switched CAN ID {hex(can_id)} to 1000ms interval")
                
                except Exception as e:
                    print(f"[Error] Failed to send message: {e}")
                
                time.sleep(task['interval'] / 1000)

        return wrapper

    def add_task(self, can_id, interval, count=None, mode=None):
        with self.lock:
            if can_id in self.tasks:
                self.tasks[can_id]['active'] = True
                self.tasks[can_id]['interval'] = interval
                self.tasks[can_id]['mode'] = mode
            else:
                self.tasks[can_id] = {
                    'active': True,
                    'interval': interval,
                    'mode': mode,
                    'thread': threading.Thread(target=self.periodic_send(can_id, interval, count))
                }
                self.tasks[can_id]['thread'].start()

    def stop_task(self, can_id):
        with self.lock:
            if can_id in self.tasks:
                self.tasks[can_id]['active'] = False
                self.tasks[can_id]['thread'].join()
                del self.tasks[can_id]


def input_handler(task_manager):
    while True:
        cmd = input("\nEnter command (1-执行逻辑1, 2-执行逻辑2, q-退出): ")
        
        if cmd == '1':
            # Wake-up mode: Send CAN messages to wake up the ECU
            # Logic 1: Send messages with IDs 0x600 and 0x391
            task_manager.add_task(0x600, 20, count=10)  # 0x600: First 10 frames at 20ms interval, then switch to 1000ms
            task_manager.add_task(0x391, 20, mode=1)  # 0x391: First 10 frames [00,02,00,00], then [00,01,00,00], maintain 20ms interval
            print("Started logic 1: Sending 10 frames each for 0x600 and 0x391 with 20ms interval. 0x600 will switch to 1000ms interval after completion.")
        elif cmd == '2':
            # Logic 2: Build upon Logic 1 with additional timing and data pattern changes
            task_manager.add_task(0x600, 20, count=10)  # 0x600: First 10 frames at 20ms interval, then switch to 1000ms
            task_manager.add_task(0x391, 20, mode=2)  # Start with logic 2 pattern transmission
            print("Started logic 2: Initial transmission started...")
            
            def delayed_actions():
                # Wait 3 seconds before changing 0x391 data pattern
                time.sleep(3)
                print("Changing 0x391 data pattern...")
                with task_manager.lock:
                    if 0x391 in task_manager.tasks:
                        task_manager.stop_task(0x391)
                        task_manager.add_task(0x391, 20, mode=2)  # Restart with new pattern for logic 2
                
                # Wait another 3 seconds before stopping 0x600
                time.sleep(3)
                print("Stopping 0x600 transmission...")
                task_manager.stop_task(0x600)
            
            timing_thread = threading.Thread(target=delayed_actions)
            timing_thread.daemon = True
            timing_thread.start()
            
        elif cmd.lower() == 'q':
            for can_id in list(task_manager.tasks.keys()):
                task_manager.stop_task(can_id)
            task_manager.bus.shutdown()
            print("Exiting...")
            break

if __name__ == "__main__":
    task_manager = CANTaskManager()
    input_thread = threading.Thread(target=input_handler, args=(task_manager,))
    input_thread.daemon = True
    input_thread.start()
    input_thread.join()