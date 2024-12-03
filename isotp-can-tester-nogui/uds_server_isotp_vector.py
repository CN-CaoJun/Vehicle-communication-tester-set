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
    print("Vector bus initialized successfully. This for ***Server***")
except Exception as e:
    print(f"Failed to initialize PCAN bus: {e}")
    exit(1)

isotp_params = {
    'stmin': 10,
    'blocksize': 4,
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
# logging.basicConfig(level=logging.DEBUG)
#A-CAN -> VCU -> 
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E9, rxid=0x7E1)
# tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x749, rxid=0x741)

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

# 定义要查找的node_id
target_node_id = "VCU"  # 这里可以根据需要修改为其他node_id

# 遍历CAN_Nodes数组，查找匹配的node_id
for node in data['CAN_Nodes']:
    if node['node_id'] == target_node_id:
        phyreq_address = node['phyreq_address']
        resp_address = node['resp_address']
        print(f"Node ID: {target_node_id}")
        print(f"phyreq_address: {phyreq_address}")
        print(f"resp_address: {resp_address}")
        break  # 如果找到了匹配的node_id，就可以退出循环
else:
    print(f"Node ID '{target_node_id}' not found in the JSON file.")


cfg.load_case("test_case.json")

try:
    while True:
        payload = isotp_layer.recv(block=False, timeout=3)
        if payload is not None:
            print("Recv Request:")
            print(payload.hex().upper())

            payload_res = cfg.find_case(payload.hex().upper())
            if  payload_res == None:
                payload = bytearray([x & 0xFF for x in range(128)])
                
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
