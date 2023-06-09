# Simple CDN Web Server

- Implements a simple cdn web server using a Primary Backup model, that can be used to host any kinds of files.

- The load_balancer acts as a geographic load balancer that redirects incoming requests to a proxy server
    - Redirects requests to a proxy server that is "close" to the requesting client/user
    - Should be an http server that redirects requests to a proxy
    - Must know locations (ports) of proxy servers
    
- The proxy server acts as a cache for the origin server.
    - If the proxy has stored the requested file then it serves the stored file
    - otherwise calls the to the origin server to serve the requested file
    - Should be an http server that either serves the file or maps the request to the grpc get method
    - Must know location (port) of origin server

- The origin server stores the original file
  - Returns the original file when requested by a proxy
  - Should be a grpc server

### CDN Sequence Diagram
![CDN Sequence Diagram](origin/files/cdn_diagram.png)

- The proxy and origin server share a proto file that defines the messages

- Extra Features
  - UI for uploading files to the origin server
  - Failure handling and fault tolerance for load_balancer and proxy servers

## Setting up the CDN network
- The `docker-compose.yml` file specifies the configuration for each server. Each server is run in its own container that represents a machine/server rack its running in on the network
- The `.env` file specifies the ports for each server
- Add the ports and service definitions in the `.env` & `docker-compose.yml` file to add more servers


## Running the network
1. Install [Docker](https://docs.docker.com/get-docker/)
2. Run `docker compose up -d`
3. Go to `http://localhost:8000/test_file.html`
4. Upload files to origin with `python UI/UI.py`
4. Stop servers with `docker compose down --rmi all`
