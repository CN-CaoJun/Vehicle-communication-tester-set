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
    'stmin': 10,
    'blocksize': 4,
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
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E9, rxid=0x7E1)

isotp_layer = isotp.NotifierBasedCanStack(
    bus = bus,
    notifier = notifier,
    address = tp_addr,
    error_handler = None,
    params = isotp_params
)

isotp_layer.start()
cfg = Config()

with open('Node_Description.json', 'r') as file:
    data = json.load(file)

target_node_id = "VCU" 

for node in data['CAN_Nodes']:
    if node['node_id'] == target_node_id:
        phyreq_address = node['phyreq_address']
        resp_address = node['resp_address']
        print(f"Node ID: {target_node_id}")
        print(f"phyreq_address: {phyreq_address}")
        print(f"resp_address: {resp_address}")
        break  
else:
    print(f"Node ID '{target_node_id}' not found in the JSON file.")


cfg.load_case("Diag_Description.json")

try:
    while True:
        payload = isotp_layer.recv(block=False, timeout=3)
        if payload is not None:
            print("Recv Request:")
            print(payload.hex().upper())

            payload_res = cfg.find_case(payload.hex().upper())
            if  payload_res == None:
                payload = bytearray([x & 0xFF for x in range(5)])
            else:
                print("Send Random Data from json file:")
                payload = bytes.fromhex(payload_res)

            isotp_layer.send(payload)
            print("Send Random Data, len = ",len(payload))
            print(payload.hex().upper())
            
        time.sleep(0.01)  

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    isotp_layer.stop()
    bus.shutdown()
