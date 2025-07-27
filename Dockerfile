FROM python:3.13.3-alpine

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
COPY uv.lock ./


COPY . .

CMD [ "uv", "sync" ]
