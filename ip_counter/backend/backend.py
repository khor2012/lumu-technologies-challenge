import redis
import clickhouse_connect
from datetime import datetime, timedelta

from timestamp_parser import parse_timestamp

class Backend:
    def parse(self, event):
        parsed = event['timestamp'].replace("'", "")
        try:
            parsed = int(parsed)
        except ValueError:
            pass
        event['timestamp'] = parse_timestamp(parsed, raw=True)


class RedisBackend(Backend):
    def __init__(self, hyperlog):
        self.connection = redis.Redis(host='localhost', port=6379, db=0)
        self.hyperlog = hyperlog | 'default'

    def process_event(self, event):
        self.connection.pfadd(self.hyperlog, event["device_ip"])

    def count(self):
        return self.connection.pfcount(self.hyperlog)


class ClickHouseBackend(Backend):
    table = 'events'

    def __init__(self, host='localhost', username='default', password='', max_events=10_000):
        self.connection = clickhouse_connect.get_client(
            host=host, username=username, password=password)
        self.connection.command(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                timestamp DateTime64,
                device_ip String,
                error_code Int8
            )
            ENGINE MergeTree ORDER BY device_ip
            """
        )
        self.max_events = max_events
        self.event_queue = []
        self.last_sent = datetime.now()

    def process_event(self, event: dict):
        row = list(event.values())
        self.event_queue.append(row)
        if len(self.event_queue) > self.max_events or datetime.now() > self.last_sent + timedelta(seconds=30):
            self.connection.insert(self.table, self.event_queue, column_names=event.keys())
            self.event_queue = []
            self.last_sent = datetime.now()

    def count(self):
        query = self.connection.query(
            f"""
            SELECT count(distinct device_ip) FROM {self.table}
            """
        )
        return query.result_rows[0]
