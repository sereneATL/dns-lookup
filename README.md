# Interview challenge

## Tech stack
- Python
- FastAPI
- Postgresql
- Prometheus
- Docker

## Getting started
At the root of the project, create a `.env` file and copy over the variables from `.env.sample`. Replace these sample values with your own values i.e. database user, database password, etc. 

To run the application, run the following command at the root
```
docker-compose up -d --build
```
To gracefully stop the running containers, run the following command at the root
```
docker-compose down
```

## Documentation
### Swagger
Generated Swagger documentation with UI is served at `/docs`

Assuming you have the containers up and running in your localhost, this URL can be found at:
```
http://localhost:3000/docs
```
### OpenAPI
Generated OpenAPI schema is served at `/v1/openapi.json`

Assuming you have the containers up and running in your localhost, this URL can be found at:
```
http://localhost:3000/v1/openapi.json
```

## Prometheus
Prometheus UI is served at port `9090`

When the containers are up and running, this URL can be found at:
```
http://localhost:9090/
```
Otherwise, prometheus metrics can be found at `http://localhost:3000/metrics`

## Access logs
Logging is performed for every request to the FastAPI application via middleware, with a unique trace ID for each request, and can be accessed via docker logs


