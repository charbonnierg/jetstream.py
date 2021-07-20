# generated by datamodel-codegen:
#   filename:  stream_msg_get_response.json
#   timestamp: 2021-07-18T15:28:00+00:00

from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel, Field, conint, constr


class IoNatsJetstreamApiV1StreamMsgGetResponse1(BaseModel):
    type: str


class Error(BaseModel):
    code: conint(ge=300, le=699) = Field(
        ..., description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1StreamMsgGetResponseItem(BaseModel):
    error: Error


class Message(BaseModel):
    subject: constr(min_length=1) = Field(
        ..., description="The subject the message was originally received on"
    )
    seq: conint(ge=0) = Field(
        ..., description="The sequence number of the message in the Stream"
    )
    data: constr(min_length=0) = Field(
        ..., description="The base64 encoded payload of the message body"
    )
    time: str = Field(..., description="The time the message was received")
    hdrs: Optional[str] = Field(
        None, description="Base64 encoded headers for the message"
    )


class IoNatsJetstreamApiV1StreamMsgGetResponseItem1(BaseModel):
    message: Message


class IoNatsJetstreamApiV1StreamMsgGetResponse(BaseModel):
    __root__: Union[
        IoNatsJetstreamApiV1StreamMsgGetResponse1,
        IoNatsJetstreamApiV1StreamMsgGetResponseItem,
        IoNatsJetstreamApiV1StreamMsgGetResponseItem1,
    ] = Field(
        ...,
        description="A response from the JetStream $JS.API.STREAM.MSG.GET API",
        title="io.nats.jetstream.api.v1.stream_msg_get_response",
    )
