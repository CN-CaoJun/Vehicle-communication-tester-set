import can
import isotp
import time
import json
from config import Config
import threading

class CANBusFactory:
    """CAN总线工厂类，用于创建不同类型的CAN接口"""
    
    def __init__(self, channel_type, is_fd,**kwargs):
        """
        初始化CAN总线工厂
        :param channel_type: CAN接口类型 ('pcan'/'vector'/'slcan'/'socketcan')
        :param kwargs: 接口特定的配置参数
        """
        self.channel_type = channel_type
        self.config = kwargs
        self.can_bus = None
        self.notifier = None
        self.is_fd = is_fd
        
    def create_bus(self):
        """
        根据配置创建CAN总线实例
        :return: (can_bus, notifier) 元组
        """
        if self.channel_type == 'pcan':
            self._create_pcan_bus()
        elif self.channel_type == 'vector':
            self._create_vector_bus()
        elif self.channel_type == 'slcan':
            self._create_slcan_bus()
        elif self.channel_type == 'socketcan':
            self._create_socketcan_bus()
        else:
            raise ValueError(f"不支持的CAN接口类型: {self.channel_type}")
            
        self.notifier = can.Notifier(self.can_bus, [])
        return self.can_bus, self.notifier
        
    def _create_pcan_bus(self):
        """创建PCAN总线实例"""
        from can.interfaces.pcan import PcanBus
        
        # PCAN通道映射
        pcan_channel_map = {
            0x51: "PCAN_USBBUS1",
            0x52: "PCAN_USBBUS2",
            0x53: "PCAN_USBBUS3",
            0x54: "PCAN_USBBUS4"
        }
        
        handle = self.config.get('handle', 0x51)  # 默认使用PCAN_USBBUS1
        if handle not in pcan_channel_map:
            raise ValueError(f"不支持的PCAN通道句柄: 0x{handle:02X}")
            
        self.can_bus = PcanBus(
            channel=pcan_channel_map[handle],
            bitrate=self.config.get('bitrate', 500000),
            fd=self.config.get('fd', False)
        )
        
    def _create_vector_bus(self):
        """创建Vector总线实例"""
        can.rc['interface'] = 'vector'
        can.rc['bustype'] = 'vector'
        can.rc['channel'] = '0'
        can.rc['app_name'] = 'Python_ISOTP_Client'
        can.rc['fd'] = False  
        can.rc['bitrate'] = 500000
        can.rc['sjw_abr'] = 16
        can.rc['tseg1_abr'] = 63
        can.rc['tseg2_abr'] = 16
    
        try:
            self.can_bus = can.Bus()
            print(f"Vector bus initialized successfully in {'CANFD' if self.is_fd else 'CAN'} mode.")
        except Exception as e:
            print(f"Failed to initialize Vector bus: {e}")
            raise

    def _create_slcan_bus(self):
        """创建SLCAN总线实例"""
        from can.interfaces.slcan import slcanBus
        
        self.can_bus = slcanBus(
            channel=self.config.get('port', 'COM34'),
            bitrate=self.config.get('bitrate', 500000)
        )
        
    def _create_socketcan_bus(self):
        """创建SocketCAN总线实例"""
        self.can_bus = can.Bus(
            interface='socketcan',
            channel=self.config.get('channel', 'can0'),
            bitrate=self.config.get('bitrate', 500000),
            fd=self.config.get('fd', False)
        )

class ISOTPLayer:
    """ISOTP协议层封装"""
    def __init__(self, bus, notifier, txid, rxid, is_fd=False):
        """
        初始化ISOTP层
        :param bus: CAN总线实例
        :param notifier: CAN通知器
        :param txid: 发送ID
        :param rxid: 接收ID
        :param is_fd: 是否使用CANFD
        """
        self.params = {
            'stmin': 0,
            'blocksize': 0,
            'override_receiver_stmin': None,
            'wftmax': 4,
            'tx_data_length': 8,
            'tx_data_min_length':8,
            'tx_padding': 0x00,
            'rx_flowcontrol_timeout': 1000,
            'rx_consecutive_frame_timeout': 100,
            'can_fd': False,
            'max_frame_size': 4095,
            'bitrate_switch': False,
            'rate_limit_enable': False,
            'listen_mode': False,
            'blocking_send': False   
        }

        self.tp_addr = isotp.Address(
            isotp.AddressingMode.Normal_11bits,
            txid=txid,
            rxid=rxid
        )

        self.layer = isotp.NotifierBasedCanStack(
            bus=bus,
            notifier=notifier,
            address=self.tp_addr,
            params=self.params
        )

    def start(self):
        """启动ISOTP层"""
        self.layer.start()
        print("[ISOTP] 协议栈启动")

    def stop(self):
        """停止ISOTP层"""
        self.layer.stop()
        print("[ISOTP] 协议栈停止")

    def send(self, payload):
        """发送数据"""
        self.layer.send(payload)

    def receive(self, timeout=1):
        """接收数据"""
        return self.layer.recv(timeout=timeout)

class UDSResponder:
    """UDS响应处理器"""
    def __init__(self, test_case_file='IMS_response.json'):
        """
        初始化UDS响应器
        :param test_case_file: 测试用例文件
        """
        self.cfg = Config()
        if not self.cfg.load_case(test_case_file):
            raise FileNotFoundError(f"测试用例文件 {test_case_file} 加载失败")
        self.running = False
        self.receive_thread = None
        self.isotp_layer = None
        
    def start_receiving(self, isotp_layer):
        """启动接收线程"""
        self.isotp_layer = isotp_layer
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
    def stop_receiving(self):
        """停止接收线程"""
        self.running = False
        if self.receive_thread:
            self.receive_thread.join()
            
    def _receive_loop(self):
        """接收循环"""
        while self.running:
            try:
                payload = self.isotp_layer.receive(timeout=0.01)
                if payload:
                    response = self.process_request(payload)
                    self.isotp_layer.send(response)
            except Exception as e:
                print(f"[UDS] 接收处理异常: {e}")
            time.sleep(0.01)

    def process_request(self, payload):
        """
        处理UDS请求并生成响应
        :param payload: 请求数据
        :return: 响应数据
        """
        hex_req = payload.hex().upper()
        print(f"[UDS] 接收请求: {hex_req}")
        
        if len(payload) == 516 and payload[0] == 0x31:  # 检查第一个字节是否为0x36
            if payload[1] == 0x01: 
                if payload[2] == 0xD0 and payload[3] == 0x02:
                    return bytes([0x71,0x01,0xD0,0x02,0x00])  # 返回0x76和序列号
            else:
                return self._create_negative_response(0x31, 0x11)  # 如果没有序列号，返回长度错误
        
        # 处理传输数据请求
        if len(payload) > 0 and payload[0] == 0x36:  # 检查第一个字节是否为0x36
            if len(payload) > 1:
                seq_number = payload[1]  # 获取第二个字节作为序列号
                return bytes([0x76, seq_number])  # 返回0x76和序列号
            else:
                return self._create_negative_response(0x36, 0x13)  # 如果没有序列号，返回长度错误
        
        # 处理其他请求
        response_hex = self.cfg.find_case(hex_req)
        if response_hex:
            print(f"[UDS] 发送响应: {response_hex}")
            return bytes.fromhex(response_hex)

        # 如果没有找到匹配的响应，返回否定响应
        nrc_response = self._create_negative_response(payload[0], 0x11)
        print(f"[UDS] 发送否定响应: {nrc_response.hex().upper()}")
        return nrc_response

    def _create_negative_response(self, sid, nrc):
        """生成否定响应"""
        return bytes([0x7F, sid, nrc])

def main():
    """主函数示例"""
    try:
        # 创建CAN总线实例
        # can_factory = CANBusFactory(channel_type='vector', is_fd=False)
        can_factory = CANBusFactory(channel_type='pcan', is_fd=False)
        bus, notifier = can_factory.create_bus()

        # 创建ISOTP层
        isotp_layer = ISOTPLayer(
            bus=bus,
            notifier=notifier,
            txid=0x759,
            rxid=0x749,
            is_fd=False
        )
        isotp_layer.start()

        # 创建UDS响应器并启动接收
        responder = UDSResponder()
        responder.start_receiving(isotp_layer)

        # 主循环保持程序运行
        while True:
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("[系统] 用户中断操作")
    finally:
        if 'responder' in locals():
            responder.stop_receiving()
        if 'isotp_layer' in locals():
            isotp_layer.stop()
        if 'bus' in locals():
            bus.shutdown()

if __name__ == "__main__":
    main()