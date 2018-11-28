import matplotlib.pyplot as plt
from config import *
import networkx as nx
from utils import json_get_req
import logging

class TopoManager(object):
    
    def __init__(self):
        self.graph = nx.Graph()
        self.is_at_peak = False
        # arguments for drawing topology
        self.__pos = None
        self.__hosts = []
        self.__devices = []
    
    def get_topo(self):
        reply = json_get_req('http://%s:%d/bandwidth/topology' % (ONOS_IP, ONOS_PORT))
        for link in reply['links']:
            n1 = link['src']
            n2 = link['dst']
            bw = link['bw'] # unit: Kbps
            if (bw > BANDWIDTH_THRESHOLD * LINK_BANDWIDTH_LIMIT):
                self.is_at_peak = True
            self.__devices.append(n1)     
            self.__devices.append(n2)
            self.graph.add_node(n1, type='device')
            self.graph.add_node(n2, type='device')
            self.graph.add_edge(n1, n2, **{'bandwidth': LINK_BANDWIDTH_LIMIT})
        for edge in reply['edges']:
            n1 = edge['host']
            n2 = edge['location']
            if n1 not in self.__hosts:
                self.__hosts.append(n1)
                self.graph.add_node(n1, type='host')
                self.graph.add_edge(n1, n2, **{'bandwidth': EDGE_BANDWIDTH_LIMIT})

    def draw_topo(self, block=True):
        self.__pos = nx.fruchterman_reingold_layout(self.graph)      
        plt.figure()
        nx.draw_networkx_nodes(self.graph, self.__pos, nodelist=self.__hosts, node_shape='o', node_color='w')
        nx.draw_networkx_nodes(self.graph, self.__pos, nodelist=self.__devices, node_shape='s', node_color='b')
        nx.draw_networkx_labels(self.graph.subgraph(self.__hosts), self.__pos, font_color='k')
        nx.draw_networkx_labels(self.graph.subgraph(self.__devices), self.__pos, font_color='k')
        nx.draw_networkx_edges(self.graph, self.__pos)
        plt.show(block=block)

class IntentManager(object):

    def __init__(self):
        self.__conns = self.__get_conns()
        self.__paths = []

    def __get_conns(self):
        reply = json_get_req('http://%s:%d/bandwidth/connections' % (ONOS_IP, ONOS_PORT))
        return sorted(reply['connections'], key = lambda k: k['bw'], reverse = True)
        
    def reroute(self, topo):
        path, reduced_topo = self.__find_path(self.__conns[0], topo)
        
    def __find_path(self, conn, topo):
        n1 = conn['one']
        n2 = conn['two']
        bw = conn['bw']
        try:
            reduced_topo = topo.copy()
            is_bad_path = False
            path = nx.shortest_path(reduced_topo, n1, n2)
            for link in zip(path, path[1:]):
                src = link[0]
                dst = link[1]
                reduced_topo[src][dst]['bandwidth'] -= bw
                if reduced_topo[src][dst]['bandwidth'] <= 0:
                    reduced_topo.remove_edge(src, dst)
                    is_bad_path = True              
            if is_bad_path == True:
                return (None, reduced_topo)
            else:
                return (path, reduced_topo)
        except nx.NetworkXNoPath:
            logging.warning("no path found between " + n1 + ' and ' + n2)
            return (None, None)

