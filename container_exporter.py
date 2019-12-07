#docker run --rm -it -m 10m --network="summit_default" -v $(pwd):/app summit_webapp /bin/bash

import requests
import json
import os

from flask import Flask


# Prometheus server
HOST = "prometheus2"
PORT = "9090"
BASE = '{}://{}:{}'.format('http', HOST, PORT)
PROM_QUERY_ENDPOINT = BASE + '/api/v1/query'

# Target container
CONTAINER_NAME  = os.getenv('CONTAINER_NAME',  "cadvisor")
PROMETHEUS_HOST = os.getenv('PROMETHEUS_HOST', HOST)
PROMETHEUS_PORT = os.getenv('PROMETHEUS_PORT', PORT)

def exec_query(query):
    # HTTP request
    params  = { 'query': query }
    r = requests.get(PROM_QUERY_ENDPOINT, params)

    # response
    if r.status_code != 200:
        print("Prometheus reply with HTTP code", r.status_code)

    return json.loads(r.text)


def collect_metrics(container_name):
    '''
    Collects container metrics from Prometheus using the HTTP API 
    '''
    metrics = {}

    # Collect memory metrics: 
    #   container_spec_memory_limit_bytes: container memory limit (when specified)
    #   container_memory_usage_bytes:      container current memory usage including all memory regardless of when it was accessed
    query = '''
        {{__name__=~"(container_memory_usage_bytes|container_spec_memory_limit_bytes)", name="{}"}} or
        {{__name__=~"machine_memory_bytes"}}
    '''.format(container_name)

    res = exec_query(query)

    metrics = { m['metric']['__name__']: int(m['value'][1]) for m in res['data']['result'] }
    
    # Identify total memory available     
    total_memory = 0
    if metrics['container_spec_memory_limit_bytes'] == 0:   # if no limit is set,
        total_memory = metrics['machine_memory_bytes']        # the max memory is the machine_memory
    else:
        total_memory = metrics['container_spec_memory_limit_bytes']
        
    # Add percentage of memory used
    metrics['container_pct_memory'] = round(metrics['container_memory_usage_bytes'] / total_memory * 100,2)

    # Collect CPU usage
    query = '''
        sum(rate(container_cpu_usage_seconds_total{{name="{}"}}[1m]))*100
    '''.format(container_name)

    res = exec_query(query)['data']['result'][0]

    cpu_usage = float(res['value'][1])
    metrics['container_cpu_usage'] = round(cpu_usage, 2)

    return metrics



# Flask app
app = Flask(__name__)

@app.route('/')
def default():
    return collect_metrics(CONTAINER_NAME)
    

@app.route('/metrics')
def metrics():
    metrics = ''
    for m in collect_metrics(CONTAINER_NAME).items():
        metrics +=  '{} {} \n'.format(m[0], m[1])
    return metrics


    
