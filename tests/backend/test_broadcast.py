import asyncio

import pytest

from backend.broadcast import Broadcast


@pytest.mark.asyncio
async def test_subscribe_and_publish():
    bc = Broadcast()
    queue = bc.subscribe()

    await bc.publish({"tag_id": "t1"})

    msg = queue.get_nowait()
    assert msg == {"tag_id": "t1"}


@pytest.mark.asyncio
async def test_multiple_subscribers():
    bc = Broadcast()
    q1 = bc.subscribe()
    q2 = bc.subscribe()

    await bc.publish({"tag_id": "t2"})

    assert q1.get_nowait() == {"tag_id": "t2"}
    assert q2.get_nowait() == {"tag_id": "t2"}


@pytest.mark.asyncio
async def test_unsubscribe():
    bc = Broadcast()
    queue = bc.subscribe()
    bc.unsubscribe(queue)

    await bc.publish({"tag_id": "t3"})

    assert queue.empty()
    assert bc.subscriber_count == 0


@pytest.mark.asyncio
async def test_full_queue_drops_message():
    bc = Broadcast(maxsize=1)
    queue = bc.subscribe()

    await bc.publish({"n": 1})
    await bc.publish({"n": 2})

    assert queue.get_nowait() == {"n": 1}
    assert queue.empty()


@pytest.mark.asyncio
async def test_unsubscribe_idempotent():
    bc = Broadcast()
    queue = bc.subscribe()
    bc.unsubscribe(queue)
    bc.unsubscribe(queue)

    assert bc.subscriber_count == 0


@pytest.mark.asyncio
async def test_subscriber_count():
    bc = Broadcast()
    assert bc.subscriber_count == 0

    q1 = bc.subscribe()
    assert bc.subscriber_count == 1

    q2 = bc.subscribe()
    assert bc.subscriber_count == 2

    bc.unsubscribe(q1)
    assert bc.subscriber_count == 1

    bc.unsubscribe(q2)
    assert bc.subscriber_count == 0
