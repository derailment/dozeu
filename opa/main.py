from config import *
from onos import TopoManager, IntentManager
import logging
import time

if __name__ == '__main__':
    """
    while True:
        topoManager = TopoManager()
        topoManager.get_topo()
        #topoManager.draw_topo()
        if topoManager.is_at_peak:
            intentManager = IntentManager()
            intentManager.reroute(topoManager.graph)
        else:
            time.sleep(POLLING_INTERVAL)
    """
    topoManager = TopoManager()
    topoManager.get_topo()
    intentManager = IntentManager()
    intentManager.reroute(topoManager.graph)
