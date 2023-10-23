import json
import logging
import os

logging.basicConfig(level=logging.INFO)

from kafka import KafkaProducer


class Producer:
    def send(self, topic, data):
        kafka_ip = os.getenv("KAFKA_IP", "continuum.accordion-project.eu:9092")
        producer = KafkaProducer(bootstrap_servers=kafka_ip,
                                 compression_type='gzip',
                                 max_request_size=3173440261,
                                 value_serializer=lambda x:
                                 json.dumps(x, ensure_ascii=False).encode('utf-8'))
        producer.send(topic, value=data)
        producer.flush()
