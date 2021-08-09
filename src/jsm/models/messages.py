from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import JetstreamModel


class Message(JetstreamModel):
    """A message read from a stream

    References:
        * Fetching the next message from a pull base consumer - [NATS Docs](https://docs.nats.io/jetstream/nats_api_reference#fetching-the-next-message-from-a-pull-based-consumer)
        * Fetching a message from a stream by sequence - [NATS Docs](https://docs.nats.io/jetstream/nats_api_reference#fetching-from-a-stream-by-sequence)
    """

    subject: str = Field(
        ...,
        description="The subject the message was originally received on",
        min_length=1,
    )
    seq: int = Field(
        ...,
        description="The sequence number of the message in the Stream",
        ge=0,
    )
    data: str = Field(
        ...,
        description="The base64 encoded payload of the message body",
        min_length=1,
    )
    time: datetime = Field(
        ...,
        description="The time the message was received",
    )
    hdrs: Optional[str] = Field(
        None,
        description="Base64 encoded headers for the message",
    )
