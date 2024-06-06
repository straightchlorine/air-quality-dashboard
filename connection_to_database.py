import json
from influxdb_client import InfluxDBClient
import csv
import os
import time

columns_order = [
    'time',
    'aceton',
    'alcohol',
    'altitude',
    'co',
    'co2',
    'humidity',
    'nh4',
    'pressure',
    'seaLevelPressure',
    'temperature',
    'toulen',
]

def load_secrets():
    with open('secrets/secrets.json') as f:
        secrets = json.load(f)
    return secrets

def connect_to_influxdb():
    secrets = load_secrets()
    client = InfluxDBClient(
        url=f"http://{secrets['host']}:{secrets['port']}",
        token=secrets['token'],
        org=secrets['organization']
    )
    return client

def write_data_to_csv(data):
    with open('data.csv', mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns_order)
        writer.writerow({columns_order[i]: data[i] for i in range(len(columns_order))})

def fetch_and_save_data():
    if not os.path.isfile('data.csv'):
        with open('data.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=columns_order)
            writer.writeheader()
    
    client = connect_to_influxdb()
    query = 'from(bucket:"{}") |> range(start: -1h) |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'.format(load_secrets()['bucket'])
    result = client.query_api().query_data_frame(org=load_secrets()['organization'], query=query)
    
    for row in result.to_dict(orient='records'):
        time_value = row.get('_time').strftime('%Y-%m-%d %H:%M:%S')
        data = [time_value] + [row.get(col) for col in columns_order[1:]]
        if not is_data_duplicate(data):
            write_data_to_csv(data)

def is_data_duplicate(new_data):
    with open('data.csv', mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == new_data[0]:
                return True
    return False

def main():
    while True:
        fetch_and_save_data()
        time.sleep(1)

if __name__ == "__main__":
    main()
