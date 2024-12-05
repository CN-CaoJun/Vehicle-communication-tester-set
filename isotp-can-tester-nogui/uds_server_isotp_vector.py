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
    print("Vector bus initialized successfully.\r\n")
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
    'bitrate_switch': True,
    'rate_limit_enable': False,
    'listen_mode': False,
    'blocking_send': False    
}
# logging.basicConfig(level=logging.DEBUG)
node_id_map = {
    'SMLS': {'RXID': 0x731, 'TXID': 0x739},
    'BMS': {'RXID': 0x7E2, 'TXID': 0x7EA},
    'PWR': {'RXID': 0x7E3, 'TXID': 0x7EB},
    'OCDC': {'RXID': 0x7E5, 'TXID': 0x7ED},
    'TMM': {'RXID': 0x7E6, 'TXID': 0x7EE},
    'HCU': {'RXID': 0x7E7, 'TXID': 0x7EF},
}
node_name = sys.argv[1]

if node_name in node_id_map:
    rx_id = node_id_map[node_name]['RXID']
    tx_id = node_id_map[node_name]['TXID']
    print("************************************************************")
    print(f"ISOTP Server : {node_name} \r\nRXID: {rx_id:#04X}  \r\nTXID: {tx_id:#04X}")
    print("************************************************************")
    
            
else:
    print(f"Note found: {node_name}")
            
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=tx_id, rxid=rx_id)

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
cfg.load_case("test_case.json")

try:
    while True:
        payload = isotp_layer.recv(block=False, timeout=3)
        if payload is not None:
            print("Recv Request:")
            print(payload.hex().upper())

            payload_res = cfg.find_case(payload.hex().upper())
            if  payload_res == None:
                
                if len(payload) < 2:
                    print("Received payload is too short to extract response length.")
                    len_res = 2
                else:
                    len_res = (payload[0] << 8) | payload[1]
                    print(f"Parsed response length: {len_res}")
                    if len_res > 4095:
                        len_res = 4095
                    
                payload = bytearray([x & 0xFF for x in range(len_res)])
            else:
                print("Send specific Data from json file:")
                payload = bytes.fromhex(payload_res)

            isotp_layer.send(payload)
            print("Send Data, len = ",len(payload))
            print(payload.hex().upper())
            
        time.sleep(0.01)  

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    isotp_layer.stop()
    bus.shutdown()
