from config import *
from onos_opa import TopoManager, IntentManager
import logging
import time
import optparse

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("--one-shot", action="store_true", dest="oneshot", default=False, help="poll only once")
    (options, args) = parser.parse_args()
    if not options.oneshot:
        while True:
            topoManager = TopoManager()
            topoManager.get_topo()
            #topoManager.draw_topo()
            if topoManager.is_congestion:
                logging.info("Detect traffic congestion...")
                intentManager = IntentManager()
                intentManager.reroute(topoManager.graph)
            else:
                logging.info("Traffic is light...")
                time.sleep(POLLING_INTERVAL)
    else:
        topoManager = TopoManager()
        topoManager.get_topo()
        intentManager = IntentManager()
        intentManager.reroute(topoManager.graph)
