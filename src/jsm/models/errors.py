from typing import Optional

from pydantic import BaseModel, Field, conint


class IoNatsJetstreamApiV1ErrorItem(BaseModel):
    code: Optional[conint(ge=300, le=699)] = Field(  # type: ignore[valid-type]
        500, description="HTTP like error code in the 300 to 500 range"
    )
    description: Optional[str] = Field(
        None, description="A human friendly description of the error"
    )


class IoNatsJetstreamApiV1ErrorResponse(BaseModel):
    type: str
    error: IoNatsJetstreamApiV1ErrorItem

    def raise_on_error(self) -> None:
        raise IoNatsJetstreamApiV1Exception(self)


class IoNatsJetstreamApiV1Exception(Exception):
    def __init__(self, response: IoNatsJetstreamApiV1ErrorResponse) -> None:
        super().__init__(
            f"Status code={response.error.code} | Description={response.error.description} | Type={response.type}"
        )
        self.__error__ = response.error
        self.__type__ = response.type

    @property
    def code(self) -> Optional[int]:
        return self.__error__.code

    @property
    def description(self) -> Optional[str]:
        return self.__error__.description

    @property
    def type(self) -> str:
        return self.type
