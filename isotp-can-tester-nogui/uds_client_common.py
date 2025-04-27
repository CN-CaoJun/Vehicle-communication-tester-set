import can
import isotp
import udsoncan
from udsoncan.client import Client
from udsoncan.connections import PythonIsoTpConnection
import time
import random
from can.interface import Bus
import logging
from config import Config
import sys
import binascii
import struct

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

class FlexRawData(udsoncan.DidCodec):
    def encode(self, val):
        if not isinstance(val, (bytes, bytearray)):
            raise ValueError("Input data must be bytes or bytearray type")
        
        if len(val) != 30:
            raise ValueError('Data length must be 30 bytes')
            
        return val  # Return raw data directly
        
    def decode(self, payload):
        if len(payload) != 30:
            raise ValueError('Received data length must be 30 bytes')
            
        return payload  # Return raw data directly

    def __len__(self):
        return 30    # Fixed return 30 bytes length

class CommonClient:
    def __init__(self, bus_type, node_name):
        """
        Initialize CommonClient
        :param bus_type: CAN bus type, supports 'vector' and 'pcan'
        :param node_name: Node name, used to determine send and receive ID
        """
        self.bus_type = bus_type

        # Node ID mapping table
        self.node_id_map = {
            'IMS': {'RXID': 0x759, 'TXID': 0x749},
            'SMLS': {'RXID': 0x739, 'TXID': 0x731},
            'HCML': {'RXID': 0x748, 'TXID': 0x740},
            'HCMR': {'RXID': 0x749, 'TXID': 0x741},
            'RCM':  {'RXID': 0x74A, 'TXID': 0x742},
            'BMS': {'RXID': 0x7EA, 'TXID': 0x7E2},
            'PWR': {'RXID': 0x7EB, 'TXID': 0x7E3},
            'OCDC': {'RXID': 0x7ED, 'TXID': 0x7E5},
            'TMM': {'RXID': 0x7EE, 'TXID': 0x7E6},
            'VCU': {'RXID': 0x7E9, 'TXID': 0x7E1},
            'HCU': {'RXID': 0x7EF, 'TXID': 0x7E7},
        }
        
        # Set send and receive ID based on node name
        if node_name in self.node_id_map:
            self.tx_id = self.node_id_map[node_name]['TXID']
            self.rx_id = self.node_id_map[node_name]['RXID']
            print(f"Node {node_name} configured:")
            print(f"TXID: {self.tx_id:#04X}")
            print(f"RXID: {self.rx_id:#04X}")
        else:
            raise ValueError(f"Unsupported node name: {node_name}")
        
        # Configure CAN bus parameters
        self._configure_can_rc()
        print(f"Bus type configured as: {can.rc['bustype']}")
        # Initialize CAN bus
        self.bus = Bus()
        print("CAN bus initialized")
        self.notifier = can.Notifier(self.bus, [])
        # Initialize ISOTP layer
        self.tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, 
                                   txid=self.tx_id, 
                                   rxid=self.rx_id)
        self.stack = isotp.NotifierBasedCanStack(
            bus=self.bus,
            notifier=self.notifier,
            address=self.tp_addr,
            params=isotp_params
        )
        
        self.uds_config = udsoncan.configs.default_client_config.copy()
        self.uds_config = {
            'request_timeout': 2,
            'p2_timeout': 1,
            'p2_star_timeout': 5,
            'security_algo': None,
            'security_algo_params': None,
            'tolerate_zero_padding': True,
            'ignore_all_zero_dtc': True,
            'dtc_snapshot_did_size': 2
        }
        
        self.uds_config['data_identifiers'] = {
                'default': '>H',
                0x7705: FlexRawData,
            }
        self.conn = PythonIsoTpConnection(self.stack)
        self.uds_client = Client( self.conn, config=self.uds_config)
        
    def _configure_can_rc(self):
        if self.bus_type == 'vector':
            can.rc['interface'] = 'vector'
            can.rc['bustype'] = 'vector'
            can.rc['channel'] = 0
            can.rc['app_name'] = 'Python_ISOTP_Server'
            can.rc['fd'] = False
            can.rc['bitrate'] = 500000
            can.rc['sjw_abr'] = 16
            can.rc['tseg1_abr'] = 63
            can.rc['tseg2_abr'] = 16
        
        elif self.bus_type == 'pcan':
            can.rc['interface'] = 'pcan'
            can.rc['bustype'] = 'pcan'
            can.rc['channel'] = 'PCAN_USBBUS1'
            can.rc['bitrate'] = 500000
        
        else:
            raise ValueError(f"Unsupported bus type: {self.bus_type}")
            
    def start(self):
        """
        Start all services
        """
        self.uds_client.open()
        
    def stop(self):
        """
        Stop all services
        """
        self.uds_client.close()
        self.stack.stop()
        self.bus.shutdown()
        
    def get_client(self):
        """
        Get UDS client instance
        """
        return self.uds_client


def main():
    """
    Main function: Handle user input and send CAN diagnostic messages
    """
    try:
        # Create CommonClient instance
        client = CommonClient('vector','IMS')
        client.start()
        print("CAN diagnostic client started")
        print("Please input command:")
        print("1 - Send diagnostic request")
        print("2 - Send custom data")
        print("q - Exit program")

        while True:
            cmd = input(">>> ").strip()
            
            if cmd.lower() == 'q':
                print("Exiting program...")
                break
                
            elif cmd == '1':
                try:
                    # Get UDS client
                    uds_client = client.get_client()
                    
                    # Add specific diagnostic request logic here
                    # Example: Read data identifier
                    response = uds_client.read_data_by_identifier([0x7705])
                    # Extract response data
                    if response.positive:
                        data = response.service_data.values[0x7705]  # Use DID as key to get value
                        # Convert bytes data to hex string
                        hex_data = ' '.join([f'{b:02X}' for b in data])
                        print(f"Hex data: {hex_data}")
                        print(f"Raw data: {data}")  # Print raw bytes data

                    else:
                        print(f"Received negative response: {response.code}")
                    
                except Exception as e:
                    print(f"Failed to send diagnostic request: {str(e)}")
            
            elif cmd == '2':
                try:
                    data_str = input("Please input data (hex format, e.g.: 10 20 30): ").strip()
                    # Convert hex string to bytes array
                    data_bytes = bytes.fromhex(data_str)
                    
                    # Use conn to send data directly
                    client.conn.send(data_bytes)
                    print(f"Data sent: {' '.join([f'{b:02X}' for b in data_bytes])}")
                    
                    # Receive response
                    response = client.conn.wait_frame(timeout=2)
                    if response:
                        print(f"Response received: {' '.join([f'{b:02X}' for b in response])}")
                    else:
                        print("No response received")
                        
                except ValueError as e:
                    print(f"Data format error: {str(e)}")
                except Exception as e:
                    print(f"Failed to send data: {str(e)}")
            
            else:
                print("Invalid command, please try again")
                
    except Exception as e:
        print(f"Program runtime error: {str(e)}")

if __name__ == "__main__":
    main()

