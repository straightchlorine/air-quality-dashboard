#!/usr/bin/env python

# Author: Piotr Krzysztof Lis - github.com/straightchlorine

import asyncio
import aiohttp
import datetime
from influxdb_client import InfluxDBClient, Point

class AsyncReadFetcher:
    """
    A class to fetch sensor readings from a device and store them in InfluxDB.

    Attributes:
        _influxdb_host (str): The host of the InfluxDB instance.
        _influxdb_port (int): The port of the InfluxDB instance.
        _influxdb_token (str): The token to authenticate with InfluxDB.
        _influxdb_organization (str): The organization to use within InfluxDB.
        _influxdb_bucket (str): Bucket within InfluxDB where the data will be stored.
        _device_ip (str): The IP address of device providing sensor readings.
        _device_port (str): The port of the device providing the readings.
        _http_handle (str): The http handle to access the data.
        _device_address (str): The address of the device in the network.
        _database_address (str): The address of the InfluxDB instance.
        sensors (dict): The sensors and their parameters to read.
    """

    # influxdb data
    _influxdb_host : str         # host of the influxdb instance
    _influxdb_port : int         # port of the influxdb instance
    _influxdb_token : str        # token to authenticate with influxdb
    _influxdb_organization : str # organization to use within influxdb
    _influxdb_bucket : str       # bucket to save the data into

    # device data
    _dev_ip : str             # ip of the device sending the data
    _dev_port : int           # port of the device sending the data
    _dev_handle : str    # handle to access the data

    _dev_url : str        # address of the device in the network
    _db_url : str      # address of the influxdb instance

    def __init__(self, host, port, token, org, bucket, sensors, dev_ip, dev_port, handle = ""):
        """
        Initialize the fetcher with the required information.

        Args:
            host (str): The host of the InfluxDB instance.
            port (int): The port of the InfluxDB instance.
            token (str): The token to authenticate with InfluxDB.
            org (str): The organization to use within InfluxDB.
            bucket (str): Bucket within InfluxDB where the data will be stored.
            dev_ip (str): The IP address of device providing sensor readings.
            dev_port (str): The port of the device providing the readings.
            handle (str): The http handle to access the data ("" by default).
            sensors (dict): The sensors and their parameters to read.
        """

        self._influxdb_host = host
        self._influxdb_port = port
        self._influxdb_token = token
        self._influxdb_organization = org
        self._influxdb_bucket = bucket

        self._dev_ip = dev_ip
        self._dev_port = dev_port
        self._dev_handle = handle

        self._dev_url = f"http://{self._dev_ip}:{self._dev_port}/{self._dev_handle}"
        self._db_url = f"http://{self._influxdb_host}:{self._influxdb_port}"

        self.sensors_and_params = sensors

    def _get_reads(self, data) -> dict[str, float]:
        """
        Based on sensors specified in sensors attribute fill the fields
        with appropriate key-value pairs for InfluxDB storage.

        Args:
            data (dict): The sensor readings to parse.
        """

        fields = {}
        for sensor in self.sensors_and_params:
            for param in self.sensors_and_params[sensor]:
                fields[param] = float(data['nodemcu'][sensor][param])
        return fields

    def _parse_into_records(self, data, device_name = 'nodemcu'):
        """
        Parse raw json file into records for InfluxDB.

        Args:
            data (dict): The sensor readings to parse.
            device_name (str): The name of the device (default is 'nodemcu').
        """

        records = {
            "measurement": "sensor_data",
            "tags": {
                "device": device_name
            },
            "timestamp": str(datetime.datetime.now().isoformat()),
        }

        records["fields"] = self._get_reads(data)
        return records 

    def _write_to_db(self, client, records):
        """
        Write the sensor readings to InfluxDB.

        Args:
            client (InfluxDBClient): The InfluxDB client to write to.
            records (dict): The sensor readings as records for InfluxDB.
        """

        with client.write_api() as writer:
            point = Point.from_dict(records, write_precision='ns')
            writer.write(bucket=self._influxdb_bucket,
                         org=self._influxdb_organization,
                         record=point)

    def _store_sensor_readings(self, records):
        """
        Store sensor readings within InfluxDB.

        Args:
            records (dict): The sensor readings in the form of InfluxDB records.
        """
        with InfluxDBClient(url=self._db_url,
                            token=self._influxdb_token,
                            org=self._influxdb_organization) as client:
            self._write_to_db(client, records)

    async def _request_sensor_readings(self, session):
        """
        Fetch the sensor readings from the device via http request.

        Args:
            session: The aiohttp session to use for the request.
        """
        async with session.get(self._dev_url) as response:
            if response.status != 200:
                print(f"Error fetching data: {response.status}")
            else:
                read = await response.json()
                return read

    async def _request_and_store(self):
        """
        Main request and store loop.
        """
        await asyncio.sleep(1)
        async with aiohttp.ClientSession() as session:
            json = await self._request_sensor_readings(session)
            self._store_sensor_readings(self._parse_into_records(json))

    async def fetch(self):
        """
        Request sensor readings from the device and store them in InfluxDB.
        """
        while True:
            await self._request_and_store()
