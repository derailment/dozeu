import json
from config import ONOS_IP, ONOS_PORT
from utils import json_get_req, json_post_req
import logging

data = {'paths': [
    {'path': ["00:00:00:00:00:02/None", "of:0000000000000001", "of:0000000000000002", "00:00:00:00:00:04/None"]},
    {'path': ["00:00:00:00:00:04/None", "of:0000000000000002", "of:0000000000000001","00:00:00:00:00:02/None"]}
  ]
}

reply = json_post_req('http://%s:%d/reroute' % (ONOS_IP, ONOS_PORT), json.dumps(data))
print reply

reply = json_get_req('http://%s:%d/bandwidth/topology' % (ONOS_IP, ONOS_PORT))
print reply

reply = json_get_req('http://%s:%d/bandwidth/connections' % (ONOS_IP, ONOS_PORT))
print reply
