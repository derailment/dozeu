from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.node import Host
from mininet.node import RemoteController
from random import randint
from functools import partial
import threading
import time
from subprocess import PIPE

def sendUDP(client, server, bandwidth, times):
    print 'Child thread: %s is sending UDP datagrams to %s (T-%s=%d)' % (client.name, server.name, client.name, time.time())
    print client.cmd('iperf -u -c %s -t %d -b %s -i 1' % (server.IP(), times, bandwidth))

class CustomRing(Topo):
    "Build custom ring topology"
    def build(self, s_num=22):
        switches = [None] * s_num
        for i in range(s_num):
            switches[i] = self.addSwitch('s%d' % (i + 1))    
        for i in range(s_num):    
            if i != s_num-1:
                self.addLink(switches[i], switches[i+1], bw=10)
            else:
                self.addLink(switches[i], switches[0], bw=10)
        h2 = self.addHost('h%d' % 2, ip='10.1.1.2/24')     
        self.addLink(switches[0], h2, bw=1000)
        h3 = self.addHost('h%d' % 3, ip='10.1.1.3/24')     
        self.addLink(switches[0], h3, bw=1000)
        h4 = self.addHost('h%d' % 4, ip='10.1.1.4/24')     
        self.addLink(switches[0], h4, bw=1000)
        h1 = self.addHost('h%d' % 1, ip='10.1.1.1/24')     
        self.addLink(switches[11], h1, bw=1000)   

def test(out):
    "Create a test network"
    topo = CustomRing()
    net = Mininet(topo=topo, controller=partial(RemoteController, ip='127.0.0.1', port=6653), link=TCLink)
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    
    print "Broadcasting gratuitous ARP"
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')
    s1 = net.get('s1')
    s12 = net.get('s12')
    print h1.cmd('arping -U -c 1 -I h1-eth0 255.255.255.255')
    print h2.cmd('arping -U -c 1 -I h2-eth0 255.255.255.255')
    print h3.cmd('arping -U -c 1 -I h3-eth0 255.255.255.255')
    print h4.cmd('arping -U -c 1 -I h4-eth0 255.255.255.255')
        
    # h1 is UDP server
    fout = open(out, 'w')
    proc1 = h1.popen('iperf -u -s -t 120 -i 1 ', stdout=PIPE, stderr=PIPE)
    proc2 = h1.popen('ts %s', shell=True, stdin=proc1.stdout, stdout=fout, stderr=fout)

    # h2, h3, h4 are UDP clients sending datagrams to h1
    h2_thread = threading.Thread(target=sendUDP, args=(h2, h1, '10M', 60))         
    h3_thread = threading.Thread(target=sendUDP, args=(h3, h1, '10M', 40))        
    h4_thread = threading.Thread(target=sendUDP, args=(h4, h1, '10M', 20))         
    
    h2_thread.start()
    time.sleep(20)
    h3_thread.start()
    time.sleep(20)
    h4_thread.start()
    time.sleep(10)
    
    # Add link between s1 and s12
    print 'Main thread: %s connects to %s (T-link=%.2f)' % (s1.name, s12.name, time.time())
    net.addLink(s1, s12, bw=10)
    time.sleep(10)
    
    h2_thread.join()
    h3_thread.join()
    h4_thread.join()
    proc1.terminate()
    proc2.terminate()

    #CLI( net )
    net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    test('iperf_server.out')
    
