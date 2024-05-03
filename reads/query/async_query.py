# Author: Piotr Krzysztof Lis - github.com/straightchlorine

import pandas as pd

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.flux_table import TableList

class AsyncQuery:
    """
    Interface to query the InfluxDB.

    Attributes:
        _influxdb_host (str): The host of the InfluxDB instance.
        _influxdb_port (int): The port of the InfluxDB instance.
        _influxdb_token (str): The token to authenticate with InfluxDB.
        _influxdb_organization (str): The organization to use within InfluxDB.
        _influxdb_bucket (str): Bucket within InfluxDB where the data will be stored.
        _db_url (str): The URL of the InfluxDB instance.
        sensors_and_params (dict): The sensors and their parameters to read.
    """

    # influxdb data
    _influxdb_host : str         # host of the influxdb instance
    _influxdb_port : int         # port of the influxdb instance
    _influxdb_token : str        # token to authenticate with influxdb
    _influxdb_organization : str # organization to use within influxdb
    _influxdb_bucket : str       # bucket to save the data into

    _db_url : str                # address of the influxdb instance

    sensors_and_params : dict    # sensors and their parameters to read

    def __init__(self, host, port, token, org, bucket, sensors):
        """
        Initialize the fetcher with the required information.

        Args:
            host (str): The host of the InfluxDB instance.
            port (int): The port of the InfluxDB instance.
            token (str): The token to authenticate with InfluxDB.
            org (str): The organization to use within InfluxDB.
            bucket (str): Bucket within InfluxDB where the data will be stored.
            sensors (dict): The sensors and their parameters to read.
        """

        self._influxdb_host = host
        self._influxdb_port = port
        self._influxdb_token = token
        self._influxdb_organization = org
        self._influxdb_bucket = bucket

        self._db_url = f"http://{self._influxdb_host}:{self._influxdb_port}"

        self.sensors_and_params = sensors

    async def _get_InfluxDB_client(self) -> InfluxDBClientAsync:
        """ Returns an InfluxDB client. """
        return InfluxDBClientAsync(url=self._db_url,
                                   token=self._influxdb_token,
                                   org=self._influxdb_organization)

    def _into_dataframe(self, tables : TableList) -> pd.DataFrame:
        """
        Turns the tables into a pandas DataFrame.
        Args:
            tables (list): The tables to turn into a DataFrame.
        Returns:
            pd.DataFrame: procured measurements as a DataFrame.
        """
        # unpacking the table 
        fields = []
        values = []
        timestamps = set()
        for table in tables:
            for record in table.records:
                fields.append(str(record.get_field()))
                values.append(record.get_value())
                timestamps.add(record.get_time())

        # creating a dictionary with pairs { parameter : measurement }
        data = {field: values[i] for i, field in enumerate(fields)}

        if len(fields) != len(values):
            raise ValueError("Fields and values have different lengths.")

        return pd.DataFrame(data=data, index=pd.DatetimeIndex(timestamps))

    async def latest(self) -> pd.DataFrame:
        """
        Queries the latest measurement of every parameter.

        Returns:
            pd.DataFrame: The latest measurement of every parameter.
        """
        # get the connection to the database via query api
        client = await self._get_InfluxDB_client()
        query_api = client.query_api()

        # query the latest measurement
        query = f'from(bucket:"{self._influxdb_bucket}") |> range(start: -1h) |> last()'
        tables = await query_api.query(query)

        # close the connection
        await client.close()

        # turn the tables into a DataFrame and return it
        return self._into_dataframe(tables)
