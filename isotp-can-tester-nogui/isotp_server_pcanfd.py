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

can.rc['channel'] = 'PCAN_USBBUS1'
can.rc['bustype'] = 'pcan'
 
# can.rc['fd'] = True  
can.rc['fd'] = True  
can.rc['bitrate'] = 500000  #Bitrate of channel in bit/s. Default is 500 kbit/s. Ignored if using CanFD.

#500K - 80%
can.rc['f_clock_mhz'] = 40 
can.rc['nom_brp'] = 1
can.rc['nom_tseg1'] = 63
can.rc['nom_tseg2'] = 16
can.rc['nom_sjw'] = 16
#2000K - 70%
can.rc['data_brp'] = 1
can.rc['data_tseg1'] = 13
can.rc['data_tseg2'] = 6
can.rc['data_sjw'] = 6
 
try:
    bus = Bus()
    notifier = can.Notifier(bus, [])
    print("PCAN-FD bus initialized successfully.")
except Exception as e:
    print(f"Failed to initialize PCAN bus: {e}")
    exit(1)

isotp_params = {
    'stmin': 1,
    'blocksize': 0,
    'override_receiver_stmin': None,
    'wftmax': 4,
    'tx_data_length': 64 if can.rc['fd'] else 8,
    'tx_data_min_length':8,
    'tx_padding': 0x00,
    'rx_flowcontrol_timeout': 1000,
    'rx_consecutive_frame_timeout': 100,
    'can_fd': can.rc['fd'],
    'max_frame_size': 4095,
    'bitrate_switch': False,
    'rate_limit_enable': False,
    'listen_mode': False,
    'blocking_send': False    
}

print("ISOTP Parameters:", isotp_params)
# logging.basicConfig(level=logging.DEBUG)
node_id_map = {
    'SMLS': {'RXID': 0x731, 'TXID': 0x739},
    'BMS': {'RXID': 0x7E2, 'TXID': 0x7EA},
    'PWR': {'RXID': 0x7E3, 'TXID': 0x7EB},
    'OCDC': {'RXID': 0x7E5, 'TXID': 0x7ED},
    'TMM': {'RXID': 0x7E6, 'TXID': 0x7EE},
    'HCU': {'RXID': 0x7E7, 'TXID': 0x7EF},
    'IBRS': {'RXID': 0x710, 'TXID': 0x718},
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
