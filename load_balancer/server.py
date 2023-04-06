import os
import json
import random
import logging
import requests
import itertools
from shapely.geometry import Point
from flask import Flask, redirect, request

PORT = os.environ.get("PORT")
NUM_AREAS = int(os.environ.get("NUM_AREAS"))
DEFAULT_PATH = os.environ.get("DEFAULT_PATH")
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])


app = Flask(__name__)
areas = [os.environ.get(f"AREA{i}_PROXIES") for i in range(1, NUM_AREAS+1)]
servers = {str(i+1): itertools.cycle([f"http://localhost:{port}/" for port in area.split(",")]) for i, area in enumerate(areas)}


def get_server(req):
    """
    Returns proxy associated with the query string 'area', if not 'area' specified returns a the next server in a random area

    :param req: The request object
    :return: A proxy server
    """
    if req.args.get('area'):
        area_proxies = servers[req.args.get('area')]
        proxy = next(area_proxies)
    else:
        area = random.choice([key for key in servers.keys()])
        proxy = next(servers[area])

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
    logging.info(f"Load Balancer start on port {PORT}")
    app.run(debug=False, host="0.0.0.0", port=PORT)
