# generated by datamodel-codegen:
#   filename:  consumer_create_response.json
#   timestamp: 2021-07-18T15:28:05+00:00

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, conint, constr


class IoNatsJetstreamApiV1ConsumerCreateResponse1(BaseModel):
    type: str


class AckPolicy(Enum):
    none = "none"
    all = "all"
    explicit = "explicit"


class ReplayPolicy(Enum):
    instant = "instant"
    original = "original"


class Config(BaseModel):
    durable_name: Optional[constr(regex=r"^[^.*>]+$", min_length=1)] = Field(
        None, description="A unique name for a durable consumer"
    )
    deliver_subject: Optional[constr(min_length=1)] = None
    deliver_policy: Optional[Union[str, int]] = "last"
    ack_policy: AckPolicy
    ack_wait: Optional[conint(ge=1)] = Field(
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
    rate_limit_bps: Optional[conint(ge=0)] = Field(
        None,
        description="The rate at which messages will be delivered to clients, expressed in bit per second",
    )
    max_ack_pending: Optional[int] = Field(
        None,
        description="The maximum number of messages without acknowledgement that can be outstanding, once this limit is reached message delivery will be suspended",
    )
    idle_heartbeat: Optional[conint(ge=0)] = Field(
        None,
        description="If the Consumer is idle for more than this many nano seconds a empty message with Status header 100 will be sent indicating the consumer is still alive",
    )
    flow_control: Optional[bool] = Field(
        None,
        description="For push consumers this will regularly send an empty mess with Status header 100 and a reply subject, consumers must reply to these messages to control the rate of message delivery",
    )
    max_waiting: Optional[conint(ge=0)] = Field(
        512,
        description="The number of pulls that can be outstanding on a pull consumer, pulls received after this is reached are ignored",
    )


class Delivered(BaseModel):
    consumer_seq: conint(ge=0) = Field(
        ..., description="The sequence number of the Consumer"
    )
    stream_seq: conint(ge=0) = Field(
        ..., description="The sequence number of the Stream"
    )


class AckFloor(BaseModel):
    consumer_seq: conint(ge=0) = Field(
        ..., description="The sequence number of the Consumer"
    )
    stream_seq: conint(ge=0) = Field(
        ..., description="The sequence number of the Stream"
    )


class Replica(BaseModel):
    name: str = Field(..., description="The server name of the peer")
    current: bool = Field(
        ..., description="Indicates if the server is up to date and synchronised"
    )
    active: float = Field(..., description="Nanoseconds since this peer was last seen")
    offline: Optional[bool] = Field(
        False, description="Indicates the node is considered offline by the group"
    )
    lag: Optional[conint(ge=0)] = Field(
        None,
        description="How many uncommitted operations this peer is behind the leader",
    )


class Cluster(BaseModel):
    name: Optional[str] = Field(None, description="The cluster name")
    leader: Optional[str] = Field(
        None, description="The server name of the RAFT leader"
    )
    replicas: Optional[List[Replica]] = Field(
        None, description="The members of the RAFT cluster"
    )


class IoNatsJetstreamApiV1ConsumerCreateResponseItem(BaseModel):
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
    num_ack_pending: conint(ge=0) = Field(
        ..., description="The number of messages pending acknowledgement"
    )
    num_redelivered: conint(ge=0) = Field(
        ..., description="The number of redeliveries that have been performed"
    )
    num_waiting: conint(ge=0) = Field(
        ..., description="The number of pull consumers waiting for messages"
    )
    num_pending: conint(ge=0) = Field(
        ..., description="The number of messages left unconsumed in this Consumer"
    )
    cluster: Optional[Cluster] = None


class Error(BaseModel):
    code: conint(ge=300, le=699) = Field(
        ..., description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1ConsumerCreateResponseItem1(BaseModel):
    error: Error


class IoNatsJetstreamApiV1ConsumerCreateResponse(BaseModel):
    __root__: Union[
        IoNatsJetstreamApiV1ConsumerCreateResponseItem1,
        IoNatsJetstreamApiV1ConsumerCreateResponseItem,
        IoNatsJetstreamApiV1ConsumerCreateResponse1,
    ] = Field(
        ...,
        description="A response from the JetStream $JS.API.CONSUMER.CREATE API",
        title="io.nats.jetstream.api.v1.consumer_create_response",
    )