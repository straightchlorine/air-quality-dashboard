import asyncio

from reads.fetch.async_fetch import AsyncReadFetcher
from reads.query.async_query import AsyncQuery

class InfluxDBInterface:
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

        self._fetcher = AsyncReadFetcher(self._influxdb_host,
                                        self._influxdb_port,
                                        self._influxdb_token,
                                        self._influxdb_organization,
                                        self._influxdb_bucket,
                                        self.sensors_and_params,
                                        self._dev_ip,
                                        self._dev_port,
                                        self._dev_handle)

        self._query_api = AsyncQuery(self._influxdb_host,
                                self._influxdb_port,
                                self._influxdb_token,
                                self._influxdb_organization,
                                self._influxdb_bucket,
                                self.sensors_and_params)

        # starting the fetching in the background
        asyncio.create_task(self._fetcher.fetch())

    @property
    def query_api(self):
        return self._query_api

    @query_api.getter
    def query_api(self):
        return self._query_api
