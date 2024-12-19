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

node_id_map = {
    'SMLS': {'RXID': 0x739, 'TXID': 0x731},
    'HCML': {'RXID': 0x748, 'TXID': 0x740},
    'HCMR': {'RXID': 0x749, 'TXID': 0x741},
    'RCM':  {'RXID': 0x74A, 'TXID': 0x742},
    'BMS': {'RXID': 0x7EA, 'TXID': 0x7E2},
    'PWR': {'RXID': 0x7EB, 'TXID': 0x7E3},
    'OCDC': {'RXID': 0x7ED, 'TXID': 0x7E5},
    'TMM': {'RXID': 0x7EE, 'TXID': 0x7E6},
    'HCU': {'RXID': 0x7EF, 'TXID': 0x7E7},
}
node_name = sys.argv[1]

if node_name in node_id_map:
    rx_id = node_id_map[node_name]['RXID']
    tx_id = node_id_map[node_name]['TXID']
    print("************************************************************")
    print(f"ISOTP Tester -> {node_name}\r\nRXID: {rx_id:#04X}\r\nTXID: {tx_id:#04X}")
    print("************************************************************")
    
else:
    print(f"not found: {node_name}")
            
tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=tx_id, rxid=rx_id)

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
        
        user_input = input("Please enter node name and length of payload or enter 'q' to exit:\r\n")
        if user_input.lower() == 'q':
            print("EXIT")
            break
        
        if user_input is not None:    
            parts = user_input.split()
            if len(parts) != 2:
                print("Invalid input format. Please enter length of payload, and expected response length (e.g., '10 20').")
                continue
            payload_length_str, expected_response_length_str = parts
            
            # if payload_length_str.isdigit() == 1:
            #     payload_length = int(payload_length_str)
            #     print("First parameter is  a integer.")
            # else:
            #     print("First parameter is not a integer.")
            
            if payload_length_str.isdigit() and 1 <= int(payload_length_str) <= 4095:
                # payload_length = int(payload_length_str)
                expected_response_length = int(expected_response_length_str)
                payload = bytearray([expected_response_length >> 8, expected_response_length & 0xFF])
                payload.extend([x & 0xFF for x in range(2, int(payload_length_str))])
            else:
                payload = bytes.fromhex(payload_length_str) 
            
            isotp_layer.send(payload)
            print("Send Request, Len = ",len(payload))

        
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
