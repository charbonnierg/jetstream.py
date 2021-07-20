# generated by datamodel-codegen:
#   filename:  consumer_list_response.json
#   timestamp: 2021-07-18T15:27:48+00:00

from __future__ import annotations

from typing import List

from pydantic import BaseModel, conint

from .consumer_info_response import IoNatsJetstreamApiV1ConsumerInfoResponseItem


class IoNatsJetstreamApiV1ConsumerListResponse(BaseModel):
    total: conint(ge=0)
    offset: conint(ge=0)
    limit: conint(ge=0)
    type: str
    consumers: List[IoNatsJetstreamApiV1ConsumerInfoResponseItem] = []
