import can
import isotp
import time
import random
from can.interface import Bus
import logging
from config import Config
import sys
import binascii

can.rc['interface'] = 'socketcan'
can.rc['channel'] = 'vcan0'
can.rc['fd'] = False  
can.rc['bitrate'] = 500000

try:
    bus = can.Bus()
    notifier = can.Notifier(bus, [])
    print("A Client on SocketCAN bus initialized successfully.")
except Exception as e:
    print(f"Failed to initialize: {e}")
    exit(1)
    
isotp_params = {
    'stmin': 8,
    'blocksize': 2,
    'override_receiver_stmin': None,
    'rx_flowcontrol_timeout': 1000,
    'rx_consecutive_frame_timeout': 1000,
    'wftmax': 0,
    'tx_data_length': 8,
    'tx_padding': 0x00,
    'rx_flowcontrol_timeout': 1000,
    'rx_consecutive_frame_timeout': 1000,
    'can_fd': False,
    'max_frame_size': 4095,
    'bitrate_switch': False,
    'rate_limit_enable': False,
    'listen_mode': False,
    'blocking_send': False    
}

logging.basicConfig(level=logging.DEBUG)
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E1, rxid=0x7E9)
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
                payload = bytearray([x & 0xFF for x in range(int(user_input))])
            else:
                payload = bytes.fromhex(user_input)
            isotp_layer.send(payload)
            print("Send Request, Len = ",len(payload))

        payload = isotp_layer.recv(block=False, timeout=3)
        if payload is not None:
            print("Recv Response")

        time.sleep(0.01)  

except KeyboardInterrupt:
    print("Stop!!")

finally:
    isotp_layer.stop()
    bus.shutdown()
