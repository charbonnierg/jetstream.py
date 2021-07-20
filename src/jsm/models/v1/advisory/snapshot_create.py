# generated by datamodel-codegen:
#   filename:  snapshot_create.json
#   timestamp: 2021-07-18T15:28:09+00:00

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, conint


class Client(BaseModel):
    start: Optional[str] = Field(
        None, description="Timestamp when the client connected"
    )
    stop: Optional[str] = Field(
        None, description="Timestamp when the client disconnected"
    )
    host: Optional[str] = Field(
        None, description="The remote host the client is connected from"
    )
    id: Optional[str] = Field(
        None, description="The internally assigned client ID for this connection"
    )
    acc: str = Field(..., description="The account this user logged in to")
    user: Optional[str] = Field(None, description="The clients username")
    name: Optional[str] = Field(
        None, description="The name presented by the client during connection"
    )
    lang: Optional[str] = Field(
        None, description="The programming language library in use by the client"
    )
    ver: Optional[str] = Field(
        None, description="The version of the client library in use"
    )
    rtt: Optional[float] = Field(
        None,
        description="The last known latency between the NATS Server and the Client in nanoseconds",
    )
    server: Optional[str] = Field(
        None, description="The server that the client was connected to"
    )
    cluster: Optional[str] = Field(
        None, description="The cluster name the server is connected to"
    )
    jwt: Optional[str] = Field(None, description="The JWT presented in the connection")
    issuer_key: Optional[str] = Field(
        None,
        description="The public signing key or account identity key used to issue the user",
    )
    name_tag: Optional[str] = Field(
        None, description="The name extracted from the user JWT claim"
    )
    tags: Optional[List[str]] = Field(None, description="Tags extracted from the JWT")


class IoNatsJetstreamAdvisoryV1SnapshotCreate(BaseModel):
    type: str
    id: str = Field(..., description="Unique correlation ID for this event")
    timestamp: str = Field(
        ..., description="The time this event was created in RFC3339 format"
    )
    stream: str = Field(..., description="The name of the Stream being snapshotted")
    blocks: conint(ge=0) = Field(
        ..., description="Approximate number of blocks in the snapshot"
    )
    block_size: conint(ge=1) = Field(
        ..., description="The size, in bytes, of every block"
    )
    client: Client = Field(
        ..., description="Details about the client that connected to the server"
    )
