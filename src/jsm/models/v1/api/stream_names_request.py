# generated by datamodel-codegen:
#   filename:  stream_names_request.json
#   timestamp: 2021-07-18T15:27:57+00:00

from __future__ import annotations

from pydantic import BaseModel, conint


class IoNatsJetstreamApiV1StreamNamesRequest(BaseModel):
    offset: conint(ge=0)