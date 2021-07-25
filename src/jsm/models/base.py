from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, Union

from pydantic import BaseModel
from pydantic.generics import GenericModel

from .errors import IoNatsJetstreamApiV1ErrorResponse, IoNatsJetstreamApiV1Exception

ItemT = TypeVar("ItemT", bound="IoNatsJetstreamApiV1ResponseItem")


class MsgProtocol(Protocol):
    @property
    def data(self) -> Any:
        ...


class IoNatsJetstreamApiV1ResponseItem(BaseModel):
    type: str

    def raise_on_error(self) -> None:
        """Raise an error if the response if a JetstreamApiError."""
        if hasattr(self, "error") and self.error:
            raise IoNatsJetstreamApiV1Exception(self)


class IoNatsJetstreamApiV1Response(GenericModel, Generic[ItemT]):
    __root__: Union[IoNatsJetstreamApiV1ErrorResponse, ItemT]

    def raise_on_error(self) -> None:
        """Raise an error if the response if a JetstreamApiError."""
        if isinstance(self.__root__, IoNatsJetstreamApiV1ErrorResponse):
            raise IoNatsJetstreamApiV1Exception(self.__root__)
