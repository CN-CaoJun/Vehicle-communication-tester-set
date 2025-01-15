import can
import isotp
import time
import random
from can.interface import Bus
import logging
from config import Config
import sys
import binascii
import json

can.rc['interface'] = 'vector'
can.rc['bustype'] = 'vector'
can.rc['channel'] = '0'
can.rc['app_name'] = 'Python_ISOTP_Server'
 
can.rc['fd'] = True  
can.rc['bitrate'] = 500000
can.rc['data_bitrate'] = 2000000

can.rc['tseg1_abr'] = 63
can.rc['tseg2_abr'] = 16
can.rc['sjw_abr'] = 16

can.rc['sam_abr'] = 1
can.rc['tseg1_dbr'] = 13
can.rc['tseg2_dbr'] = 6
can.rc['sjw_dbr'] = 6

try:
    bus = Bus()
    notifier = can.Notifier(bus, [])
    print("Vector bus initialized successfully.\r\n")
except Exception as e:
    print(f"Failed to initialize Vector bus: {e}")
    exit(1)

#VCU_02
msg = can.Message(arbitration_id = 0x99, is_extended_id=False, data=[0xFE, 0x3F, 0xFE, 0x7F, 0xFE, 0xFF, 0x38, 0x00], is_fd=True)

total_messages = 6000

try:
    sent_count = 0
    while sent_count < total_messages:
        bus.send(msg)
        # print(f"Message sent on CAN ID {msg.arbitration_id}: {binascii.hexlify(msg.data)}")
        sent_count += 1
        time.sleep(0.1)  
        # time.sleep(1)  
    print(f"Sent {total_messages} messages. Exiting.")
except KeyboardInterrupt:
    print("Stopped sending messages.")
except Exception as e:
    print(f"Error sending message: {e}")
finally:
    bus.shutdown()