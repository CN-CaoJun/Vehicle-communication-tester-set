import can
import isotp
import time

class CanIsotpSender:
    def __init__(self, channel, bustype, bitrate, rxid, txid, stmin=6, blocksize=2):
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.rxid = rxid
        self.txid = txid
        self.stmin = stmin
        self.blocksize = blocksize
        self.bus = None
        self.notifier = None
        self.isotp_layer = None

    def initialize(self):
        try:
            self.bus = can.interface.Bus(channel=self.channel, bustype=self.bustype, bitrate=self.bitrate)
            self.notifier = can.Notifier(self.bus, [])
            isotp_params = {
                'stmin': self.stmin,
                'blocksize': self.blocksize,
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
            tp_addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=self.txid, rxid=self.rxid)
            self.isotp_layer = isotp.NotifierBasedCanStack(
                bus=self.bus,
                notifier=self.notifier,
                address=tp_addr,
                error_handler=None,
                params=isotp_params
            )
            self.isotp_layer.start()
            print("CAN ISOTP sender initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize CAN ISOTP sender: {e}")
            raise

    def send_data(self, data, dlc=8):
        if self.isotp_layer is None:
            print("CAN ISOTP sender is not initialized.")
            return

        if isinstance(data, str):
            data = data.encode('utf-8')

        # 补齐数据到 DLC 长度
        if len(data) < dlc:
            data += b'\x00' * (dlc - len(data))

        try:
            self.isotp_layer.send(data[:dlc])
            print(f"CAN data sent: Data={data[:dlc].hex()}")
        except Exception as e:
            print(f"Failed to send CAN data: {e}")

    def receive_data(self, timeout=3):
        if self.isotp_layer is None:
            print("CAN ISOTP sender is not initialized.")
            return None

        try:
            payload = self.isotp_layer.recv(block=False, timeout=timeout)
            if payload is not None:
                print(f"Received data: {payload.hex()}")
            return payload
        except Exception as e:
            print(f"Failed to send CAN data: {e}")