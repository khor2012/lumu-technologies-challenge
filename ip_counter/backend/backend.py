import redis
import clickhouse_connect
from datetime import datetime, timedelta
import time

from timestamp_parser import parse_timestamp

from threading import Thread, Lock

EVENT_QUEUE = []


class Backend:
    def parse(self, event):
        parsed = event['timestamp'].replace("'", "")
        try:
            parsed = int(parsed)
        except ValueError:
            pass
        event['timestamp'] = parse_timestamp(parsed, raw=True)


class RedisBackend(Backend):
    def __init__(self, hyperlog='default'):
        self.connection = redis.Redis(host='localhost', port=6379, db=0)
        self.hyperlog = hyperlog

    def process_event(self, event):
        self.connection.pfadd(self.hyperlog, event["device_ip"])

    def count(self):
        return self.connection.pfcount(self.hyperlog)


class ClickHouseBackend(Backend):
    table = 'events'
    keys = ["timestamp", "device_ip", "error_code"]

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
        self.last_sent = datetime.now()

        self.data_lock = Lock()
        thread = Thread(target=self.async_insert, args=(EVENT_QUEUE,self.last_sent))
        thread.start()


    def async_insert(self, event_queue, last_sent):
        while True:
            if datetime.now() > last_sent + timedelta(seconds=30) and event_queue:
                self.connection.insert(self.table, event_queue, column_names=self.keys)
                with self.data_lock:
                    event_queue.clear()
                last_sent = datetime.now()
                print("Flushing events", last_sent)
            time.sleep(0.1)

    def process_event(self, event: dict):
        global EVENT_QUEUE
        row = list(event.values())
        with self.data_lock:
            EVENT_QUEUE.append(row)
        if len(EVENT_QUEUE) > self.max_events:
            print(f"Inserting {len(EVENT_QUEUE)} events")
            self.connection.insert(self.table, EVENT_QUEUE, column_names=self.keys)
            with self.data_lock:
                EVENT_QUEUE.clear()
            self.last_sent = datetime.now()

    def count(self):
        query = self.connection.query(
            f"""
            SELECT count(distinct device_ip) FROM {self.table}
            """
        )
        return query.result_rows[0]
