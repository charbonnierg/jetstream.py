# generated by datamodel-codegen:
#   filename:  stream_leader_stepdown_response.json
#   timestamp: 2021-07-18T15:27:45+00:00

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field, conint


class IoNatsJetstreamApiV1StreamLeaderStepdownResponse1(BaseModel):
    type: Optional[str] = None


class Error(BaseModel):
    code: conint(ge=300, le=699) = Field(
        ..., description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1StreamLeaderStepdownResponseItem(BaseModel):
    error: Error


class IoNatsJetstreamApiV1StreamLeaderStepdownResponseItem1(BaseModel):
    success: bool = Field(..., description="If the leader successfully stood down")


class IoNatsJetstreamApiV1StreamLeaderStepdownResponse(BaseModel):
    __root__: Union[
        IoNatsJetstreamApiV1StreamLeaderStepdownResponse1,
        IoNatsJetstreamApiV1StreamLeaderStepdownResponseItem,
        IoNatsJetstreamApiV1StreamLeaderStepdownResponseItem1,
    ] = Field(
        ...,
        description="A response from the JetStream $JS.API.STREAM.LEADER.STEPDOWN API",
        title="io.nats.jetstream.api.v1.stream_leader_stepdown_response",
    )