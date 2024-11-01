import sys
import argparse
import json
import redis
from datetime import datetime, timedelta
from backend.backend import RedisBackend, ClickHouseBackend

if sys.version_info >= (3, 12, 0):
    import six
    sys.modules['kafka.vendor.six.moves'] = six.moves

from kafka import KafkaConsumer

HYPERLOGLOG_NAME = 'default'


def main():
    parser = argparse.ArgumentParser(description='Kafka Message Receiver')
    parser.add_argument('--topic', required=True, help='Kafka topic to send messages to')
    parser.add_argument('--bootstrap_servers', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('--backend', default='clickhouse', choices=['clickhouse', 'redis'], help='Which data store to use.')
    args = parser.parse_args()

    consumer = KafkaConsumer(args.topic, bootstrap_servers=args.bootstrap_servers,
                             value_deserializer=lambda v: json.loads(v),)

    backend = RedisBackend() if args.backend == 'redis' else ClickHouseBackend()

    last_print = datetime.now()
    for message in consumer:
        event = message.value
        backend.parse(event)
        backend.process_event(event)
        if datetime.now() > last_print + timedelta(seconds=30):
            print("Total devices:", backend.count())
            last_print = datetime.now()

if __name__ == '__main__':
    main()
