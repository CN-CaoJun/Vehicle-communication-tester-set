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
can.rc['app_name'] = 'IMS_Diag_CLient'
 
can.rc['fd'] = False
can.rc['bitrate'] = 500000
# can.rc['data_bitrate'] = 2000000

can.rc['sjw_abr'] = 16
can.rc['tseg1_abr'] = 63
can.rc['tseg2_abr'] = 16

# can.rc['sam_abr'] = 1
# can.rc['sjw_dbr'] = 6
# can.rc['tseg1_dbr'] = 13
# can.rc['tseg2_dbr'] = 6

try:
    bus = Bus()
    notifier = can.Notifier(bus, [])
    print("Vector bus initialized successfully. This for ***Client***")
except Exception as e:
    print(f"Failed to initialize PCAN bus: {e}")
    exit(1)
    
isotp_params = {
    'stmin': 10,
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

# logging.basicConfig(level=logging.DEBUG)

# Fixed IDs for ISOTP communication
rx_id = 0x759
tx_id = 0x749

print("************************************************************")
print(f"ISOTP Tester\r\nRXID: {rx_id:#04X}\r\nTXID: {tx_id:#04X}")
print("************************************************************")

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
        
        user_input = input("Press Enter to start calibration injection or 'q' to exit:\r\n")
        if user_input.lower() == 'q':
            print("EXIT")
            break
        
        # Send calibration data
        cal_data = bytes.fromhex('2E EF E2 00 10 40 9C 00 10 40 9C 00 10 40 9C')
        isotp_layer.send(cal_data)
        print("Send Calibration Data: ", cal_data.hex().upper())
        
        # Receive and validate response
        response = isotp_layer.recv(block=False, timeout=3)
        if response is not None:
            if len(response) > 0 and response[0] == 0x6E:
                print("Received Positive Response")
                print("Response Data:", response.hex().upper())
            else:
                print("Received Negative Response or Invalid Data")
                if len(response) > 0:
                    print("Response Data:", response.hex().upper())

        time.sleep(0.01)  

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    isotp_layer.stop()
    bus.shutdown()
