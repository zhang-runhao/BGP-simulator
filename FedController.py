import socket
import time

class FedController:
    '''
    联邦控制器的类,拥有一个存储本地控制器AS号的集合

    class variables:
        (a) Controller_Connected:     字典 (初始为空) - 存放已经连接的控制器的AS号, 键为AS号, 值为标志位是否收敛
        (b) Controller_Connected_Socket: 字典 (初始为空) - 存放已经连接的控制器的AS号, 键为AS号, 值为socket对象
    '''

    def __init__(self, AS_to_connect):
        self.Controller_Connected = {}
        self.Controller_Connected_Socket = {}
        print('Connecting to controllers...')
        for key, value in AS_to_connect.items():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((value[0], value[1]))
            self.Controller_Connected[key] = False
            self.Controller_Connected_Socket[key] = s

            s.sendall(f'Hello, Controller {key}'.encode())
            data = s.recv(1024)
            print(f'Received {data!r}')

    def is_converged(self):
        for key, value in self.Controller_Connected.items():
            if value == False:
                return False
        return True

    '''
    联邦控制器核心逻辑:
    循环,直到所有控制器都收敛
        对于每一个控制器
            发送start!消息, 让控制器开始工作进行一轮BGP
            接收消息
            如果消息为converged!
                将标志位设为True
    '''
    def work(self):
        while not self.is_converged():
            time.sleep(3)
            for key, value in self.Controller_Connected.items():
                self.Controller_Connected[key] = False
                self.Controller_Connected_Socket[key].sendall('start!'.encode())
                data = self.Controller_Connected_Socket[key].recv(1024)
                print(f'Received {data!r}')
                data = data.decode()
                if data == 'converged!':
                    self.Controller_Connected[key] = True
                    print(f'Controller {key} is converged!')
                elif data == 'not converged!':
                    self.Controller_Connected[key] = False
                    print(f'Controller {key} is not converged!')
        print('All controllers are converged!')
        for key, value in self.Controller_Connected.items():
            self.Controller_Connected_Socket[key].sendall('close'.encode())
            self.Controller_Connected_Socket[key].close()


if __name__ == '__main__':
    AS_to_connect = {1: ['localhost', 111], 2: ['localhost', 211]}
    controller = FedController(AS_to_connect)
    controller.work()