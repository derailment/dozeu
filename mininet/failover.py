from topos.ring import RingTopo
from mininet.log import setLogLevel
from mininet.net import Mininet
from functools import partial
from mininet.node import RemoteController
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
import time
import threading

def sendUDP(client, server, message):
    for i in range(40):
        print 'Child thread:',
        print client.cmd('sudo python tools/udpclient.py -i %s -m %s' % (server.IP(), message)) 
        time.sleep(1)

def changeLink(timing, net):
    experiments = {
        5: ('s2', 's3', 'down'),
        15: ('s2', 's3', 'up'),
        20: ('s4', 's5', 'down'),
        30: ('s4', 's5', 'up')
    }
    args = experiments.get(timing)
    if args is not None:
        net.configLinkStatus(args[0], args[1], args[2])

def test(s_num, h1_id, h2_id, out, msg):
    "Create a test network"
    topo = RingTopo(s_num)
    net = Mininet(topo=topo, controller=partial(RemoteController, ip='127.0.0.1', port=6653))
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    
    print "Broadcasting gratuitous ARP"
    h1 = net.get('h%d' % h1_id)
    h2 = net.get('h%d' % h2_id)
    print h1.cmd('arping -U -c 1 -I h%d-eth0 255.255.255.255' % h1_id)
    print h2.cmd('arping -U -c 1 -I h%d-eth0 255.255.255.255' % h2_id)
    
    # h2 is UDP server  
    print "UDP server (%s) is listening..." % h2.IP()
    p2 = h2.popen('sudo python tools/udpserver.py -i %s -f %s &' % (h2.IP(), out))
        
    # h1 is UDP client sending message to h2
    c_thread = threading.Thread(target=sendUDP, args=(h1, h2, msg)) 
    c_thread.start()

    # Up or down a link within network  
    for i in range(40):
        print 'Main thread:', 'This might change a link within the network.' 
        changeLink(i + 1, net)
        time.sleep(1)

    # Count number of UDP datagrams h2 received
    c_thread.join()
    p2.terminate()
    udp_num = int(h2.cmd('grep -cow %s %s' % (msg, out)))
    print 'h2 received %d UDP datagrams' % udp_num,
    if udp_num >= 30:
        print '(>= 30), failover testing passed.'
    else:
        print '(< 30), failover testing failed.'
    
    CLI( net )
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    test(s_num=5, h1_id=2, h2_id=3, out='bar.out', msg='Hello')


