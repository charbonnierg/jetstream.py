# type: ignore[no-untyped-def]
import pytest

from jsm import JS


@pytest.mark.asyncio
async def test_consumer_get_next(js: JS):
    STREAM = "test_consumer_get_next"
    await js.stream_delete(STREAM)
    await js.stream_create(STREAM, [f"{STREAM}.>"])

    await js.stream_publish(f"{STREAM}.foo.1", b"test", headers={"foo": "bar"})

    await js.consumer_durable_create(STREAM, "durable1", deliver_policy="all")

    await js.stream_publish(f"{STREAM}.bar.1", b"test", headers={"foo": "bar"})

    await js.consumer_durable_create(STREAM, "durable2", deliver_policy="last")

    await js.consumer_durable_create(STREAM, "durable3", deliver_policy="new")

    msg_response = await js.consumer_pull_next(STREAM, "durable1")
    msg_response2 = await js.consumer_pull_next(STREAM, "durable2")
    msg_response3 = await js.consumer_pull_next(STREAM, "durable3", no_wait=True)

    assert msg_response.subject == f"{STREAM}.foo.1"
    assert msg_response.hdrs == {"foo": "bar"}

    assert msg_response2.subject == f"{STREAM}.bar.1"
    assert msg_response2.hdrs == {"foo": "bar"}

    assert msg_response3 is None

    await js.stream_delete(STREAM)
