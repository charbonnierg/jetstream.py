# generated by datamodel-codegen:
#   filename:  stream_template_delete_response.json
#   timestamp: 2021-07-18T15:27:50+00:00

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field, conint


class IoNatsJetstreamApiV1StreamTemplateDeleteResponse1(BaseModel):
    type: str


class Error(BaseModel):
    code: conint(ge=300, le=699) = Field(
        ..., description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1StreamTemplateDeleteResponseItem(BaseModel):
    error: Error


class IoNatsJetstreamApiV1StreamTemplateDeleteResponseItem1(BaseModel):
    success: bool


class IoNatsJetstreamApiV1StreamTemplateDeleteResponse(BaseModel):
    __root__: Union[
        IoNatsJetstreamApiV1StreamTemplateDeleteResponse1,
        IoNatsJetstreamApiV1StreamTemplateDeleteResponseItem,
        IoNatsJetstreamApiV1StreamTemplateDeleteResponseItem1,
    ] = Field(
        ...,
        description="A response from the JetStream $JS.API.STREAM.TEMPLATE.DELETE API",
        title="io.nats.jetstream.api.v1.stream_template_delete_response",
    )
