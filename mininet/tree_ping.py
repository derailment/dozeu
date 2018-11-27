from topos.tree import TreeTopo 
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import Host
from mininet.node import RemoteController
from random import randint
from functools import partial
from mininet.cli import CLI

def test(d, f):
    "Create and test a tree network"
    topo = TreeTopo(depth=d, fanout=f)
    net = Mininet(topo=topo, controller=partial(RemoteController, ip='127.0.0.1', port=6653))
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    print "Broadcasting gratuitous ARP"
    # Choose any two of hosts
    h_num = len(net.hosts)
    h1_id = randint(1, h_num)
    h2_id = randint(1, h_num)
    while True:
      if h2_id != h1_id:
        break
      h2_id = randint(1, h_num)  
    h1 = net.get('h%d' % h1_id)
    h2 = net.get('h%d' % h2_id)
    h1_arp_res = h1.cmd('arping -U -c 1 -I h%d-eth0 255.255.255.255' % h1_id)
    h2_arp_res = h2.cmd('arping -U -c 1 -I h%d-eth0 255.255.255.255' % h2_id)
    print h1_arp_res
    print h2_arp_res
    print "Testing network connectivity"
    #net.pingAll()
    h1.sendCmd('ping -c 10 ' + h2.IP())
    print h1.waitOutput()
    h2.sendCmd('ping -c 10 ' + h1.IP())
    print h2.waitOutput()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    test(4, 2)


