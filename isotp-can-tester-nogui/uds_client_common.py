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

class CommonClient:
    def __init__(self, bus_type, node_name):
        """
        初始化CommonClient
        :param bus_type: CAN总线类型，支持'vector'和'pcan'
        :param node_name: 节点名称，用于确定发送和接收ID
        """
        self.bus_type = bus_type

        # 节点ID映射表
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
        
        # 根据节点名称设置发送和接收ID
        if node_name in self.node_id_map:
            self.tx_id = self.node_id_map[node_name]['TXID']
            self.rx_id = self.node_id_map[node_name]['RXID']
            print(f"已配置节点 {node_name}:")
            print(f"TXID: {self.tx_id:#04X}")
            print(f"RXID: {self.rx_id:#04X}")
        else:
            raise ValueError(f"不支持的节点名称: {node_name}")
        
        # 配置CAN总线参数
        self._configure_can_rc()
        print(f"Bus type configured as: {can.rc['bustype']}")
        # 初始化CAN总线
        self.bus = Bus()
        print("CAN总线已初始化")
        self.notifier = can.Notifier(self.bus, [])
        # 初始化ISOTP层
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
            raise ValueError(f"不支持的总线类型: {self.bus_type}")
            
    def start(self):
        """
        启动所有服务
        """
        self.uds_client.open()
        
    def stop(self):
        """
        停止所有服务
        """
        self.uds_client.close()
        self.stack.stop()
        self.bus.shutdown()
        
    def get_client(self):
        """
        获取UDS客户端实例
        """
        return self.uds_client


def main():
    """
    主函数：处理用户输入并发送CAN诊断消息
    """
    try:
        # 创建CommonClient实例
        client = CommonClient('vector','IMS')
        client.start()
        print("CAN诊断客户端已启动")
        print("请输入命令：")
        print("1 - 发送诊断请求")
        print("2 - 发送自定义数据")
        print("q - 退出程序")

        while True:
            cmd = input(">>> ").strip()
            
            if cmd.lower() == 'q':
                print("正在退出程序...")
                break
                
            elif cmd == '1':
                try:
                    # 获取UDS客户端
                    uds_client = client.get_client()
                    
                    # 这里可以添加具体的诊断请求逻辑
                    # 例如：读取数据标识符
                    response = uds_client.read_data_by_identifier([0xF186])
                    print(f"收到响应: {response}")
                    
                except Exception as e:
                    print(f"发送诊断请求失败: {str(e)}")
            
            elif cmd == '2':
                try:
                    data_str = input("请输入要发送的数据(十六进制格式，如: 10 20 30): ").strip()
                    # 将输入的十六进制字符串转换为字节数组
                    data_bytes = bytes.fromhex(data_str)
                    
                    # 使用conn直接发送数据
                    client.conn.send(data_bytes)
                    print(f"已发送数据: {' '.join([f'{b:02X}' for b in data_bytes])}")
                    
                    # 接收响应
                    response = client.conn.wait_frame(timeout=2)
                    if response:
                        print(f"收到响应: {' '.join([f'{b:02X}' for b in response])}")
                    else:
                        print("未收到响应")
                        
                except ValueError as e:
                    print(f"数据格式错误: {str(e)}")
                except Exception as e:
                    print(f"发送数据失败: {str(e)}")
            
            else:
                print("无效的命令，请重试")
                
    except Exception as e:
        print(f"程序运行错误: {str(e)}")

if __name__ == "__main__":
    main()

