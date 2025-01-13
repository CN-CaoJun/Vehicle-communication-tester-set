import socket
import argparse

def tcp_client(server_ip, server_port):
    # 创建一个TCP/IP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # 连接到服务器
        client_socket.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")
        
        while True:
            # 从用户输入获取消息
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Exiting...")
                break
            
            # 发送数据
            client_socket.sendall(message.encode('utf-8'))
            print(f"Sent: {message}")
            
            # 接收响应
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Received: {response}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        # 关闭连接
        client_socket.close()
        print("Connection closed.")

if __name__ == "__main__":

    server_ip = "10.245.69.27"
    server_port = 6001  # 根据实际情况修改端口号

    tcp_client(server_ip, server_port)