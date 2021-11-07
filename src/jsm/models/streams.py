# Copyright 2021 - Guillaume Charbonnier
# Licensed under the Apache License, Version 2.0 (the "License");
# http://www.apache.org/licenses/LICENSE-2.0
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, root_validator, validator

from .base import BaseRequest, BaseResponse, JetstreamModel
from .clusters import Cluster
from .messages import Message


class Retention(str, Enum):
    """How message retention is considered"""

    limits = "limits"
    interest = "interest"
    workqueue = "workqueue"


class Storage(str, Enum):
    """The type of storage backend"""

    file = "file"
    memory = "memory"


class Discard(str, Enum):
    """Discard policy when a stream reaches it's limits"""

    old = "old"
    new = "new"


class Placement(JetstreamModel):
    """Placement directives to consider when placing replicas of this stream"""

    cluster: str = Field(
        ...,
        description="The desired cluster name to place the stream",
        min_length=1,
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags required on servers hosting this stream",
    )


class External(JetstreamModel):
    api: str = Field(
        ...,
        description="The subject prefix that imports the other account/domain $JS.API.CONSUMER.> subjects",
    )
    deliver: Optional[str] = Field(
        None, description="The delivery subject to use for the push consumer"
    )


class Mirror(JetstreamModel):
    """Placement directives to consider when placing replicas of this stream, random placement when unset"""

    name: str = Field(
        ...,
        description="Stream name",
        regex=r"^[^.*>]+$",
        min_length=1,
    )
    opt_start_seq: Optional[int] = Field(
        None,
        description="Sequence to start replicating from",
        ge=0,
    )
    opt_start_time: Optional[str] = Field(
        None,
        description="Time stamp to start replicating from",
    )
    filter_subject: Optional[str] = Field(
        None,
        description="Replicate only a subset of messages based on filter",
    )
    external: Optional[External] = Field(
        None,
        description="Configuration referencing a stream source in another account or JetStream domain",
    )


class Source(JetstreamModel):
    name: str = Field(
        ...,
        description="Stream name",
        regex=r"^[^.*>]+$",
        min_length=1,
    )
    opt_start_seq: Optional[int] = Field(
        None,
        description="Sequence to start replicating from",
        ge=0,
    )
    opt_start_time: Optional[str] = Field(
        None,
        description="Time stamp to start replicating from",
    )
    filter_subject: Optional[str] = Field(
        None,
        description="Replicate only a subset of messages based on filter",
    )
    external: Optional[External] = Field(
        None,
        description="Configuration referencing a stream source in another account or JetStream domain",
    )


class Config(JetstreamModel):
    """Stream configuration

    References:
        Streams - [NATS Docs](https://docs.nats.io/jetstream/concepts/streams)
    """

    name: Optional[str] = Field(
        None,
        description="A unique name for the Stream, empty for Stream Templates.",
        regex=r"^[^.*>]*$",
        min_length=0,
    )
    subjects: Optional[List[str]] = Field(
        None,
        description="A list of subjects to consume, supports wildcards. Must be empty when a mirror is configured. May be empty when sources are configured.",
        min_length=0,
    )
    retention: Retention = Field(
        ...,
        description="How messages are retained in the Stream, once this is exceeded old messages are removed.",
    )
    max_consumers: int = Field(
        ...,
        description="How many Consumers can be defined for a given Stream. -1 for unlimited.",
        ge=-1,
    )
    max_msgs: int = Field(
        ...,
        description="How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.",
        ge=-1,
    )
    max_msgs_per_subject: Optional[int] = Field(
        -1,
        description="For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit",
        ge=-1,
    )
    max_bytes: int = Field(
        ...,
        description="How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.",
        ge=-1,
    )
    max_age: int = Field(
        ...,
        description="Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.",
        ge=0,
    )
    max_msg_size: Optional[int] = Field(
        -1,
        description="The largest message that will be accepted by the Stream. -1 for unlimited.",
        ge=-1,
    )
    storage: Storage = Field(
        ...,
        description="The storage backend to use for the Stream.",
    )
    num_replicas: int = Field(
        ...,
        description="How many replicas to keep for each message.",
        ge=1,
        le=5,
    )
    no_ack: Optional[bool] = Field(
        False,
        description="Disables acknowledging messages that are received by the Stream.",
    )
    template_owner: Optional[str] = Field(
        None,
        description="When the Stream is managed by a Stream Template this identifies the template that manages the Stream.",
    )
    discard: Optional[Discard] = Field(
        "old",
        description="When a Stream reach it's limits either old messages are deleted or new ones are denied",
    )
    duplicate_window: Optional[int] = Field(
        0,
        description="The time window to track duplicate messages for, expressed in nanoseconds. 0 for default",
        ge=0,
    )
    placement: Optional[Placement] = Field(
        None,
        description="Placement directives to consider when placing replicas of this stream, random placement when unset",
    )
    mirror: Optional[Mirror] = Field(
        None,
        description="Maintains a 1:1 mirror of another stream with name matching this property.  When a mirror is configured subjects and sources must be empty.",
    )
    sources: Optional[List[Source]] = Field(
        None,
        description="List of Stream names to replicate into this Stream",
    )


class DeletedItem(JetstreamModel):
    __root__: int = Field(..., ge=0)


class Lost(JetstreamModel):
    msgs: Optional[List[int]] = Field(
        None,
        description="The messages that were lost",
        # When field is a list, "ge" constraint is verified for each member
        ge=0,
    )
    bytes: Optional[int] = Field(
        None,
        description="The number of bytes that were lost",
    )


class State(JetstreamModel):
    messages: int = Field(
        ...,
        description="Number of messages stored in the Stream",
        ge=0,
    )
    bytes: int = Field(
        ...,
        description="Combined size of all messages in the Stream",
        ge=0,
    )
    first_seq: int = Field(
        ...,
        description="Sequence number of the first message in the Stream",
        ge=0,
    )
    first_ts: Optional[datetime] = Field(
        None,
        description="The timestamp of the first message in the Stream",
    )
    last_seq: int = Field(
        ...,
        description="Sequence number of the last message in the Stream",
    )
    last_ts: Optional[datetime] = Field(
        None,
        description="The timestamp of the last message in the Stream",
    )
    deleted: Optional[List[DeletedItem]] = Field(
        None,
        description="IDs of messages that were deleted using the Message Delete API or Interest based streams removing messages out of order",
    )
    num_deleted: Optional[int] = Field(
        None,
        description="The number of deleted messages",
        ge=0,
    )
    lost: Optional[Lost] = Field(
        None,
        description="Records messages that were damaged and unrecoverable",
    )
    consumer_count: int = Field(
        ...,
        description="Number of Consumers attached to the Stream",
        ge=0,
    )


class PubAck(JetstreamModel):
    stream: str = Field(..., description="Name of the stream")
    seq: int = Field(..., description="Sequence of the message in the steam")
    domain: Optional[str] = Field(
        None, description="JetStream domain which acknowledged the message"
    )
    duplicate: Optional[bool] = None


class IoNatsJetstreamApiV1StreamItem(JetstreamModel):
    config: Config = Field(
        ...,
        description="The active configuration for the Stream",
    )
    state: State = Field(
        ...,
        description="Detail about the current State of the Stream",
    )
    created: str = Field(
        ...,
        description="Timestamp when the stream was created",
    )
    mirror: Optional[Mirror] = Field(
        None, description="Information about an upstream stream source in a mirror"
    )
    sources: Optional[List[Source]] = Field(
        None, description="Streams being sourced into this Stream"
    )
    cluster: Optional[Cluster] = None


class IoNatsJetstreamApiV1StreamCreateResponse(
    IoNatsJetstreamApiV1StreamItem, BaseResponse
):
    pass


class IoNatsJetstreamApiV1StreamInfoResponse(
    IoNatsJetstreamApiV1StreamItem, BaseResponse
):
    pass


class IoNatsJetstreamApiV1StreamUpdateResponse(
    IoNatsJetstreamApiV1StreamItem, BaseResponse
):
    pass


class IoNatsJetstreamApiV1StreamListResponse(BaseResponse):
    total: int = Field(
        ...,
        description="Total number of streams without regard to offset or limit",
        ge=0,
    )
    offset: int = Field(
        ...,
        description="Number of streams to skip",
        ge=0,
    )
    limit: int = Field(
        ...,
        description="Maximum number of streams to return",
        ge=0,
    )
    streams: List[IoNatsJetstreamApiV1StreamItem] = Field(
        [],
        description="A list of streams",
    )


class IoNatsJetstreamApiV1StreamNamesResponse(BaseResponse):
    total: int = Field(
        ...,
        description="Total number of streams without regard to offset or limit",
        ge=0,
    )
    offset: int = Field(
        ...,
        description="Number of streams to skip",
        ge=0,
    )
    limit: int = Field(
        ...,
        description="Maximum number of streams to return",
        ge=0,
    )
    streams: List[str] = Field(
        [],
        description="A list of stream names",
    )

    @validator("streams", always=True, pre=True)
    def ensure_streams(cls, v: Any) -> Any:
        if v is None:
            return []
        return v


class IoNatsJetstreamApiV1StreamDeleteResponse(BaseResponse):
    success: bool


class IoNatsJetstreamApiV1StreamMsgGetResponse(BaseResponse):
    message: Message


class IoNatsJetstreamApiV1StreamMsgDeleteResponse(BaseResponse):
    success: bool


class IoNatsJetstreamApiV1StreamPurgeResponse(BaseResponse):
    success: bool
    purged: int = Field(
        ...,
        description="Number of messages purged from the Stream",
        ge=0,
    )


class IoNatsJetstreamApiV1StreamSnapshotResponse(BaseResponse):
    config: Config
    state: State


class CreateRequestConfig(JetstreamModel):

    name: Optional[str] = Field(
        None,
        description="A unique name for the Stream, empty for Stream Templates.",
        regex=r"^[^.*>]*$",
        min_length=0,
    )
    subjects: Optional[List[str]] = Field(
        None,
        description="A list of subjects to consume, supports wildcards. Must be empty when a mirror is configured. May be empty when sources are configured.",
        min_length=0,
    )
    retention: Retention = Field(
        ...,
        description="How messages are retained in the Stream, once this is exceeded old messages are removed.",
    )
    max_consumers: int = Field(
        ...,
        description="How many Consumers can be defined for a given Stream. -1 for unlimited.",
        ge=-1,
    )
    max_msgs: int = Field(
        ...,
        description="How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.",
        ge=-1,
    )
    max_msgs_per_subject: Optional[int] = Field(
        -1,
        description="For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit",
        ge=-1,
    )
    max_bytes: int = Field(
        ...,
        description="How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.",
        ge=-1,
    )
    max_age: int = Field(
        ...,
        description="Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.",
        ge=0,
    )
    max_msg_size: Optional[int] = Field(
        -1,
        description="The largest message that will be accepted by the Stream. -1 for unlimited.",
        ge=-1,
    )
    storage: Storage = Field(
        ..., description="The storage backend to use for the Stream."
    )
    num_replicas: int = Field(
        ...,
        description="How many replicas to keep for each message.",
        ge=1,
        le=5,
    )
    no_ack: Optional[bool] = Field(
        False,
        description="Disables acknowledging messages that are received by the Stream.",
    )
    template_owner: Optional[str] = Field(
        None,
        description="When the Stream is managed by a Stream Template this identifies the template that manages the Stream.",
    )
    discard: Optional[Discard] = Field(
        "old",
        description="When a Stream reach it's limits either old messages are deleted or new ones are denied",
    )
    duplicate_window: Optional[int] = Field(
        0,
        description="The time window to track duplicate messages for, expressed in nanoseconds. 0 for default",
        ge=0,
    )
    placement: Optional[Placement] = Field(
        None,
        description="Placement directives to consider when placing replicas of this stream, random placement when unset",
    )
    mirror: Optional[Mirror] = Field(
        None,
        description="Maintains a 1:1 mirror of another stream with name matching this property.  When a mirror is configured subjects and sources must be empty.",
    )
    sources: Optional[List[Source]] = Field(
        None, description="List of Stream names to replicate into this Stream"
    )


class IoNatsJetstreamApiV1StreamCreateRequest(CreateRequestConfig, BaseRequest):
    pass


class IoNatsJetstreamApiV1StreamUpdateRequest(CreateRequestConfig, BaseRequest):
    pass


class IoNatsJetstreamApiV1StreamInfoRequest(BaseRequest):
    deleted_details: Optional[bool] = Field(
        None,
        description="When true will result in a full list of deleted message IDs being returned in the info response",
    )


class IoNatsJetstreamApiV1StreamListRequest(BaseRequest):
    offset: Optional[int] = Field(
        None,
        description="Number of streams to skip",
        ge=0,
    )


class IoNatsJetstreamApiV1StreamNamesRequest(BaseRequest):
    offset: Optional[int] = Field(
        None,
        description="Number of streams to skip",
        ge=0,
    )


class IoNatsJetstreamApiV1StreamMsgGetRequest(BaseRequest):
    seq: Optional[int] = Field(
        None,
        description="Stream sequence number of the message to retrieve. Cannot be combined with last_by_subj",
    )
    last_by_subj: Optional[str] = Field(
        None,
        description="Retrieves the last message for a given subject, cannot be combined with seq",
    )

    @root_validator
    def check_exclusive_params(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure exactly 1 parameter is set between 'seq' and 'last_by_subj'"""
        seq = values.get("seq", None)
        last_by_subj = values.get("last_by_subj", None)
        if seq and last_by_subj:
            raise ValueError(
                "Both 'seq' and 'last_by_subj' arguments cannot be specified at same time"
            )
        if seq is None and not last_by_subj:
            raise ValueError(
                "Either 'seq' or 'last_by_subj' argument must be specified."
            )
        return values


class IoNatsJetstreamApiV1StreamMsgDeleteRequest(BaseRequest):
    seq: int = Field(
        ...,
        description="Stream sequence number of the message to delete",
    )
    no_erase: Optional[bool] = Field(
        None,
        description="Default will securely remove a message and rewrite the data with random data, set this to true to only remove the message",
    )


class IoNatsJetstreamApiV1StreamPurgeRequest(BaseRequest):
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


class IoNatsJetstreamApiV1StreamSnapshotRequest(BaseRequest):
    deliver_subject: str = Field(
        ...,
        description="The NATS subject where the snapshot will be delivered",
        min_length=1,
    )
    no_consumers: Optional[bool] = Field(
        None,
        description="When true consumer states and configurations will not be present in the snapshot",
    )
    chunk_size: Optional[int] = Field(
        None,
        description="The size of data chunks to send to deliver_subject",
        ge=1024,
    )
    jsck: Optional[bool] = Field(
        False,
        description="Check all message's checksums prior to snapshot",
    )
