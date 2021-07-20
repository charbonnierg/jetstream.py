# generated by datamodel-codegen:
#   filename:  consumer_quorum_lost.json
#   timestamp: 2021-07-18T15:28:11+00:00

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, conint


class Replicas(BaseModel):
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


class IoNatsJetstreamAdvisoryV1ConsumerQuorumLost(BaseModel):
    type: str
    id: str = Field(..., description="Unique correlation ID for this event")
    timestamp: str = Field(
        ..., description="The time this event was created in RFC3339 format"
    )
    stream: str = Field(
        ..., description="The name of the Stream the Consumer belongs to"
    )
    consumer: str = Field(..., description="The name of the Consumer that lost quorum")
    replicas: Replicas