from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import Field, PrivateAttr

from .base import JetstreamModel

if TYPE_CHECKING:
    from jsm.api.subscription import Msg


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
    data: bytes = Field(
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
    _msg: Optional[Msg] = PrivateAttr(None)

    @classmethod
    def from_msg(cls, msg: Msg) -> Message:
        """Parse a JetStream message from an NATS message"""
        tokens = msg.reply.split(".")
        if len(tokens) != 9 or tokens[0] != "$JS" or tokens[1] != "ACK":
            raise ValueError(
                "Failed to parse message. Message is not a valid JetStream message"
            )
        message = Message(
            subject=msg.subject,
            seq=tokens[6],
            data=msg.data,
            time=datetime.fromtimestamp(
                int(tokens[7]) / 1_000_000_000.0, tz=timezone.utc
            ),
            hdrs=None,
        )
        message._msg = msg
        return message

    async def respond(self, payload: Optional[bytes] = None) -> None:
        if self._msg:
            await self._msg.respond(payload)
            return
        raise Exception("No subject to send acknowledgment to.")

    async def ack(self) -> None:
        if self._msg:
            await self._msg.ack()
            return
        raise Exception("No subject to send acknowledgment to.")

    @property
    def sid(self) -> int:
        if self._msg:
            return self._msg.sid  # type: ignore[no-any-return]
        else:
            raise Exception("Message was not received from a subscription.")

    @property
    def reply(self) -> str:
        if self._msg:
            return self._msg.reply  # type: ignore[no-any-return]
        else:
            raise Exception("No subject to reply to.")
