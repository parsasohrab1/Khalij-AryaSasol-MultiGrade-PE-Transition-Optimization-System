"""Replay simulated DCS samples to Kafka (stand-in for the real DCS/OPC connector).

Requires `pip install kafka-python` and `docker compose -f infra/docker-compose.yml up -d`.
UNTESTED against a live broker. Run: python replay_to_kafka.py [--speed 60]
"""
import argparse
import json
import time

from kafka import KafkaProducer  # type: ignore

from khalij_ampt.grades import UNITS
from khalij_ampt.simulator import random_campaigns, simulate_unit

ap = argparse.ArgumentParser()
ap.add_argument("--speed", type=float, default=60.0, help="x real time (1 sample = 1 min)")
ap.add_argument("--bootstrap", default="localhost:9092")
a = ap.parse_args()

prod = KafkaProducer(bootstrap_servers=a.bootstrap,
                     value_serializer=lambda v: json.dumps(v, default=str).encode())
frames = {u: simulate_unit(u, random_campaigns(u, 5, 0), seed=0) for u in UNITS}
for i in range(min(len(f) for f in frames.values())):
    for u, f in frames.items():
        prod.send(f"dcs.{u.lower()}", f.iloc[i].to_dict())
    time.sleep(60.0 / a.speed)
prod.flush()
