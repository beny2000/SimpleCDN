import os
import json
import random
import logging
import requests
from shapely.geometry import Point
from flask import Flask, redirect, request

PORT = os.environ.get("PORT")
PROXY_PORTS = os.environ.get("PROXIES")
DEFAULT_PATH = os.environ.get("DEFAULT_PATH")
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.StreamHandler()])


app = Flask(__name__)
servers = {str(i): (f"http://localhost:{port}/", 37.7749, -122.4194)
           for i, port in enumerate(PROXY_PORTS.split(","))}


def get_IP_location(ip_address):
    """
    Returns the latitude and longitude of the IP address

    :param ip_address: The IP address to get the location of
    :return: A tuple of latitude and longitude
    """

    request_url = 'https://geolocation-db.com/jsonp/' + ip_address
    response = requests.get(request_url)

    result = response.content.decode()
    result = result.split("(")[1].strip(")")
    result = json.loads(result)
    logging.info(f"Request from: {result}")
    return result['latitude'], result['longitude']


def get_closest_server(ip):
    """
    Finds the closest server to that IP address, returns the URL of that
    server

    :param ip: The IP address of the client
    :return: The url of the closest server to the client.
    """
    client_longitude, client_latitude = get_IP_location(ip)
    client_location = Point(client_longitude, client_latitude)
    closest_server = None
    min_distance = float('inf')

    for server, (url, lat, long) in servers:

        server_location = Point(lat, long)
        distance = client_location.distance(server_location)

        if distance < min_distance:
            closest_server = url
            min_distance = distance

    return closest_server


def get_server(req):
    """
    Returns proxy associated with the query string 'area', if not 'area' specified returns a random server

    :param req: The request object
    :return: A proxy server
    """
    if req.args.get('area'):
        proxy = servers[req.args.get('area')][0]
    else:
        # proxy = get_closest_server(req.remote_addr) # enable on public network to geographically select a proxy
        proxy = random.choice([i[0] for i in servers.values()])

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
