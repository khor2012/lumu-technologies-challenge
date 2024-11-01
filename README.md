# Lumu Technologies Challenge

## Part 1

The first part has been resolved in the file `timestamp_parser/timestamp_parser.py`.
For verification I've implemented an small tester that loads the `input.txt` file
which rows are comma-separated where the first element is the input and the second
is the expected format.

### How to run

```bash
python timestamp_parser/test.py
```

Make sure to add different scenarios on the `input.txt` file.

## Part 2

## Redis implementation

For the implementation I've decided to use `redis` as the data store. I've decided
to use the [HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog) algorithm
which is already implemented in `redis`. The HyperLogLog algorithm is able to
estimate cardinalities of > 10^9 with a typical accuracy (standard error) of 2%,
using 1.5 kB of memory.

If having approximated values wouldn't fit, a second solution is proposed.

### How to run

1. Start the services (kafka, zookeeper, redis):

```bash
docker compose up -d
```

2. Start the consumer:

```bash
python ip_counter/consumer.py --topic "example" --backend redis
```

3. Start the producer:

```bash
python ip_counter/producer.py --topic "example" --num_devices 10000 --pause_ms 0 --num_messages 1000000
```

*Output*:

```
Total devices: 10035
Total devices: 10035
Total devices: 10035
Total devices: 10035
Total devices: 10035
Total devices: 10035
```

As explained above this solution have accuracy problems but reduces the overall
complexity of the system and highly reduces the storage needed.

## ClickHouse implementation

ClickHouse is an analytical database which allows for high data ingestion
and consumption. I've created a table called events to store all the events.

To improve the data ingestion rate I've decided to implement batching of insert
and to make we are not too much behind the Kafka events, event batches are
flush every 30 seconds just to make sure no events are lost in case the event
batch is not full. This is mainly because ClickHouse is really good at batch inserts.

```sql
CREATE TABLE IF NOT EXISTS events (
    timestamp DateTime64,
    device_ip String,
    error_code Int8
)
ENGINE MergeTree ORDER BY device_ip
```

### How to run

1. Start the services (kafka, zookeeper, redis):

```bash
docker compose up -d
```

2. Start the consumer:

```bash
python ip_counter/consumer.py --topic "example" --backend clickhouse
```

3. Start the producer:

```bash
python ip_counter/producer.py --topic "example" --num_devices 10000 --pause_ms 0 --num_messages 1000000
```

*Output*:

```
Total devices: (10000,)
Total devices: (10000,)
Total devices: (10000,)
Total devices: (10000,)
```

This solution have similar performance as the Redis implementation but has the
advantage of having exact numbers and the data is available for later retrieval
and analysis.
