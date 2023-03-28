from flask import Flask, redirect
import random

app = Flask(__name__)

# Define a list of available servers
servers = [
    "http://localhost:5000/",
    "http://localhost:5001/",
]

# Define a route for the load balancer
@app.route('/<path:path>')
def serve_GET(path):
    # Choose a server from the list of available servers
    server = random.choice(servers)
    # Redirect the request to the chosen server
    return redirect(server + path)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8000)
