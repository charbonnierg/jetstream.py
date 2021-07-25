"""This example will guide you in:
    - creating a stream with jetstream.py
    - listing available streams
    - updating the newly created stream configuration
    - delete the newly created stream
"""
from loguru import logger

from jsm.api.client import Client as JS

js = JS()

STREAM = "test-01"


async def main() -> None:
    # Connect to the JetStream server
    await js.connect()

    # By default, a stream will only listen for messages on a single subject
    # which is the name of the stream. Moreover, it does not enforce any limit
    # on number of messages, size, age, or consumer number.
    create_res = await js.stream_create(
        STREAM, subjects=["test.>"], raise_on_error=False
    )
    logger.info(f"Received response of type '{create_res.type}': {create_res}")
    create_res.raise_on_error()
    logger.debug(f"Successfully created stream with response: {create_res}")

    # List the available streams
    list_res = await js.stream_list()
    # Total number of streams is available as `total` attribute
    logger.info(f"Found {list_res.total} stream{'s' if list_res.total > 1 else ''}")
    # The `streams` attribute contains `jsm.models.v1.api.IoNatsJetstreamApiV1StreamInfoResponseItem` objects
    assert list_res.streams[-1].config.name == STREAM

    # Update the stream we just created, for example update the subjects the stream should listen to
    update_res = await js.stream_update(STREAM, subjects=["test.>", "demo.>"])
    logger.info(f"Successfully updated stream with response: {update_res}")

    # We can confirm that stream has been updated
    info_res = await js.stream_info(STREAM)
    logger.info(f"Successfully fetched stream info with response: {info_res}")
    assert info_res.config.name == STREAM and info_res.config.subjects == [
        "test.>",
        "demo.>",
    ]


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
