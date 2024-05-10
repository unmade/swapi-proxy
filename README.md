# SWAPI Proxy

A generic proxy service configured to proxy to [SWAPI][SWAPI] by default.

The service can act as a proxy to any service. By default it set up to proxy
to [SWAPI][SWAPI]. Available services can be set by providing a `SERVICES`
environment variable, see [.env](.env). The value of the variable is a list
of objects, where each object has the following schema:

| field   | type    | default | description |
| :-----: | :-----: | :-----: | :---------: |
| name    | string  | -       | a unique name for the service, that will be used as prefix in endpoint |
| host    | string  | -       | a base url of the service (e.g. https://swapi.dev/api) |
| timeout | number  | 30.0    | a default timeout for all requests to that service |
| rate_limit        | number | 100 | maximum number of requests that can be made within a `rate_limit_period` |
| rate_limit_period | number | 3600 | duration in seconds within which the maximum number of requests can be made |
| max_concurrent_requests | number | 10 | maximum concurrent requests during aggregated requests |

Note, that rate limits are defined per each service individually.

The `max_concurrent_requests` limits the maximum number of concurrent requests
during aggregated calls. For example, if client wants to aggregate 20 calls and
`max_concurrent_requests` set to 10, then there will be at most 10 parallel
requests to the upstream service.

## Quickstart

### Running with Docker

The fastest and easiest way to run the project is using [Docker][Docker]:

```bash
docker compose up
```

By default that starts the project on `8000` port.

An example of a single proxy request:

```bash
curl -X 'GET' 'http://localhost:8000/proxy/swapi/films/1' -H 'accept: application/json'
```

To request multiple resource in a single call:

```bash
curl -X 'POST' 'http://localhost:8000/proxy_batch/swapi' \
    -H 'Content-Type: application/json' \
    --data '{"items": [{"path": "/films/1"}, {"path": "/films/2"}]}'
```

Note, this endpoint supports only aggregation only on GET resources.

#### Testing

You can test the project using the advantages of Docker multi-stage builds:

```bash
docker build -t proxy-tester --target tester .
docker run --rm proxy-tester
```

Note, that this way tests that require redis will be excluded from the run.

### Running locally

Make sure you have the latest [python 3.12][python.org] installed.

Recommended way is to create a new virtual and install dependencies:

```bash
python3.12 -m venv .venv
pip install -r requirements/base.txt -r requirements/test.txt -r requirements/lint.txt -r requirements/dev.txt
```

After that you can start the development.

To run the development server:

```bash
fastapi dev src/api/main.py
```

To test the project:

```bash
pytest --cov
```

To run linters:

```bash
pre-commit run --all-files
```

[Docker]: https://www.docker.com
[python.org]: https://www.python.org/downloads/
[SWAPI]: https://swapi.dev
