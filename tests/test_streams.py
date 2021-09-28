# type: ignore[no-untyped-def]
import pytest

from jsm import JS
from jsm.models.streams import (
    IoNatsJetstreamApiV1StreamListResponse,
    IoNatsJetstreamApiV1StreamNamesResponse,
)


@pytest.mark.asyncio
async def test_list_streams(js: JS):
    response = await js.stream_list()
    assert isinstance(response, IoNatsJetstreamApiV1StreamListResponse)
    assert isinstance(response.streams, list)


@pytest.mark.asyncio
async def test_list_stream_names(js: JS):
    response = await js.stream_names()
    assert isinstance(response, IoNatsJetstreamApiV1StreamNamesResponse)
    assert isinstance(response.streams, list)


@pytest.mark.asyncio
async def test_list_existing_streams(js: JS):
    STREAM = "test_list_streams"
    await js.stream_create(STREAM)

    stream_response = await js.stream_list()
    assert stream_response.total >= 1
    assert len(stream_response.streams) >= 1
    assert stream_response.streams[-1].config.name == STREAM
    await js.stream_delete(STREAM)


@pytest.mark.asyncio
async def test_list_existing_stream_names(js: JS):
    STREAM = "test_list_stream_names"
    await js.stream_create(STREAM)

    name_response = await js.stream_names()
    assert name_response.total >= 1
    assert len(name_response.streams) >= 1
    assert name_response.streams[-1] == STREAM
    await js.stream_delete(STREAM)


@pytest.mark.asyncio
async def test_stream_msg_get(js: JS):
    STREAM = "test_stream_msg_get"
    await js.stream_delete(STREAM)
    await js.stream_create(STREAM, [f"{STREAM}.*"])

    await js.stream_publish(f"{STREAM}.1", b"test", headers={"foo": "bar"})

    msg_response = await js.stream_msg_get(STREAM, seq=1)
    msg_response2 = await js.stream_msg_get(STREAM, last_by_subj=f"{STREAM}.1")
    assert msg_response == msg_response2
    assert msg_response.message.data == b"test"
    assert msg_response2.message.hdrs == {"foo": "bar"}
    await js.stream_delete(STREAM)
