#!/usr/bin/env python
import json
import asyncio
import threading
from ahttpdc.reads.interface import DatabaseInterface

# load the secrets
with open('secrets/secrets.json', 'r') as f:
    secrets = json.load(f)

sensors = {
    'bmp180': ['altitude', 'pressure', 'seaLevelPressure'],
    'mq135': ['aceton', 'alcohol', 'co', 'co2', 'nh4', 'toulen'],
    'ds18b20': ['temperature'],
    'dht22': ['humidity'],
}

# create the DatabaseInterface object
interface = DatabaseInterface(
    secrets['host'],
    secrets['port'],
    secrets['token'],
    secrets['organization'],
    secrets['bucket'],
    sensors,
    secrets['dev_ip'],
    secrets['dev_port'],
    secrets['handle'],
)


def enable():
    asyncio.run(interface._fetcher.schedule_fetcher())


if __name__ == '__main__':
    fetch_thread = threading.Thread(target=enable, args=(interface,))
    fetch_thread.start()
