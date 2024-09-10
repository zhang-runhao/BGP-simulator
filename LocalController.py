from BGPspeaker import BGPspeaker
import socket
import threading
import json
import argparse

class LocalController:
    '''
    本地控制器的类,每个控制器都是一个AS的节点,拥有多个BGP speaker

    class variables:
        (a) AS_number:      integer -AS号
        (b) BGPspeakers:    字典 (初始为空) - 字典 (i) 键为RouterID (ii) 值为BGPspeaker对象
    '''

    def __init__(self, AS_number):
        self.BGPspeakers = {}
        self.AS_number = AS_number
        self.ip_port = []

    def add_speaker(self, AS_number, Router_id):
        self.BGPspeakers[Router_id] = BGPspeaker(AS_number, Router_id, self.ip_port)

    def add_IBGP_peer(self, Router_id1, Router_id2):
        self.BGPspeakers[Router_id1].IBGP_peers[Router_id2] = self.BGPspeakers[Router_id2]
        self.BGPspeakers[Router_id2].IBGP_peers[Router_id1] = self.BGPspeakers[Router_id1]

    def add_EBGP_peer(self, Router_id1, Router_id2, controller_ip):
        self.BGPspeakers[Router_id1].EBGP_peers[Router_id2] = controller_ip

    def one_round_BGP(self):
        for speaker in self.BGPspeakers:
            for item in self.BGPspeakers[speaker].Routing_table:
                print(f'{speaker} routing table: {item} {self.BGPspeakers[speaker].Routing_table[item]}')
                if self.BGPspeakers[speaker].Routing_table[item][3] == 1:
                    self.BGPspeakers[speaker].announce_path_to_EBGP_peers(item, self.BGPspeakers[speaker].Routing_table[item])
                    print(f'{speaker} announce {item} to IBGP peers')
                elif self.BGPspeakers[speaker].Routing_table[item][3] == 2:
                    self.BGPspeakers[speaker].announce_path_to_IBGP_peers(item, self.BGPspeakers[speaker].Routing_table[item])
                    print(f'{speaker} announce {item} to IBGP peers')
                    self.BGPspeakers[speaker].announce_path_to_EBGP_peers(item, self.BGPspeakers[speaker].Routing_table[item])
                    print(f'{speaker} announce {item} to EBGP peers')

    def ebgp_recieve_server(self, host, port):
        global flag
        print('EBGP server start')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.bind((host, port))
            s.listen()
            print(f'Server listening on {host}:{port}')
            while flag:
                print(flag)
                try:
                    conn, addr = s.accept()
                    with conn:
                        print(f'Connected by {addr}')
                        data = conn.recv(1024)
                        print(f'Received {data!r}')
                        data = data.decode()
                        data = json.loads('{' + data + '}')
                        data['path_to_announce_1'] = int(data['path_to_announce_1'])
                        data['path_to_announce_2'] = data['path_to_announce_2'][1:-1].split(',')
                        data['path_to_announce_2'] = [int(item) for item in data['path_to_announce_2']]
                        data['path_to_announce_3'] = int(data['path_to_announce_3']) 
                        data['path_to_announce'] = [data['path_to_announce_0'], data['path_to_announce_1'], data['path_to_announce_2'], data['path_to_announce_3']]
                        for item in data['path_to_announce']:
                            print(item)
                        self.BGPspeakers[data['Peer']].receive_path_from_EBGP_peer(data['IP_prefix'], data['path_to_announce'], data['Router_id'])
                        if not data:
                            break
                        conn.sendall("EBGP update data received".encode())
                except socket.timeout:
                    continue
            return
        print('EBGP server closed')

    def is_converged(self):
        for speaker in self.BGPspeakers:
            for item in self.BGPspeakers[speaker].Routing_table:
                if self.BGPspeakers[speaker].Routing_table[item][3] != 0:
                    return False
        return True

    def connect_to_fed_controller(self, host, port):
        global flag
        flag = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f'Server listening on {host}:{port}')
            conn, addr = s.accept()
            with conn:
                print(f'Connected by {addr}')
                while flag:
                    data = conn.recv(1024)
                    print(f'Received {data!r}')
                    data = data.decode()
                    if data == 'start!':
                        self.one_round_BGP()
                        if self.is_converged():
                            conn.sendall('converged!'.encode())
                        else:
                            conn.sendall('not converged!'.encode())
                    elif data == 'close':
                        print('Closing connection')
                        flag = False
                        print(flag)
                        s.close()
                        print('Connection closed')
                        return
                    else:
                        conn.sendall('data received'.encode())

if __name__ == '__main__':
    controller = LocalController(1)
    controller.ip_port = ['localhost', 2121]
    # 拾取拓扑
    controller.add_speaker(1, '1.1')
    controller.add_speaker(1, '1.2')
    controller.add_speaker(1, '1.3')

    controller.add_IBGP_peer('1.1', '1.2')
    controller.add_IBGP_peer('1.2', '1.3')
    controller.add_IBGP_peer('1.3', '1.1')

    controller.add_EBGP_peer('1.3', '2.3', ['localhost', 212])

    controller.BGPspeakers['1.1'].net_add('1.1.0.1')
    controller.BGPspeakers['1.1'].net_add('1.1.0.2')

    controller.BGPspeakers['1.2'].net_add('1.2.0.1')
    controller.BGPspeakers['1.2'].net_add('1.2.0.2')

    # 一个线程与联邦控制器建立连接，一个线程监听EBGP连接
    flag = True

    t1 = threading.Thread(target=controller.connect_to_fed_controller, args=('localhost', 111))
    t2 = threading.Thread(target=controller.ebgp_recieve_server, args=('localhost', 112))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    for speaker in controller.BGPspeakers:
        for key, value in controller.BGPspeakers[speaker].Routing_table.items():
            print(f'{speaker} routing table: {key} {value}')




    