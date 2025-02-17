# Lumu Technologies Challenge

## Part 1

The first part has been resolved in the file `timestamp_parser/timestamp_parser.py`.
For verification I've implemented an small tester that loads the `input.txt` file
which rows are comma-separated where the first element is the input and the second
is the expected format.

### How to run

```bash
python ip_counter/test.py
```

*Output*:

```
val: 2021-12-03T16:15:30.235Z
in : 2021-12-03T16:15:30.235Z
out: 2021-12-03T16:15:30.235

val: 3336042095000
in : 2075-09-18T14:21:35.000Z
out: 2075-09-18T14:21:35.000+00:00

...
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

As the main program loop depends on the consumer (receiving the event), we need
to run a process in parallel to insert the events every 30 secons, this is achieved
using python `threading` library and using a `Lock` to share the list of events and
the `last_sent` time.

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
