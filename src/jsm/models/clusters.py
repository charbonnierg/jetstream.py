from typing import List, Optional

from pydantic import BaseModel, Field, conint


class Replica(BaseModel):
    name: str = Field(..., description="The server name of the peer")
    current: bool = Field(
        ..., description="Indicates if the server is up to date and synchronised"
    )
    active: float = Field(..., description="Nanoseconds since this peer was last seen")
    offline: Optional[bool] = Field(
        False, description="Indicates the node is considered offline by the group"
    )
    lag: Optional[conint(ge=0)] = Field(  # type: ignore[valid-type]
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
