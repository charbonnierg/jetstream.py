# generated by datamodel-codegen:
#   filename:  stream_remove_peer_request.json
#   timestamp: 2021-07-18T15:27:51+00:00

from __future__ import annotations

from pydantic import BaseModel, Field, constr


class IoNatsJetstreamApiV1StreamRemovePeerRequest(BaseModel):
    peer: constr(min_length=1) = Field(
        ..., description="Server name of the peer to remove"
    )