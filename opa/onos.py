import matplotlib.pyplot as plt
from config import *
import networkx as nx
from utils import json_get_req, json_post_req
import json
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
            #test
            print 'cp of link bw:', bw
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
        self.__conns = []
        self.__reroute_msg = {'paths': []}

    def __get_conns(self):
        reply = json_get_req('http://%s:%d/bandwidth/connectivity' % (ONOS_IP, ONOS_PORT))
        return sorted(reply['connectivities'], key = lambda k: k['bw'], reverse = True)
        
    def reroute(self, topo):
        self.__conns = self.__get_conns()
        for conn in self.__conns:
            _topo = topo
            n1 = conn['one']
            n2 = conn['two']
            bw = conn['bw']
            #test 
            print '<', n1, n2, 'bw:', bw, '>'
            while True:
                path, reduced_topo = self.__find_path(n1, n2, bw, _topo)
                if reduced_topo == None:
                    # found no path in this connectivity; do nothing
                    break
                elif path == None:
                    # found path that has insufficient capacity; find another path on reduced topology
                    _topo = reduced_topo
                    continue
                else:
                    self.__reroute_msg['paths'].append({'path': path})
                    topo = self.__reduce_capacity_on_path(path, topo, bw)
                    break
        #test
        print self.__reroute_msg['paths'][0:]
        
        self.__send_paths(self.__reroute_msg)
        
    def __find_path(self, n1, n2, bw, topo):
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
            logging.info("No path found: %s, %s", n1, n2)
            return (None, None)

    def __reduce_capacity_on_path(self, path, reduced_topo, bw):
        for link in zip(path, path[1:]):
            src = link[0]
            dst = link[1]
            reduced_topo[src][dst]['bandwidth'] -= bw
        return reduced_topo
   
    def __send_paths(self, reroute_msg):
        # add paths in reverse direction
        reversed_paths = []
        routes = reroute_msg['paths']
        for route in routes:
            reversed_path = {'path': route['path'][::-1]}
            if reversed_path not in routes:  
                reversed_paths.append(reversed_path)
        routes.extend(reversed_paths)   
        # send paths for rerouting   
        reply = json_post_req('http://%s:%d/reroute' % (ONOS_IP, ONOS_PORT), json.dumps(reroute_msg))
        if reply != '':
            logging.info('Reroute: %s', reply)
