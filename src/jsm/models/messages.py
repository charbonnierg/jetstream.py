# Copyright 2021 - Guillaume Charbonnier
# Licensed under the Apache License, Version 2.0 (the "License");
# http://www.apache.org/licenses/LICENSE-2.0
from __future__ import annotations

from base64 import b64decode
from datetime import datetime, timezone
from email.parser import BytesParser
from typing import Dict, Optional

from pydantic import Field, PrivateAttr, validator

from _nats.aio.client import (
    CTRL_LEN,
    DESC_HDR,
    NATS_HDR_LINE,
    STATUS_HDR,
    STATUS_MSG_LEN,
    Msg,
)

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
    data: bytes = Field(
        ...,
        description="The base64 encoded payload of the message body",
        min_length=1,
    )
    time: datetime = Field(
        ...,
        description="The time the message was received",
    )
    hdrs: Optional[Dict[str, str]] = Field(
        None,
        description="Base64 encoded headers for the message",
    )
    _msg: Optional[Msg] = PrivateAttr(None)

    @validator("hdrs", pre=True, always=True)
    def parse_b64_headers(cls, v):  # type: ignore[no-untyped-def]
        if not isinstance(v, str):
            return v
        parser = BytesParser()
        hdrs: Dict[str, str] = {}
        headers = b64decode(v)
        raw_headers = headers[len(NATS_HDR_LINE) :]
        parsed_hdrs = parser.parsebytes(raw_headers)
        # Check if it is an inline status message like:
        #
        # NATS/1.0 404 No Messages
        #
        if len(parsed_hdrs.items()) == 0:
            _inline = headers[len(NATS_HDR_LINE) - 1 :]
            status = _inline[:STATUS_MSG_LEN]
            desc = _inline[STATUS_MSG_LEN + 1 : len(_inline) - CTRL_LEN - CTRL_LEN]
            hdrs[STATUS_HDR] = status.decode()
            hdrs[DESC_HDR] = desc.decode()
        else:
            for k, v in parsed_hdrs.items():
                hdrs[k] = v

        return hdrs

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
            hdrs=msg.headers,
        )
        message._msg = msg
        return message

    async def respond(self, payload: Optional[bytes] = None) -> None:
        if self._msg:
            await self._msg.respond(payload or b"")
            return
        raise Exception("No subject to send acknowledgment to.")

    async def ack(self) -> None:
        if self._msg:
            await self._msg.respond(b"")
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
