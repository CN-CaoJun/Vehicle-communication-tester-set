import socket
import argparse

def udp_client(server_ip, server_port):
    # 创建一个UDP/IP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        while True:
            # 从用户输入获取消息
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Exiting...")
                break
            
            # 发送数据
            client_socket.sendto(message.encode('utf-8'), (server_ip, server_port))
            print(f"Sent: {message}")
            
            # 接收响应
            response, server_address = client_socket.recvfrom(1024)
            print(f"Received from {server_address}: {response.decode('utf-8')}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        # 关闭连接
        client_socket.close()
        print("Connection closed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Client to send custom messages.")
    parser.add_argument("server_ip", type=str, help="Server IP address")
    parser.add_argument("server_port", type=int, help="Server port number")

    args = parser.parse_args()

    server_ip = args.server_ip
    server_port = args.server_port

    udp_client(server_ip, server_port)