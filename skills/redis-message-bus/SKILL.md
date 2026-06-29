---
name: redis-message-bus
version: 1.0.0
author: open-community
license: MIT
description: |
  Full-async Redis message bus for multi-agent clusters.
  Provides Pub/Sub broadcast, Stream persistent queue, service discovery,
  and heartbeat detection. Built on asyncio + aioredis.
  Ideal for agent clusters that need one-to-many and many-to-many
  communication with guaranteed message delivery.
  Industry scenarios: financial analysis workflows, game server orchestration,
  IoT device coordination, SaaS multi-tenant task dispatch.
---

# redis-message-bus

Full-async Redis message bus — the "central post office" for multi-agent clusters.

## Design Motivation

P2P messaging (e.g. a P2P Messaging Layer) supports direct node-to-node communication, but broadcasting a message to all nodes requires N separate calls. redis-message-bus uses Redis Pub/Sub for broadcast and Stream for persistent queuing, plus service discovery and heartbeat — acting as a cluster-level "central post office".

## Core Capabilities

| Capability | Description |
|---|---|
| Pub/Sub Broadcast | Real-time one-to-many message push (fast, fire-and-forget) |
| Stream Persistence | Durable message queue — messages survive disconnects |
| Service Discovery | Nodes auto-register on startup; others discover available peers |
| Heartbeat Detection | 3s interval, 10s timeout auto-eviction |
| Async Throughout | Built on `asyncio` + `aioredis` |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  agent-alpha │     │  agent-beta  │     │  agent-gamma │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │    Pub/Sub        │   Stream          │
       ├───────────────────┼───────────────────┤
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Redis     │
                    │  (Pub/Sub   │
                    │   + Stream)  │
                    └─────────────┘
```

**Why Pub/Sub + Stream?** Pub/Sub is sub-millisecond but messages are lost if subscribers disconnect. Stream is slower but durable. The solution: senders write to both channels simultaneously; receivers get real-time notifications via Pub/Sub and use Stream to backfill any gaps detected by sequence number.

## Configuration

```yaml
# redis-message-bus config
redis:
  host: ${REDIS_HOST:localhost}
  port: 6379
  db: 0
  password: ${REDIS_PASSWORD:}

bus:
  pubsub_channels:
    - "agent:broadcast"       # cluster-wide broadcast
    - "agent:task:dispatch"   # task dispatch
    - "agent:task:complete"   # task completion notification
  stream_name: "agent:persistent"
  consumer_group: "agent-workers"

heartbeat:
  interval: 3       # heartbeat interval (seconds)
  timeout: 10       # eviction timeout (seconds)
  retry: 3          # retry count
```

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `REDIS_HOST` | Redis server hostname/IP | `your-redis-host` |
| `REDIS_PASSWORD` | Redis authentication password | `YOUR_REDIS_PASSWORD` |

## Python API (Async)

```python
import asyncio
from redis_message_bus import MessageBus

bus = MessageBus(
    redis_url="redis://:YOUR_REDIS_PASSWORD@your-redis-host:6379/0",
    node_id="agent-alpha",
    channels=["agent:broadcast", "agent:task:dispatch"],
    stream_name="agent:persistent",
    consumer_group="agent-workers",
    heartbeat_interval=3,
    heartbeat_timeout=10,
)


async def main():
    await bus.start()

    # --- Service Discovery ---
    await bus.register_service(
        service_name="data-analyst",
        capabilities=["trend", "anomaly", "comparison"],
    )
    peers = await bus.discover_services(capability="anomaly")

    # --- Pub/Sub Broadcast ---
    await bus.publish(
        channel="agent:broadcast",
        message={"type": "config_update", "key": "threshold", "value": 0.85},
    )

    # --- Stream (Persistent Queue) ---
    await bus.send_to_stream(
        stream="agent:persistent",
        message={
            "type": "task_dispatch",
            "task_id": "task-001",
            "target": "agent-beta",
            "payload": {"action": "analyze", "dataset": "/data/q2_report.csv"},
        },
    )

    # --- Receive Messages ---
    async for msg in bus.listen(timeout=30):
        if msg["source"] == "pubsub":
            print(f"[Broadcast] {msg['data']}")
        elif msg["source"] == "stream":
            print(f"[Persistent] {msg['data']}")
            await bus.ack_stream_message(msg["id"])

    # --- Heartbeat ---
    await bus.stop()


asyncio.run(main())
```

### API Reference

| Method | Description |
|---|---|
| `start()` | Connect to Redis, start heartbeat and listeners |
| `stop()` | Graceful shutdown, deregister service |
| `register_service(service_name, capabilities)` | Register node in service discovery |
| `discover_services(capability=None)` | Query registered nodes |
| `publish(channel, message)` | Pub/Sub broadcast |
| `send_to_stream(stream, message)` | Write to persistent Stream |
| `listen(timeout=30)` | Yield messages from Pub/Sub + Stream |
| `ack_stream_message(msg_id)` | Acknowledge Stream message processed |
| `get_heartbeat_status()` | Return dict of node health |

## Degradation Strategy

Redis is a single point of failure — if it goes down, all dependent Skills fail simultaneously.

**Two-level degradation:**

1. **Level 1**: On Redis disconnect, write messages to a local SQLite queue; retry Redis connection with exponential backoff.
2. **Level 2**: If Redis stays unreachable for 5+ minutes, switch to an async handoff channel (e.g. GitHub Issues or file-based relay).

```yaml
# Degradation config
degradation:
  level1:
    backend: "sqlite"
    path: "./.cache/message_queue.db"
    retry_backoff_max: 60
  level2:
    trigger_after_minutes: 5
    backend: "file_relay"
    relay_path: "./.cache/relay/"
```

## Comparison with P2P Messaging Layer

| Dimension | P2P Messaging Layer | redis-message-bus |
|---|---|---|
| Topology | Peer-to-peer, decentralized | Centralized (Redis broker) |
| Latency | Low (< 5ms in same LAN) | Low (Pub/Sub sub-ms) |
| Broadcast | N calls for N peers | Single Pub/Sub call |
| Persistence | None (fire-and-forget) | Stream persistent queue |
| Deployment | No external dependency | Requires Redis server |
| Suitable for | Encrypted private channel, 1:1 | 1:many, many:many, guaranteed delivery |

**Selection rule**: Use P2P Messaging Layer for lightweight 1:1 encrypted messaging; use redis-message-bus when you need broadcast, persistence, or service discovery.

## Industry Scenarios

### Financial Analysis Workflow
A coordinator agent dispatches analysis tasks to specialist agents (risk, credit, compliance). Results are broadcast via Pub/Sub and persisted to Stream for audit trail. If an agent disconnects, it recovers missed results from Stream on reconnect.

### Game Server Orchestration
A game master agent broadcasts state changes (player joins, events) to all game logic agents via Pub/Sub. Matchmaking requests go through Stream for guaranteed processing. Service discovery tracks which game agents are online.

### IoT Device Coordination
An edge controller agent publishes sensor threshold alerts via Pub/Sub to all downstream processors. Device telemetry flows through Stream for replay capability. Heartbeat tracks device agent availability across zones.

### SaaS Multi-Ttenant Task Dispatch
A tenant isolator agent routes tasks to tenant-specific worker agents using channel namespacing (e.g. `agent:tenant-001:dispatch`). Stream provides per-tenant message ordering. Service discovery maps tenant IDs to available workers.

## Pitfalls & Lessons Learned

### 1. Pub/Sub Messages Are Lost on Disconnect
If a subscriber disconnects, all messages during the disconnect window are gone. **Fix**: always write critical messages to Stream simultaneously; Pub/Sub serves only as a real-time "signal flare".

### 2. Redis Is a Single Point of Failure
When Redis goes down, all 4+ dependent Skills fail at once. **Fix**: implement two-level degradation (local queue + async relay). Test the degradation path — an untested fallback is no fallback.

### 3. Stream MAXLEN Truncation
Redis Stream defaults to ~10,000 entries before truncation. If consumers are slow, old messages get evicted. **Fix**: set MAXLEN generously or use `XTRIM` with `MINID` for time-based retention.

### 4. Consumer Group Lag
If a consumer crashes without ACKing, pending entries pile up. **Fix**: monitor `XPENDING` and implement a reclaim timer that re-assigns messages idle beyond a threshold.

## Quick Start

```bash
# Start Redis locally
docker run -d --name redis-bus -p 6379:6379 redis:7-alpine

# Install
pip install redis-message-bus

# Run
python -m redis_message_bus --config bus_config.yaml
```

## Files

```
redis-message-bus/
├── SKILL.md
├── redis_message_bus/
│   ├── __init__.py
│   ├── bus.py            # MessageBus core
│   ├── discovery.py      # Service discovery
│   ├── heartbeat.py      # Heartbeat detection
│   ├── degradation.py    # Fallback to SQLite / file relay
│   └── config.py         # Configuration loader
├── tests/
│   ├── test_bus.py
│   ├── test_discovery.py
│   ├── test_heartbeat.py
│   └── test_degradation.py
└── bus_config.yaml
```
