from __future__ import annotations

from pydantic import Field

from .base import BaseResponse, JetstreamModel


class Limits(JetstreamModel):
    """Account limits

    References:
        * Multi-tenancy & Resource Mgmt, NATS Docs - https://docs.nats.io/jetstream/resource_management
    """

    max_memory: int = Field(
        ...,
        description="The maximum amount of Memory storage Stream Messages may consume",
        ge=-1,
    )
    max_storage: int = Field(
        ...,
        description="The maximum amount of File storage Stream Messages may consume",
        ge=-1,
    )
    max_streams: int = Field(
        ...,
        description="The maximum number of Streams an account can create",
        ge=-1,
    )
    max_consumers: int = Field(
        ...,
        description="The maximum number of Consumer an account can create",
        ge=-1,
    )


class Api(JetstreamModel):
    """API stats"""

    total: int = Field(
        ...,
        description="Total number of API requests received for this account",
        ge=0,
    )
    errors: int = Field(
        ...,
        description="API requests that resulted in an error response",
        ge=0,
    )


class IoNatsJetstreamApiV1AccountInfoResponse(BaseResponse):
    """Account information

    References:
        * Account Information, NATS Docs - https://docs.nats.io/jetstream/administration/account#account-information
    """

    memory: int = Field(
        ...,
        description="Memory Storage being used for Stream Message storage",
        ge=0,
    )
    storage: int = Field(
        ...,
        description="File Storage being used for Stream Message storage",
        ge=0,
    )
    streams: int = Field(
        ...,
        description="Number of active Streams",
        ge=0,
    )
    consumers: int = Field(
        ...,
        description="Number of active Consumers",
        ge=0,
    )
    limits: Limits = Field(..., description="Account limits")
    api: Api = Field(..., description="API requests count")
