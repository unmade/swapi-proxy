# stage: build
FROM python:3.12-slim as builder

RUN python -m venv /opt/.venv

ENV PATH="/opt/.venv/bin:$PATH" \
    PIP_CACHE_DIR=/root/.cache/pip

WORKDIR /home/datasnipper/swapi-proxy

COPY ./requirements/base.txt ./requirements/

RUN --mount=type=cache,target=$PIP_CACHE_DIR pip install -r requirements/base.txt


# stage: test
FROM python:3.12-slim as tester

ENV VIRTUAL_ENV=/opt/.venv \
    PATH="/opt/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /home/datasnipper/swapi-proxy
COPY ./requirements/test.txt ./requirements/

RUN pip install -r requirements/test.txt

COPY ./.coveragerc ./
COPY ./src ./src
COPY ./tests ./tests

CMD ["pytest", "--cov", "-m", "not redis"]


# stage: api
FROM python:3.12-slim as api

RUN addgroup teamdatasnipper --gid 1000 && \
    useradd datasnipper --uid 1000 --gid teamdatasnipper --home-dir /home/datasnipper/

ENV VIRTUAL_ENV=/opt/.venv \
    PATH="/opt/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /home/datasnipper/swapi-proxy

COPY ./README.md ./
COPY --chown=datasnipper:teamdatasnipper ./src ./src

USER datasnipper
ENTRYPOINT ["fastapi", "run", "src/api/main.py"]
