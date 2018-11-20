import json
from config import ONOS_IP, ONOS_PORT
from utils import json_get_req, json_post_req
import logging

data = {'paths': []}
reply = json_post_req('http://%s:%d/reroute' % (ONOS_IP, ONOS_PORT), json.dumps(data))
print reply

reply = json_get_req('http://%s:%d/topology' % (ONOS_IP, ONOS_PORT))
print reply

reply = json_get_req('http://%s:%d/bandwidth' % (ONOS_IP, ONOS_PORT))
print reply
