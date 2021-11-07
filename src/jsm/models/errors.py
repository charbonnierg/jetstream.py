# Copyright 2021 - Guillaume Charbonnier
# Licensed under the Apache License, Version 2.0 (the "License");
# http://www.apache.org/licenses/LICENSE-2.0
from pydantic import Field

from jsm.api.errors import JetStreamError

from .base import BaseResponse, JetstreamModel


class IoNatsJetstreamApiV1ErrorItem(JetstreamModel):
    """An error as found in a JetStream API response"""

    code: int = Field(
        500, description="HTTP like error code in the 300 to 500 range", ge=300, le=699
    )
    description: str = Field(
        "", description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1ErrorResponse(BaseResponse):
    """A JetStream API error response"""

    error: IoNatsJetstreamApiV1ErrorItem

    def raise_on_error(self) -> None:
        """Raise an error using instance attributes (description, code, type)"""
        raise JetStreamError(self.error.description, self.error.code, self.type)
