"""This example will show you how to list existing streams within a Jetstream deployment
"""
from loguru import logger

from jsm.api.client import Client as JS

js = JS()


async def main() -> None:
    # Connect to the JetStream server
    await js.connect()

    # List the available streams
    list_res = await js.stream_list()

    # Total number of streams is available as `total` attribute
    logger.info(f"Found {list_res.total} stream{'s' if list_res.total > 1 else ''}")
    # The `streams` attribute contains `jsm.models.v1.api.IoNatsJetstreamApiV1StreamInfoResponseItem` objects
    logger.debug(list_res.streams)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
