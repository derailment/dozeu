from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.net import Mininet
from functools import partial
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections
from mininet.util import irange
from mininet.cli import CLI
import time

class CustomLinear( Topo ):
    "Linear topology of k switches, with n hosts per switch."
    def build( self, k=10, **_opts):
        lastSwitch = None
        for i in irange( 1, k ):
            # Add switch
            switch = self.addSwitch( 's%s' % i )
            # Connect switch to previous
            if lastSwitch:
                self.addLink( lastSwitch, switch, port1=i * 2 - 3, port2=i * 2 - 2 )
            lastSwitch = switch
            # Add host to switch
            host = self.addHost( 'h%s' % i, ip='10.1.1.%d/24' % i )
            self.addLink( host, switch, port1 = i + 10, port2 = i + 20 )

def test(s_num, h1_id, h2_id):
    "Create a test network"
    topo = CustomLinear(s_num)
    net = Mininet(topo=topo, controller=partial(RemoteController, ip='127.0.0.1', port=6653))
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    
    print "Broadcasting gratuitous ARP"
    h1 = net.get('h%d' % h1_id)
    h2 = net.get('h%d' % h2_id)
    print h1.cmd('arping -U -c 1 -I h%d-eth1%d 255.255.255.255' % (h1_id, h1_id))
    print h2.cmd('arping -U -c 1 -I h%d-eth1%d 255.255.255.255' % (h2_id, h2_id))
    
    # Test bandwidth
    # h1 is UDP client; h2 is UDP server
    print "T0=%f" % time.time()
    net.iperf(hosts=[h1, h2], udpBw='50K', seconds=30, l4Type='UDP')
    print "T1=%f" % time.time()

    #CLI( net )
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    test(s_num=4, h1_id=1, h2_id=4)


