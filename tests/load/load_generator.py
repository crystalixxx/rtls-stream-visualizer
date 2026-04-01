"""UDP load generator for RTLS Stream Visualizer.

Generates valid LS-1000 JSON payloads at a configurable rate and sends them
over UDP to the ``udp_receiver``.  Designed for load / stress / soak testing
of the full pipeline (UDP -> RabbitMQ -> backend -> DB / WebSocket).

Usage::

    python -m tests.load.load_generator \
        --rate 200 --duration 120 --tags 50 \
        --host 127.0.0.1 --port 9999
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from tests.load.tag_pool import (
    build_random_hex_tag_pool,
    build_sequential_tag_pool,
    write_tag_pool,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class Stats:
    sent: int = 0
    errors: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def inc_sent(self) -> None:
        with self.lock:
            self.sent += 1

    def inc_errors(self) -> None:
        with self.lock:
            self.errors += 1


DEFAULT_TAG_STATE_FILE = Path("tests/load/.active_tags.json")


def _build_tag_pool(
    num_tags: int,
    *,
    tag_prefix: str,
    tag_width: int,
    random_tags: bool,
) -> list[str]:
    if random_tags:
        return build_random_hex_tag_pool(num_tags)
    return build_sequential_tag_pool(num_tags, prefix=tag_prefix, width=tag_width)


def _persist_tag_pool(path: str | None, tags: list[str]) -> None:
    if not path:
        return
    write_tag_pool(path, tags)
    logger.info("Wrote active tag pool to %s", path)


def _make_payload(tag_id: str, seq: int) -> bytes:
    """Build a payload conforming to the LS-1000 JSON schema."""
    now = time.strftime("%Y-%m-%d %H:%M:%S") + f".{random.randint(0, 999):03d}"
    obj = {
        "devid": tag_id,
        "seq": seq % 65536,
        "timestamp": now,
        "samples": [
            {"aid": _generate_hex_id(), "tof": round(random.uniform(0.1, 50.0), 3)}
            for _ in range(random.randint(1, 4))
        ],
        "position": {
            "rgn": random.randint(0, 5),
            "x": round(random.uniform(0.0, 100.0), 2),
            "y": round(random.uniform(0.0, 100.0), 2),
            "z": round(random.uniform(0.0, 10.0), 2),
        },
        "lat": round(random.uniform(55.0, 56.0), 6),
        "lng": round(random.uniform(37.0, 38.0), 6),
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sender_loop(
    host: str,
    port: int,
    rate: float,
    duration: float,
    tags: list[str],
    stats: Stats,
    stop: threading.Event,
) -> None:
    """Send datagrams at *rate* msg/sec until *duration* elapses or *stop* is set."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / rate
    seq = 0
    deadline = time.monotonic() + duration
    next_send = time.monotonic()

    try:
        while not stop.is_set() and time.monotonic() < deadline:
            now = time.monotonic()
            if now < next_send:
                time.sleep(next_send - now)

            tag_id = random.choice(tags)
            payload = _make_payload(tag_id, seq)
            try:
                sock.sendto(payload, (host, port))
                stats.inc_sent()
            except OSError:
                stats.inc_errors()
            seq += 1
            next_send += interval
    finally:
        sock.close()


def run(
    host: str,
    port: int,
    rate: int,
    duration: int,
    num_tags: int,
    workers: int,
    tag_prefix: str,
    tag_width: int,
    random_tags: bool,
    tag_state_file: str | None,
) -> Stats:
    tags = _build_tag_pool(
        num_tags,
        tag_prefix=tag_prefix,
        tag_width=tag_width,
        random_tags=random_tags,
    )
    _persist_tag_pool(tag_state_file, tags)
    stats = Stats()
    stop = threading.Event()

    per_worker_rate = rate / workers
    logger.info(
        "Starting %d worker(s): target %d msg/s total (%d/worker), "
        "duration %ds, %d unique tags, dest %s:%d",
        workers,
        rate,
        int(per_worker_rate),
        duration,
        num_tags,
        host,
        port,
    )

    threads: list[threading.Thread] = []
    t0 = time.monotonic()
    for _ in range(workers):
        t = threading.Thread(
            target=_sender_loop,
            args=(host, port, per_worker_rate, duration, tags, stats, stop),
            daemon=True,
        )
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Interrupted, stopping workers...")
        stop.set()
        for t in threads:
            t.join(timeout=3)

    elapsed = time.monotonic() - t0
    actual_rate = stats.sent / elapsed if elapsed > 0 else 0

    logger.info("--- Results ---")
    logger.info("Duration       : %.1f s", elapsed)
    logger.info("Sent           : %d", stats.sent)
    logger.info("Errors         : %d", stats.errors)
    logger.info("Actual rate    : %.1f msg/s", actual_rate)
    logger.info("Target rate    : %d msg/s", rate)

    return stats


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="UDP load generator for RTLS pipeline")
    p.add_argument("--host", default="127.0.0.1", help="UDP destination host")
    p.add_argument("--port", type=int, default=9999, help="UDP destination port")
    p.add_argument("--rate", type=int, default=100, help="Target messages per second")
    p.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    p.add_argument("--tags", type=int, default=20, help="Number of unique tag IDs")
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Sender threads (increase for rate > ~500)",
    )
    p.add_argument(
        "--tag-prefix",
        default="TAG",
        help="Prefix for deterministic tag IDs shared with Locust",
    )
    p.add_argument(
        "--tag-width",
        type=int,
        default=4,
        help="Zero-padding width for deterministic tag IDs",
    )
    p.add_argument(
        "--random-tags",
        action="store_true",
        help="Use random hex tag IDs instead of deterministic shared IDs",
    )
    p.add_argument(
        "--tag-state-file",
        default=str(DEFAULT_TAG_STATE_FILE),
        help="Where to write the active tag pool for Locust synchronization",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    run(
        host=args.host,
        port=args.port,
        rate=args.rate,
        duration=args.duration,
        num_tags=args.tags,
        workers=args.workers,
        tag_prefix=args.tag_prefix,
        tag_width=args.tag_width,
        random_tags=args.random_tags,
        tag_state_file=args.tag_state_file,
    )


if __name__ == "__main__":
    main()
