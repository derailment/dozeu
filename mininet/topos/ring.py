from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import Host
from mininet.node import RemoteController
from random import randint
from functools import partial

class RingTopo(Topo):
  "Build ring topology"
  def build(self, s_num=20):
    switches = [None] * s_num
    hosts = [None] * s_num
    for i in range(s_num):
      switches[i] = self.addSwitch('s%d' % (i + 1))     
      hosts[i] = self.addHost('h%d' % (i + 1), ip='10.1.1.%d/24' % (i + 1))     
      self.addLink(switches[i], hosts[i])
    for i in range(s_num):    
      if i != s_num-1:
        self.addLink(switches[i], switches[i+1])
      else:
        self.addLink(switches[i], switches[0])
