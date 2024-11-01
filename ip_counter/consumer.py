import sys
import argparse
import json


if sys.version_info >= (3, 12, 0):
    import six
    sys.modules['kafka.vendor.six.moves'] = six.moves

from kafka import KafkaConsumer


def process_message(message: dict):
    print(message)

def main():
    parser = argparse.ArgumentParser(description='Kafka Message Receiver')
    parser.add_argument('--topic', required=True, help='Kafka topic to send messages to')
    parser.add_argument('--bootstrap_servers', default='localhost:9092', help='Kafka bootstrap servers')
    args = parser.parse_args()

    consumer = KafkaConsumer(args.topic, bootstrap_servers=args.bootstrap_servers,
                             value_deserializer=lambda v: json.loads(v),)

    for message in consumer:
        process_message(message.value)


if __name__ == '__main__':
    main()
