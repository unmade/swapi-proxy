# SWAPI Proxy

A generic proxy service. By default configured to proxy to [SWAPI][SWAPI].

## Quickstart

### Running with Docker

The fastest and easiest to run the project is using [Docker][Docker]:

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

## Notes on implementation

_TBD_

[Docker]: https://www.docker.com
[python.org]: https://www.python.org/downloads/
[SWAPI]: https://swapi.dev
