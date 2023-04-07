import os
import re
import json
import time
import random
import logging
import requests
import itertools
from threading import Thread
from flask import Flask, redirect, request

PORT = os.environ.get("PORT")
NUM_AREAS = int(os.environ.get("NUM_AREAS"))
DEFAULT_PATH = os.environ.get("DEFAULT_PATH")
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])


app = Flask(__name__)
areas = [os.environ.get(f"AREA{i}_PROXIES").split(",") for i in range(NUM_AREAS)]
servers = {str(i): itertools.cycle([f"http://localhost:{port}/" for port in area]) for i, area in enumerate(areas)}
liveliness = {f"http://localhost:{port}/": False for area in areas for port in area}
proxies = [f'http://proxy{idx}.{i}:{area[i]}/' for idx, area in enumerate(areas) for i in range(len(area))]


def check_liveliness(proxies, liveliness):
    """
    Checks the liveliness of a list of proxies by sending requests to them and updates
    the liveliness dictionary
    """

    while True:
        for addr in proxies:
            try:
                alive = requests.get(addr + 'heartbeat').text
                liveliness[re.sub(r"http://proxy([0-9].[0-9]):([0-9]+)/", 
                              r"http://localhost:\2/", addr)] = True if str(alive) == 'OK' else False
            except Exception:
                liveliness[re.sub(r"http://proxy([0-9].[0-9]):([0-9]+)/", 
                              r"http://localhost:\2/", addr)] = False


def get_server(req):
    """
    Selects a proxy server based on the given area ID or a random one (if area ID not passed), and
    checks if it is alive before returning it. If its dead it will try all proxies in that area.
    If that area is dead then it will try the other areas
    
    :param req: The request object that contains the area ID of the incoming request
    :return: a proxy server to handle a request.
    """
    area_id = req.args.get('area')
    if not area_id:
        area_id = random.choice([key for key in servers.keys()])

    area_retry_count = 0
    while area_retry_count <= len(areas):
        area_proxies = servers[area_id]
        proxy = next(area_proxies)

        # return proxy if it is alive
        if liveliness[proxy]:
            return proxy
        logging.warning(f'Proxy {proxy} is dead')

        # try the next proxies in the area
        proxy_retry_count = 1
        while proxy_retry_count <= len(areas[int(area_id) - 1]):
            proxy = next(area_proxies)
            proxy_retry_count += 1

            if liveliness[proxy]:
                return proxy
            
            
        # no proxy in the area is alive then try proxies in the next area
        logging.warning(f'Area {area_id} is dead')
        area_retry_count += 1
        area_id = str(((int(area_id) + 1) % len(areas))) 

    logging.info(f'Routing request to {proxy}')
    return proxy



@app.route('/')
def serve_main():
    """
    Redirects request for no file to the default path
    :return: A redirect to the proxy with the default path.
    """
    server = get_server(request)
    return redirect(server + DEFAULT_PATH)


@app.route('/<path:path>')
def serve_GET(path):
    """
    Redirect to the "closest" proxy server that has the file

    :param path: The path of the file requested
    :return: A redirect to the proxy
    """

    server = get_server(request)
    return redirect(server + path)


if __name__ == "__main__":
    th = Thread(target=check_liveliness, args=(proxies, liveliness,))
    th.start()

    logging.info(f"Starting Load Balancer on port {PORT}")
    app.run(debug=False, host="0.0.0.0", port=PORT)
