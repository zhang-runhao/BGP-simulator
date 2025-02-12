import argparse
import json
import os

class AStopo:
    def __init__(self, topo_file):
        self.topo_file = topo_file
        self.topo = json.load(open(topo_file, 'r'))
        self.ASN = self.topo['ASN']
        self.router_name_set = self.topo['router_name_set']
        self.router_distance_dict = self.topo['router_distance_dict']
        self.ip_router = self.topo['ip_router']

if __name__ == '__main__':
    as_topo = {}
    parser = argparse.ArgumentParser(description='Local Controller')
    parser.add_argument('--topo', type=str, default='./fulltopo/topo5as30sw/')
    args = parser.parse_args()
    host_as_dict = {}
    sw_as_dict = {}
    for file in os.listdir(args.topo):
        if file.startswith('as'):
            topo = AStopo(args.topo + file)
            as_topo[topo.ASN] = topo
            for router in topo.router_name_set:
                sw_as_dict[router] = topo.ASN
            for k, v in topo.ip_router.items():
                host_as_dict[k] = topo.ASN
                
    routing_tables = {}
    for file in os.listdir('./routing_tables/'):
        asn = int(file.split('.')[0][-1])
        routing_tables[asn] = json.load(open('./routing_tables/' + file, 'r'))
        print("routing table for as %d is loaded" % asn)
    
    # 分别为所有host之间计算路径跳数,放入一个src_host - dst_host - hops的csv文件中
    host_hops = []
    path = []
    for src_host in host_as_dict.keys():
        for dst_host in host_as_dict.keys():
            path = []
            if src_host == dst_host:
                continue
            hop = 0
            src_router = as_topo[host_as_dict[src_host]].ip_router[src_host]
            dst_router = as_topo[host_as_dict[dst_host]].ip_router[dst_host]
            next_hop = routing_tables[sw_as_dict[src_router]][src_router][dst_host][0]
            while next_hop != dst_router:
                if sw_as_dict[next_hop] != sw_as_dict[src_router]:
                    hop += 1
                elif sw_as_dict[next_hop] == sw_as_dict[src_router]:
                    hop += as_topo[sw_as_dict[next_hop]].router_distance_dict[next_hop][src_router]
                src_router = next_hop
                path.append(src_router)
                next_hop = routing_tables[sw_as_dict[src_router]][src_router][dst_host][0]
            if sw_as_dict[next_hop] != sw_as_dict[src_router]:
                    hop += 1
            elif sw_as_dict[next_hop] == sw_as_dict[src_router]:
                hop += as_topo[sw_as_dict[next_hop]].router_distance_dict[next_hop][src_router]
                path.append(next_hop)
            host_hops.append([src_host, dst_host, hop, path])
    
    with open('host_hops.csv', 'w') as f:
        for item in host_hops:
            f.write(",".join(map(str, item)) + "\n")