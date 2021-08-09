from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from .utils import convert_datetime_to_iso_8601_with_z_suffix


class JetstreamModel(BaseModel):
    class Config:
        json_encoder = {datetime: convert_datetime_to_iso_8601_with_z_suffix}


class BaseRequest(JetstreamModel):
    pass


class BaseResponse(JetstreamModel):
    type: str

    def raise_on_error(self) -> None:
        """Do not return an error by default."""
        return
