from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr

from .base import IoNatsJetstreamApiV1ResponseItem
from .clusters import Cluster


class Retention(Enum):
    limits = "limits"
    interest = "interest"
    workqueue = "workqueue"


class Storage(Enum):
    file = "file"
    memory = "memory"


class Discard(Enum):
    old = "old"
    new = "new"


class Placement(BaseModel):
    cluster: constr(min_length=1) = Field(  # type: ignore[valid-type]
        ..., description="The desired cluster name to place the stream"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags required on servers hosting this stream"
    )


class External(BaseModel):
    api: str = Field(
        ...,
        description="The subject prefix that imports the other account/domain $JS.API.CONSUMER.> subjects",
    )
    deliver: Optional[str] = Field(
        None, description="The delivery subject to use for the push consumer"
    )


class Mirror(BaseModel):
    name: constr(regex=r"^[^.*>]+$", min_length=1) = Field(  # type: ignore[valid-type]  # noqa: F722
        ..., description="Stream name"
    )
    opt_start_seq: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        None, description="Sequence to start replicating from"
    )
    opt_start_time: Optional[str] = Field(
        None, description="Time stamp to start replicating from"
    )
    filter_subject: Optional[str] = Field(
        None, description="Replicate only a subset of messages based on filter"
    )
    external: Optional[External] = Field(
        None,
        description="Configuration referencing a stream source in another account or JetStream domain",
    )


class Source(BaseModel):
    name: constr(regex=r"^[^.*>]+$", min_length=1) = Field(  # type: ignore[valid-type]  # noqa: F722
        ..., description="Stream name"
    )
    opt_start_seq: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        None, description="Sequence to start replicating from"
    )
    opt_start_time: Optional[str] = Field(
        None, description="Time stamp to start replicating from"
    )
    filter_subject: Optional[str] = Field(
        None, description="Replicate only a subset of messages based on filter"
    )
    external: Optional[External] = Field(
        None,
        description="Configuration referencing a stream source in another account or JetStream domain",
    )


class Config(BaseModel):
    name: Optional[constr(regex=r"^[^.*>]*$", min_length=0)] = Field(  # type: ignore[valid-type]  # noqa: F722
        None, description="A unique name for the Stream, empty for Stream Templates."
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
    max_consumers: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How many Consumers can be defined for a given Stream. -1 for unlimited.",
    )
    max_msgs: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.",
    )
    max_msgs_per_subject: Optional[conint(ge=-1)] = Field(  # type: ignore[valid-type]
        -1,
        description="For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit",
    )
    max_bytes: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.",
    )
    max_age: conint(ge=0) = Field(  # type: ignore[valid-type]
        ...,
        description="Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.",
    )
    max_msg_size: Optional[conint(ge=-1)] = Field(  # type: ignore[valid-type]
        -1,
        description="The largest message that will be accepted by the Stream. -1 for unlimited.",
    )
    storage: Storage = Field(
        ..., description="The storage backend to use for the Stream."
    )
    num_replicas: conint(ge=1, le=5) = Field(  # type: ignore[valid-type]
        ..., description="How many replicas to keep for each message."
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
    duplicate_window: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        0,
        description="The time window to track duplicate messages for, expressed in nanoseconds. 0 for default",
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


class DeletedItem(BaseModel):
    __root__: conint(ge=0)  # type: ignore[valid-type]


class Lost(BaseModel):
    msgs: Optional[List[conint(ge=0)]] = Field(  # type: ignore[valid-type]
        None, description="The messages that were lost"
    )
    bytes: Optional[int] = Field(None, description="The number of bytes that were lost")


class State(BaseModel):
    messages: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Number of messages stored in the Stream"
    )
    bytes: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Combined size of all messages in the Stream"
    )
    first_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Sequence number of the first message in the Stream"
    )
    first_ts: Optional[str] = Field(
        None, description="The timestamp of the first message in the Stream"
    )
    last_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Sequence number of the last message in the Stream"
    )
    last_ts: Optional[str] = Field(
        None, description="The timestamp of the last message in the Stream"
    )
    deleted: Optional[List[DeletedItem]] = Field(
        None,
        description="IDs of messages that were deleted using the Message Delete API or Interest based streams removing messages out of order",
    )
    num_deleted: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        None, description="The number of deleted messages"
    )
    lost: Optional[Lost] = Field(
        None, description="Records messages that were damaged and unrecoverable"
    )
    consumer_count: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Number of Consumers attached to the Stream"
    )


class IoNatsJetstreamApiV1StreamItem(BaseModel):
    config: Config = Field(..., description="The active configuration for the Stream")
    state: State = Field(
        ..., description="Detail about the current State of the Stream"
    )
    created: str = Field(..., description="Timestamp when the stream was created")
    cluster: Optional[Cluster] = None
    mirror: Optional[Mirror] = Field(
        None, description="Information about an upstream stream source in a mirror"
    )
    sources: Optional[List[Source]] = Field(
        None, description="Streams being sourced into this Stream"
    )


class Message(BaseModel):
    subject: constr(min_length=1) = Field(  # type: ignore[valid-type]
        ..., description="The subject the message was originally received on"
    )
    seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the message in the Stream"
    )
    data: constr(min_length=0) = Field(  # type: ignore[valid-type]
        ..., description="The base64 encoded payload of the message body"
    )
    time: str = Field(..., description="The time the message was received")
    hdrs: Optional[str] = Field(
        None, description="Base64 encoded headers for the message"
    )


class IoNatsJetstreamApiV1StreamCreateResponse(
    IoNatsJetstreamApiV1StreamItem, IoNatsJetstreamApiV1ResponseItem
):
    pass


class IoNatsJetstreamApiV1StreamInfoResponse(IoNatsJetstreamApiV1StreamCreateResponse):
    pass


class IoNatsJetstreamApiV1StreamUpdateResponse(
    IoNatsJetstreamApiV1StreamCreateResponse
):
    pass


class IoNatsJetstreamApiV1StreamListResponse(IoNatsJetstreamApiV1ResponseItem):
    total: conint(ge=0)  # type: ignore[valid-type]
    offset: conint(ge=0)  # type: ignore[valid-type]
    limit: conint(ge=0)  # type: ignore[valid-type]
    type: str
    streams: Optional[List[IoNatsJetstreamApiV1StreamItem]] = None


class IoNatsJetstreamApiV1StreamNamesResponse(IoNatsJetstreamApiV1ResponseItem):
    total: conint(ge=0)  # type: ignore[valid-type]
    offset: conint(ge=0)  # type: ignore[valid-type]
    limit: conint(ge=0)  # type: ignore[valid-type]
    streams: Optional[List[str]] = None


class IoNatsJetstreamApiV1StreamDeleteResponse(IoNatsJetstreamApiV1ResponseItem):
    success: bool


class IoNatsJetstreamApiV1StreamMsgGetResponse(IoNatsJetstreamApiV1ResponseItem):
    message: Message


class IoNatsJetstreamApiV1StreamMsgDeleteResponse(IoNatsJetstreamApiV1ResponseItem):
    success: bool


class IoNatsJetstreamApiV1StreamPurgeResponse(IoNatsJetstreamApiV1ResponseItem):
    success: bool
    purged: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Number of messages purged from the Stream"
    )


class IoNatsJetstreamApiV1StreamSnapshotResponse(IoNatsJetstreamApiV1ResponseItem):
    config: Config
    state: State


class IoNatsJetstreamApiV1StreamCreateRequest(BaseModel):
    name: Optional[constr(regex=r"^[^.*>]*$", min_length=0)] = Field(  # type: ignore[valid-type]  # noqa: F722
        None, description="A unique name for the Stream, empty for Stream Templates."
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
    max_consumers: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How many Consumers can be defined for a given Stream. -1 for unlimited.",
    )
    max_msgs: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.",
    )
    max_msgs_per_subject: Optional[conint(ge=-1)] = Field(  # type: ignore[valid-type]
        -1,
        description="For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit",
    )
    max_bytes: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.",
    )
    max_age: conint(ge=0) = Field(  # type: ignore[valid-type]
        ...,
        description="Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.",
    )
    max_msg_size: Optional[conint(ge=-1)] = Field(  # type: ignore[valid-type]
        -1,
        description="The largest message that will be accepted by the Stream. -1 for unlimited.",
    )
    storage: Storage = Field(
        ..., description="The storage backend to use for the Stream."
    )
    num_replicas: conint(ge=1, le=5) = Field(  # type: ignore[valid-type]
        ..., description="How many replicas to keep for each message."
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
    duplicate_window: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        0,
        description="The time window to track duplicate messages for, expressed in nanoseconds. 0 for default",
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


class IoNatsJetstreamApiV1StreamInfoRequest(BaseModel):
    deleted_details: Optional[bool] = Field(
        None,
        description="When true will result in a full list of deleted message IDs being returned in the info response",
    )


class IoNatsJetstreamApiV1StreamListRequest(BaseModel):
    offset: conint(ge=0)  # type: ignore[valid-type]


class IoNatsJetstreamApiV1StreamNamesRequest(BaseModel):
    offset: conint(ge=0)  # type: ignore[valid-type]


class IoNatsJetstreamApiV1StreamUpdateRequest(IoNatsJetstreamApiV1StreamCreateRequest):
    pass


class IoNatsJetstreamApiV1StreamMsgGetRequest(BaseModel):
    seq: int = Field(
        ..., description="Stream sequence number of the message to retrieve"
    )


class IoNatsJetstreamApiV1StreamMsgDeleteRequest(BaseModel):
    seq: int = Field(..., description="Stream sequence number of the message to delete")
    no_erase: Optional[bool] = Field(
        None,
        description="Default will securely remove a message and rewrite the data with random data, set this to true to only remove the message",
    )


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


class IoNatsJetstreamApiV1StreamSnapshotRequest(BaseModel):
    deliver_subject: constr(min_length=1) = Field(  # type: ignore[valid-type]
        ..., description="The NATS subject where the snapshot will be delivered"
    )
    no_consumers: Optional[bool] = Field(
        None,
        description="When true consumer states and configurations will not be present in the snapshot",
    )
    chunk_size: Optional[conint(ge=1024)] = Field(  # type: ignore[valid-type]
        None, description="The size of data chunks to send to deliver_subject"
    )
    jsck: Optional[bool] = Field(
        False, description="Check all message's checksums prior to snapshot"
    )
