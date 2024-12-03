import can
import isotp
import time
import random
from can.interface import Bus
import logging
from config import Config
import sys
import binascii

can.rc['interface'] = 'vector'
can.rc['bustype'] = 'vector'
can.rc['channel'] = '0'
can.rc['app_name'] = 'Python_ISOTP_Client'
 
can.rc['fd'] = True  
can.rc['bitrate'] = 500000
can.rc['data_bitrate'] = 2000000

can.rc['sjw_abr'] = 16
can.rc['tseg1_abr'] = 63
can.rc['tseg2_abr'] = 16

can.rc['sam_abr'] = 1

can.rc['sjw_dbr'] = 6
can.rc['tseg1_dbr'] = 13
can.rc['tseg2_dbr'] = 6

try:
    bus = Bus()
    notifier = can.Notifier(bus, [])
    print("Vector bus initialized successfully. This for ***Client***")
except Exception as e:
    print(f"Failed to initialize PCAN bus: {e}")
    exit(1)
    
isotp_params = {
    'stmin': 4,
    'blocksize': 8,
    'override_receiver_stmin': None,
    'wftmax': 4,
    'tx_data_length': 64,
    'tx_data_min_length':8,
    'tx_padding': 0x00,
    'rx_flowcontrol_timeout': 1000,
    'rx_consecutive_frame_timeout': 100,
    'can_fd': True,
    'max_frame_size': 4095,
    'bitrate_switch': False,
    'rate_limit_enable': False,
    'listen_mode': False,
    'blocking_send': False    
}

logging.basicConfig(level=logging.DEBUG)

tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x731, rxid=0x739)

isotp_layer = isotp.NotifierBasedCanStack(
    bus = bus,
    notifier = notifier,
    address = tp_addr,
    error_handler = None,
    params = isotp_params
)

isotp_layer.start()

try:
    while True:
        
        user_input = input("Please enter len data or the hexadecimal data to be sent (e.g. 1A2B3C), or enter 'q' to exit:\r\n")
        if user_input.lower() == 'q':
            print("EXIT")
            break
    
        if user_input is not None:
            if user_input.isdigit() and 1 <= int(user_input) <= 4095:
                # payload = bytes([random.randint(0, 255) for _ in range(int(user_input))])
                payload = bytearray([x & 0xFF for x in range(int(user_input))])
            else:
                payload = bytes.fromhex(user_input)
            
            isotp_layer.send(payload)
            print("Send Request, Len = ",len(payload))
            # for i in range(0, len(payload), 64):
                # print(f"{i//64 + 1:03d}: {payload[i:i+64].hex().upper()}")

        
        payload = isotp_layer.recv(block=False, timeout=3)
        if payload is not None:
            print("Recv Response")
            # print("Recv Response, len is", len(payload))
            # for i in range(0, len(payload), 64):
            #     print(f"{i//64 + 1:03d}: {payload[i:i+64].hex().upper()}")

        time.sleep(0.01)  

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    isotp_layer.stop()
    bus.shutdown()
