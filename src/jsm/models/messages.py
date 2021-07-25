from typing import Optional

from pydantic import BaseModel, Field, conint, constr


class Message(BaseModel):
    subject: constr(min_length=1) = Field(  # type: ignore[valid-type]
        ..., description="The subject the message was originally received on"
    )
    seq: conint(ge=0) = Field(  # type: ignore[valid-type]
        ..., description="The sequence number of the message in the Stream"
    )
    data: constr(min_length=0) = Field(  # type: ignore[valid-type]
        ..., description="The base64 encoded payload of the message body"
    )
    time: str = Field(..., description="The time the message was received")
    hdrs: Optional[str] = Field(
        None, description="Base64 encoded headers for the message"
    )
