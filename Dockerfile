FROM python:3.8-slim-buster

RUN apt-get update && \
    apt-get install -y libpq-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir psycopg2-binary alembic

WORKDIR /usr/src/bugout/brood

COPY . /usr/src/bugout/brood

RUN pip3 install --no-cache-dir -e .

EXPOSE 7474

ENTRYPOINT ["./dev.sh"]