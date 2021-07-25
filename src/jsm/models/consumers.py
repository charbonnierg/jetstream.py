from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, conint, constr

from .base import IoNatsJetstreamApiV1ResponseItem
from .clusters import Cluster


class AckPolicy(Enum):
    none = "none"
    all = "all"
    explicit = "explicit"


class ReplayPolicy(Enum):
    instant = "instant"
    original = "original"


class Config(BaseModel):
    durable_name: Optional[constr(regex=r"^[^.*>]+$", min_length=1)] = Field(  # type: ignore[valid-type]  # noqa: F722
        None, description="A unique name for a durable consumer"
    )
    deliver_subject: Optional[constr(min_length=1)] = None  # type: ignore[valid-type]
    deliver_policy: Optional[Union[str, int]] = "last"
    ack_policy: AckPolicy
    ack_wait: Optional[conint(ge=1)] = Field(  # type: ignore[valid-type]
        None,
        description="How long (in nanoseconds) to allow messages to remain un-acknowledged before attempting redelivery",
    )
    max_deliver: Optional[int] = Field(
        None,
        description="The number of times a message will be redelivered to consumers if not acknowledged in time",
    )
    filter_subject: Optional[str] = None
    replay_policy: ReplayPolicy
    sample_freq: Optional[str] = None
    rate_limit_bps: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        None,
        description="The rate at which messages will be delivered to clients, expressed in bit per second",
    )
    max_ack_pending: Optional[int] = Field(
        None,
        description="The maximum number of messages without acknowledgement that can be outstanding, once this limit is reached message delivery will be suspended",
    )
    idle_heartbeat: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        None,
        description="If the Consumer is idle for more than this many nano seconds a empty message with Status header 100 will be sent indicating the consumer is still alive",
    )
    flow_control: Optional[bool] = Field(
        None,
        description="For push consumers this will regularly send an empty mess with Status header 100 and a reply subject, consumers must reply to these messages to control the rate of message delivery",
    )
    max_waiting: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
        512,
        description="The number of pulls that can be outstanding on a pull consumer, pulls received after this is reached are ignored",
    )


class Delivered(BaseModel):
    consumer_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the Consumer"
    )
    stream_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the Stream"
    )


class AckFloor(BaseModel):
    consumer_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the Consumer"
    )
    stream_seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the Stream"
    )


class IoNatsJetstreamApiV1ConsumerItem(BaseModel):
    stream_name: str = Field(..., description="The Stream the consumer belongs to")
    name: str = Field(
        ...,
        description="A unique name for the consumer, either machine generated or the durable name",
    )
    config: Config
    created: str
    delivered: Delivered = Field(
        ..., description="The last message delivered from this Consumer"
    )
    ack_floor: AckFloor = Field(
        ..., description="The highest contiguous acknowledged message"
    )
    num_ack_pending: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The number of messages pending acknowledgement"
    )
    num_redelivered: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The number of redeliveries that have been performed"
    )
    num_waiting: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The number of pull consumers waiting for messages"
    )
    num_pending: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The number of messages left unconsumed in this Consumer"
    )
    cluster: Optional[Cluster] = None


class IoNatsJetstreamApiV1ConsumerCreateResponse(
    IoNatsJetstreamApiV1ConsumerItem, IoNatsJetstreamApiV1ResponseItem
):
    pass


class IoNatsJetstreamApiV1ConsumerInfoResponse(
    IoNatsJetstreamApiV1ConsumerCreateResponse
):
    pass


class IoNatsJetstreamApiV1ConsumerDeleteResponse(IoNatsJetstreamApiV1ResponseItem):
    success: bool


class IoNatsJetstreamApiV1ConsumerListResponse(IoNatsJetstreamApiV1ResponseItem):
    total: conint(ge=0)  # type: ignore[valid-type]
    offset: conint(ge=0)  # type: ignore[valid-type]
    limit: conint(ge=0)  # type: ignore[valid-type]
    type: str
    consumers: List[IoNatsJetstreamApiV1ConsumerItem] = []


class IoNatsJetstreamApiV1ConsumerNamesResponse(IoNatsJetstreamApiV1ResponseItem):
    total: conint(ge=0)  # type: ignore[valid-type]
    offset: conint(ge=0)  # type: ignore[valid-type]
    limit: conint(ge=0)  # type: ignore[valid-type]
    type: str
    consumers: List[str] = []


class IoNatsJetstreamApiV1ConsumerListRequest(BaseModel):
    offset: conint(ge=0)  # type: ignore[valid-type]


class IoNatsJetstreamApiV1ConsumerCreateRequest(BaseModel):
    stream_name: str = Field(
        ..., description="The name of the stream to create the consumer in"
    )
    config: Config = Field(..., description="The consumer configuration")


class IoNatsJetstreamApiV1ConsumerNamesRequest(BaseModel):
    offset: conint(ge=0)  # type: ignore[valid-type]
    subject: Optional[str] = Field(
        None,
        description="Filter the names to those consuming messages matching this subject or wildcard",
    )
