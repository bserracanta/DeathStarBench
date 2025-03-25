import requests
import pandas as pd
import datetime
import time
import os
import argparse

# Prometheus URL
PROMETHEUS_URL = "http://localhost:30772"

# Define start and end times
parser = argparse.ArgumentParser(description="Prometheus data scraper")
parser.add_argument("--start", type=str, help="Start time in 'YYYYMMDD_HHMMSS' format")
parser.add_argument("--end", type=str, help="End time in 'YYYYMMDD_HHMMSS' format")
parser.add_argument("--folder", type=str, help="Output directory for CSV files")
args = parser.parse_args()
# start_t = "2025-03-11 12:40:43"
# end_t = "2025-03-11 12:57:51"
start_t = args.start
end_t = args.end
output_dir = args.folder

print(start_t)
print(end_t)


# Convert to UNIX timestamp
START_TIME = int(datetime.datetime.strptime(start_t, '%Y-%m-%d %H:%M:%S').timestamp())
END_TIME = int(datetime.datetime.strptime(end_t, '%Y-%m-%d %H:%M:%S').timestamp())

# Step interval (modify as needed)
STEP = "15s"

POD_MAPPING = {
    "compose.*": "compose_pods",
    "nginx-thrift.*": "nginx-thrift_pods",
    "text-service.*": "text-service_pods",
    "user-mention.*": "user-mention_pods"
}

# Queries for each plot
QUERIES = {
    "cpu_consumption": [
        'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="default", container=~"compose.*"}[3m]))',
        'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="default", container=~"nginx-thrift.*"}[3m]))',
        'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="default", container=~"text-service.*"}[3m]))',
        'sum by (service) (rate(container_cpu_usage_seconds_total{namespace="default", container=~"user-mention.*"}[3m]))'
    ],
    "cpu_utilization": [
        '(sum(rate(container_cpu_usage_seconds_total{namespace="default", container=~"compose.*"}[3m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="default", container=~"compose.*", service="kube-state-metrics"})) * 100',
        '(sum(rate(container_cpu_usage_seconds_total{namespace="default", container=~"nginx-thrift.*"}[3m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="default", container=~"nginx-thrift.*", service="kube-state-metrics"})) * 100',
        '(sum(rate(container_cpu_usage_seconds_total{namespace="default", container=~"text-service.*"}[3m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="default", container=~"text-service.*", service="kube-state-metrics"})) * 100',
        '(sum(rate(container_cpu_usage_seconds_total{namespace="default", container=~"user-mention.*"}[3m])) / sum(kube_pod_container_resource_limits{resource="cpu", namespace="default", container=~"user-mention.*", service="kube-state-metrics"})) * 100'
    ],
    "replica_count": [
        'count by (app) (kube_pod_info{pod=~"compose.*", app_kubernetes_io_instance="kube-state-metrics"})',
        'count by (app) (kube_pod_info{pod=~"nginx-thrift.*", app_kubernetes_io_instance="kube-state-metrics"})',
        'count by (app) (kube_pod_info{pod=~"text-service.*", app_kubernetes_io_instance="kube-state-metrics"})',
        'count by (app) (kube_pod_info{pod=~"user-mention.*", app_kubernetes_io_instance="kube-state-metrics"})'
    ]
}

# Function to query Prometheus
def query_prometheus(promql):
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        "query": promql,
        "start": START_TIME,
        "end": END_TIME,
        "step": STEP
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        return None

# Function to process results and save to CSV
def process_and_save(queries, filename):
    data_dict = {}
    timestamps = set()
    
    # Loop through queries
    for query in queries:
        result = query_prometheus(query)
        if not result or "data" not in result or "result" not in result["data"]:
            print(f"No data for query: {query}")
            return
        
        for metric in result["data"]["result"]:
            # Since there are no labels, assign manually from the query
            service_name = "unknown"
            for regex, pod_name in POD_MAPPING.items():
                if regex in query:
                    service_name = pod_name
                    break
            
            data_points = metric["values"]  # List of [timestamp, value]
            
            for ts, value in data_points:
                ts = int(ts)  # Convert timestamp to integer
                if ts not in data_dict:
                    data_dict[ts] = {}
                data_dict[ts][service_name] = float(value)
                timestamps.add(ts)
    
    # Convert to DataFrame
    timestamps = sorted(timestamps)
    df = pd.DataFrame([{**{"timestamp": ts}, **data_dict.get(ts, {})} for ts in timestamps])
    
    # Convert timestamp to readable format
    df["timestamp"] = df["timestamp"].apply(lambda x: datetime.datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    
    # Save to CSV

    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/{filename}"
    df.to_csv(output_path, index=False)
    print(f"Saved: {filename}")

# Run for each plot
process_and_save(QUERIES["cpu_consumption"], f"cpu_consumption_{START_TIME}.csv")
process_and_save(QUERIES["cpu_utilization"], f"cpu_utilization_{START_TIME}.csv")
process_and_save(QUERIES["replica_count"], f"replica_count_{START_TIME}.csv")