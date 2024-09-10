import random
from collections import defaultdict
from copy import deepcopy
import socket
import copy
import pickle


class BGPspeaker:
    '''
    BGP speaker的类,每个BGP speaker都是一个AS的节点,拥有IP前缀,与其他BGP speaker的对等关系。

    class variables:
        (a) AS_number:      integer -AS号
        (b) Router_id:      string - BGP speaker的RouterID
        (b) IP_prefix:      集合 (初始为空) - 存放本地IP前缀
        (c) IBGP_peers:     字典 (初始为空) - 字典 (i) 键为对等体RouterID (ii) 值为对等体的IBGP speaker对象
        (d) EBGP_peers:     字典 (初始为空) - 字典 (i) 键为对等体RouterID (ii) 值为对等体的IP地址,端口号
        (g) Routing_table:  字典 (初始为空) 存优选后的路由表 - 字典 (i) 键为目标地址 (ii) 值为一个列表,
        [下一跳RouterID, localpref, AS路径(列表), 标志位(0宣告完毕/1还需宣告给IBGP/2还需宣告给IBGP和EBGP)]
    '''

    '''
    构造函数
    Input arguments:
        (a) AS_number:        integer
        (b) Router_id:        string
    '''

    def __init__(self, AS_number, Router_id, ip_port):
        self.AS_number = AS_number
        self.Router_id = Router_id
        self.IPprefix = set()
        self.IBGP_peers = {}
        self.EBGP_peers = {}
        self.Routing_table = {}
        self.ip_port = ip_port

    '''
    添加本地IP前缀
    '''
    def net_add(self, IP_prefix):
        self.IPprefix.add(IP_prefix)
        self.Routing_table[IP_prefix] = [self.Router_id, 100, [self.AS_number], 2]

    '''
    向ibgp邻居宣告路由 
    
    Input arguments:
        (a) IP_prefix:           string - IP前缀
        (b) path_to_announce:    list - 路由表项
    '''
    def announce_path_to_IBGP_peers(self, IP_prefix, path_to_announce):
        path_to_announce[3] = path_to_announce[3] - 1
        for peer in self.IBGP_peers:
            self.IBGP_peers[peer].receive_path_from_IBGP_peer(IP_prefix, path_to_announce, self.Router_id)

    '''
    从ibgp邻居接收路由

    Input arguments:
        (a) IP_prefix:            string - IP前缀
        (b) path_to_receive:    list - 路由表项

    如果不在路由表中,则直接添加
    如果在路由表中,如果新的localpref更大,或者localpref相等但是AS路径更短,则更新路由表
    '''
    def receive_path_from_IBGP_peer(self, IP_prefix, path_to_receive, Router_id, localpref=100):
        if IP_prefix not in self.Routing_table:
            self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
            self.Routing_table[IP_prefix][0] = Router_id
            localpref = self.get_localpref(IP_prefix, self.Routing_table[IP_prefix], self.ip_port[0], self.ip_port[1])
            self.Routing_table[IP_prefix][1] = localpref
            self.Routing_table[IP_prefix][3] = 1  # 标志位设为1表示还需宣告给EBGP
            print(f'{self.Router_id} receive {IP_prefix} from {Router_id} {self.Routing_table[IP_prefix]}')
        else:
            if path_to_receive[1] > self.Routing_table[IP_prefix][1]:
                self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
                self.Routing_table[IP_prefix][3] = 1 # 标志位设为1表示还需宣告给IBGP
            elif path_to_receive[1] == self.Routing_table[IP_prefix][1] and len(path_to_receive[2]) < len(self.Routing_table[IP_prefix][2]):
                self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
                self.Routing_table[IP_prefix][3] = 1 # 标志位设为1表示还需宣告给IBGP

    '''
    向ebgp邻居宣告路由

    Input arguments:
        (a) IP_prefix:            string - IP前缀
        (b) path_to_announce:    list - 路由表项
    '''
    def announce_path_to_EBGP_peers(self, IP_prefix, path_to_announce):
        print(f'announce {IP_prefix} to EBGP peers is called')
        print(self.EBGP_peers)
        path_to_announce[3] = path_to_announce[3] - 1
        for peer in self.EBGP_peers:
            print(f'Connecting to {self.EBGP_peers[peer][0]}:{self.EBGP_peers[peer][1]}')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.EBGP_peers[peer][0], self.EBGP_peers[peer][1]))
                s.sendall(f'"IP_prefix":"{IP_prefix}", "path_to_announce_0":"{path_to_announce[0]}", "path_to_announce_1":"{path_to_announce[1]}", "path_to_announce_2":"{path_to_announce[2]}", "path_to_announce_3":"{path_to_announce[3]}", "Router_id":"{self.Router_id}", "Peer":"{peer}"'.encode())
                data = s.recv(1024)
                print(f'Received {data!r}')
            # self.EBGP_peers[peer].receive_path_from_EBGP_peer(IPprefix, path_to_announce, self.Router_id)

    '''
    从ebgp邻居接收路由

    Input arguments:
        (a) IP_prefix:          string - IP前缀
        (b) path_to_receive:    list - 路由表项
        (c) Router_id:          integer - 发送路由的RouterID

    如果不在路由表中,则直接添加
    如果在路由表中,如果新的localpref更大,或者localpref相等但是AS路径更短,则更新路由表
    更新AS路径
    '''
    def receive_path_from_EBGP_peer(self, IP_prefix, path_to_receive, Router_id, localpref=100):
        if IP_prefix not in self.Routing_table:
            self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
            self.Routing_table[IP_prefix][2].append(self.AS_number)
            self.Routing_table[IP_prefix][0] = Router_id
            localpref = self.get_localpref(IP_prefix, self.Routing_table[IP_prefix], self.ip_port[0], self.ip_port[1])
            self.Routing_table[IP_prefix][1] = localpref
            self.Routing_table[IP_prefix][3] = 2 # 标志位设为2表示还需宣告给IBGP和EBGP
        else:
            if path_to_receive[1] > self.Routing_table[IP_prefix][1]:
                self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
                self.Routing_table[IP_prefix][2].append(self.AS_number)
                self.Routing_table[IP_prefix][0] = Router_id
                self.Routing_table[IP_prefix][3] = 2 # 标志位设为2表示还需宣告给IBGP和EBGP
            elif path_to_receive[1] == self.Routing_table[IP_prefix][1] and len(path_to_receive[2]) < len(self.Routing_table[IP_prefix][2]):
                self.Routing_table[IP_prefix] = copy.deepcopy(path_to_receive)
                self.Routing_table[IP_prefix][2].append(self.AS_number)
                self.Routing_table[IP_prefix][0] = Router_id
                self.Routing_table[IP_prefix][3] = 2 # 标志位设为1表示已宣告给IBGP和EBGP
                
    
    def get_localpref(self, IP_prefix, routing_table_item, server_ip, server_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, server_port))
            data = {'IP_prefix': IP_prefix, 'Router_id': self.Router_id, 'next_hop': routing_table_item[0]}
            s.sendall(pickle.dumps(data))
            data = s.recv(1024)
            print(f'Received {data!r}')
        return int(data.decode())
