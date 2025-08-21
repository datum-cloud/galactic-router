FROM python:3

COPY src src
COPY pyproject.toml .

RUN pip install -e .

ENTRYPOINT ["galactic-router"]
