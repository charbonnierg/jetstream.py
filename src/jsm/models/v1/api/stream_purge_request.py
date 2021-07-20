# generated by datamodel-codegen:
#   filename:  stream_purge_request.json
#   timestamp: 2021-07-18T15:27:50+00:00

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IoNatsJetstreamApiV1StreamPurgeRequest(BaseModel):
    filter: Optional[str] = Field(
        None, description="Restrict purging to messages that match this subject"
    )
    seq: Optional[int] = Field(
        None,
        description="Purge all messages up to but not including the message with this sequence. Can be combined with subject filter but not the keep option",
    )
    keep: Optional[int] = Field(
        None,
        description="Ensures this many messages are present after the purge. Can be combined with the subject filter but not the sequence",
    )
