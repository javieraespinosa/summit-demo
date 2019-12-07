
FROM python:3.6-slim

RUN apt-get update; \
	apt-get install -y --no-install-recommends wget

WORKDIR /prometheus
RUN wget https://github.com/prometheus/node_exporter/releases/download/v0.18.1/node_exporter-0.18.1.linux-amd64.tar.gz \
 && tar xvfz node_exporter-*.*-amd64.tar.gz \
 && rm node_exporter-*.*-amd64.tar.gz \
 && mv node_exporter*  node_exporter

WORKDIR /app
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

