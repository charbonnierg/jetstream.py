from __future__ import annotations

from pydantic import BaseModel, Field, conint

from .base import IoNatsJetstreamApiV1ResponseItem


class Limits(BaseModel):
    max_memory: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="The maximum amount of Memory storage Stream Messages may consume",
    )
    max_storage: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ...,
        description="The maximum amount of File storage Stream Messages may consume",
    )
    max_streams: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ..., description="The maximum number of Streams an account can create"
    )
    max_consumers: conint(ge=-1) = Field(  # type: ignore[valid-type]
        ..., description="The maximum number of Consumer an account can create"
    )


class Api(BaseModel):
    total: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Total number of API requests received for this account"
    )
    errors: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="API requests that resulted in an error response"
    )


class IoNatsJetstreamApiV1AccountInfoResponse(IoNatsJetstreamApiV1ResponseItem):
    memory: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="Memory Storage being used for Stream Message storage"
    )
    storage: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="File Storage being used for Stream Message storage"
    )
    streams: conint(ge=0) = Field(..., description="Number of active Streams")  # type: ignore[valid-type]
    consumers: conint(ge=0) = Field(..., description="Number of active Consumers")  # type: ignore[valid-type]
    limits: Limits
    api: Api
