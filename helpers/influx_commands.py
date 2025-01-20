import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import influxdb_client
from datetime import datetime


def connect_influxdb(url, token, org):
    # Influx db init
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()
    print('Influx initialised')
    return client, write_api, query_api

def read_from_influx(query_api, bucket, measurement, field):
    query = f'''
    from(bucket: "{bucket}")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "{measurement}")
    |> filter(fn: (r) => r["_field"] == "{field}")
    |> filter(fn: (r) => r["host"] == "host1")
    |> last()
    '''
    tables = query_api.query(query)
    for table in tables:
        for record in table.records:
            return record.get_value()

def write_to_influx(write_api, org, bucket, measurement, field, double_data):
    point = Point(measurement) \
    .tag("host", "host1") \
    .field(field, double_data)
    write_api.write(bucket=bucket, org=org, record=point)
    print("Written")

def close_influx(client):
    client.close()