from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from .base import BaseRequest, BaseResponse, JetstreamModel
from .clusters import Cluster


class AckPolicy(str, Enum):
    """Policies defining how messages should be adcknowledged.

    If an ack is required but is not received within the AckWait window, the message will be redelivered.

    References:
        * Consumers, AckPolicy - [NATS Docs](https://docs.nats.io/jetstream/concepts/consumers#ackpolicy)
    """

    none = "none"
    all = "all"
    explicit = "explicit"


class DeliverPolicy(str, Enum):
    """When a consumer is first created, it can specify where in the stream it wants to start receiving messages.

    This is the DeliverPolicy, and this enumeration defines allowed values.

    References:
        * Consumers, DeliverPolicy/OptStartSeq/OptStartTime - [NATS Docs](https://docs.nats.io/jetstream/concepts/consumers#deliverpolicy-optstartseq-optstarttime)
    """

    all = "all"
    last = "last"
    new = "new"
    last_per_subject = "last_per_subject"
    by_start_sequence = "by_start_sequence"
    by_start_time = "by_start_time"


class ReplayPolicy(Enum):
    """The replay policy applies when the DeliverPolicy is one of:
        * all
        * by_start_sequence
        * by_start_time
    since those deliver policies begin reading the stream at a position other than the end.

    References:
        * Consumers, ReplayPolicy - [NATS Docs](https://docs.nats.io/jetstream/concepts/consumers#replaypolicy)
    """

    instant = "instant"
    original = "original"


class Config(JetstreamModel):
    """Consumer configuration.

    Field descriptions are available in source code.

    References:
        * Consumers - [NATS Docs](https://docs.nats.io/jetstream/concepts/consumers)
    """

    deliver_policy: DeliverPolicy = Field(
        "last",
        description="Specify where in the stream the consumer should start receiving messages",
    )
    ack_policy: AckPolicy = Field(
        "explicit",
        description="How messages should be acknowledged",
    )
    durable_name: Optional[str] = Field(
        None,
        description="A unique name for a durble consumer (by default, a consumer is ephemeral, setting the name make the consumer durable)",
        min_length=1,
        regex=r"^[^.*>]+$",
    )
    deliver_subject: Optional[str] = Field(
        None,
        description="The subject to deliver observed messages. Not allowed for pull subscriptions",
        min_length=1,
    )
    ack_wait: Optional[int] = Field(
        None,
        description="How long (in nanoseconds) to allow messages to remain un-acknowledged before attempting redelivery",
        ge=1,
    )
    max_deliver: Optional[int] = Field(
        None,
        description="The number of times a message will be redelivered to consumers if not acknowledged in time",
    )
    filter_subject: Optional[str] = Field(
        None,
        description="Select a subset of the parent stream subject to receive messages from",
    )
    replay_policy: ReplayPolicy = Field(
        ReplayPolicy.instant,
        description="Specify how messages in the stream will be pushed to the client when deliver_policy is one of 'all', 'by_start_sequence', 'by_start_time'",
    )
    sample_freq: Optional[str] = None
    rate_limit_bps: Optional[int] = Field(
        None,
        description="The rate at which messages will be delivered to clients, expressed in bit per second",
        ge=0,
    )
    max_ack_pending: Optional[int] = Field(
        None,
        description="The maximum number of messages without acknowledgement that can be outstanding, once this limit is reached message delivery will be suspended",
    )
    idle_heartbeat: Optional[int] = Field(
        description="If the Consumer is idle for more than this many nano seconds a empty message with Status header 100 will be sent indicating the consumer is still alive",
        ge=0,
    )
    flow_control: Optional[bool] = Field(
        None,
        description="For push consumers this will regularly send an empty mess with Status header 100 and a reply subject, consumers must reply to these messages to control the rate of message delivery",
    )
    max_waiting: Optional[int] = Field(
        512,
        description="The number of pulls that can be outstanding on a pull consumer, pulls received after this is reached are ignored",
        ge=0,
    )
    ops_start_seq: Optional[int] = Field(
        None,
        description="The sequence to start replay on, ignored if deliver_policy is not start_by_sequence",
    )
    ops_start_time: Optional[int] = Field(
        None,
        description="The sequence to start replay on, ignored if deliver_policy is not start_by_sequence",
    )


class Delivered(JetstreamModel):
    """Last message delivered from this consumer

    Fields descriptions are available in source code.
    """

    consumer_seq: int = Field(
        ...,
        description="The sequence number of the Consumer",
        ge=0,
    )
    stream_seq: int = Field(
        ...,
        description="The sequence number of the Stream",
        ge=0,
    )


class AckFloor(JetstreamModel):
    """Highest contiguous acknowledged message

    Fields descriptions are available in source code.
    """

    consumer_seq: int = Field(
        ...,
        description="The sequence number of the Consumer",
        ge=0,
    )
    stream_seq: int = Field(
        ...,
        description="The sequence number of the Stream",
        ge=0,
    )


class IoNatsJetstreamApiV1ConsumerItem(JetstreamModel):
    """View of a stream"""

    stream_name: str = Field(
        ...,
        description="The Stream the consumer belongs to",
    )
    name: str = Field(
        ...,
        description="A unique name for the consumer, either machine generated or the durable name",
    )
    config: Config = Field(
        ...,
        description="Stream config",
    )
    created: datetime = Field(
        ...,
        description="Stream creation timestamp",
    )
    delivered: Delivered = Field(
        ...,
        description="The last message delivered from this Consumer",
    )
    ack_floor: AckFloor = Field(
        ...,
        description="The highest contiguous acknowledged message",
    )
    num_ack_pending: int = Field(
        ...,
        description="The number of messages pending acknowledgement",
        ge=0,
    )
    num_redelivered: int = Field(
        ...,
        description="The number of redeliveries that have been performed",
        ge=0,
    )
    num_waiting: int = Field(
        ...,
        description="The number of pull consumers waiting for messages",
        ge=0,
    )
    num_pending: int = Field(
        ...,
        description="The number of messages left unconsumed in this Consumer",
        ge=0,
    )
    cluster: Optional[Cluster] = None


class IoNatsJetstreamApiV1ConsumerCreateResponse(
    IoNatsJetstreamApiV1ConsumerItem, BaseResponse
):
    """Reply from `$JS.API.CONSUMER.CREATE.*.*`"""

    pass


class IoNatsJetstreamApiV1ConsumerInfoResponse(
    IoNatsJetstreamApiV1ConsumerItem, BaseResponse
):
    """Reply from `$JS.API.CONSUMER.INFO.*.*`"""

    pass


class IoNatsJetstreamApiV1ConsumerDeleteResponse(BaseResponse):
    """Reply from `$JS.API.CONSUMER.DELETE.*.*`"""

    success: bool


class IoNatsJetstreamApiV1ConsumerListResponse(BaseResponse):
    """Reply from `$JS.API.CONSUMER.LIST.*`"""

    total: int = Field(
        ...,
        description="Total number of consumers without regard to offset or limit",
        ge=0,
    )
    offset: int = Field(
        ...,
        description="Number of consumers to skip",
        ge=0,
    )
    limit: int = Field(
        ...,
        description="Maximum number of consumers to return",
        ge=0,
    )
    consumers: List[IoNatsJetstreamApiV1ConsumerItem] = Field(
        [],
        description="A list of consumer items",
    )


class IoNatsJetstreamApiV1ConsumerNamesResponse(BaseResponse):
    """Reply from `$JS.API.CONSUMER.NAMES.*`"""

    total: int = Field(
        ...,
        description="Total number of consumers without regard to offset or limit",
        ge=0,
    )
    offset: int = Field(
        ...,
        description="Number of consumers to skip",
        ge=0,
    )
    limit: int = Field(
        ...,
        description="Maximum number of consumers to return",
        ge=0,
    )
    consumers: List[IoNatsJetstreamApiV1ConsumerItem] = Field(
        [],
        description="A list of consumer names",
    )


class IoNatsJetstreamApiV1ConsumerCreateRequest(BaseRequest):
    """Request options for `$JS.API.CONSUMER.CREATE.*.*`"""

    stream_name: str = Field(
        ...,
        description="The name of the stream to create the consumer for",
    )
    config: Config = Field(
        ...,
        description="The consumer configuration",
    )


class IoNatsJetstreamApiV1ConsumerListRequest(BaseRequest):
    """Request options for `$JS.API.CONSUMER.LIST.*`"""

    offset: Optional[int] = Field(
        None,
        description="Number of consumers to skip",
        ge=0,
    )


class IoNatsJetstreamApiV1ConsumerNamesRequest(BaseRequest):
    """Request options for `$JS.API.CONSUMER.NAMES.*`"""

    offset: Optional[int] = Field(
        None,
        description="Number of consumers to skip",
        ge=0,
    )
    subject: Optional[str] = Field(
        None,
        description="Filter the names to those consuming messages matching this subject or wildcard",
        min_length=1,
    )
