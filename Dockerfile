FROM python:3.10-slim

WORKDIR /api

RUN pip install -q poetry

COPY poetry.lock pyproject.toml ./

RUN poetry install -n

COPY . .

CMD [ "/api/scripts/run_server.sh" ]
