# Simple Primary Backup CDN

## Running the project
1. Install [Docker](https://docs.docker.com/get-docker/)
2. Run `docker compose up`
3. Go to `http://localhost:8000/test_file.html`


- Implement a simple cdn web server using a Primary Backup model, that can be used to host any kinds of files.

- The primary acts as a load balancer that redirects incoming requests to a backup server
    - Redirects requests to a backup server that is "close" to the requesting client/user
    - Should be an http server that redirects requests to a backup
    - Must know locations (ports) of backup servers
    
- The backup server acts as a proxy cache for the origin server.
    - If the backup has stored the requested file then it serves the stored file
    - otherwise calls the to the origin server to serve the requested file
    - Should be an http server that either serves the file or maps the request to the grpc get method
    - Must know location (port) of origin server

- The origin server stores the original file
  - Returns the original file when requested by a backup
  - Should be a grpc server

- The backup and origin server share a proto file that defines the messages
  - https://github.com/gooooloo/grpc-file-transfer (example file transfer in grpc)

- Extra Features
  - UI for uploading files to the origin server
  - Failure handling and fault tolerance for primary and backup servers