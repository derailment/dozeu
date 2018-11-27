from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import Host
from mininet.node import RemoteController
from random import randint
from functools import partial
from mininet.util import irange

class LinearTopo( Topo ):
    "Linear topology of k switches, with n hosts per switch."
    def build( self, k=10, **_opts):
        lastSwitch = None
        for i in irange( 1, k ):
            # Add switch
            switch = self.addSwitch( 's%s' % i )
            # Add host to switch
            host = self.addHost( 'h%s' % i, ip='10.1.1.%d/24' % i )
            self.addLink( host, switch )
            # Connect switch to previous
            if lastSwitch:
                self.addLink( switch, lastSwitch )
            lastSwitch = switch
