#!/usr/bin/env python

from mininet.topo import Topo
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.link import TCLink
from config import *


class CustomTopo(Topo):
    def __init__(self, **opts):
        super(CustomTopo, self).__init__(**opts)
 
        s = [self.addSwitch('s%d' % n) for n in range(1, 4)]
        h = [self.addHost('h%d' % n, ip = '10.1.1.%d/24' % n) for n in range(1, 5)]
        link_bw = LINK_BANDWIDTH_LIMIT / 1000
        self.addLink(s[0], s[1], bw = link_bw)
        self.addLink(s[0], s[2], bw = link_bw)
        self.addLink(s[2], s[1], bw = link_bw)

        edge_bw = EDGE_BANDWIDTH_LIMIT / 1000
        self.addLink(h[0], s[0], bw = edge_bw)
        self.addLink(h[1], s[0], bw = edge_bw)
        self.addLink(h[2], s[1], bw = edge_bw)
        self.addLink(h[3], s[1], bw = edge_bw)


if __name__ == '__main__':
    net = Mininet(topo=CustomTopo(),
                  controller=RemoteController,
                  cleanup=True,
                  autoSetMacs=True,
                  link=TCLink)
    net.start()
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')

    p3 = h3.popen('iperf -s')
    p4 = h4.popen('iperf -s')
    p1 = h1.popen('iperf -c 10.1.1.3 -t 600 -b 8M')
    p2 = h2.popen('iperf -c 10.1.1.4 -t 600 -b 8M')

    CLI(net)    
    p1.terminate()
    p2.terminate()
    p3.terminate()
    p4.terminate()
    net.stop()
