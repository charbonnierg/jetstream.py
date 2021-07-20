# generated by datamodel-codegen:
#   filename:  meta_server_remove_response.json
#   timestamp: 2021-07-18T15:27:40+00:00

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field, conint


class IoNatsJetstreamApiV1MetaServerRemoveResponse1(BaseModel):
    type: Optional[str] = None


class Error(BaseModel):
    code: conint(ge=300, le=699) = Field(
        ..., description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1MetaServerRemoveResponseItem(BaseModel):
    error: Error


class IoNatsJetstreamApiV1MetaServerRemoveResponseItem1(BaseModel):
    success: bool = Field(..., description="If the peer was successfully removed")


class IoNatsJetstreamApiV1MetaServerRemoveResponse(BaseModel):
    __root__: Union[
        IoNatsJetstreamApiV1MetaServerRemoveResponse1,
        IoNatsJetstreamApiV1MetaServerRemoveResponseItem,
        IoNatsJetstreamApiV1MetaServerRemoveResponseItem1,
    ] = Field(
        ...,
        description="A response from the JetStream $JS.API.SERVER.REMOVE API",
        title="io.nats.jetstream.api.v1.meta_server_remove_response",
    )
