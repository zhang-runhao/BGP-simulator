from LocalController import LocalController
import socket
import threading

if __name__ == '__main__':
    controller = LocalController(2)
    controller.ip_port = ['localhost', 2221]
    # 拾取拓扑
    controller.add_speaker(2, '2.1')
    controller.add_speaker(2, '2.2')
    controller.add_speaker(2, '2.3')

    controller.add_IBGP_peer('2.1', '2.2')
    controller.add_IBGP_peer('2.2', '2.3')
    controller.add_IBGP_peer('2.3', '2.1')

    controller.add_EBGP_peer('2.3', '1.3', ['localhost', 112])

    controller.BGPspeakers['2.1'].net_add('2.1.0.1')
    controller.BGPspeakers['2.1'].net_add('2.1.0.2')
    controller.BGPspeakers['2.2'].net_add('2.2.0.1')
    controller.BGPspeakers['2.2'].net_add('2.2.0.2')

    # 一个线程与联邦控制器建立连接，一个线程监听EBGP连接
    t1 = threading.Thread(target=controller.connect_to_fed_controller, args=('localhost', 211))
    t2 = threading.Thread(target=controller.ebgp_recieve_server, args=('localhost', 212))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    for speaker in controller.BGPspeakers:
        for key, value in controller.BGPspeakers[speaker].Routing_table.items():
            print(f'{speaker} routing table: {key} {value}')