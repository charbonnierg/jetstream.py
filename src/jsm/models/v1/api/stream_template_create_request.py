# generated by datamodel-codegen:
#   filename:  stream_template_create_request.json
#   timestamp: 2021-07-18T15:27:47+00:00

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr


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
    cluster: constr(min_length=1) = Field(
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
    name: constr(regex=r"^[^.*>]+$", min_length=1) = Field(
        ..., description="Stream name"
    )
    opt_start_seq: Optional[conint(ge=0)] = Field(
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


class External1(BaseModel):
    api: str = Field(
        ...,
        description="The subject prefix that imports the other account/domain $JS.API.CONSUMER.> subjects",
    )
    deliver: Optional[str] = Field(
        None, description="The delivery subject to use for the push consumer"
    )


class Source(BaseModel):
    name: constr(regex=r"^[^.*>]+$", min_length=1) = Field(
        ..., description="Stream name"
    )
    opt_start_seq: Optional[conint(ge=0)] = Field(
        None, description="Sequence to start replicating from"
    )
    opt_start_time: Optional[str] = Field(
        None, description="Time stamp to start replicating from"
    )
    filter_subject: Optional[str] = Field(
        None, description="Replicate only a subset of messages based on filter"
    )
    external: Optional[External1] = Field(
        None,
        description="Configuration referencing a stream source in another account or JetStream domain",
    )


class Config(BaseModel):
    name: Optional[constr(regex=r"^[^.*>]*$", min_length=0)] = Field(
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
    max_consumers: conint(ge=-1) = Field(
        ...,
        description="How many Consumers can be defined for a given Stream. -1 for unlimited.",
    )
    max_msgs: conint(ge=-1) = Field(
        ...,
        description="How many messages may be in a Stream, oldest messages will be removed if the Stream exceeds this size. -1 for unlimited.",
    )
    max_msgs_per_subject: Optional[conint(ge=-1)] = Field(
        -1,
        description="For wildcard streams ensure that for every unique subject this many messages are kept - a per subject retention limit",
    )
    max_bytes: conint(ge=-1) = Field(
        ...,
        description="How big the Stream may be, when the combined stream size exceeds this old messages are removed. -1 for unlimited.",
    )
    max_age: conint(ge=0) = Field(
        ...,
        description="Maximum age of any message in the stream, expressed in nanoseconds. 0 for unlimited.",
    )
    max_msg_size: Optional[conint(ge=-1)] = Field(
        -1,
        description="The largest message that will be accepted by the Stream. -1 for unlimited.",
    )
    storage: Storage = Field(
        ..., description="The storage backend to use for the Stream."
    )
    num_replicas: conint(ge=1, le=5) = Field(
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
    duplicate_window: Optional[conint(ge=0)] = Field(
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


class IoNatsJetstreamApiV1StreamTemplateCreateRequest(BaseModel):
    name: str = Field(..., description="A unique name for the Template")
    config: Config = Field(
        ..., description="The template configuration to create Streams with"
    )
    max_streams: conint(ge=-1) = Field(
        ..., description="The maximum number of streams to allow using this Template"
    )
